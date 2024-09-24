# Trajectories

Trajectories are classes returned by LaVague agents containing information about an agent run and the list of actions performed.

They contain the following attributes:

- `start_url`: The URL provided as input for this run
- `objective`: The text objective that was given as input for this run
- `run_id`: A unique run id
- `output`: Text output where expected
- `actions`: The series of [actions](./actions.md) generated during this run
- `status`: Whether the agent run was `completed` or `failed`

![Trajectory light](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/trajectory.png#only-light)
![Trajectory dark](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/trajectory-dark.png#only-dark)
## Integrations

This Trajectory can be passed to `exporter` functions to be converted into replayable automation code in the format required your use case.

![Trajectory Export light](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/trajectory-export.png#only-light)
![Trajectory Export dark](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/trajectory-export-dark.png#only-dark)

Currently, we only provide a `PyTest exporter`, but we plan to work with the community to build exporters to cover a wide range of use cases.