import asyncio
import time
from functools import partial
from collections import deque
from datetime import datetime
import threading
import traceback
import random

from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
from communex.module.module import Module
from loguru import logger
from substrateinterface import Keypair

from kaiwa_subnet.base import BaseValidator
from kaiwa_subnet.base.utils import get_netuid
from kaiwa_subnet.validator._config import ValidatorSettings
from kaiwa_subnet.validator.dataset import ValidationDataset
from kaiwa_subnet.validator.utils import normalize_score, weight_score
from kaiwa_subnet.validator.embed import EmbeddingModel
from kaiwa_subnet.base.infer import InferenceEngine
from kaiwa_subnet.base.schema import ChatCompletionRequest
from communex.module.module import Module, endpoint
from typing import List
from pydantic import BaseModel


class WeightHistory(BaseModel):
    time: datetime
    data: List


class Validator(BaseValidator, Module):
    def __init__(self, key: Keypair, settings: ValidatorSettings | None = None) -> None:
        super().__init__()
        super(BaseValidator, self).__init__()
        self.settings = settings or ValidatorSettings()
        self.key = key
        self.netuid = get_netuid(self.c_client)
        self.model = InferenceEngine(settings=settings)
        self.dataset = ValidationDataset()
        self.call_timeout = self.settings.call_timeout
        self.weights_histories = deque(maxlen=10)
        self.embed = EmbeddingModel()

    @property
    def c_client(self):
        return CommuneClient(get_node_url(use_testnet=self.settings.use_testnet))

    async def validate_step(self):
        score_dict = dict()
        duration_dict = dict()
        modules_info = self.get_queryable_miners()

        input = self.get_validate_input()
        logger.debug("input:", input)
        futures = []
        for miner_info in modules_info.values():
            future = asyncio.create_task(
                self.get_miner_generation_with_elapsed(
                    input=input, miner_info=miner_info
                )
            )
            futures.append(future)
        miner_answers = await asyncio.gather(*futures)
        vali_answer = await self.model.chat(input=input)
        vali_answer_embed = self.embed.embed(
            vali_answer["choices"][0]["message"]["content"]
        )
        for uid, miner_response in zip(modules_info.keys(), miner_answers):
            miner_answer, elapsed = miner_response
            if not miner_answer:
                logger.debug(f"Skipping miner {uid}: no answer")
                continue
            try:
                miner_answer_embed = self.embed.embed(
                    miner_answer["choices"][0]["message"]["content"]
                )
            except Exception as e:
                print(e)
                continue
            score = self.embed.similarity(miner_answer_embed, vali_answer_embed)
            if score == 0:
                logger.debug(f"Skipping miner {uid}: score is 0")
                continue
            logger.debug(f"uid {uid}, score: {score}, elapsed time: {elapsed}")
            score_dict[uid] = score
            duration_dict[uid] = elapsed

        if not score_dict:
            logger.info("score_dict empty, skip set weights")
            return

        normalized_scores = normalize_score(score_dict, duration_dict)
        weighted_scores = weight_score(normalized_scores)

        weight_data = list(
            zip(
                weighted_scores.keys(),
                score_dict.values(),
                duration_dict.values(),
                normalized_scores.values(),
                weighted_scores.values(),
            )
        )
        logger.debug("scores: {}", weight_data)
        self.weights_histories.append(
            WeightHistory(
                time=datetime.now(),
                data=weight_data,
            )
        )

        weighted_scores = {k: v for k, v in weighted_scores.items() if v > 0}
        if not weighted_scores:
            logger.info("weighted_scores empty, skip set weights")
            return
        try:
            uids = list(weighted_scores.keys())
            weights = list(weighted_scores.values())
            logger.info("Setting weights for {count} uids", count=len(uids))
            logger.debug(f"Setting weights for the following uids: {weighted_scores}")
            self.c_client.vote(
                key=self.key, uids=uids, weights=weights, netuid=self.netuid
            )
        except Exception as e:
            logger.error(e)

    def get_validate_input(self) -> ChatCompletionRequest:
        return ChatCompletionRequest(
            model=self.settings.model,
            messages=[{"role": "user", "content": self.dataset.random_prompt()}],
            seed=random.randint(0, 20000000),
            temperature=0,
            top_logprobs=None,
            top_k=1,
        )

    def validation_loop(self) -> None:
        settings = self.settings
        while True:
            try:
                logger.info(f"run validation loop")
                start_time = time.time()
                asyncio.run(self.validate_step())
                elapsed = time.time() - start_time
                if elapsed < settings.iteration_interval:
                    sleep_time = settings.iteration_interval - elapsed
                    logger.info(f"Sleeping for {sleep_time}")
                    time.sleep(sleep_time)
            except Exception as e:
                print(traceback.format_exc())

    def start_validation_loop(self):
        logger.info("start sync loop")
        self._loop_thread = threading.Thread(target=self.validation_loop, daemon=True)
        self._loop_thread.start()

    @endpoint
    def get_weights_history(self):
        return list(self.weights_histories)

    def serve(self):
        from communex.module.server import ModuleServer
        import uvicorn

        self.start_validation_loop()

        if self.settings.port:
            logger.info("server enabled")
            server = ModuleServer(self, self.key, subnets_whitelist=[self.netuid])
            app = server.get_fastapi_app()
            uvicorn.run(app, host=self.settings.host, port=self.settings.port)
        else:
            while True:
                time.sleep(60)


if __name__ == "__main__":
    settings = ValidatorSettings(use_testnet=True)
    Validator(key=classic_load_key("validator"), settings=settings).serve()
