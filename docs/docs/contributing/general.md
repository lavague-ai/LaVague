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

## 👨‍💻 Dev environment

### Fork & clone repo

To get started working locally on LaVague, firstly make sure you have have [forked](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) and then clone the LaVague repo to your local environment:

```bash
git clone https://github.com/USER_NAME/LaVague
```

### Installing LaVague with poetry

The LaVague repo is made up of several sub-packages. We recommend using [poetry](https://python-poetry.org/) for local installation of LaVague.

For Linux users with debian-based distributions, you can do this by running:

```bash
sudo apt update
sudo apt install pipx
pipx install poetry
```

> For installation on other Linux distributions or operating systems, see the [official Poetry installation guide](https://python-poetry.org/docs/#installing-with-pipx).

You can now install the lavague package from the root of your forked repo:

```bash
poetry shell
poetry install --with dev
```

The poetry shell command will create a virtual environment specifically for this package.

This `install` command will install all the default packages in our LaVague package bundle - you can see which packages are included in this bundle in out `pyproject.toml` file at the root of our repo.

!!! note "Non-default package installation"

    If you want to use a non-default integration, you can then locally install the specific package with `pip`.

    For example, if you want to use a non-default context such as the Gemini context. You would need to run:

    ```bash
    pip install -e lavague-integrations/contexts/lavague-contexts-gemini
    ```

### Previewing local modifications

For local modifications to a package's files to be taken into account, you can locally install that specific package with `pip -e`.

For example, if you are making changes within the lavague.core package. You can run the following command:

```bash
pip install -e lavague-core
```