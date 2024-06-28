from kaiwa_subnet.base.config import KaiwaBaseSettings
from typing import List


class MinerSettings(KaiwaBaseSettings):
    host: str
    port: int
