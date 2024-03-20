
# How to set-up & run LaVague

## Quick tour in Google Colab

If you just want to test out LaVague without having to install anything locally, you can run our [Quick Tour notebook with Google Colab](https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/quick-tour.ipynb).

## Testing Azure OpenAI script with Docker **Coming soon 🚧 **

We also prepared an example using Azure OpenAI with Docker in the `examples` folder. To run this example, you need to do the following:

1) Update the `examples/azure-openai/.env file with your OpenAI config details
2) Move to the azure-openai directory:`cd examples/azure-openai/`
3) Build the docker image: `docker build -t lavague-azure .`
4) Run your image: `docker run -d -p 8000:8000 -e AZURE_API_KEY=your_api_key -e AZURE_API_ENDPOINT=your_endpoint lavague-azure`
5) Now you can go to localhost:8000 to interact with the LaVague demo.

## Step 1: Preparing your environment

LaVague currently supports only Selenium as a web automation tool, which requires users to first install a webdriver to interface with the chosen browser (Chrome, Firefox, etc.).

In this guide we will walk you through two installation options: either can either run LaVague within [our pre-configured dev container](#run-lavague-with-our-dev-container) which will handle the webdriver installation for you, or you can do this [installation manually](#installing-the-webdriver-locally).

### Running LaVague with our Dev container

⚠️ Pre-requisites:
- 🐋 Docker: Ensure Docker is installed and running on your machine. Docker is used to create and manage your development container
- Visual Studio Code
- Visual Studio Code's Remote - Containers Extension: You can download this extension by searching for it within the Extensions view

To open the project in our dev container you need to:

1. Open VSCode at the root of the LaVague repo.
2. Click on the blue "><" icon in the bottom left corner, then select "Reopen in Container" in the drop-down menu that then appears.

VS Code will then build the container based on the Dockerfile and devcontainer.json files in the .devcontainer folder. This process might take a few minutes the first time you run it.

### Installing the webdriver locally

An alternative option is to manually install the webdriver. The following instructions are valid for users working on Debian-based Linux distributions. For instructions on how to install a driver on a different OS or distribution, [see the Selenium documentation](https://selenium-python.readthedocs.io/installation.html#drivers)

You may first need to update the list of available packages for your system:

```
sudo apt update
```

Next, you will need to make sure you have the following packages installed on your system:
```
sudo apt install -y ca-certificates fonts-liberation unzip \
libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 \
libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \
libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils`
``

Finally, you can download the necessary files for the Chrome webdriver with the following code:
```
wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip
wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip
unzip chrome-linux64.zip
unzip chromedriver-linux64.zip
rm chrome-linux64.zip chromedriver-linux64.zip
```

> For instructions on how to install a driver on a different OS, [see the Selenium documentation](https://selenium-python.readthedocs.io/installation.html#drivers)

## Step 2: Installing LaVague

To install LaVague, run the following:

```
pip install lavague
```

## Step 3: Running LaVague scripts

You can then run any of our example scripts or create your own. For example:

```
python examples/scripts/huggingface_api.py
```

> Note that these example scripts may come with additional requirements, such as inputting an API key into the script before they will run successfully. Please check the comments in the script you want to test before running in.