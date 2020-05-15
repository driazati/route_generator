import requests
import json

try:
    from secret import bing_api_key
except Exception as e:
    bing_api_key = None

def clean(s):
    return s.replace("(", "").replace("'", "").replace(")", "").strip()

def get_coords(state, city, address):
    url = f"Locations/US/{state}/{city}/{address}"
    r = bing_api("get", url)
    return Coord(*r["resourceSets"][0]["resources"][0]["point"]["coordinates"])



def bing_api(method, url, data=None):
    if bing_api_key is None:
        raise RuntimeError("Could find find api key in secret.py")
    base = "http://dev.virtualearth.net/REST/v1/"
    if method == "get":
        if data is None:
            data = {}
        new_data = {**data}
        new_data["key"] = bing_api_key
        response = requests.get(base + url, params=new_data)
        return json.loads(response.content.decode("utf-8"))
    if method == "post":
        response = requests.post(base + url, params={"key": bing_api_key}, data=data)
        return json.loads(response.content.decode("utf-8"))
    else:
        raise RuntimeError("Unsupported method")



def driving_distance(unordered_coordinates):
    if len(unordered_coordinates) == 1:
        return 0, {}

    params = {f"waypoint.{index + 1}": f"{c[0]},{c[1]}" for index, c in enumerate(unordered_coordinates)}
    params['optimizeWaypoints'] = True
    params['optimize'] = 'timeWithTraffic'

    r = bing_api('get', 'Routes/Driving', params)
    data = r['resourceSets'][0]['resources'][0]
    seconds = data['travelDurationTraffic']
    return seconds / 60, data