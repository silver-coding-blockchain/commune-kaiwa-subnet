from kaiwa_subnet.base.config import KaiwaBaseSettings
from typing import List


class GatewaySettings(KaiwaBaseSettings):
    host: str
    port: int
