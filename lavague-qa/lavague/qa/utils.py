def remove_comments(code):
    return "\n".join(
        [line for line in code.split("\n") if not line.strip().startswith("#")]
    )


def clean_llm_output(code: str) -> str:
    return code.replace("```python", "").replace("```", "").replace("```\n", "")
