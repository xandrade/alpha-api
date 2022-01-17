from asyncio.log import logger

# import youtube_dl
import urllib.request
import json
import urllib


_VALID_URL = r"https?://(?:www\.)?youtube\.com/watch\?v=(?P<id>[0-9A-Za-z_-]{1,10})$"


def get_video_title(video_id):
    data = get_video_info(video_id)
    if data:
        return data["title"]
    else:
        return None


def get_video_info(video_id):
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % video_id}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())

    return data if data else None


def get_videos():

    videos = [
        # "saJUAhmjGoA", # SOS Life
        # "L1mPYhHs7Io&list=UUSHVrCpsFXdnxC34qUj7nOp5w",  # SOS Life
        "rL7yMKkHAdI",  # 13-Jan-2022 203 views -> 13-Jan-2022 396 views
        # "DelrwCeXkvg",  # Pavel 3705 14-Jan-2022 3:41pm -> 3,803 views 15-Jan-2022 2:33pm
        "KOysJXrPTtw",
        "FaIvDpyBNDY",
        "-yHJZqoKyrI",
        "_ifWAxhJjoA",
        "-FJq8X9YXr4",
        "IUOxW9a7Ds4",
        "01GTELF_PII",
        "GQeY_P-zxPQ",
    ]
    return videos


if __name__ == "__main__":

    videos = get_videos()
    for video_id in videos:
        print(get_video_title(video_id=video_id))
