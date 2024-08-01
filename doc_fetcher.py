import requests
import requests_cache
requests_cache.install_cache('requests_cache', expire_after=3600*24)

def clear_cache():
    requests_cache.clear()

def get_raw_stex_url(archive: str, filename: str):
    return f"https://gl.mathhub.info/{archive}/-/raw/main/source/{filename}"


def get_raw_stex(archive: str, filename: str):
    url = get_raw_stex_url(archive, filename)
    # print(f'getting url: {url}')
    return requests.get(url).text
