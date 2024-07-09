from typing import Any, List
import yaml
from .setup import Setup
from .test import ExpectTest, TaskTest


class Task:
    def __init__(self, url: str, prompt: str, tests: List[TaskTest]):
        self.url = url
        self.prompt = prompt
        self.tests = tests

    def __str__(self) -> str:
        return f"Task(url={self.url}, prompt={self.prompt}, tests={len(self.tests)})"


class TestConfig:
    setup: Setup
    tasks: list[Task] = []

    def __init__(self, directory: str):
        self.directory = directory
        with open(f"{directory}/config.yml", "r") as f:
            data = yaml.safe_load(f)
            self.setup = Setup.parse(data)
            for task_data in data["tasks"]:
                task = Task(
                    task_data.get("url", self.setup.default_url),
                    task_data["prompt"],
                    self._parse_test(task_data),
                )
                self.tasks.append(task)

    def __str__(self) -> str:
        return "\n".join([str(t) for t in self.tasks])

    def _parse_test(self, task_data: Any) -> List[TaskTest]:
        tests: List[TaskTest] = []

        if "expect" in task_data:
            tests += ExpectTest.parse(task_data["expect"])

        return tests
