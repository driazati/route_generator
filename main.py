import collections
import csv
import pprint
import pickle
import random
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import great_circle

from helpers import *

Coordinates = collections.namedtuple("Coordinates", ["lat", "lon"])


# Parameters
MIN_DELIVERY_WINDOW_DAYS = 30
STATE = "GA"
CITY = "atlanta"
ADDRESSES_FILE = "file.csv"
FIX_MISSING_ADDRESSES = False


addresses = pickle.load(open("addresses.pkl", "rb"))

num_bad_addresses = 0
num_total = 0
num_with_recent_deliveries = 0

# This is the list of all the people that will get deliveries
requesters = []

# Read the CSV file and get a list of people requesting deliveries
for row in csv.DictReader(open(ADDRESSES_FILE, "r")):
    num_total += 1
    if int(row["Days since delivery"]) < MIN_DELIVERY_WINDOW_DAYS:
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


# Store the addressess so we don't have to fetch them from Bing every time
pickle.dump(addresses, open("addresses.pkl", "wb"))

print(" ======= stats =======")
print("total entries:", num_total)
print(
    f"skipped (delivery was in the last {MIN_DELIVERY_WINDOW} days):",
    num_with_recent_deliveries,
)
print("skipped (address was bad):", num_bad_addresses)
print("calculating routes for:", len(requesters))


# Run kmeans to find clusters of people
locations_by_idx = [[r["coords"].lat, r["coords"].lon] for r in requesters]
num_clusters = int(len(requesters) / GROUP_SIZE)
kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(np.array(locations_by_idx))

groups = [[] for i in range(num_clusters)]

for index, group_index in enumerate(kmeans.labels_):
    groups[group_index].append(index)


# Print out groups
for group in groups:
    waypoints = [requesters[i]['coords'] for i in group]
    if len(waypoints) > 20:
        print("Skipping group that is too big")
        continue

    # Find the drive time for the whole route
    travel_time_minutes, data = driving_distance(waypoints)
    print('\n')

    print(f"Driving distance: {round(travel_time_minutes, 2)} min")

    # Finding the driving distance optimizes the order of the destinations, so
    # use that
    if 'waypointsOrder' not in data:
        order = [i for i in range(len(group))]
    else:
        order = [int(x.replace('wp.', '')) for x in data['waypointsOrder']]

    for i, ordered_index in enumerate(order):
        idx = group[ordered_index]
        r = requesters[idx]
        # Show the address
        print(f"{i}. {r['row']['Computed Address']}")
        if travel_time_minutes > 0 and i < len(order) - 1:
            # Show the driving time from this address to the next one in the list
            travel_time_from_last_waypoint_minutes = data['routeLegs'][i]['travelDuration'] / 60
            print(f"\t{round(travel_time_from_last_waypoint_minutes, 2)} minutes")
