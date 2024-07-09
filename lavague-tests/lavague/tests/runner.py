from typing import List, Dict
from lavague.core.agents import WebAgent
from lavague.core.world_model import WorldModel
from lavague.core.action_engine import ActionEngine
from lavague.drivers.selenium.base import SeleniumDriver
from .config import Task, TestConfig


class RunResult:
    success: int


class TestRunner:
    def __init__(self, sites: List[TestConfig]):
        self.sites = sites

    def run(self):
        for site in self.sites:
            try:
                site.setup.start()
                self._run_tasks(site.tasks)
            finally:
                site.setup.stop()

    def _run_tasks(self, tasks: List[Task]):
        for task in tasks:
            try:
                self._run_single_task(task)
            except Exception as e:
                print(e)

    def _run_single_task(self, task: Task):
        driver = SeleniumDriver(headless=False)
        action_engine = ActionEngine(driver=driver)
        world_model = WorldModel()
        agent = WebAgent(world_model, action_engine)
        agent.get(task.url)
        agent.run(task.prompt)
        context = self._get_context(agent)

        for test in task.tests:
            test.is_passing(context)

    def _get_context(self, agent: WebAgent) -> Dict[str, str]:
        return {
            "URL": agent.driver.get_url(),
            "Status": "success" if agent.result.success else "failure",
            "Output": agent.result.output,
        }

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self.sites])
