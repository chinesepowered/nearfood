import random
from itertools import product

import datasets

SAMPLE_SIZE = 1000
SEED = 42
PATH = "3_digit_addition"

random.seed(SEED)
datasets.Dataset.from_generator(
    lambda: iter(
        {
            "input": f"{a} + {b}",
            "output": str(a + b)
        }
        for a, b in random.sample(list(product(range(1000), range(1000))), SAMPLE_SIZE)
    ),
    features=datasets.Features(
        {
            "input": datasets.Value("string"),
            "output": datasets.Value("string")
        }
    )
).save_to_disk(PATH)