from dataclasses import dataclass, asdict
from typing import List
import json


@dataclass
class ViewItem:
    """Class for keeping track of view."""

    video_id: str = ""
    video_url: str = ""
    video_title: str = ""
    redirect_url: str = ""
    duration: int = 0

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class LikeItem:
    """Class for keeping track of like."""

    video: str = ""


@dataclass
class SubscribeItem:
    """Class for keeping track of subcribe."""

    channel: str = ""


@dataclass
class RequestItem:
    """Class for keeping track of an item in request."""

    request = List[ViewItem]
