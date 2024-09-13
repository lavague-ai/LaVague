from PIL import Image
import base64
import os
from typing import TypeVar, Generic, Dict, Type, Optional
from pydantic import BaseModel, validate_call
import time

T = TypeVar("T")


class Action(BaseModel, Generic[T]):
    """Action performed by the agent."""

    engine: str
    args: T
    preaction_screenshot: Optional[str] = None
    postaction_screenshot: Optional[str] = None

    @property
    def preaction_screenshot_image(self) -> Image:
        return (
            Image.open(self.preaction_screenshot) if self.preaction_screenshot else None
        )

    @property
    def postaction_screenshot_image(self) -> Image:
        return (
            Image.open(self.postaction_screenshot)
            if self.postaction_screenshot
            else None
        )

    @classmethod
    def parse(cls, action_dict: Dict) -> "Action":
        return cls(**action_dict)


class ActionParser(BaseModel):
    engine_action_builders: Dict[str, Type[Action]]
    store_images: bool = False
    storage_path: str = "./screenshots"
    _image_index = 0

    def __init__(self):
        super().__init__(engine_action_builders={})
        os.makedirs(self.storage_path, exist_ok=True)

    @validate_call
    def register(self, engine: str, action: Type[Action]):
        self.engine_action_builders[engine] = action

    def unregister(self, engine: str):
        if engine in self.engine_action_builders:
            del self.engine_action_builders[engine]

    def parse(self, action_dict: Dict) -> Action:
        engine = action_dict.get("engine")

        if self.store_images:
            action_dict = action_dict.copy()
            action_dict["preaction_screenshot"] = self._store_image(
                action_dict.get("preaction_screenshot")
            )
            action_dict["postaction_screenshot"] = self._store_image(
                action_dict.get("postaction_screenshot")
            )

        target_type = self.engine_action_builders.get(engine, Action)
        return target_type.parse(action_dict)

    def _store_image(self, image: str) -> str:
        """Store image on disk and return absolute path"""
        if image is None:
            return None
        self._image_index += 1
        timestamp = str(int(time.time()))
        image_parts = image.split(",", 1)
        if len(image_parts) == 2:
            header, encoded_data = image_parts
            extension = header.split("/")[1].split(";")[0]
            image_name = f"{timestamp}_{self._image_index}.{extension}"
        else:
            encoded_data = image_parts[0]
            image_name = f"{timestamp}_{self._image_index}.png"
        image_path = os.path.join(self.storage_path, image_name)
        image_data = base64.b64decode(encoded_data)
        with open(image_path, "wb") as file:
            file.write(image_data)
        return os.path.abspath(image_path)


DEFAULT_PARSER = ActionParser()
