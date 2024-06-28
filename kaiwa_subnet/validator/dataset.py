import random
import time

from datasets import load_dataset


class ValidationDataset:
    def __init__(self) -> None:
        random.seed(int(time.time()))
        rand = random.randint(0, 1000000)
        print("random", rand)
        self.dataset = load_dataset("chenghao/quora_questions").shuffle(seed=rand)

    def random_prompt(self) -> str:
        index = random.randint(0, len(self.dataset["train"]))
        print("rand_index", index)
        return self.dataset["train"][index]["questions"]


if __name__ == "__main__":
    ValidationDataset()
