from enum import Enum

class Environment(Enum):
    DEV = "DEV"
    STAGE = "STAGE"
    PROD = "PROD"
    TEST = "TEST"

class ExecutionMode(Enum):
    INTERACTIVE = "INTERACTIVE"
    BATCH = "BATCH"
    API = "API"
    SYSTEM = "SYSTEM"
