from typing import List, Dict
from lavague.core.agents import WebAgent
from lavague.core.world_model import WorldModel
from lavague.core.action_engine import ActionEngine
from lavague.drivers.selenium.base import SeleniumDriver
from .config import Task, TestConfig, TaskTest
from pandas import DataFrame


class TestFailure:
    def __init__(self, test: TaskTest, message: str):
        self.test = test
        self.message = message

    def __str__(self) -> str:
        return f"{self.test} - {self.message}"


class SingleRunResult:
    def __init__(self, task: Task, dataframe: DataFrame):
        self.successes: List[TaskTest] = []
        self.failures: List[TestFailure] = []
        self.task = task
        self.dataframe = dataframe

    def get_test_count(self) -> int:
        return len(self.successes) + len(self.failures)

    def __str__(self) -> str:
        success = "o" if self.is_success() else "x"
        string = f"[{success}] {self.task.name}\n"
        for test in self.successes:
            string += f"        {str(test)}\n"
        for test in self.failures:
            string += f"    (x) {str(test)}\n"
        return string

    def is_success(self) -> bool:
        return len(self.failures) == 0


class RunResults:
    def __init__(self, site: TestConfig, results: List[SingleRunResult]):
        self.site = site
        self.results = results

    def __str__(self) -> str:
        return "\n".join(str(r) for r in self.results)

    def is_success(self) -> bool:
        return all([r.is_success() for r in self.results])


class RunnerResult:
    def __init__(self, results: List[RunResults]):
        self.results = results

    def __str__(self) -> str:
        successes = 0
        failures = 0
        for r in self.results:
            for sr in r.results:
                successes += len(sr.successes)
                failures += len(sr.failures)

        total = successes + failures
        if total == 0:
            return "No tests run"
        summary = f"Result: {round(100 * successes / total)} % ({successes} / {total})"
        return "\n".join(str(r) for r in self.results) + "\n" + summary

    def is_success(self) -> bool:
        return all([r.is_success() for r in self.results])


class TestRunner:
    def __init__(self, sites: List[TestConfig], headless=True):
        self.sites = sites
        self.headless = headless

    def run(self) -> RunnerResult:
        results: List[RunResults] = []
        for site in self.sites:
            try:
                site.setup.start()
                task_results = self._run_tasks(site.tasks)
                results.append(RunResults(site, task_results))
            finally:
                site.setup.stop()

        return RunnerResult(results)

    def _run_tasks(self, tasks: List[Task]):
        results: List[SingleRunResult] = []
        for task in tasks:
            try:
                r = self._run_single_task(task)
                results.append(r)
            except Exception as e:
                print(e)

        return results

    def _run_single_task(self, task: Task) -> SingleRunResult:
        driver = SeleniumDriver(headless=self.headless)
        action_engine = ActionEngine(driver=driver, n_attempts=task.n_attempts)
        world_model = WorldModel()
        agent = WebAgent(world_model, action_engine, n_steps=task.max_steps)
        agent.get(task.url)
        agent.run(task.prompt, user_data=task.user_data)
        dataframe = agent.logger.return_pandas()
        context = self._get_context(agent)
        driver.destroy()

        result = SingleRunResult(task, dataframe)
        for test in task.tests:
            error = test.get_error(context)
            if error is None:
                result.successes.append(test)
            else:
                result.failures.append(TestFailure(test, error))

        return result

    def _get_context(self, agent: WebAgent) -> Dict[str, str]:
        return {
            "URL": agent.driver.get_url(),
            "Status": "success" if agent.result.success else "failure",
            "Output": agent.result.output,
            "Steps": agent.logger.current_step,
            "HTML": agent.driver.get_html(),
        }

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self.sites])
