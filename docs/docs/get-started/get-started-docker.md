# Getting started with Docker

Another way to get started without needing to download anything, is to use LaVague with Docker.

Pre-requisites:

- You will need [Docker installed](https://docs.docker.com/get-docker/) to proceed!

## (🚧 coming soon) Running our default Docker image (GPT3.5 with OpenAI)

We have created a [default Docker image]((🚧 coming soon)) which will launch an interactive Gradio demo using GPT3.5 with `openai`.

To run this example, you will need to:

- (🚧 coming soon) Download our `lavague-openai` image from `Dockerhub`: `docker pull lavague-openai`
- Run your image: `docker run -d -p 7860:7860 -e OPENAI_API_KEY=your_api_key lavague-openai`
- Wait a few minutes for the container to run the launch command internally, then go to localhost:7860 to interact with the LaVague demo

## Using LaVague Docker with custom integrations

While we provide this default Docker image using the OpenAI API, you can build a custom image with a different integration (for example with the HuggingFace Inference API or the Azure OpenAI API) by building our Dockerfile with the configuration files of your choice.

### Docker config files

Our Docker image works with our CLI `lavague --i instructions.yaml -c config.py launch` under the hood. We provide default files using the OpenAI API with GPT3.5 but different integrations can be achieved by modifying these config files:

- The `instructions.yaml` file: The first line should contain the website URL you wish to perform actions on and the following lines include the default clickable instruction suggestions you wish to appear in the resulting Gradio demo
![instructions-default](../../assets/openai-default.png)

- An `config.py` file: This file will define parameters such as the LLM to be used. See the [customization guide](./customization.md) for more details on all the customizable elements available in this file.

![default-config](../../assets/openai-default.png)

⚠️ We expect these two config files, named `instructions.yaml` and `config.py` to be in the current directory when building your Docker image.

## Build and run your LaVague Docker image

To build and run your Docker image to launch LaVague:

- Go to the `docker` folder from the root of the `LaVague` repo
- For custom integrations, modify or replace the `instructions.yaml` and `config.py` files
- Build the docker image: `docker build -t lavague-custom .`
- Run your image: `docker run -d -p 7860:7860 -e OPENAI_API_KEY=your_api_key lavague-custom` - you can pass whatever environment variables are necessary for your integration
- Wait a few minutes for the container to run the launch command internally, then go to `localhost:7860` to interact with the LaVague demo
