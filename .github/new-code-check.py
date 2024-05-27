from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, PythonEngine, WorldModel
from lavague.core.agents import WebAgent

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
python_engine = PythonEngine()
world_model = WorldModel()

agent = WebAgent(world_model, action_engine, python_engine)

url = "https://huggingface.co"
objective = "Provide the code to use Falcon 11B"

agent.get(url)
output = agent.run(objective, display=True)
result = output[-1]

expected_output = """from transformers import AutoTokenizer, AutoModelForCausalLM
import transformers
import torch
model = "tiiuae/falcon-11B"
tokenizer = AutoTokenizer.from_pretrained(model)
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.bfloat16,
)
sequences = pipeline(
    "Can you explain the concepts of Quantum Computing?",
    max_length=200,
    do_sample=True,
    top_k=10,
    num_return_sequences=1,
    eos_token_id=tokenizer.eos_token_id,
)
for seq in sequences:
    print(f"Result: {seq['generated_text']}")"""

assert (
    result.strip() == expected_output.strip()
), f"Output does not match expected:\nExpected: {expected_output}\nActual: {result}"
print("Output matches expected.")
