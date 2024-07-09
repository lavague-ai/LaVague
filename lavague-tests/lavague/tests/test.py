from abc import ABC, abstractmethod
import re
from typing import Callable, Dict, Any, Union

OperatorFunction = Callable[[Any, Any], bool]

operators: Dict[str, OperatorFunction] = {
    "is": lambda a, b: a == b,
    "is not": lambda a, b: a != b,
    "is lower than": lambda a, b: a < b,
    "is greater than": lambda a, b: a > b,
    "contains": lambda a, b: b in a,
    "does not contain": lambda a, b: b not in a,
}


def add_operator(name: str, fn: OperatorFunction):
    operators[name] = fn


class TaskTest(ABC):
    @abstractmethod
    def is_passing(self, context: Any) -> bool:
        pass


class ExpectTest(TaskTest):
    prop: str
    op: OperatorFunction
    value: str

    def __init__(self, expect: str):
        operator_pattern = "|".join(re.escape(op) for op in operators)
        pattern = rf"([\s\w]+)\s*({operator_pattern})\s*(.+)"
        match = re.match(pattern, expect)
        if match:
            self.prop = match.group(1).strip()
            self.op = operators[match.group(2)]
            self.value = match.group(3)
        else:
            raise ValueError(f"Invalid expect string '{expect}'")

    def is_passing(self, context: Any) -> bool:
        prop_value = context.get(self.prop, "")
        op_fn = operators[self.op]
        return op_fn(prop_value, self.value)

    @classmethod
    def parse(cls, tests: Union[str, list[str]]) -> list[TaskTest]:
        if isinstance(tests, str):
            tests = [tests]
        return [cls(test) for test in tests]
