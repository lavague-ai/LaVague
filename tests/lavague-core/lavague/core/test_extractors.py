from unittest.mock import patch

import pytest

from lavague.core.extractors import (
    DynamicExtractor,
    PythonFromMarkdownExtractor,
)


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ('{"score": 0.9, "ret": "safe"}', {"score": 0.9, "ret": "safe"}),
        ("[1, True, None, 'text']", [1, True, None, "text"]),
        ("('value', 2)", ("value", 2)),
    ],
)
def test_python_extractor_accepts_literals(literal, expected):
    output = f"```python\n{literal}\n```"

    assert PythonFromMarkdownExtractor().extract_as_object(output) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo unsafe')",
        "[value for value in range(3)]",
        "open('/tmp/lavague-test', 'w')",
    ],
)
def test_python_extractor_rejects_executable_expressions(expression):
    output = f"```python\n{expression}\n```"

    with pytest.raises((ValueError, SyntaxError)):
        PythonFromMarkdownExtractor().extract_as_object(output)


def test_dynamic_extractor_does_not_execute_python_block():
    output = "```python\n__import__('os').system('echo unsafe')\n```"

    with patch("os.system") as system:
        with pytest.raises((ValueError, SyntaxError)):
            DynamicExtractor().extract_as_object(output)

    system.assert_not_called()
