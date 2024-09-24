
from pydantic import BaseModel
from lavague.action import Action

class ExtractionOutput(BaseModel):
    xpath: str
    description: str
    text: str
    outer_html: str

class WebExtractionAction(Action[ExtractionOutput]):
    pass