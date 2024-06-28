from typing import Callable, List
import inspect
import re
import ast

DEFAULT_ENGINES: List[str] = [
    "Navigation Controls",
    "Python Engine",
    "Navigation Engine",
    "COMPLETE",
]


class VariableVisitor(ast.NodeVisitor):
    """Helper class to visit AST nodes and extract variables assigned in the code."""

    def __init__(self):
        super().__init__()
        self.output = []

    def visit_Assign(self, node):
        # For each assignment, print the targets (variables)
        for target in node.targets:
            if isinstance(target, ast.Name):  # Ensure it's a variable assignment
                self.output.append(target.id)


def return_assigned_variables(code_snippet):
    """Returns the variables assigned in a code snippet."""
    parsed = ast.parse(code_snippet)

    # Create a VariableVisitor object
    visitor = VariableVisitor()

    # Visit (i.e., traverse) the AST nodes
    visitor.visit(parsed)

    return visitor.output


def keep_assignments(code_snippet):
    # Regex to match variable assignments. This pattern assumes variable names are valid Python identifiers
    # and captures typical assignment statements, excluding those that might appear in comments or strings.
    pattern = r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*.+"

    # Filter and keep only lines with variable assignments
    assignments = [line for line in code_snippet.split("\n") if re.match(pattern, line)]

    # Join the filtered lines back into a string
    return "\n".join(assignments)


def extract_code_from_funct(funct: Callable) -> List[str]:
    """Extract code lines from a function while removing the first line (function definition) and the last line (return) and correcting indentation"""
    source_code = inspect.getsource(funct)
    source_code_lines = source_code.splitlines()[1:]  # remove the first line
    nident = len(source_code_lines[0]) - len(
        source_code_lines[0].lstrip()
    )  # count nb char in indentation
    return [
        line[nident:] for line in source_code_lines[:-1]
    ]  # every line except the return


def extract_imports_from_lines(lines: List[str]) -> str:
    """Only keep import lines from python code lines and join them"""
    return "\n".join(
        [line for line in lines if line.startswith("from") or line.startswith("import")]
    )


import re


def extract_world_model_instruction(text):
    # Use a regular expression to find the content after "Instruction:"
    instruction_patterns = [
        r"Instruction:\s*((?:- .*\n?)+)",  # For multi-line hyphenated instructions
        r"### Instruction:\s*((?:- .*\n?)+)",  # For multi-line hyphenated instructions with ### prefix
        r"Instruction:\s*((?:\d+\.\s.*\n?)+)",  # For multi-line numbered instructions
        r"### Instruction:\s*((?:\d+\.\s.*\n?)+)",  # For multi-line numbered instructions with ### prefix
        r"Instruction:\s*```(.*?)```",  # For block of text within triple backticks
        r"### Instruction:\s*```(.*?)```",  # For block of text within triple backticks with ### prefix
        r"Instruction:\s*(.*)",  # For single-line instructions
        r"### Instruction:\s*(.*)",  # For single-line instructions with ### prefix
    ]

    longest_instruction = ""

    for pattern in instruction_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        for instruction_text in matches:
            instruction_text = instruction_text
            # Check if the instruction is multi-line or single-line
            if "\n" in instruction_text:
                # Remove newlines and extra spaces for multi-line instructions
                instruction_str = " ".join(
                    line for line in instruction_text.split("\n")
                )
            else:
                instruction_str = instruction_text
            # Update longest_instruction if the current one is longer
            if len(instruction_str) > len(longest_instruction):
                longest_instruction = instruction_str

    if longest_instruction:
        return longest_instruction

    raise ValueError("No instruction found in the text.")


def extract_next_engine(text: str, next_engines: List[str] = DEFAULT_ENGINES) -> str:
    # Use a regular expression to find the content after "Next engine:"

    next_engine_patterns = [r"Next engine:\s*(.*)", r"### Next Engine:\s*(.*)"]

    for pattern in next_engine_patterns:
        next_engine_match = re.search(pattern, text)
        if next_engine_match:
            extracted_text = next_engine_match.group(1).strip()
            # To avoid returning a non-existent engine

            for engine in next_engines:
                if engine.lower() in extracted_text.lower():
                    return engine

    raise ValueError(f"No next engine found in the text: {text}")


def extract_and_eval(string):
    # Regular expression to match a list inside a string
    match = re.search(r"\[.*?\]", string, re.DOTALL)
    if match:
        list_string = match.group(0)
        try:
            result = ast.literal_eval(list_string)
            return result
        except (SyntaxError, ValueError):
            return "Error: The extracted string is not a valid Python literal."
    else:
        return "Error: No list found in the string."


def clean_html(
    html_to_clean: str,
    tags_to_remove: List[str] = ["style", "svg", "script"],
    attributes_to_keep: List[str] = ["id", "href"],
) -> str:
    """
    Clean HTML content by removing specified tags and attributes while keeping specified attributes.

    Args:
        html_to_clean (str): The HTML content to clean.
        tags_to_remove (List[str]): List of tags to remove from the HTML content. Default is ['style', 'svg', 'script'].
        attributes_to_keep (List[str]): List of attributes to keep in the HTML tags. Default is ['id', 'href'].

    Returns:
        str: The cleaned HTML content.

    Example:
    >>> from clean_html_for_llm import clean_html
    >>> cleaned_html = clean_html('<div id="main" style="color:red">Hello <script>alert("World")</script></div>', tags_to_remove=['script'], attributes_to_keep=['id'])
    """
    for tag in tags_to_remove:
        html_to_clean = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>", "", html_to_clean, flags=re.DOTALL
        )

    attributes_to_keep = "|".join(attributes_to_keep)
    pattern = rf'\b(?!({attributes_to_keep})\b)\w+(?:-\w+)?\s*=\s*["\'][^"\']*["\']'
    cleaned_html = re.sub(pattern, "", html_to_clean)
    return cleaned_html
