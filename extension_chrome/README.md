## Setup your dev environment

### 1. Setup

`yarn` or `npm install`

### 2. Running

`yarn dev` or `npm run dev`

This will allow the extension built files to be updated in real time when changes are made in the code.

### 3.Install the Chrome extension

#### Installing the latest version

You can install the latest published version of the Chrome extension here: https://chromewebstore.google.com/detail/lavague/johbmggagpndaefakonkdfjpcfdmbfbm

#### Test your extension from local

You can build the project in order to upload and test it on in your Chrome navigator by running:
`yarn build` or `npm run build`

Then run the project with the following code:
`yarn dev` or `npm run dev`

It will build the project in watch mode. Project build in `dist` directory will be updated upon save.

Finally, you can upload and test your locally modified Chrome extension by doing the following:
-   Go to the Extensions page [chrome://extensions/](chrome://extensions/)
-   Click the `Load unpacked` button
-   Select the `dist` directory

Ta-da! The extension has been successfully installed. Every time you update the extension code, click the refresh button on the LaVague extension.

### 4. Setup LaVague Driver Server

You will then need to use LaVague to serve an instance of `AgentServer`. This allows the LaVague extension communicates with a Driver Server using Websockets.

```shell
pip install lavague-core lavague-server lavague-drivers-remote
```

You will also need to make sure your `OPENAI_API_KEY` is set in your current environment.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.driverserver import DriverServer
from lavague.server import AgentServer, AgentSession

def create_agent(session: AgentSession):
    world_model = WorldModel()
    driver = DriverServer(session)
    action_engine = ActionEngine(driver)
    return WebAgent(world_model, action_engine)

server = AgentServer(create_agent)
server.serve()
```

See [https://github.com/lavague-ai/LaVague/blob/main/examples/chrome_extension.py] for our latest example script.

Now you can interact with our LaVague browser extension directly in your Chrome navigator:

<table>
  <tr>
    <td><img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/launch-ext.png?raw=true" alt="Launch Extension" style="width: 120%; max-width: 300px;"></td>
    <td><img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/prompt_ext.png?raw=true" alt="Example Query Chrome" style="width: 120%; max-width: 300px;"></td>
  </tr>
</table>

<img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/beatles-found.png?raw=true" alt="Launch Extension" style="width: 60%">