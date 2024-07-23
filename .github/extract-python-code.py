import re
import sys


def extract_python_code(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Regular expression to match Python code blocks
    python_code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)

    # Join the extracted code blocks into a single string
    extracted_code = "\n\n".join(python_code_blocks)

    # Replace agent.demo with agent.run
    modified_code = extracted_code.replace("agent.demo", "agent.run")

    # Remove occurrences of `, display=True`
    modified_code = re.sub(r',\s*display=True', '', modified_code)

    # Remove occurrences of `, display=True`
    modified_code = re.sub(r'\bdisplay\([^\)]*\)', '', modified_code)
    return modified_code


if __name__ == "__main__":
    # Check if at least one file path is provided as an argument
    if len(sys.argv) < 2:
        print(
            "Usage: python extract_python_code.py <path_to_markdown_file> [<additional_paths_to_markdown_files>...]"
        )
        sys.exit(1)

    # Extract and modify Python code for each provided file path
    script_files = []
    for file_path in sys.argv[1:]:
        try:
            # Extract and modify Python code
            extracted_code = extract_python_code(file_path)

            # Save the extracted code to a new Python file named based on the input file
            output_file = f"extracted_code_{file_path.split('/')[-1].split('.')[0]}.py"
            with open(output_file, "w") as file:
                file.write(extracted_code)
            script_files.append(output_file)
            print(
                f"Python code has been extracted and saved to '{output_file}' from '{file_path}'."
            )
        except Exception as e:
            print(f"Failed to process '{file_path}': {e}")

    # Save the list of generated script files
    with open("generated_scripts.txt", "w") as file:
        for script_file in script_files:
            file.write(script_file + "\n")
