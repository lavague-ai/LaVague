from __future__ import annotations
from typing import Optional, Generator, List
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer, QueryBundle, PromptTemplate
from llama_index.core.base.llms.base import BaseLLM
from string import Template
import ast
from llama_index.core.base.embeddings.base import BaseEmbedding
from lavague.core.extractors import BaseExtractor, PythonFromMarkdownExtractor
from lavague.core.retrievers import BaseHtmlRetriever, OpsmSplitRetriever
from lavague.core.base_driver import BaseDriver
from lavague.core.action_template import ActionTemplate
from lavague.core.context import Context, get_default_context

ACTION_ENGINE_PROMPT_TEMPLATE = ActionTemplate(
    """
{driver_capability}

HTML:
{context_str}
Query: {query_str}
Completion:

""",
    PythonFromMarkdownExtractor(),
)


class ActionEngine:
    """
    ActionEngine leverages the llm model and the embedding model to output code from the prompt and the html page.

    Args:
        driver (`BaseDriver`):
            The Web driver used to interact with the headless browser
        llm (`BaseLLM`)
            llama-index LLM that will generate the action
        embedding (`BaseEmbedding`)
            llama-index Embedding model
        retriever (`BaseHtmlRetriever`)
            Specify which algorithm will be used for RAG
        prompt_template (`PromptTemplate`)
            Squelette of the final prompt
        extractor (`BaseExtractor`)
            Specify how to extract the final code from the llm answer
    """

    def __init__(
        self,
        driver: BaseDriver,
        llm: BaseLLM = get_default_context().llm,
        embedding: BaseEmbedding = get_default_context().embedding,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = ACTION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = ACTION_ENGINE_PROMPT_TEMPLATE.extractor,
    ):
        self.driver: BaseDriver = driver
        self.llm: BaseLLM = llm
        self.embedding: BaseEmbedding = embedding
        self.retriever: BaseHtmlRetriever = retriever
        self.prompt_template: PromptTemplate = prompt_template.partial_format(
            driver_capability=driver.get_capability()
        )
        self.extractor: BaseExtractor = extractor

    @classmethod
    def from_context(
        cls,
        context: Context,
        driver: BaseDriver,
        retriever: BaseHtmlRetriever = OpsmSplitRetriever(),
        prompt_template: PromptTemplate = ACTION_ENGINE_PROMPT_TEMPLATE.prompt_template,
        extractor: BaseExtractor = ACTION_ENGINE_PROMPT_TEMPLATE.extractor,
    ) -> ActionEngine:
        """
        Create an ActionEngine from a context
        """
        return cls(
            driver,
            context.llm,
            context.embedding,
            retriever,
            prompt_template,
            extractor,
        )

    def _get_query_engine(self, streaming: bool = True) -> RetrieverQueryEngine:
        """
        Get the llama-index query engine

        Args:
            html: (`str`)
            streaming (`bool`)

        Return:
            `RetrieverQueryEngine`
        """

        response_synthesizer = get_response_synthesizer(
            streaming=streaming, llm=self.llm
        )

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=self.retriever.to_llama_index(self.driver, self.embedding),
            response_synthesizer=response_synthesizer,
        )

        query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": self.prompt_template}
        )

        return query_engine

    def get_nodes(self, query: str) -> List[str]:
        """
        Get the nodes from the html page

        Args:
            html (`str`): The html page

        Return:
            `List[str]`: The nodes
        """
        source_nodes = self.retriever.retrieve_html(
            self.driver, self.embedding, QueryBundle(query_str=query)
        )
        source_nodes = [node.text for node in source_nodes]
        return source_nodes

    def get_action_from_context(self, context: str, query: str) -> str:
        """
        Generate the code from a query and a context
        """
        prompt = self.prompt_template.format(context_str=context, query_str=query)
        response = self.llm.complete(prompt).text
        code = self.extractor.extract(response)
        return code

    def get_action(self, query: str) -> Optional[str]:
        """
        Generate the code from a query

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page

        Return:
            `str`: The generated code
        """
        query_engine = self._get_query_engine(streaming=False)
        response = query_engine.query(query)
        code = response.response
        return self.extractor.extract(code)

    def get_action_streaming(self, query: str) -> Generator[str, None, None]:
        """
        Stream code from a query and an url

        Args:
            query (`str`): Instructions given at the end of the prompt to tell the model what to do on the html page
            url (`str`): The url of the target html page

        Return:
            `Generator[str, None, None]`: Generator for the generated code
        """
        query_engine = self._get_query_engine(streaming=True)
        streaming_response = query_engine.query(query)
        for text in streaming_response.response_gen:
            yield text
            
    def rephrase_query(self, query: str) -> List[dict]:
        """
        Rephrase the query

        Args:
            query (`str`): The query to rephrase

        Return:
            `List[dict]`: The rephrased query as a list of dictionaries
        """
        
        rephrase_prompt = Template("""
        You are an AI system designed to convert text-based instructions for web actions into standardized instructions.

        Here are previous examples:

        Text instruction: Type 'Command R plus' on the search bar with placeholder "Search ..."
        Standardized instruction: [{'query':'input"Search ..."', 'action':'Click on the input "Search ..." and type "Command R plus"'}]

        Text instruction: Click on the search bar with placeholder "Rechercher sur Wikipédia", type "Yann LeCun," and press Enter.
        Standardized instruction: [{'query':'input"Rechercher sur Wikipédia"', 'action':'Click on the input "Rechercher sur Wikipédia", type "Yann LeCun," and press Enter'}]

        Text instruction: Click on 'Installation', next to 'Effective and efficient diffusion'
        Standardized instruction: [{'query':'button"Installation"', 'action':'Click on "Installation"'}]
        
        Text instruction:  Locate the input element labeled "Email Address" and type in "example@example.com". Locate the input element labeled "First name" and type in "John". Locate the input element labeled "Last name" and type in "Doe". Locate the input element labeled "Phone" and type in "555-555-5555".
        Standardized instruction: [{'query':'input"Email Address"', 'action':'Click on the input "Email Address" and type "example@example.com"'}, {'query':'input"First name"', 'action':'Click on the input "First name" and type "John"'}, {'query':'input"Last name"', 'action':'Click on the input "Last name" and type "Doe"'}, {'query':'input"Phone"', 'action':'Click on the input "Phone" and type "555-555-5555"'}]

        Text instruction: In the login form, locate the input element labeled “Username” and type “user123”. Locate the input element labeled “Password” and type “pass456”.
        Standardized instruction: [{'query':'input”Username”', 'action':'Click on the input “Username” and type “user123”'}, {'query':'input”Password”', 'action':'Click on the input “Password” and type “pass456”'}]
        
        Text instruction: Press the button labeled “Submit” at the bottom of the form.
        Standardized instruction: [{'query':'button”Submit”', 'action':'Click on the button “Submit”'}]
        
        Text instruction: ${instruction}
        Standardized instruction:
        """)
        
        rephrase_prompt = rephrase_prompt.safe_substitute(instruction=query)
        response = self.llm.complete(rephrase_prompt).text
        response = response.strip('```json\n').strip('\n``` \n')
        rephrased_query = ast.literal_eval(response)
        return rephrased_query

