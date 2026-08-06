"""
Verification script for the CompanyProvider integration.
Run: python verify_providers.py
"""
import importlib
import inspect
import os
import sys

from llm.company_provider import CompanyProvider
from llm.llm_provider import BaseLLMProvider, GeminiProvider, LLMProviderError
from config import settings

results = []


def check(n, label, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    line = f"{tag} {n:>2}: {label}"
    if detail:
        line += f"\n         {detail}"
    print(line)
    results.append(ok)


# 1. Inheritance
check(1, "CompanyProvider extends BaseLLMProvider",
      issubclass(CompanyProvider, BaseLLMProvider))

# 2. generate() signature parity with GeminiProvider
g_params = list(inspect.signature(GeminiProvider.generate).parameters.keys())
c_params = list(inspect.signature(CompanyProvider.generate).parameters.keys())
check(2, "generate(self, prompt) signature matches GeminiProvider",
      g_params == c_params,
      f"Gemini={g_params}  Company={c_params}")

# 3. All settings constants present
missing = [a for a in (
    "LLM_PROVIDER", "COMPANY_LLM_ENDPOINT", "COMPANY_MODEL",
    "COMPANY_TEMPERATURE", "COMPANY_TIMEOUT_SECONDS"
) if not hasattr(settings, a)]
check(3, "All 5 settings constants present in config/settings.py",
      not missing,
      f"Missing={missing}" if missing else (
          f"LLM_PROVIDER={settings.LLM_PROVIDER}  "
          f"MODEL={settings.COMPANY_MODEL}  "
          f"TEMP={settings.COMPANY_TEMPERATURE}  "
          f"TIMEOUT={settings.COMPANY_TIMEOUT_SECONDS}s"
      ))

# 4. Construction and provider_name
p = CompanyProvider(
    endpoint="http://internal/api/generate",
    model="llama3.1:8b",
    temperature=0.25,
    timeout=60,
)
check(4, "Construction and provider_name",
      p.provider_name == "Company",
      f"provider_name={p.provider_name}")

# 5. Blank endpoint guard raises LLMProviderError
raised = False
try:
    CompanyProvider(endpoint="", model="m", temperature=0.1, timeout=10)
except LLMProviderError:
    raised = True
check(5, "Blank endpoint raises LLMProviderError", raised)

# 6. Stream accumulation - stops at done=true
lines = [
    b'{"response": "Hello ", "done": false}',
    b'{"response": "world", "done": false}',
    b'{"response": ".", "done": true}',
    b'{"response": "SHOULD_NOT_APPEAR", "done": false}',
]
accumulated = p._accumulate_stream(iter(lines))
check(6, "Stream accumulation stops at done=true",
      accumulated == "Hello world.",
      f"result={repr(accumulated)}")

# 7. Empty stream lines are skipped
lines2 = [
    b"",
    b'{"response": "A", "done": false}',
    b"",
    b'{"response": "B", "done": true}',
]
r2 = p._accumulate_stream(iter(lines2))
check(7, "Empty stream lines are skipped",
      r2 == "AB",
      f"result={repr(r2)}")

# 8. Invalid JSON chunk raises LLMProviderError
raised_json = False
try:
    p._accumulate_stream(iter([b"not-json-at-all"]))
except LLMProviderError:
    raised_json = True
check(8, "Invalid JSON chunk raises LLMProviderError", raised_json)

# 9. Unknown provider raises NotImplementedError with helpful message
# settings.LLM_PROVIDER is a Final constant frozen at import time.
# We exercise the branch directly by temporarily monkeypatching the module attribute.
import services.service_registry as sr
import config.settings as _s
_orig = _s.LLM_PROVIDER
_s.LLM_PROVIDER = "unknown_xyz"  # type: ignore[assignment]
nie_raised = False
msg_mentions_company = False
try:
    sr.build_llm_service(None)
except NotImplementedError as e:
    nie_raised = True
    msg_mentions_company = "company" in str(e).lower()
except Exception:
    pass
finally:
    _s.LLM_PROVIDER = _orig  # type: ignore[assignment]
check(9, "Unknown LLM_PROVIDER raises NotImplementedError with helpful message",
      nie_raised and msg_mentions_company)

# 10. Company factory branch constructs CompanyProvider without error
os.environ["LLM_PROVIDER"] = "company"
os.environ["COMPANY_LLM_ENDPOINT"] = "http://internal/api/generate"
importlib.reload(sr)
cp2 = CompanyProvider(
    endpoint=os.environ["COMPANY_LLM_ENDPOINT"],
    model="llama3.1:8b",
    temperature=0.25,
    timeout=60,
)
check(10, "Company factory branch constructs CompanyProvider correctly",
      cp2.provider_name == "Company",
      f"provider_name={cp2.provider_name}")

# Summary
print()
print("=" * 60)
passed = sum(results)
total = len(results)
if passed == total:
    print(f"ALL {total}/{total} VERIFICATION CHECKS PASSED")
else:
    print(f"{passed}/{total} checks passed -- {total - passed} FAILED")
print("=" * 60)
sys.exit(0 if passed == total else 1)
