## Setup your dev environment

### 1. Setup

`yarn` or `npm install`

### 2. Running

`yarn dev` or `npm run dev`

This will allow the extension built files to be updated in real time when changes are made in the code.

### 3. Building

`yarn build` or `npm run build`

Build the project, usually used for publishing it on the store.

## Test the Chrome extension

### Run locally

`yarn dev` or `npm run dev`

It will build the project in watch mode. Project build in `dist` directory will be updated upon save.

### Test your extension

-   Go to the Extensions page [chrome://extensions/](chrome://extensions/)
-   Click the `Load unpacked` button
-   Select the `dist` directory

Ta-da! The extension has been successfully installed. Every time you update the extension code, click the refresh button on the LaVague extension.

## Setup LaVague Driver Server

The LaVague extension communicates with a Driver Server using Websockets.

```shell
pip install lavague-core lavague-drivers-remote
```

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.driverserver import DriverServer
from lavague.core.extractors import JsonFromMarkdownExtractor

driver = DriverServer()
world_model = WorldModel()
action_engine = ActionEngine(driver, extractor=JsonFromMarkdownExtractor())
agent = WebAgent(world_model, action_engine)
driver.accept_prompts(agent)
```
