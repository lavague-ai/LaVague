import inspect
import re
from typing import Any, Callable, Optional
from contextlib import contextmanager
from lavague.exporter.base import TrajectoryExporter
from lavague.action.navigation import NavigationOutput
from lavague.action.extraction import ExtractionOutput
from lavague.trajectory import TrajectoryData

import ast
import astor
import textwrap


class ContextManagerExcluder(ast.NodeTransformer):
    def __init__(self, context_manager_name):
        self.context_manager_name = context_manager_name

    def visit_FunctionDef(self, node):
        # Filter out the With nodes that match our context manager
        node.body = [
            stmt
            for stmt in node.body
            if not (
                isinstance(stmt, ast.With)
                and isinstance(stmt.items[0].context_expr, ast.Call)
                and isinstance(stmt.items[0].context_expr.func, ast.Name)
                and stmt.items[0].context_expr.func.id == self.context_manager_name
            )
        ]
        return node


def exclude_context_manager(source_code, context_manager_name):
    # Dedent the source code
    source_code = textwrap.dedent(source_code)

    # Find the line breaks in the source code
    line_breaks = [
        i
        for i, line in enumerate(source_code.splitlines(keepends=True))
        if line == "\n"
    ]

    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Apply the transformer
    transformer = ContextManagerExcluder(context_manager_name)
    modified_tree = transformer.visit(tree)

    # Generate the modified source code
    modified_source = astor.to_source(modified_tree)

    # re-insert line breaks
    modified_lines = modified_source.splitlines(keepends=True)
    for index in line_breaks:
        if index < len(modified_lines):
            modified_lines.insert(index, "\n")

    return "".join(modified_lines)


@contextmanager
def exclude_from_export():
    yield


class PythonExporter(TrajectoryExporter):
    """
    A class for exporting trajectories (sequences of actions) into Python code.

    This class provides a framework for translating various types of actions
    (like clicking, hovering, extracting data, etc.) into Python code snippets
    that can be used in test scripts or automation tasks.

    Key features:
    1. Translates method code into Python strings, replacing action attribute
       references with their actual values.
    2. Extracts method bodies, removing definitions and filtering out excluded functions.
    3. Supports excluding specific methods from export using the @exclude_from_export decorator.
    4. Provides placeholder methods for different action types (click, hover, extract, etc.)
       to be implemented by subclasses.
    5. Generates setup and teardown code for trajectories.
    6. Translates specific action types into Python code.

    This class is designed to be extended by more specific exporters, such as
    PythonSeleniumExporter and QASeleniumExporter, which can implement logic
    for translating actions into Selenium-based Python code and potentially
    incorporate AI-generated test assertions.
    """

    def translate(
        self,
        method: Callable,
        output: NavigationOutput | ExtractionOutput,
        string_only: bool = False,
    ) -> Optional[str]:
        """Takes the code of method, replace each use of the 'action' parameter with the actual action attributes.
        Replacement is done only on attributes of the action used in the method.
        """
        source = self.extract_method_body(method)

        # Find all action attribute accesses
        attribute_pattern = r"action_output\.(\w+)"
        source = self.replace_code_with_value(
            source, output, attribute_pattern, "action_output.", string_only
        )

        # Filter out lines within exclude_from_export context
        filtered_lines = []
        for line in source.split("\n"):
            if "raise NotImplementedError" in line:
                # Extract the original error message and raise it
                error_message = (
                    line.split("NotImplementedError(", 1)[1]
                    .rsplit(")", 1)[0]
                    .strip("\"'")
                )
                raise NotImplementedError(error_message)

            filtered_lines.append(line)

        filtered_source = "\n".join(filtered_lines)
        return filtered_source.strip() or None

    def translate_boilerplate(
        self, method: Callable, trajectory: TrajectoryData, string_only: bool = False
    ) -> str:
        """
        Translates the boilerplate code in the source code.
        """
        source = self.extract_method_body(method)

        # Find all action attribute accesses
        attribute_pattern = r"trajectory\.(\w+)"
        source = self.replace_code_with_value(
            source, trajectory, attribute_pattern, "trajectory.", string_only
        )
        return source

    def replace_code_with_value(
        self,
        source: str,
        object: Any,
        attribute_pattern: str,
        attribute_prefix: str,
        string_only: bool = True,
    ) -> str:
        """
        Replaces all occurrences of the attribute pattern in the source code with the actual value of the attribute.
        """
        attributes = re.findall(attribute_pattern, source)

        # Replace action attribute accesses with their actual values
        for attr in attributes:
            if hasattr(object, attr):
                value = getattr(object, attr)

                if isinstance(value, str):
                    value = f"'{value}'"
                else:
                    if string_only:
                        raise ValueError(
                            f"Unsupported type for attribute {attr}: {type(value)}, expected string"
                        )
                    value = str(value)
                source = re.sub(f"{attribute_prefix}{attr}", str(value), source)

        return source

    def extract_method_body(self, method: Callable) -> str:
        """
        Extracts the body of a method, removing the method definition and filtering out excluded functions.
        """
        source = inspect.getsource(method)
        source = exclude_context_manager(source, "exclude_from_export")

        # Remove leading whitespace and the method definition
        lines = source.split("\n")[1:]
        indentation = len(lines[0]) - len(lines[0].lstrip())
        source = "\n".join(
            line[indentation:] if line.strip() else line for line in lines
        )
        return source

    def setup(self, trajectory: TrajectoryData):
        raise NotImplementedError("setup is not implemented")

    def teardown(self, trajectory: TrajectoryData):
        raise NotImplementedError("teardown is not implemented")

    def click(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("click is not implemented")

    def hover(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("hover is not implemented")

    def extract(self, action_output: ExtractionOutput) -> Optional[str]:
        raise NotImplementedError("extract is not implemented")

    def set_value(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("set_value is not implemented")

    def set_value_and_enter(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("set_value_and_enter is not implemented")

    def type_key(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("type_key is not implemented")

    def scroll(self, action_output: NavigationOutput) -> Optional[str]:
        raise NotImplementedError("scroll is not implemented")

    def generate_setup(self, trajectory: TrajectoryData) -> str | None:
        return self.translate_boilerplate(self.setup, trajectory)

    def generate_teardown(self, trajectory: TrajectoryData) -> str | None:
        return self.translate_boilerplate(self.teardown, trajectory)

    def translate_click(self, action_output: NavigationOutput) -> Optional[str]:
        return self.translate(self.click, action_output)

    def translate_hover(self, action_output: NavigationOutput) -> Optional[str]:
        return self.translate(self.hover, action_output)

    def translate_extract(self, action_output: ExtractionOutput) -> Optional[str]:
        return self.translate(self.extract, action_output)

    def translate_set_value(self, action_output: NavigationOutput) -> Optional[str]:
        return self.translate(self.set_value, action_output)

    def translate_set_value_and_enter(
        self, action_output: NavigationOutput
    ) -> Optional[str]:
        return self.translate(self.set_value_and_enter, action_output)

    def translate_type_key(self, action_output: NavigationOutput) -> Optional[str]:
        return self.translate(self.type_key, action_output)

    def translate_scroll(self, action_output: NavigationOutput) -> Optional[str]:
        return self.translate(self.scroll, action_output)
