from pydantic import BaseModel
from lavague.sdk.action import Action


class ExtractionOutput(BaseModel):
    xpath: str
    description: str
    text: str
    outer_html: str


class WebExtractionAction(Action[ExtractionOutput]):
    pass
