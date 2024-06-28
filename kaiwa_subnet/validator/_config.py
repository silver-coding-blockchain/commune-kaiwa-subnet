from kaiwa_subnet.base.config import KaiwaBaseSettings
from typing import List


class ValidatorSettings(KaiwaBaseSettings):
    host: str = "0.0.0.0"
    port: int = 0
    iteration_interval: int = 300
