"""
Module Contract
===============

Purpose:
    Concrete implementation of BaseLLMProvider for the company's internal
    LLM inference endpoint. Streams chunked JSON responses and reconstructs
    the complete plain-text output.

Consumes:
    - Pre-rendered string prompts from PromptBuilder via LLMService.
    - Configuration injected at construction time (endpoint, model, temperature, timeout).

Produces:
    - A single reconstructed plain-text string identical in contract to GeminiProvider.

Does NOT:
    - Call os.getenv() or import config.settings.
    - Import pandas, ReviewResult, or any analytics module.
    - Return raw JSON or dict structures.
    - Expose requests exceptions to its callers.
    - Log prompt contents, URLs containing credentials, or API tokens.

Downstream Consumers:
    - LLMService (provider-agnostic orchestration layer)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Iterator

import requests
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    Timeout,
)

from llm.llm_provider import (
    BaseLLMProvider,
    LLMEmptyResponseError,
    LLMNetworkError,
    LLMProviderError,
)

logger = logging.getLogger(__name__)


class CompanyProvider(BaseLLMProvider):
    """
    Concrete BaseLLMProvider implementation for the company's internal Ollama-compatible
    streaming inference endpoint.

    The endpoint contract is:
        POST <endpoint>
        Body: { "model": str, "prompt": str, "temperature": float }
        Response: Newline-delimited JSON stream
        Each chunk: { "response": str, "done": bool, ... }

    The provider accumulates all streamed chunks and returns a single plain-text
    string. It is fully transparent to the LLMService layer above it.
    """

    def __init__(
        self,
        endpoint: str,
        model: str,
        temperature: float,
        timeout: int,
    ) -> None:
        """
        Initialize the CompanyProvider using strict dependency injection.

        Args:
            endpoint: The base URL of the company's internal inference API.
            model: The model identifier string (e.g., 'llama3.1:8b').
            temperature: Sampling temperature controlling generation randomness.
            timeout: Request timeout in seconds applied to the streaming connection.

        Raises:
            LLMProviderError: If the endpoint string is missing or blank.
        """
        super().__init__()

        if not endpoint or not endpoint.strip():
            raise LLMProviderError(
                "CompanyProvider requires a valid endpoint URL. "
                "Ensure COMPANY_LLM_ENDPOINT is set in .env."
            )

        self._endpoint = endpoint.strip()
        self._model = model
        self._temperature = temperature
        self._timeout = timeout

        logger.info(
            "[%s] Initialized. Model: %s | Temperature: %.2f | Timeout: %ds",
            self.provider_name,
            self._model,
            self._temperature,
            self._timeout,
        )

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """Return the canonical name identifying this provider."""
        return "Company"

    def generate(self, prompt: str) -> str:
        """
        Submit a prompt to the company's internal inference endpoint and return
        the fully reconstructed plain-text response.

        The endpoint streams newline-delimited JSON. Each line is a chunk
        containing a partial ``response`` string and a ``done`` boolean flag.
        This method accumulates all chunks and returns the complete text.

        Args:
            prompt: The complete, pre-rendered prompt string prepared by LLMService.

        Returns:
            The fully reconstructed plain-text response as a single string.

        Raises:
            ValueError: If the prompt is empty or whitespace-only.
            LLMNetworkError: On connection failures or request timeouts.
            LLMProviderError: On HTTP errors, invalid stream format, or unexpected
                failures that do not map to a more specific domain exception.
            LLMEmptyResponseError: If the API returns a successful response but
                no text content is accumulated across all chunks.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        logger.info(
            "[%s] Submitting prompt to model '%s'.",
            self.provider_name,
            self._model,
        )

        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "temperature": self._temperature,
        }

        started_at = time.monotonic()

        try:
            response = requests.post(
                self._endpoint,
                json=payload,
                stream=True,
                timeout=self._timeout,
            )
            response.raise_for_status()

            logger.info("[%s] Receiving streamed response.", self.provider_name)

            result = self._accumulate_stream(response.iter_lines())

        except ReadTimeout as exc:
            logger.error(
                "[%s] Read timed out after %ds waiting for streamed data.",
                self.provider_name,
                self._timeout,
            )
            raise LLMNetworkError(
                f"Read timeout while streaming from company endpoint after {self._timeout}s."
            ) from exc

        except Timeout as exc:
            logger.error(
                "[%s] Request timed out after %ds.",
                self.provider_name,
                self._timeout,
            )
            raise LLMNetworkError(
                f"Request to company endpoint timed out after {self._timeout}s."
            ) from exc

        except RequestsConnectionError as exc:
            logger.error(
                "[%s] Connection error: unable to reach endpoint.",
                self.provider_name,
            )
            raise LLMNetworkError(
                "Could not connect to the company inference endpoint. "
                "Verify the service is reachable from this host."
            ) from exc

        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            logger.error(
                "[%s] HTTP error %s returned by endpoint.",
                self.provider_name,
                status_code,
            )
            raise LLMProviderError(
                f"Company endpoint returned HTTP {status_code}."
            ) from exc

        except LLMProviderError:
            # Re-raise already-mapped domain exceptions produced inside _accumulate_stream
            raise

        except Exception as exc:
            logger.error(
                "[%s] Unexpected error during generation: %s",
                self.provider_name,
                str(exc),
                exc_info=True,
            )
            raise LLMProviderError(
                f"Unexpected failure during company LLM generation: {exc}"
            ) from exc

        elapsed = time.monotonic() - started_at

        if not result.strip():
            raise LLMEmptyResponseError(
                "Company endpoint returned a successful response but "
                "no text was accumulated across all stream chunks."
            )

        logger.info(
            "[%s] Generation completed successfully in %.2fs.",
            self.provider_name,
            elapsed,
        )
        return result.strip()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _accumulate_stream(self, lines: Iterator[bytes]) -> str:
        """
        Consume a newline-delimited JSON stream and reconstruct the full text.

        Each line must be a JSON object with:
            - ``"response"`` (str): The text fragment for this chunk.
            - ``"done"`` (bool): If ``True``, streaming has completed and
              iteration stops immediately.

        Args:
            lines: An iterator of raw byte lines produced by ``response.iter_lines()``.

        Returns:
            The fully accumulated plain-text string across all received chunks.

        Raises:
            LLMProviderError: If any line cannot be decoded as valid JSON, indicating
                an unexpected or malformed endpoint response format.
        """
        accumulated: list[str] = []

        for raw_line in lines:
            if not raw_line:
                # iter_lines() yields empty bytes for blank lines; skip them.
                continue

            try:
                chunk: dict = json.loads(raw_line)
            except (JSONDecodeError, ValueError) as exc:
                logger.error(
                    "[%s] Failed to decode stream chunk as JSON.",
                    self.provider_name,
                )
                raise LLMProviderError(
                    "Received an invalid JSON chunk from the company endpoint. "
                    "The streaming response format may have changed."
                ) from exc

            fragment = chunk.get("response", "")
            if fragment:
                accumulated.append(fragment)

            if chunk.get("done"):
                break

        return "".join(accumulated)
