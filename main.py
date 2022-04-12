import argparse
import asyncio
import httpx
import re
import sys
import uuid

regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!\[\,\]:%_\+.~#?&\/\/=]*)"
types = ["image/gif", "image/png", "image/jpeg", "image/bmp", "image/webp"]


class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    NONE = '\033[0m'


def generate_urls(url, dict, arr, result, i=0):
    length = len(dict)
    if i < length:
        keys = list(dict)
        k = keys[i]
        v = dict[k]
        min = v[0]
        max = v[1]
        i = i + 1
        for n in range(min, max + 1):
            arr[i - 1] = n
            if i == length:
                r = url
                for x in range(len(arr)):
                    r = r.replace(keys[x], str(arr[x]), 1)
                result.append(r)
            generate_urls(url, dict, arr, result, i)


def get_intervals_and_parse(url):
    intervals = {}
    tokenized_url = url
    arr = re.findall(r"\[([^]]*)\]", tokenized_url)
    for item in arr:
        guid = uuid.uuid4().hex
        tokenized_url = tokenized_url.replace(f"[{item}]", guid, 1)
        interval = [int(x) for x in item.split(",")]
        intervals[guid] = interval
    return intervals, tokenized_url


async def download_file(url, output):
    print(f"[+] Trying {url} ...")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=1000)
            if r.is_success:
                print(f"{Color.YELLOW} [+] Discovered {url} ! {Color.NONE}")
                mime = r.headers["Content-Type"]
                if mime in types:
                    ext = mime.split("/")[-1]
                    file = f"{uuid.uuid4()}.{ext}"
                    path = f"{output}\\{file}"
                    with open(path, "wb") as f:
                        f.write(r.content)
                    print(f"{Color.GREEN} \t[+] Downloading {file} ... {Color.NONE}")
        except TimeoutError as ex1:
            print(f"{Color.RED} [!] Timeout error on {url}. Error details: {ex1}) {Color.NONE}")
        except Exception as ex:
            print(f"{Color.RED} [!] Unhandled error when downloading on {url}. Error details: {ex}) {Color.NONE}")


def parse_args():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--url", "-u", type=str,
                            help="URL with intervals, example: http://website.com/[i,j]/photo[i,j].jpg")
        parser.add_argument("--output", "-o", type=str, help="output directory for saving the downloaded files",
                            default=".")
        args = parser.parse_args()
        url = args.url
        output = args.output
        if re.fullmatch(pattern=regex, string=url):
            return url, output
        else:
            print(f"{Color.RED} [!] Not a valid URL {Color.NONE}")
    except Exception as ex:
        print(f"{Color.RED} [!] Unhandled error parsing arguments: {ex}) {Color.NONE}")
    sys.exit(1)


async def main():
    url, output = parse_args()
    print("[+] Generating URLs ...")
    intervals, tokenized_url = get_intervals_and_parse(url)
    aux_arr = [0] * len(intervals)
    url_list = []
    generate_urls(tokenized_url, intervals, aux_arr, url_list)
    tasks = []
    print(f"[+] Searching for files in {len(url_list)} URLs ...")
    for u in url_list:
        t = asyncio.create_task(download_file(u, output))
        tasks.append(t)
    await asyncio.wait(tasks)
    sys.exit(0)


asyncio.run(main())
