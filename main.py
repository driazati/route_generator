import os
import requests
import collections
import csv
import json
from math import radians, cos, sin, asin, sqrt
import pprint
import pickle
import urllib.parse
import random
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import great_circle
import matplotlib
import matplotlib.pyplot as plt
import random

Coord = collections.namedtuple("Coord", ["lat", "lon"])

# import torch

# from kmeans_pytorch import kmeans


# data_size, dims, num_clusters = 1000, 2, 3
# x = np.random.randn(data_size, dims) / 6
# x = torch.from_numpy(x)

# print(x.shape)
# breakpoint()

# cluster_ids_x, cluster_centers = kmeans(
#     X=x, num_clusters=num_clusters, distance='euclidean', device=torch.device('cpu')
# )

# import sys
# sys.exit(0)



def bing_api(method, url, data=None):
    base = "http://dev.virtualearth.net/REST/v1/"
    if method == "get":
        if data is None:
            data = {}
        new_data = {**data}
        new_data["key"] = api_key
        response = requests.get(base + url, params=new_data)
        return json.loads(response.content.decode("utf-8"))
    if method == "post":
        response = requests.post(base + url, params={"key": api_key}, data=data)
        return json.loads(response.content.decode("utf-8"))
    else:
        raise RuntimeError("Unsupported method")


state = "GA"
city = "atlanta"


def get_coords(address):
    print(address)
    url = f"Locations/US/{state}/{city}/{address}"
    r = bing_api("get", url)
    return Coord(*r["resourceSets"][0]["resources"][0]["point"]["coordinates"])


requesters = []

reader = csv.DictReader(open("file.csv", "r"))


def clean(s):
    return s.replace("(", "").replace("'", "").replace(")", "").strip()


loaded_addresses = pickle.load(open("addresses.pkl", "rb"))

num_skipped = 0
num_total = 0
num_with_recent_deliveries = 0
addresses = loaded_addresses
MIN_DELIVERY_WINDOW = 30
for row in reader:
    num_total += 1
    # pprint.pprint(row)
    if int(row["Days since delivery"]) < MIN_DELIVERY_WINDOW:
        # Skip people who have had deliveries in the last month
        # print("meow")
        num_with_recent_deliveries += 1
        continue
    address = row["Computed Address"]
    if address in loaded_addresses:
        lat, lon = loaded_addresses[address]
        coords = Coord(lat=lat, lon=lon)
    else:
        print("No record found for", address)
        num_skipped += 1
        # continue
        # print("Calling bing API")
        # try:
        # 	coords = get_coords(address)
        # except:
        # 	print("Failed to get", address)
    addresses[address] = (coords.lat, coords.lon)
    requesters.append(
        {"row": row, "coords": coords, "distances": [], "visited": False,}
    )
    # if num_total > 50:
    # 	break

pickle.dump(addresses, open("addresses.pkl", "wb"))

# requesters = requesters[:10]

print(" ======= stats =======")
print("total entries:", num_total)
print(
    f"skipped (delivery was in the last {MIN_DELIVERY_WINDOW} days):",
    num_with_recent_deliveries,
)
print("skipped (address was bad):", num_skipped)
print("calculating routes for:", len(requesters))


# group_size = 5
# from torchvision import transforms
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint

locations_by_idx = []
lats = []
lons = []

for r in requesters:
    locations_by_idx.append([r["coords"].lat, r["coords"].lon])
    lats.append(r["coords"].lat)
    lons.append(r["coords"].lon)


GROUP_SIZE = 5
num_clusters = len(requesters) // GROUP_SIZE


# cluster_ids_x, cluster_centers = kmeans(
#     X=x, num_clusters=num_clusters, distance='euclidean', device=torch.device('cpu'), max_iter=200
# )

# import pandas as pd, numpy as np

# from sklearn.mixture import GaussianMixture


# # from shapely.geometry import MultiPoint
# # df = pd.read_csv('summer-travel-gps-full.csv')
# # coords = df.as_matrix(columns=['lat', 'lon'])

coords = np.array(locations_by_idx)

