import os
import argparse
import yaml
from text_generation import Client

# Check if running in Google Colab
try:
    from google.colab import userdata

    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if IN_COLAB:
    fetch_secret = userdata.get
else:
    fetch_secret = os.getenv

BASE_URL = "https://api-inference.huggingface.co/models/"
BASE_MODEL = "HuggingFaceM4/idefics2-8b"
SYSTEM_PROMPT = "System: The following is a conversation between Idefics2, a highly knowledgeable and intelligent visual AI assistant created by Hugging Face, referred to as Assistant, and a human user called User. In the following interactions, User and Assistant will converse in natural language, and Assistant will do its best to answer User’s questions. Assistant has the ability to perceive images and reason about them, but it cannot generate images. Assistant was built to be respectful, polite and inclusive. It knows a lot, and always tells the truth. When prompted with an image, it does not make up facts.<end_of_utterance>\nAssistant: Hello, I'm Idefics2, Huggingface's latest multimodal assistant. How can I help you?<end_of_utterance>\n"


class HuggingFaceMMLLM:
    def __init__(self, hf_api_key=None, model=BASE_MODEL, base_url=BASE_URL):
        if hf_api_key is None:
            hf_api_key = fetch_secret("HF_TOKEN")
            if hf_api_key is None:
                raise ValueError("HF_TOKEN is not set")

        api_url = base_url + model

        self.client = Client(
            base_url=api_url,
            headers={"x-use-cache": "0", "Authorization": f"Bearer {hf_api_key}"},
        )

    def upload_image(self, file_path, cloudinary_config=None):
        import cloudinary
        import cloudinary.uploader

        if cloudinary_config is None:
            cloudinary_config = {
                "cloud_name": fetch_secret("CLOUDINARY_CLOUD_NAME"),
                "api_key": fetch_secret("CLOUDINARY_API_KEY"),
                "api_secret": fetch_secret("CLOUDINARY_API_SECRET"),
            }
            if None in cloudinary_config.values():
                raise ValueError(
                    "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, or CLOUDINARY_API_SECRET is not set.\nFor more information go on https://cloudinary.com/documentation/image_upload_api_reference"
                )

            cloudinary.config(**cloudinary_config)
        img_url = cloudinary.uploader.upload(file_path)["url"]
        return img_url

    def complete(self, query, file_path=None, url=None, structured=True):
        if file_path is None and url is None:
            raise ValueError("Either file_path or url must be provided")

        generation_args = {
            "max_new_tokens": 512,
            "repetition_penalty": 1.1,
            "do_sample": False,
        }

        if file_path:
            img_url = self.upload_image(file_path)
        else:
            img_url = url

        prompt_with_image = (
            SYSTEM_PROMPT + f"User:![]({img_url}) {query}<end_of_utterance>\nAssistant:"
        )
        output = self.client.generate(
            prompt=prompt_with_image, **generation_args
        ).generated_text

        if structured:
            try:
                output = yaml.safe_load(output.strip())
            except yaml.YAMLError:
                output = output.strip()

        return output


def main():
    parser = argparse.ArgumentParser(
        description="Process an image through a Hugging Face model and run LaVague Agent."
    )
    parser.add_argument("--file_path", help="Path to the image file")
    parser.add_argument("--url", help="URL of the image")
    parser.add_argument("--local", help="If set, LaVague Agent will not be run")

    args = parser.parse_args()

    # Set the OPENAI_API_KEY environment variable
    os.environ["OPENAI_API_KEY"] = fetch_secret("OPENAI_API_KEY")

    if not args.file_path and not args.url:
        raise ValueError("Either file_path or url must be provided")

    from llama_index.embeddings.openai import OpenAIEmbedding
    from lavague.drivers.selenium import SeleniumDriver
    from lavague.core import ActionEngine, WorldModel
    from lavague.core.agents import WebAgent

    if args.local:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        embedding = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    else:
        embedding = OpenAIEmbedding(model="text-embedding-3-large")

    selenium_driver = SeleniumDriver(headless=False)
    action_engine = ActionEngine(selenium_driver, embedding=embedding)
    world_model = WorldModel()
    agent = WebAgent(world_model, action_engine, time_between_actions=2.5)

    form_url = "https://form.jotform.com/241363523875359"
    objective = "Fill out this form. Do not provide a cover letter"

    agent.get(form_url)

    query = "Extract name, email, phone number, current company, a summary of experience, and a summary of education from this cv. Provide your output in YAML format."

    hf_mm_llm = HuggingFaceMMLLM()
    user_data = hf_mm_llm.complete(query=query, file_path=args.file_path, url=args.url)

    print("Extracted Data from :")
    print(user_data)

    agent.run(objective, user_data=user_data)


if __name__ == "__main__":
    main()
