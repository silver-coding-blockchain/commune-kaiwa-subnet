import asyncio
import concurrent.futures
import random
import threading
import time

import uvicorn
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
from communex.module.client import ModuleClient
from communex.types import Ss58Address
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from loguru import logger
from substrateinterface import Keypair

from kaiwa_subnet.base import BaseValidator
from kaiwa_subnet.base.utils import (
    get_netuid,
)
from kaiwa_subnet.base.schema import ChatCompletionRequest
from kaiwa_subnet.gateway._config import GatewaySettings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Gateway(BaseValidator):
    def __init__(self, key: Keypair, settings: GatewaySettings) -> None:
        super().__init__()
        self.settings = settings or GatewaySettings()
        self.c_client = CommuneClient(
            get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.key = key
        self.netuid = get_netuid(self.c_client)
        self.call_timeout = self.settings.call_timeout
        self.top_miners = {}
        self.validators: dict[int, tuple[list[str], Ss58Address]] = {}

        self.sync()

    def sync(self):
        logger.info("fetching top miners...")
        self.top_miners = self.get_top_weights_miners(16)
        logger.info("fetched miners: {}", self.top_miners)

        logger.info("fetching validators...")
        self.validators = self.get_validators()
        logger.info("fetched validators: {}", self.validators)

    def sync_loop(self):
        while True:
            time.sleep(60)
            self.sync()

    def start_sync_loop(self):
        logger.info("start sync loop")
        self._loop_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self._loop_thread.start()

    def get_top_miners(self):
        return self.top_miners

    def get_validator_weights_history(self, validator_info):
        try:
            connection, validator_key = validator_info
            module_ip, module_port = connection
            logger.debug(f"Call {validator_key} - {module_ip}:{module_port}")
            client = ModuleClient(host=module_ip, port=int(module_port), key=self.key)
            result = asyncio.run(
                client.call(
                    fn="get_weights_history",
                    target_key=validator_key,
                    params={},
                    timeout=10,
                )
            )
        except Exception:
            return None
        return result

    def get_all_validators_weights_history(self):
        rv = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            it = executor.map(
                self.get_validator_weights_history, self.validators.values()
            )
            validator_answers = [*it]

        for uid, response in zip(self.validators.keys(), validator_answers):
            rv.append({"uid": uid, "weights_history": response})
        return rv


@app.post(
    "/chat",
)
async def chat(req: ChatCompletionRequest):
    req.top_logprobs = None
    top_miners = list(app.m.get_top_miners().values())
    top_miners = random.sample(top_miners, min(len(top_miners), 5))
    tasks = [
        app.m.get_miner_generation_async(miner_info, req) for miner_info in top_miners
    ]
    for future in asyncio.as_completed(tasks):
        result = await future
        if result:
            logger.debug(result)
            return result
    return Response()


@app.get("/weights")
async def get_all_validators_weights_history():
    return app.m.get_all_validators_weights_history()


if __name__ == "__main__":
    settings = GatewaySettings(
        host="0.0.0.0",
        port=9009,
        use_testnet=True,
    )
    app.m = Gateway(key=classic_load_key("kaiwa-validator"), settings=settings)
    app.m.start_sync_loop()
    uvicorn.run(app=app, host=settings.host, port=settings.port)
