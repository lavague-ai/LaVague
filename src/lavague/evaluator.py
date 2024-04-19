import re
import ast
from bs4 import BeautifulSoup
import os
from .action_engine import ActionEngine
import pandas as pd
import re

decontaminate_html = lambda x: re.sub(r' backend_node_id="\d+"', '', x)

def keep_assignments(code_snippet):
    # Regex to match variable assignments. This pattern assumes variable names are valid Python identifiers
    # and captures typical assignment statements, excluding those that might appear in comments or strings.
    pattern = r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*.+'

    # Filter and keep only lines with variable assignments
    assignments = [line for line in code_snippet.split('\n') if re.match(pattern, line)]

    # Join the filtered lines back into a string
    return "\n".join(assignments)

# This function will be used to visit each node in the AST
class VariableVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.output = []
    
    def visit_Assign(self, node):
        
        # For each assignment, print the targets (variables)
        for target in node.targets:
            if isinstance(target, ast.Name):  # Ensure it's a variable assignment
                self.output.append(target.id)

def return_first_assignment_variables(code_snippet):
    # Parse the code snippet into an abstract syntax tree (AST)
    parsed = ast.parse(code_snippet)
    
    # Create a VariableVisitor object
    visitor = VariableVisitor()
    
    # Visit (i.e., traverse) the AST nodes
    visitor.visit(parsed)
    
    # Return the variables found
    return visitor.output[0]

def inject_backend_node_id(html):
    # Parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    
    # Initialize a unique ID counter
    backend_node_id = 1
    
    # Loop through each element in the HTML
    for element in soup.find_all(True):  # True finds all tags
        # Add the 'backend_node_id' attribute with the current ID
        element['backend_node_id'] = backend_node_id
        # Increment the ID for the next element
        backend_node_id += 1
    
    # Return the modified HTML as a string
    return str(soup)

def extract_backend_node_ids(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return set([tag['backend_node_id'] for tag in soup.find_all(attrs={"backend_node_id": True})])

def id_recall(ground_truth_outer_html, context_str):
    ground_truth_ids = extract_backend_node_ids(ground_truth_outer_html)
    context_ids = extract_backend_node_ids(context_str)
    recall = len(ground_truth_ids & context_ids) / len(ground_truth_ids)
    return recall

def id_precision(ground_truth_outer_html, context_str):
    ground_truth_ids = extract_backend_node_ids(ground_truth_outer_html)
    context_ids = extract_backend_node_ids(context_str)
    precision = len(ground_truth_ids & context_ids) / len(context_ids)
    return precision


def load_html(html, driver):
    """Loads a specific HTML content into the browser."""
    file_path = 'sample_page.html'

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html)
        
    abs_file_path = os.path.abspath("sample_page.html")

    # Use the file:/// protocol to load the local HTML file
    driver.get(f"file:///{abs_file_path}")

class SeleniumActionEvaluator:
    def __init__(self, driver, action_engine: ActionEngine, inject_node: bool=True):
        self.driver = driver
        self.action_engine = action_engine
        self.inject_node = inject_node
    def evaluate(self, query, html, ground_truth_code) -> float:
        driver = self.driver
        action_engine = self.action_engine

        html = inject_backend_node_id(html)

        load_html(html, driver)

        assignment_code = keep_assignments(ground_truth_code)

        # Split the code into lines and keep only the first assignment
        assignment_code = assignment_code.split("\n")[0]

        
        variable_name = return_first_assignment_variables(ground_truth_code)
        code = f"""from selenium.webdriver.common.by import By
{assignment_code}
ground_truth_element = {variable_name}
ground_truth_outer_html = driver.execute_script("return arguments[0].outerHTML;", ground_truth_element)
        """.strip()
        
        local_scope = {"driver": driver}

        exec(code, globals(), local_scope)
        ground_truth_outer_html = local_scope["ground_truth_outer_html"]

        source_nodes = action_engine.get_nodes(query, html)
        context_str = "\n".join(source_nodes)

        recall_retriever = id_recall(ground_truth_outer_html, context_str)
        precision_retriever = id_precision(ground_truth_outer_html, context_str)

        # We remove the backend node ids to ensure the LLM does not use them
        decontaminated_context_str = decontaminate_html(context_str)

        generated_code = action_engine.manual_complete(decontaminated_context_str, query)

        # Keep only the variable assignments in the generated code
        assignment_code = keep_assignments(generated_code)

        # Split the code into lines and keep only the first assignment
        assignment_code = assignment_code.split("\n")[0]

        variable_name = return_first_assignment_variables(assignment_code)
        code = f"""from selenium.webdriver.common.by import By
{assignment_code}
target_element = {variable_name}
target_outer_html = driver.execute_script("return arguments[0].outerHTML;", target_element)
        """.strip()
        
        
        local_scope = {"driver": driver}
        try:
            exec(code, globals(), local_scope)
            target_outer_html = local_scope["target_outer_html"]

            # Execute the code to define the first variable
            # Assign the variable to the target_element variable which will be used afterwards to compute score
            
            recall_llm = id_recall(ground_truth_outer_html, target_outer_html)
            precision_llm = id_precision(ground_truth_outer_html, target_outer_html)
            valid_generated_code = "Yes"
        except Exception as e:
            recall_llm = 0
            precision_llm = 0
            valid_generated_code = str(e)
            
        output = {
            "recall_retriever": recall_retriever,
            "precision_retriever": precision_retriever,
            "recall_llm": recall_llm,
            "precision_llm": precision_llm,
            "valid_generated_code": valid_generated_code
        }
    
        return output
        
    def evaluate_df(self, df, column_mapping = {"query": "query", "html": "html", "ground_truth_code": "selenium_ground_truth"}):
        
        results = []
        for i, row in df.iterrows():
            query = row[column_mapping["query"]]
            html = row[column_mapping["html"]]
            ground_truth_code = row[column_mapping["ground_truth_code"]]
            result = self.evaluate(query, html, ground_truth_code)
            results.append(result)
        return pd.DataFrame(results)