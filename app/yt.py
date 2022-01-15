from asyncio.log import logger
import youtube_dl
import loguru


def my_hook(d):
    if d["status"] == "finished":
        print("Done downloading, now converting ...")


ydl_opts = {
    "outtmpl": ".",
    "writesubtitles": True,
    "format": "mp4",
    "writethumbnail": True,
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #a = ydl.download(["https://studio.youtube.com/channel/UClS6845cywUS0IzUGYapIpQ"])
    a = ydl.extract_info("https://studio.youtube.com/channel/UClS6845cywUS0IzUGYapIpQ", download=False)
    print(a)


_VALID_URL = r"https?://(?:www\.)?youtube\.com/watch\?v=(?P<id>[0-9A-Za-z_-]{1,10})$"
