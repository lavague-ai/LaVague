from abc import ABC, abstractmethod
import re
from typing import Callable, Dict, Any, Union, Optional
from operator import eq, ne, contains, lt, gt

OperatorFunction = Callable[[Any, Any], bool]

operators: Dict[str, OperatorFunction] = {
    "is": eq,
    "is not": ne,
    "is lower than": lt,
    "is greater than": gt,
    "contains": contains,
    "does not contain": lambda a, b: not contains(a, b),
}


def add_operator(name: str, fn: OperatorFunction):
    operators[name] = fn


class TaskTest(ABC):
    @abstractmethod
    def get_error(self, context: Any) -> Optional[str]:
        pass


class ExpectTest(TaskTest):
    prop: str
    op: OperatorFunction
    value: str

    def __init__(self, expect: str):
        self.expect = expect
        operator_pattern = "|".join(re.escape(op) for op in operators)
        pattern = rf"([\s\w]+)\s*({operator_pattern})\s*(.+)"
        match = re.match(pattern, expect)
        if match:
            self.prop = match.group(1).strip()
            self.op = operators[match.group(2)]
            self.value = match.group(3)
        else:
            available = ", ".join(operators.keys())
            raise ValueError(
                f"Invalid expect string '{expect}', available operators are {available}"
            )

    def get_error(self, context: Any) -> Optional[str]:
        prop_value = context.get(self.prop, "")
        if self.op(prop_value, self.value):
            return None
        return f"was: {prop_value[:60]}"

    def __str__(self) -> str:
        return self.expect

    @classmethod
    def parse(cls, tests: Union[str, list[str]]) -> list[TaskTest]:
        if isinstance(tests, str):
            tests = [tests]
        return [cls(test) for test in tests]
