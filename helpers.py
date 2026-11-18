import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def cf_api(method, params=None):
    params = params or {}
    url = "https://codeforces.com/api/" + method + "?" + urlencode(params)

    request = Request(url, headers={"User-Agent": "VornixCP/1.0"})

    with urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("status") != "OK":
        raise ValueError(data.get("comment", "Codeforces API error"))

    return data["result"]
