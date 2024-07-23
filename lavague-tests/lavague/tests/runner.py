from typing import List, Dict
from lavague.core.context import Context
from lavague.core.agents import WebAgent
from lavague.core.world_model import WorldModel
from lavague.core.action_engine import ActionEngine
from lavague.drivers.selenium.base import SeleniumDriver
from lavague.core.token_counter import TokenCounter
from .config import Task, TestConfig, TaskTest
from pandas import DataFrame
import time


class TestFailure:
    def __init__(self, test: TaskTest, message: str):
        self.test = test
        self.message = message

    def __str__(self) -> str:
        return f"{self.test} - {self.message}"


class SingleRunResult:
    def __init__(self, task: Task, dataframe: DataFrame, execution_time: float):
        self.successes: List[TaskTest] = []
        self.failures: List[TestFailure] = []
        self.task = task
        self.dataframe = dataframe
        self.execution_time = execution_time

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
        tokens_used = 0
        tokens_cost = 0.0
        total_execution_time = 0.0

        for r in self.results:
            for sr in r.results:
                successes += len(sr.successes)
                failures += len(sr.failures)
                tokens_used += sr.dataframe["total_step_tokens"].sum()
                tokens_cost += sr.dataframe["total_step_cost"].sum()
                total_execution_time += sr.execution_time

        total = successes + failures
        if total == 0:
            return "No tests run"
        summary = f"Result: {round(100 * successes / total)} % ({successes} / {total}) in {total_execution_time:.1f}s\n"
        summary += f"Tokens: {tokens_used} ({tokens_cost:.4f} $)"
        return "\n".join(str(r) for r in self.results) + "\n" + summary

    def is_success(self) -> bool:
        return all([r.is_success() for r in self.results])


class TestRunner:
    def __init__(
        self,
        context: Context,
        sites: List[TestConfig],
        token_counter: TokenCounter,
        headless=True,
        log_to_db=False,
    ):
        self.context = context
        self.sites = sites
        self.token_counter = token_counter
        self.headless = headless
        self.log_to_db = log_to_db

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
        action_engine = ActionEngine.from_context(
            context=self.context, driver=driver, n_attempts=task.n_attempts
        )
        world_model = WorldModel.from_context(context=self.context)
        agent = WebAgent(
            world_model,
            action_engine,
            token_counter=self.token_counter,
            n_steps=task.max_steps,
        )
        agent.get(task.url)

        # run agent and measure execution time
        start_time = time.time()
        agent.run(task.prompt, user_data=task.user_data, log_to_db=self.log_to_db)
        end_time = time.time()
        execution_time = end_time - start_time

        dataframe = agent.logger.return_pandas()
        context = self._get_context(agent)
        driver.destroy()

        result = SingleRunResult(task, dataframe, execution_time)
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
            "Tabs": agent.driver.get_tabs(),
        }

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self.sites])
