# LaVague Chrome Extension

## Using the latest LaVague Chrome Extension release

### Install necessary packages

You will need to install the following lavague packages:

```shell
pip install lavague-core lavague-server lavague-drivers-remote
```

You will also need to make sure your `OPENAI_API_KEY` is set in your current environment.

### Running the LaVague Chrome Extension server

Next, you will need to use LaVague to serve an instance of `AgentServer`. This allows the LaVague extension communicates with a Driver Server using Websockets.

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

You can see our latest example script [here](https://github.com/lavague-ai/LaVague/blob/main/examples/chrome_extension.py).

### Using the extension

Now you're ready to install and interact with with our LaVague browser extension directly in your Chrome navigator.

You can install the extension [here](https://chromewebstore.google.com/detail/lavague/johbmggagpndaefakonkdfjpcfdmbfbm).

<table>
  <tr>
    <td><img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/launch-ext.png?raw=true" alt="Launch Extension" style="width: 100%; max-width: 300px;"></td>
    <td><img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/prompt_ext.png?raw=true" alt="Example Query Chrome" style="width: 100%; max-width: 300px;"></td>
  </tr>
</table>

<img src="https://github.com/lavague-ai/LaVague/blob/update-chrome-readme/docs/assets/beatles-found.png?raw=true" alt="Launch Extension" style="width: 85%">


## LaVague Chrome Extension from local

To interact with a locally modified version of the extension, you'll need to take the following additional steps.

### 1. Setup

`yarn` or `npm install`

### 2. Build or run

You can build the project with:
`yarn build` or `npm run build`

This will build the project as a minified production build.

You can run the project with:
`yarn dev` or `npm run dev`

This will allow the extension built files to be updated in real time when changes are made in the code using `watch mode`.

### 3. Upload your local Chrome Extension

Finally, you can upload and test your locally modified Chrome extension by doing the following:
-   Go to the Extensions page [chrome://extensions/](chrome://extensions/)
-   Click the `Load unpacked` button
-   Select the `dist` directory

Ta-da! The extension has been successfully installed. Every time you update the extension code, click the refresh button on the LaVague extension.

### 4. Launch the LaVague Chrome Extension server

Finally you will need to serve an instance of `AgentServer` by running the following code:

```shell
pip install lavague-core lavague-server lavague-drivers-remote
```

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

Note, you will need to set a valid `OPENAI_API_KEY` environment variable for this to work.

You will now be able to interact with your LaVague extension in your Chrome navigator.