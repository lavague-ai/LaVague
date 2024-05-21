from llama_index.core import PromptTemplate
from lavague.core.extractors import BaseExtractor


class ActionTemplate:
    """
    Define a template, extractor pair
    """

    def __init__(self, prompt_template: str, extractor: BaseExtractor):
        self.prompt_template: PromptTemplate = PromptTemplate(prompt_template)
        self.extractor: BaseExtractor = extractor