# kms_per_radian = 6371.0088
# epsilon = 0.5 / kms_per_radian
# # db = DBSCAN(eps=epsilon, min_samples=5, algorithm='ball_tree', metric='haversine').fit(coords)
# db = DBSCAN(eps=epsilon, min_samples=5, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
# cluster_labels = db.labels_
# breakpoint()
# num_clusters = len(set(cluster_labels))
# clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])
# print('Number of clusters: {}'.format(num_clusters))

# # breakpoint()
def kmeans():
    kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(coords)
    # gm = GaussianMixture(n_components=num_clusters, random_state=0).fit(points)
    groups = []
    for i in range(kmeans.labels_.max() + 1):
        groups.append([])

    i = 0
    for index in kmeans.labels_:
        groups[index].append(i)
        i += 1
    return groups


# Start pairing up requesters
# def custom():
# 	groups = []
# 	indices = [i for i in range(len(requesters))]
# 	random.shuffle(indices)
# 	for r in requesters:
# 		r['visited'] = False

# 	for this_index in indices:
# 		r = requesters[this_index]
# 		if r['visited']:
# 			continue
# 		r["visited"] = True

# 		group = [this_index]
# 		center = [r['coords'].lat, r['coords'].lon]
# 		for i in range(GROUP_SIZE - 1):
# 			# find the closest non-visited neighbor, add them to the group with this one,
# 			# and mark it visited
# 			min_distance = 9999999999999
# 			min_requester_index = -1
# 			for other_index, other_r in enumerate(requesters):
# 				if other_r['visited']:
# 					# Skip visited
# 					continue
# 				dist = great_circle(center, other_r['coords']).km
# 				if dist < min_distance:
# 					min_distance = dist
# 					min_requester_index = other_index

# 			if min_requester_index != -1:
# 				item = requesters[min_requester_index]
# 				center[0] = (center[0] * len(group) + item['coords'].lat) / (len(group) + 1)
# 				center[1] = (center[1] * len(group) + item['coords'].lon) / (len(group) + 1)
# 				group.append(min_requester_index)
# 				item["visited"] = True
# 		groups.append(group)
# 	return groups


# calculate distance matrix
print("calculating distances")
for r in requesters:
    for other_r in requesters:
        r["distances"].append(great_circle(r["coords"], other_r["coords"]).km)


def custom():
    groups = []
    indices = [i for i in range(len(requesters))]
    random.shuffle(indices)
    for r in requesters:
        r["visited"] = False

    for this_index in indices:
        r = requesters[this_index]
        if r["visited"]:
            continue
        r["visited"] = True

        group = [this_index]
        center = [r["coords"].lat, r["coords"].lon]
        for i in range(GROUP_SIZE - 1):
            # find the closest non-visited neighbor, add them to the group with this one,
            # and mark it visited
            min_distance = 9999999999999
            min_requester_index = -1
            for other_index, other_dist in enumerate(requesters):
                other_r = requesters[other_index]
                if other_r["visited"]:
                    # Skip visited
                    continue
                dist = r["distances"][other_index]
                if dist < min_distance:
                    min_distance = dist
                    min_requester_index = other_index

            if min_requester_index != -1:
                item = requesters[min_requester_index]
                center[0] = (center[0] * len(group) + item["coords"].lat) / (
                    len(group) + 1
                )
                center[1] = (center[1] * len(group) + item["coords"].lon) / (
                    len(group) + 1
                )
                group.append(min_requester_index)
                item["visited"] = True
        groups.append(group)
    return groups


def rate(groups):
    total_distance = 0
    for group in groups:
        avg_lat = 0
        avg_lon = 0
        for x in group:
            avg_lat += requesters[x]["coords"].lat
            avg_lon += requesters[x]["coords"].lon
        avg_lat = avg_lat / len(group)
        avg_lon = avg_lon / len(group)

        for x in group:
            lat = requesters[x]["coords"].lat
            lon = requesters[x]["coords"].lon
            dist = great_circle([lat, lon], [avg_lat, avg_lon])
            total_distance += dist.km

    return total_distance


best_groups = None
min_score = None
for i in range(1000):
    print("Iteration:", i)
    groups = custom()
    if best_groups is None:
        best_groups = groups
        min_score = rate(groups)
    else:
        score = rate(groups)
        if score < min_score:
            print("\tFound new minimum")
            min_score = score
            best_groups = groups
    print("\tMin score: ", min_score)



