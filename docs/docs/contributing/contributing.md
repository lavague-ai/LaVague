# LaVague Guide for Contributors 🌊

Thanks for your interest in the project! We really appreciate all contributions, from bug reports, to suggestions to helping us build new features. Your support is vital in helping us build an awesome tool!

In this guide, we'll outline how you can contribute to the project.

If you have any further questions, please contact us on [Discord](https://discord.gg/SDxn9KpqX9).

## Reporting bugs

We track bugs using [GitHub issues](https://github.com/lavague-ai/LaVague/issues/).

You can report a bug by opening a [new issue](https://github.com/lavague-ai/LaVague/issues/new/choose) using the 'bug report' template.

Please check that your bug has not already been reported before submitting a bug report and include as many details as possible to help us fix bugs faster!

## Suggesting new features

You can make a [new feature request](https://github.com/lavague-ai/LaVague/issues/new/choose) by creating a new issue and selecting the 'new feature' template.

Please provide as much information as possible: the behavior you want, why, and examples of how this feature would be used!

## Contributing to the codebase

### Identifying a feature to work on

You can see the features we're looking for help on by selecting the ['help wanted' label in our listed issues](https://github.com/lavague-ai/LaVague/labels/help%20wanted).

If one of these interests you, or you see another unassigned issue that you'd like to work on, let us know in the #contribute Discord channel or by commenting in the issue!

If you would like to work on a feature that is not listed in our GitHub issues, let us know by creating a new issue and waiting for us to validate it with the 'accepted' label.

### Setting up your local environment

Firstly, you'll need to [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) the LaVague repo.

You can create a local dev environment, by creating and activating a virtual Python environment:

```
python -m venv env .
source env/bin/activate
```

You'll then need to clone your forked repository using git:

```
git clone https://github.com/<username>/LaVague.git
cd LaVague
```

We then need to download the Chrome driver which is necessary for interfacing with the Chrome browser with Selenium. You can do this by running our dependencies script:

```
bash install-dependencies.sh
```

> For instructions on how to install a driver for a different browser or instructions for downloading drivers on a different OS, [see the Selenium documentation](https://selenium-python.readthedocs.io/installation.html#drivers)

Finally you can install the LaVague package locally in "editable" mode with the following command:

```
pip install -e .[dev]
```

### Pull requests

Once you've finished building your feature, you can submit it for review by [opening a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

When submitting a PR, please:

- Use a descriptive title
- [Link](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) to the issue you were working on in the PR
- Add any relevant information to the description that you could help us review your code
- [Rebase your branch](https://docs.github.com/en/get-started/using-git/about-git-rebase) against the latest version of `main`.
- **Coming soon** Check your branch passes all GitHub actions pass.

If you need any help or want to discuss the feature you are working on more before submitting, reach out to us on [Discord](https://discord.gg/SDxn9KpqX9)!

### Contributing to the documentation

To contribute to the documentation, firstly you'll need to [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) the LaVague repo.

You'll then need to clone your forked repository using git:

```
git clone https://github.com/<username>/LaVague.git
cd LaVague
```

#### Adding to the documentation

If you want to create a new page or section, you should define this in the `mkdocs.yml` file in the `nav` section.

You should place your file or section into a relevantly named folder within the `docs/docs` folder.

#### How to test your updates:

Firstly, from the root of the repo, create a virtual environment and install the documentation requirements:

```
python -m venv my-env .
source my-env/bin/activate
pip install -r docs/requirements.txt
```

Next, you can load a preview of the documentation in the browser with the following command:
```
mkdocs serve --strict
```

Please check in your browser that all looks correct before submitting your proposed updates to us.

#### Submitting your proposed changes

You can then submit your proposed additions for review, by [opening a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

If you have any issues with this process or with testing your changes, send us a message on our [Discord `support` channel](https://discord.gg/SDxn9KpqX9)).

## License

Note that all contributions made to this project are subject to the project's [Apache 2.0 License](https://github.com/lavague-ai/LaVague/blob/main/LICENSE) 
