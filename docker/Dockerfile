FROM nvidia/cuda:12.3.2-devel-ubuntu22.04

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y ca-certificates fonts-liberation unzip \
libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 \
libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 wget \
libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils \
software-properties-common git zsh curl

# Install chrome and chromedriver for ubuntu22
RUN wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip \
&& wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip \
&& unzip chromedriver-linux64.zip -d /home/$USERNAME \
&& unzip chrome-linux64.zip -d /home/$USERNAME \
&& rm chrome-linux64.zip chromedriver-linux64.zip

# We need python3.10 to build the project
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && apt-get install -y python3.10

# We need git to clone the repository, ensure it's installed
RUN apt-get update && apt-get install -y git

USER $USERNAME

# Clone the lavague repository
RUN git clone https://github.com/lavague-ai/LaVague /home/$USERNAME/LaVague

# Make localhost accessible externally
RUN sed -i "s/demo.launch(server_port=server_port, share=True, debug=True)/demo.launch(server_name='0.0.0.0', server_port=server_port, share=True, debug=True)/g" /home/$USERNAME/LaVague/src/lavague/command_center.py

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 \
&& python3.10 -m pip install virtualenv \
&& python3.10 -m pip install /home/$USERNAME/LaVague --force-reinstall \
&& python3.10 -m pip install llama-index-llms-azure-openai

WORKDIR /home/$USERNAME

# Copy the necessary files into the Docker image
COPY config.py /home/$USERNAME/config.py
COPY instructions.txt /home/$USERNAME/instructions.txt
COPY entrypoint.sh /home/$USERNAME/entrypoint.sh

RUN sudo chmod 755 /home/$USERNAME/entrypoint.sh

# fix path problem
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Modify the ENTRYPOINT to execute the lavague-launch command and keep the container running
COPY entrypoint.sh /home/$USERNAME/entrypoint.sh
RUN sudo chmod +x /home/$USERNAME/entrypoint.sh
ENTRYPOINT ["/home/vscode/entrypoint.sh"]