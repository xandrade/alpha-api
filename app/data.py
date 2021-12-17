from dataclasses import dataclass, asdict
from typing import List
import json


@dataclass
class ViewItem:
    """Class for keeping track of view."""

    video: str = ""
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


if __name__ == "__main__":

    videos = [
        "pAVk0tLJvA0",
        "QMyahx3soiM",
        "ffC08UqcFw0",
        "IeXppHVrsug",
        "EvLcyB9VNrU",
        "gXRGI0NE-7E",
        "wxGyA9mGRK8",
        "-fukPEXrQas",
        "8fGe2sidmGg",
        "1JmBBX8KOOQ",
        "kvza7Y2_FNk",
        "-xEzBOO337A",
        "HtVBWnQNaGE",
        "EGGM94l1fKU",
        "FB12t1_LHWI",
        "r92LBThuBmc",
        "7ZEdnyHQ_No",
        "ahaI1xRKYYk",
        "ERFin10XwDw",
        "Te7k0T_hkkI",
        "mwthQLYEcNk",
        "KmcjB_Fdxm0",
        "CTgbZ8tOu2c",
        "96r-OdsZcgE",
        "3Slh4cICQDs",
        "_Lssqh8m7oE",
        "-gk1Lc6hE2Y",
        "lPRo4B36AaA",
        "bdl7GgI7egY",
        "n3PUlsd5tlc",
        "Wmug-C65tGI",
        "PvXZBcLuTPs",
        "QMyahx3soiM",
        "GnuHsc1S5vY",
    ]

    requests = RequestItem()

    requests.request = [ViewItem(video=video, duration=30) for video in videos]

    requests.request.append(ViewItem(video="antonio", duration=30))

    print(requests.request)
