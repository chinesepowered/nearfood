from pydantic import BaseModel
from huggingface import Dataset
from nearai.solvers import SolverStrategy

from typing import Dict, List

class ThreeDigitAdditionDatum(BaseModel):
    input: str
    output: str

class ThreeDigitAdditionSolver(SolverStrategy):
    """Solver for the 3 digit addition benchmark."""

    def __init__(self, dataset_ref: Dataset, model: str = "", agent: str = ""):
        super().__init__(model, agent)
        self.dataset_ref = dataset_ref

    def evaluation_name(self) -> str:
        return "3_digit_addition"

    def compatible_datasets(self) -> List[str]:
        return ["3_digit_addition"]

    def solve(self, datum: Dict[str, str]) -> bool:
        datum = ThreeDigitAdditionDatum(**datum)
        label = datum.input.replace(" + ", "+")
        session = self.start_inference_session(label)

        goal = f"""Please add the following numbers together: {datum.input}\n\nOutput the result only."""
        result = session.run_task(goal).strip()
        return result == datum.output