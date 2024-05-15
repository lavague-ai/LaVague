# General contribution guidelines

## 🪲 Reporting bugs

We track bugs using [GitHub issues](https://github.com/lavague-ai/LaVague/issues/).

You can report a bug by opening a [new issue](https://github.com/lavague-ai/LaVague/issues/new/choose) using the 'bug report' template.

Please check that your bug has not already been reported before submitting a bug report and include as many details as possible to help us fix bugs faster!

## 💡Suggesting new features

You can make a [new feature request](https://github.com/lavague-ai/LaVague/issues/new/choose) by creating a new issue and selecting the 'new feature' template.

Please provide as much information as possible: the behavior you want, why, and examples of how this feature would be used!

## 👩‍💻 Code contribution process

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

- 📢 We outline tasks on our backlog: we recommend you check out issues with the help-wanted labels & good first issue labels
- 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue!
- 🤝 We will discuss with you and assign you the task with a community assigned label
- 💬 We will then be available to discuss this task with you
- 🍴 [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) the LaVague repo!
- ⬆️ When you are ready, submit your work for review by [opening a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)
- ✅ We will review & merge your code or request changes/give feedback

!!! tip "QA"
    When submitting a PR, please:

    - Use a descriptive title
    - [Link](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) to the issue you were working on in the PR
    - Add any relevant information to the description that you could help us review your code
    - [Rebase your branch](https://docs.github.com/en/get-started/using-git/about-git-rebase) against the latest version of `main`.
    - Check your branch passes all GitHub actions pass.

> If you want any help or guidance on developing the feature you are working on more before submitting, reach out to us on [Discord](https://discord.gg/SDxn9KpqX9)!

⚠️ Note, we aim to merge as many PRs as possible but we cannot guarantee to merge PRs and they are subject to our review process.

## 🐋 Setting up your dev container (Docker integration)

Feel free to make use of our pre-configured dev container in VSCode to quickly set up a dev environment.

!!! note "Pre-requisites"

    - 🐋 Docker: Ensure Docker is installed and running on your machine
    - Visual Studio Code + Visual Studio Code's Remote - Containers Extension
    - Ensure you have forked the LaVague repo and git cloned it locally

To open the project in our dev container you need to:

1. Open VSCode at the root of your clone of your forked LaVague repo.
2. Click on the blue "><" icon in the bottom left corner, then select "Reopen in Container" in the drop-down menu that then appears.

VS Code will then build the container based on the Dockerfile and devcontainer.json files in the .devcontainer folder. This will install all necessary dependencies and install the current LaVague repo in 'edit' mode. You are now ready to run LaVague CLI commands and modify the source code files as required.

⏳ Note, this process might take a few minutes the first time you run it.

> Note, if you want to view the Gradio generated with `lavague [OPTIONS] launch` in-browser on your host machine, you'll need to use the generated `public URL`!