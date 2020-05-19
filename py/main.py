import collections
import csv
import pprint
import pickle
import random
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import great_circle
import tkinter as tk
import tkinter.filedialog as filedialog
from os.path import expanduser


from helpers import *

Coordinates = collections.namedtuple("Coordinates", ["lat", "lon"])


# Parameters
MIN_DELIVERY_WINDOW_DAYS = 30
STATE = "GA"
CITY = "atlanta"
ADDRESSES_FILE = "file.csv"
FIX_MISSING_ADDRESSES = False
GROUP_SIZE = 5

MAX_GROUP_SIZE = 25


class RouteGenerator:
    def __init__(self, min_delivery_window_days):
        self.min_delivery_window_days = min_delivery_window_days

        self.num_bad_addresses = 0
        self.num_total = 0
        self.num_with_recent_deliveries = 0

        self.requesters = None

    # Read the CSV file and get a list of people requesting deliveries
    def read_csv(self, file_name, state, city):
        # Load addresses that we have seen before so we don't have to go out to Bing
        # again
        addresses = pickle.load(open("addresses.pkl", "rb"))

        self.requesters = []

        for row in csv.DictReader(open(file_name, "r")):
            self.num_total += 1
            if int(row["Days since delivery"]) < self.min_delivery_window_days:
                # Skip people who have had deliveries in the last month
                self.num_with_recent_deliveries += 1
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
                        coords = get_coords(state, city, address)
                    except:
                        print("Failed to get", address)
                        self.num_bad_addresses += 1
                        continue
                else:
                    self.num_bad_addresses += 1
                    continue
            addresses[address] = (coords.lat, coords.lon)
            self.requesters.append(
                {"row": row, "coords": coords}
            )

        # Store the addressess so we don't have to fetch them from Bing every time
        pickle.dump(addresses, open("addresses.pkl", "wb"))

    def print_stats(self):
        print(" ======= stats =======")
        print("total entries:", self.num_total)
        print(
            f"skipped (delivery was in the last {self.min_delivery_window_days} days):",
            self.num_with_recent_deliveries,
        )
        print("skipped (address was bad):", self.num_bad_addresses)
        print("calculating routes for:", len(self.requesters))

    def calculate_groups(self):
        # Run kmeans to find clusters of people
        locations_by_idx = [[r["coords"].lat, r["coords"].lon] for r in self.requesters]
        num_clusters = int(len(self.requesters) / GROUP_SIZE)
        kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(np.array(locations_by_idx))


        potential_groups = [[] for i in range(num_clusters)]

        for index, group_index in enumerate(kmeans.labels_):
            potential_groups[group_index].append(index)


        # some of the groups at this point are too big for bing to handle and need to be split up
        groups = []

        # bing can't find a route between more than 25 destinations
        for potential_group in potential_groups:
            if len(potential_group) <= MAX_GROUP_SIZE:
                groups.append(potential_group)
            else:
                curr = 0
                while curr < len(potential_group):
                    partial_group = potential_group[curr:curr + MAX_GROUP_SIZE]
                    groups.append(partial_group)
                    curr += MAX_GROUP_SIZE

        return groups


def print_groups(generator, groups, output=None):
    if output is None:
        output = print
    # Print out output
    for group in groups:
        waypoints = [generator.requesters[i]['coords'] for i in group]
        if len(waypoints) >= MAX_GROUP_SIZE:
            raise RuntimeError("Group was too big")

        # Find the drive time for the whole route
        travel_time_minutes, data = driving_distance(waypoints)
        output('\n')

        output(f"Driving distance: {round(travel_time_minutes, 2)} min")

        # Finding the driving distance optimizes the order of the destinations, so
        # use that
        if 'waypointsOrder' not in data:
            order = [i for i in range(len(group))]
        else:
            order = [int(x.replace('wp.', '')) for x in data['waypointsOrder']]

        for i, ordered_index in enumerate(order):
            idx = group[ordered_index]
            r = generator.requesters[idx]
            # Show the address
            output(f"{i}. {r['row']['Computed Address']}")
            if travel_time_minutes > 0 and i < len(order) - 1:
                # Show the driving time from this address to the next one in the list
                travel_time_from_last_waypoint_minutes = data['routeLegs'][i]['travelDuration'] / 60
                output(f"\t{round(travel_time_from_last_waypoint_minutes, 2)} minutes")



# This is the list of all the people that will get deliveries
# generator = RouteGenerator(MIN_DELIVERY_WINDOW_DAYS)
# generator.read_csv(ADDRESSES_FILE, STATE, CITY)
# groups = generator.calculate_groups()
# print_groups(groups)

# from tkinter import 
downloads_dir = expanduser("~")

window = tk.Tk()

window.title("Route Generator")

lbl = tk.Label(window, text="Route Generator", font=("Arial Bold", 30))
# lbl.grid(column=0, row=0)
lbl.pack()



T = None
btn, btn2, btn3 = None, None, None
file = ''
output_string = ''

def choose_file():
    global file
    file = filedialog.askopenfilename(initialdir=downloads_dir, title="Choose .csv file", filetypes=[("csv files","*.csv")])
    btn2["state"] = "normal"


def output(text):
    global output_string
    print(text)
    T.insert(tk.END, text + '\n')
    output_string += text + '\n'

def calculate():
    if file is None:
        return

    generator = RouteGenerator(MIN_DELIVERY_WINDOW_DAYS)
    generator.read_csv(ADDRESSES_FILE, STATE, CITY)
    groups = generator.calculate_groups()
    print_groups(generator, groups, output)
    btn3["state"] = "normal"


def copy():
    window.clipboard_clear()
    window.clipboard_append(output_string)
    window.update()

btn = tk.Button(window, text="Choose file", command=choose_file)
btn.pack()

btn2 = tk.Button(window, text="Calculate routes", command=calculate)
btn2.pack()
btn2["state"] = "disabled"

btn3 = tk.Button(window, text="Copy text to clipboard", command=copy)
btn3.pack()
btn3["state"] = "disabled"

T = tk.Text(window, height=500, width=100)
T.pack(expand=True)


window.geometry('600x600')
window.mainloop()