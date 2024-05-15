# Documentation
## Introduction
Welcome to the Documentation section of our contributing guide. Effective documentation serves as a comprehensive manual on how to use, troubleshoot, and contribute to our project. 

Whether you're a seasoned contributor or a first-time participant, enhancing our documentation helps make our codebase and interfaces more accessible and easier to use.

## Getting started
### Prerequisites
Before contributing to our documentation, you should have a basic understanding of our project's goals and structure. Familiarity with [Markdown](https://www.markdownguide.org/basic-syntax/) syntax and [GitHub workflow](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git) is also beneficial.

Our full documentation is maintained directly in our GitHub repository and we use [MkDocs](https://www.mkdocs.org/) for all of it.

### Setup
To set up your environment for documentation work:

- [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) your own copy of the LaVague repository.

- Clone the repository with 
```
git clone https://github.com/your_username/LaVague.git
```

- Install required tools with 
```
pip install mkdocs mkdocs-jupyter mkdocs-material
```

- To see your changes in real-time, start serving the documentation locally with
```
mkdocs serve
```

You're now ready to contribute to our documentation!

## How to contribute
### Step by step guide
In the repository you'll find ```mkdocs.yml```, it is the file that holds our docs configuration. If you want to add new pages or reorganize the documentation tree, the ```nav```section in this file is where you should look. 

The ```docs``` folder contains all the actual content of the documentation. This is where you can modify existing content or create new pages. 

When you're ready to submit your changes as a PR, you can then submit your proposed additions for review, by pushing your changes to your forked repo and then [opening a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

### Examples
- To modify the architecture page:
    1. go to ```docs/docs/architecture.md``` and start modifying the file.

- To add a new page under the advanced section: 
    1. create a new ```your_new_page_name.md``` file under ```docs/docs/advanced``` and add some content. 
    2. In the ```nav``` section in ```mkdocs.yml```, add a link to your new page in the appropriate section. 


## Best practices
### FAQ
- I can't see my changes on the documentation

Make sure you've executed the ```mkdocs serve``` command from the root of the repo of your local clone and that you're looking on the right local URL ```http://127.0.0.1:8000/en/latest/```

### Need help ?
Join our [Discord](https://discord.gg/invite/SDxn9KpqX9) to ask us any questions!