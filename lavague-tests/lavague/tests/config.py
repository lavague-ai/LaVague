from typing import Any, List, Dict
import yaml
from lavague.tests.setup import Setup
from lavague.tests.test import ExpectTest, TaskTest


class Task:
    def __init__(
        self,
        name: str,
        url: str,
        prompt: str,
        max_steps: int,
        tests: List[TaskTest],
        user_data: Dict,
        n_attempts: int,
    ):
        self.name = name
        self.url = url
        self.prompt = prompt
        self.max_steps = max_steps
        self.tests = tests
        self.user_data = user_data
        self.n_attempts = n_attempts

    def __str__(self) -> str:
        return f"Task(name={self.name}, url={self.url}, prompt={self.prompt}, tests={len(self.tests)})"


class TestConfig:
    setup: Setup

    def __init__(self, directory: str):
        self.directory = directory
        self.tasks: list[Task] = []

        with open(f"{directory}/config.yml", "r") as f:
            self.data = yaml.safe_load(f)
            self.setup = Setup.parse(directory, self.data)

            for task_data in self.data["tasks"]:
                self.read_task(task_data)

    def read_task(self, task_data: Dict):
        prompt = task_data["prompt"]
        url = task_data.get("url", self.setup.default_url)
        user_data = {
            **self.data.get("user_data", {}),
            **task_data.get("user_data", {}),
        }
        task = Task(
            task_data.get("name", f"{prompt} from {url}"),
            url,
            prompt,
            task_data.get("max_steps", self.data.get("max_steps", 5)),
            self._parse_test(task_data),
            user_data,
            task_data.get("n_attempts", self.data.get("n_attempts", 1)),
        )
        self.tasks.append(task)

    def __str__(self) -> str:
        return "\n".join([str(t) for t in self.tasks])

    def _parse_test(self, task_data: Any) -> List[TaskTest]:
        tests: List[TaskTest] = []

        if "expect" in task_data:
            tests += ExpectTest.parse(task_data["expect"])

        return tests
