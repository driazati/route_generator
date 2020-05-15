import collections
import csv
import pprint
import pickle
import random
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import great_circle
# import matplotlib.pyplot as plt
# from sklearn.cluster import DBSCAN
# from shapely.geometry import MultiPoint

from helpers import *

Coordinates = collections.namedtuple("Coordinates", ["lat", "lon"])


# Parameters
MIN_DELIVERY_WINDOW = 30
GROUP_SIZE = 5
STATE = "GA"
CITY = "atlanta"
ADDRESSES_FILE = "file.csv"
FIX_MISSING_ADDRESSES = False
ITERATIONS = 500


addresses = pickle.load(open("addresses.pkl", "rb"))

num_bad_addresses = 0
num_total = 0
num_with_recent_deliveries = 0

requesters = []
for row in csv.DictReader(open(ADDRESSES_FILE, "r")):
    num_total += 1
    if int(row["Days since delivery"]) < MIN_DELIVERY_WINDOW:
        # Skip people who have had deliveries in the last month
        num_with_recent_deliveries += 1
        continue
    address = row["Computed Address"]
    if address in addresses:
        # Cached entry for this address was found, use it
        coords = Coordinates(*addresses[address])
    else:
        # No cached entry for this address was found, fetch its coordinates
        # from Bing and store them for later
        print("No record found for", address)
        if FIX_MISSING_ADDRESSES:
            print("Calling bing API")
            try:
                coords = get_coords(STATE, CITY, address)
            except:
                print("Failed to get", address)
                num_bad_addresses += 1
                continue
        else:
            num_bad_addresses += 1
            continue
    addresses[address] = (coords.lat, coords.lon)
    requesters.append(
        {"row": row, "coords": coords}
    )

pickle.dump(addresses, open("addresses.pkl", "wb"))

print(" ======= stats =======")
print("total entries:", num_total)
print(
    f"skipped (delivery was in the last {MIN_DELIVERY_WINDOW} days):",
    num_with_recent_deliveries,
)
print("skipped (address was bad):", num_bad_addresses)
print("calculating routes for:", len(requesters))

# calculate distance matrix
print("calculating distances...")
for r in requesters:
    r['distances'] = []
    for other_r in requesters:
        r["distances"].append(great_circle(r["coords"], other_r["coords"]).km)
print("\tdone")


def group_requesters():
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


# Randomly choose a set of groupings and rate it
best_groups = None
min_score = None
for i in range(ITERATIONS):
    print("Iteration:", i)
    groups = group_requesters()
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





locations_by_idx = []
lats = []
lons = []


for r in requesters:
    locations_by_idx.append([r["coords"].lat, r["coords"].lon])
    lats.append(r["coords"].lat)
    lons.append(r["coords"].lon)


# Run kmeans
# num_clusters = int(len(requesters) / GROUP_SIZE)
# kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(np.array(locations_by_idx))

# potential_groups = [[] for i in range(num_clusters)]

# for index, group_index in enumerate(kmeans.labels_):
#     potential_groups[group_index].append(index)


# some of the groups at this point are too big and need to be split up
# groups = []
# for potential_group in potential_groups:
#     if len(potential_group) <= GROUP_SIZE:
#         groups.append(potential_group)
#     else:
#         curr = 0
#         while curr < len(potential_group):
#             partial_group = potential_group[curr:curr + GROUP_SIZE]
#             groups.append(partial_group)
#             curr += GROUP_SIZE



# dont split the groups
# groups = potential_groups



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


# fig, ax = plt.subplots()
# coll = ax.scatter(lats, lons, c=make_colors(), picker=0.01)
# artist = None


def on_pick(ev):
    r = requesters[ev.ind[0]]
    pprint.pprint(r["row"]["Computed Address"])
    ev.artist.set_facecolors(make_group_colors(r["group_idx"]))
    global artist
    artist = ev.artist
    fig.canvas.draw()


def press(event):
    if event.key == "x":
        artist.set_facecolors(revert_colors())
        fig.canvas.draw()


# fig.canvas.callbacks.connect("pick_event", on_pick)
# fig.canvas.mpl_connect("key_press_event", press)

# plt.show()

def average_coords(coords):
    avg_lat = 0
    avg_lon = 0
    for c in coords:
        avg_lat += c.lat
        avg_lon += c.lon
    avg_lat = avg_lat / len(coords)
    avg_lon = avg_lon / len(coords)

    return avg_lat, avg_lon


for group in groups:
    waypoints = [requesters[i]['coords'] for i in group]
    if len(waypoints) > 20:
        print("Skipping group that is too big")
        continue
    travel_time_minutes, data = driving_distance(waypoints)
    print('\n')

    print(f"Driving distance: {round(travel_time_minutes, 2)} min")

    if 'waypointsOrder' not in data:
        order = [i for i in range(len(group))]
    else:
        order = [int(x.replace('wp.', '')) for x in data['waypointsOrder']]
    for i, ordered_index in enumerate(order):
        idx = group[ordered_index]
        r = requesters[idx]
        print(f"{i}. {r['row']['Computed Address']}")
        if travel_time_minutes > 0 and i < len(order) - 1:
            travel_time_from_last_waypoint_minutes = data['routeLegs'][i]['travelDuration'] / 60
            print(f"\t{round(travel_time_from_last_waypoint_minutes, 2)} minutes")
