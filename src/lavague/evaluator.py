import re
import ast
from bs4 import BeautifulSoup
import os
from .action_engine import ActionEngine
import pandas as pd
import re
from tqdm import tqdm

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

def contains_backend_node_id(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Search for any tags with the 'backend_node_id' attribute
    if soup.find(attrs={"backend_node_id": True}):
        # If any such tags are found, return True
        return True
    # If no such tags are found, return False
    return False

def extract_backend_node_ids(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return set([tag['backend_node_id'] for tag in soup.find_all(attrs={"backend_node_id": True})])

def id_recall(ground_truth_outer_html, retrieved_context):
    ground_truth_ids = extract_backend_node_ids(ground_truth_outer_html)
    context_ids = extract_backend_node_ids(retrieved_context)
    recall = len(ground_truth_ids & context_ids) / len(ground_truth_ids)
    return recall

def id_precision(ground_truth_outer_html, retrieved_context):
    ground_truth_ids = extract_backend_node_ids(ground_truth_outer_html)
    context_ids = extract_backend_node_ids(retrieved_context)
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

def get_outer_html(html, driver, code):
    load_html(html, driver)
    assignment_code = keep_assignments(code)

        # Split the code into lines and keep only the first assignment
    assignment_code = assignment_code.split("\n")[0]

    variable_name = return_first_assignment_variables(code)
    code = f"""from selenium.webdriver.common.by import By
{assignment_code}
element = {variable_name}
outer_html = driver.execute_script("return arguments[0].outerHTML;", element)
    """.strip()
    
    local_scope = {"driver": driver}

    exec(code, globals(), local_scope)
    outer_html = local_scope["outer_html"]
    return outer_html

class SeleniumActionEvaluator:
    def __init__(self, driver, action_engine: ActionEngine, inject_node: bool=True, raise_exceptions: bool=False):
        self.driver = driver
        self.action_engine = action_engine
        self.inject_node = inject_node
        self.raise_exceptions = raise_exceptions
        
    def evaluate_retriever(self, query, html, ground_truth_code, return_context: bool=False):
        driver = self.driver
        action_engine = self.action_engine
        
        ground_truth_outer_html = get_outer_html(html, driver, ground_truth_code)

        source_nodes = action_engine.get_nodes(query, html)
        retrieved_context = "\n".join(source_nodes)

        recall_retriever = id_recall(ground_truth_outer_html, retrieved_context)
        precision_retriever = id_precision(ground_truth_outer_html, retrieved_context)
        
        if return_context:
            return {
                "ground_truth_outer_html": ground_truth_outer_html,
                "retrieved_context": retrieved_context,
                "recall_retriever": recall_retriever,
                "precision_retriever": precision_retriever
            }
        else:
            return {
                "recall_retriever": recall_retriever,
                "precision_retriever": precision_retriever
            }
    def evaluate_llm(self, query, html, ground_truth_outer_html, retrieved_context, record_error: bool=False):
        action_engine = self.action_engine
        driver = self.driver
        
        decontaminated_retrieved_context = decontaminate_html(retrieved_context)

        generated_code = action_engine.manual_complete(decontaminated_retrieved_context, query)
        
        # In case of missing backend node ids, we raise an error
        if not contains_backend_node_id(html):
            raise ValueError("The HTML content does not contain backend node ids.")
        
        try:
            targeted_outer_html = get_outer_html(html, driver, generated_code)
            recall_llm = id_recall(ground_truth_outer_html, targeted_outer_html)
            precision_llm = id_precision(ground_truth_outer_html, targeted_outer_html)
            if record_error:
                error = None
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                recall_llm = 0
                precision_llm = 0
                error = str(e)
        output = {
            "recall_llm": recall_llm,
            "precision_llm": precision_llm
        }
        if record_error:
            output["error"] = error
        return output
        
    def evaluate(self, query, html, ground_truth_code, 
                 return_context: bool=False, record_error: bool=False) -> float:
        html_with_id = inject_backend_node_id(html)
        
        outputs = self.evaluate_retriever(query, html_with_id, ground_truth_code, return_context=return_context)
        ground_truth_outer_html, retrieved_context, recall_retriever, precision_retriever = outputs.values()

        # We remove the backend node ids to ensure the LLM does not use them
        output = self.evaluate_llm(query, html_with_id, ground_truth_outer_html, retrieved_context, record_error=record_error)
        recall_llm, precision_llm = output.values()
            
        output = {
            "recall_retriever": recall_retriever,
            "precision_retriever": precision_retriever,
            "recall_llm": recall_llm,
            "precision_llm": precision_llm,
        }
    
        return output
        
    def batch_evaluate_retriever(self, queries, htmls, ground_truth_codes, 
                                 return_context: bool=False):
        
        results = []
        for query, html, ground_truth_code in tqdm(zip(queries, htmls, ground_truth_codes)):
            html_with_id = inject_backend_node_id(html)
            result = self.evaluate_retriever(query, html_with_id, ground_truth_code, return_context=return_context)
            results.append(result)
        return pd.DataFrame(results)
    
    def batch_evaluate_llm(self, queries, htmls, ground_truth_outer_htmls, retrieved_contexts, 
                           record_error: bool=False):
        
        results = []
        for query, html, ground_truth_outer_html, retrieved_context in tqdm(zip(queries, htmls, ground_truth_outer_htmls, retrieved_contexts)):
            html_with_id = inject_backend_node_id(html)
            result = self.evaluate_llm(query, html_with_id, ground_truth_outer_html, retrieved_context, 
                                       record_error=record_error)
            results.append(result)
        return pd.DataFrame(results)
        
    def batch_evaluate(self, queries, htmls, ground_truth_codes,
                        return_context: bool=False, record_error: bool=False):
        
        retriever_results = self.batch_evaluate_retriever(queries, htmls, ground_truth_codes, return_context=True)
        ground_truth_outer_htmls = retriever_results["ground_truth_outer_html"].tolist()
        retrieved_contexts = retriever_results["retrieved_context"].tolist()
        
        llm_results = self.batch_evaluate_llm(queries, htmls, ground_truth_outer_htmls, retrieved_contexts, record_error=record_error)
        results = pd.concat([retriever_results, llm_results], axis=1)
        
        if not return_context:
            results = results.drop(columns=["ground_truth_outer_html", "retrieved_context"])
        
        return results
        