from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()

agent = WebAgent(world_model, action_engine)

url = "https://huggingface.co"
objective = "Provide the code to use Falcon 11B"

agent.get(url)
output = agent.run(objective, display=False)

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
    device_map="auto",
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

expected_output_2 = """from transformers import AutoTokenizer, AutoModelForCausalLM
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

# Remove all whitespace characters from both strings before comparison
expected_output_stripped = "".join(expected_output.strip().split())
expected_output_2_stripped = "".join(expected_output_2.strip().split())
result_stripped = "".join(result.strip().split())

# Check if the stripped expected output is contained within the stripped result
assert (
    expected_output_stripped in result_stripped
    or expected_output_2_stripped in result_stripped
), f"Output does not match expected:\nExpected: {expected_output}\nActual: {result}"
print("Output matches expected.")