fig, ax = plt.subplots()


def make_colors():
    for group_idx, group in enumerate(groups):
        color = "#%02X%02X%02X" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        for x in group:
            requesters[x]["color"] = color
            requesters[x]["group_idx"] = group_idx

    colors = []
    for r in requesters:
        colors.append(r["color"])
    return colors


def make_group_colors(group_idx):
    for r in requesters:
        if r["group_idx"] != group_idx:
            r["orig_color"] = r["color"]
            r["color"] = (0, 0, 0, 0.1)

    colors = []
    for r in requesters:
        colors.append(r["color"])
    return colors


def revert_colors():
    for r in requesters:
        if "orig_color" in r:
            r["color"] = r["orig_color"]
            del r["orig_color"]

    colors = []
    for r in requesters:
        colors.append(r["color"])
    return colors
    # for group_idx, group in enumerate(groups):
    # 	color = '#%02X%02X%02X' % (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    # 	for x in group:
    # 		requesters[x]['color'] = color
    # 		requesters[x]['group_idx'] = group_idx
    # for r in requesters:
    # 	colors.append(r['color'])


coll = ax.scatter(lats, lons, c=make_colors(), picker=0.01)

# for group in groups:
# 	glats = []
# 	glons = []
# 	for x in group:
# 		r = requesters[x]
# 		glats.append(r['coords'].lat)
# 		glons.append(r['coords'].lon)
# 	ax.scatter(lats, lons)
artist = None


def on_pick(ev):
    r = requesters[ev.ind[0]]
    pprint.pprint(r["row"]["Computed Address"])
    ev.artist.set_facecolors(make_group_colors(r["group_idx"]))
    global artist
    artist = ev.artist
    # breakpoint()
    # coll._facecolors[ev.ind][0] = [1, 1, 0, 1]
    # coll._facecolors[ev.ind,:] = (1, 0, 0, 1)
    # coll._edgecolors[ev.ind,:] = (1, 0, 0, 1)
    fig.canvas.draw()


def press(event):
    # breakpoint()
    if event.key == "x":
        artist.set_facecolors(revert_colors())
        fig.canvas.draw()


fig.canvas.callbacks.connect("pick_event", on_pick)
fig.canvas.mpl_connect("key_press_event", press)

plt.show()

# map_url = 'https://www.google.com/maps/dir/{}/@33.7913848,-84.3668247,12z/data=!4m32!4m31!1m5!1m1!1s0x88f5a62744668579:0xc376be45bdf63cb8!2m2!1d-84.2129553!2d33.8403534!1m5!1m1!1s0x88f503102a16e671:0xe49306f6f7f0876a!2m2!1d-84.4068225!2d33.7284129!1m5!1m1!1s0x88f50313a031e73b:0x565210a4e87a0de1!2m2!1d-84.4106598!2d33.7342226!1m5!1m1!1s0x88f50346383db9c5:0xce5cd02ef75e9eeb!2m2!1d-84.4265555!2d33.7414743!1m5!1m1!1s0x88f50348522680b3:0x5ef122f0d3e2fe16!2m2!1d-84.4300882!2d33.7403!3e0'
# for group in groups:
# 	avg_lat = 0
# 	avg_lon = 0
# 	for c in coords:
# 		avg_lat += c.lat
# 		avg_lon += c.lon
# 	avg_lat = avg_lat / len(coords)
# 	avg_lon = avg_lon / len(coords)

# 	print(f"Center: {avg_lat}, {avg_lon}")
# 	for x in group:
# 		address = requesters[x]['row']['Computed Address']
# 		lat = requesters[x]['coords'].lat
# 		lon = requesters[x]['coords'].lon
# 		addresses.append(f"{lat} +{lon}")
# 		dist = round(great_circle([lat, lon], [avg_lat, avg_lon]) * 100, 2)
# 		print(f"[{dist}] {lat}, {lon}: {address}")
# 	# print(map_url.format('/'.join(addresses)))
# 	print("\n")

# pprint.pprint(requesters)
