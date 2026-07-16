from abc import ABC, abstractmethod

from schemas import LineVerdict, Step


class Judge(ABC):
    """A judge verifies whether each step follows from the previous one.

    Subject-agnostic contract: swap the judge, keep the product.
    """

    @abstractmethod
    def check(self, problem: str, steps: list[Step]) -> list[LineVerdict]:
        ...