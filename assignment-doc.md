# Tree Search for Language Model Agents

# Paper

### Useful links
- [arxiv link](https://arxiv.org/pdf/2407.01476)
- [code repo](https://jykoh.com/search-agents)
- [connected papers graph](https://www.connectedpapers.com/main/9345e55a21959948499cee997522aa5eac7ed588/Tree-Search-for-Language-Model-Agents/graph)
- [citing papers in Google Scholar](https://scholar.google.com/scholar?cites=13230322798034830837&as_sdt=2005&sciodt=0,5&hl=fr) (6 citations)
- [paperswithcode page](https://paperswithcode.com/paper/tree-search-for-language-model-agents) (mainly empty)
- [NotebookLM](https://notebooklm.google.com/notebook/db9807c1-b72f-48af-9dc3-9358e6a11992?_gl=1*10fcps2*_ga*MTI4MDU1NDA0NS4xNzMwOTc3Mzcz*_ga_W0LDH41ZCB*MTczMDk3OTE3OS4yLjAuMTczMDk3OTE4MC4wLjAuMA..)


### Abstract
Autonomous agents powered by language models (LMs) have demonstrated
promise in their ability to perform decision-making tasks such as web automation.
However, a key limitation remains: LMs, primarily optimized for natural language
understanding and generation, struggle with multi-step reasoning, planning, and
using environmental feedback when attempting to solve realistic computer tasks.
Towards addressing this, we propose an inference-time search algorithm for LM
agents to explicitly perform exploration and multi-step planning in interactive web
environments. Our approach is a form of best-first tree search that operates within
the actual environment space, and is complementary with most existing state-ofthe-art agents.
It is the first tree search algorithm for LM agents that shows effectiveness on realistic web tasks.
On the challenging VisualWebArena benchmark,
applying our search algorithm on top of a GPT-4o agent yields a 39.7% relative
increase in success rate compared to the same baseline without search, setting a
state-of-the-art success rate of 26.4%. On WebArena, search also yields a 28.0%
relative improvement over a baseline agent, setting a competitive success rate of
19.2%. Our experiments showcase the effectiveness of search for web agents, and
we demonstrate that performance scales with increased test-time compute. We
conduct a thorough analysis of our results to highlight improvements from search,
limitations, and promising directions for future work. Our code and models are
publicly released at jykoh.com/search-agents.

### Principle

![image](https://jykoh.com/search-agents/qualitative_48.png)

**Objective:**  
Fulfill the user instruction by going from a starting state to an (unknown) target state in a web environment.

**Principle:**  
Instead of choosing only one sequential path, we will treat this like a tree traversal problem,
with the ability to choose from multiple leaf nodes at each step and to go back to a previous (more promising) state.

**Hyperparameters:**
- max depth: max number of levels to explore in the tree
- branching factor: max number of children to explore at each step
- search budget: max number of steps to take during search

**Approach:**
Until stopping condition is met:
- select a state from the priority queue
- go to this state
- compute its score using the value function
- update the best score if needed
- explore `b` children states under depth condition `d` and add them to the priority queue

**Stopping conditions:**
- steps budget is exhausted
- there are no more states to explore
- goal state is reached

**Key components:**
- value function: to evaluate the quality of a state.
This is done by:
  - asking the language model if it is on the right track (Yes/No = 1/0)
  - sampling the language model to get a more accurate score (eg: 20 samples)
  - score will be the average of the samples
- backtracking method: being able to go back to a previous state
- priority queue: to select the next states to explore (can be breadth-first, depth-first, best-first, etc.)


### Reproducibility: ❓

Not assessed but [should be feasible](https://github.com/kohjingyu/search-agents?tab=readme-ov-file#end-to-end-evaluation-on-vwa).  
NOTE: need to setup [WebArena](https://github.com/web-arena-x/webarena) / [VisualWebArena](https://github.com/web-arena-x/visualwebarena) through an AWS AMI.


# Implementation

### Design and architectural choices

Implementation has been made through the `TreeSearchWebAgent` class, that inherits from `WebAgent`.  
The `run_step` method is the main place where the algorithm is implemented.

Please note that design choice decision relies mostly on ease of implementation rather than SWE best practices.


### Demonstration

If needed, simply install the project from source:
```bash
pip install -e .
```

Then run:
```bash
python assignmennt-demo.py
```


### Areas for improvement

Some serious shortcuts have been taken in the implementation and can be improved:
- backtracking: the cleanest way to implement it would be to go from the root node then downstream to the target node by re-playing actions.
Yet, for simplicity we just go the node URL.
  - this is a huge simplification that will cause the algorithm not to work with websites where the URL is not a "unique state identifier" (e.g.: Single Page Applications)
  - yet, this has practical advantages beyond implementation: it speeds up the way we get to the target state and avoid all the possible errors on the way (e.g.: cookie pop-up that does not exist anymore)
- value function: is a key component of the algorithm, yet it seems (empirically) quite binary even with sampling and averaging, so it probably requires more prompt engineering.
- action sampling: actions should be properly deduplicated (e.g.: by prompting a LLM) rather than by using a non-semantic and simplistic approach such as `SequenceMatcher`.

Also noticed but more package-related:
- parsing robustness:
  - output parsing of instructions sometimes fail (e.g: the model returned "# instructions:" instead of "### Instructions:")
  - some commands are not recognized
  ```bash
  ValueError: Unknown instruction: ** Use the search bar to search for "MTEB leaderboard".
  ```
- most of the time, when using a search bar, the model only input text but does not click / press Enter to validate it.


# Conclusions
- tree search is a promising approach to improve the performance of language model agents in web environments:
its general exploration capabilities can help to find the right path to the target state rather than getting stuck.  
In this way, it looks as a natural extension of standard sequential approaches.  
Furthermore, as can be seen in [WebArena leaderboard](https://docs.google.com/spreadsheets/d/1M801lEpBbKSNwP-vDBkC_pF7LdyGU1f_ufZb_NWNBZQ/edit?gid=0#gid=0)
those methods rank quite well in the leaderboard
- yet, its implementation is quite complex and results rely heavily on the quality of the value function and action sampling
- further tree methods, such as MCTS could be explored to improve agents performance and overcome the previously mentioned limitations
- finally, other research directions include different paradigms such as [Agent Workflow Memory](https://arxiv.org/pdf/2409.07429)
