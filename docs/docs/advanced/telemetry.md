### 📈 Telemetry

By default, LaVague collects the following user data telemetry values to help us improve the product:

- Version of LaVague installed
- Code generated for each web action step
- LLM used (i.e GPT4)
- Multi modal LLM used (i.e GPT4)
- Randomly generated anonymous user ID
- Whether you are using a CLI command or our library directly
- The instruction used/generated
- The objective used (if you are using the agent)
- The chain of thoughts (if you are using the agent)
- The interaction zone on the page (bounding box)
- The viewport size of your browser
- The URL you performed an action on
- Whether the action failed or succeeded
- Error message, where relevant
- The source nodes (chunks of HTML code retrieved from the web page to perform this action)

This information helps us monitor the performance of LaVague and what features are most interesting to develop in the future.

## 🚫 Turn off all telemetry

If you want to turn off telemetry, you can set the `TELEMETRY_VAR` environment variable to`NONE`:

If you are running LaVague locally you can persistently set this variable for your environment before running LaVague with the following steps:

- Add `TELEMETRY_VAR=NONE` to your ~/.bashrc, ~/.bash_profile, or ~/.profile file (which file you have depends on your shell and its configuration)
- Use `source ~/.bashrc (or .bash_profile or .profile) to apply your modifications without having to log out and back in

In a notebook cell, you can use:
```
import os
os.environ['TELEMETRY_VAR'] = "NONE"
```

For our Docker, you can add the variable environment as part of your docker run command:
`docker run -e TELEMETRY_VAR=NONE [REST OF DOCKER RUN COMMAND]`
