from typing import Callable, List
import inspect


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
