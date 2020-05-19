def bing_api(method, url, data=None):
	base = 'http://dev.virtualearth.net/REST/v1/'
	if method == 'get':
		if data is None:
			data = {}
		new_data = { **data }
		new_data['key'] = api_key
		response = requests.get(base + url, params=new_data)
		return json.loads(response.content.decode('utf-8'))
	if method == 'post':
		response = requests.post(base + url, params={'key': api_key}, data=data)
		return json.loads(response.content.decode('utf-8'))
	else:
		raise RuntimeError("Unsupported method")



def get_coords(state, city, address):
	url = f"Locations/US/{state}/{city}/{address}"
	r = bing_api('get', url)
	return Coord(*r['resourceSets'][0]['resources'][0]['point']['coordinates'])


for d in requesters:
	d['coords'] = get_coords(d['address'])


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







# calculate distance matrix
# print("calculating distances...")
# for r in requesters:
#     r['distances'] = []
#     for other_r in requesters:
#         r["distances"].append(great_circle(r["coords"], other_r["coords"]).km)
# print("\tdone")


# def group_requesters():
#     groups = []
#     indices = [i for i in range(len(requesters))]
#     random.shuffle(indices)
#     for r in requesters:
#         r["visited"] = False

#     for this_index in indices:
#         r = requesters[this_index]
#         if r["visited"]:
#             continue
#         r["visited"] = True

#         group = [this_index]
#         center = [r["coords"].lat, r["coords"].lon]
#         for i in range(GROUP_SIZE - 1):
#             # find the closest non-visited neighbor, add them to the group with this one,
#             # and mark it visited
#             min_distance = 9999999999999
#             min_requester_index = -1
#             for other_index, other_dist in enumerate(requesters):
#                 other_r = requesters[other_index]
#                 if other_r["visited"]:
#                     # Skip visited
#                     continue
#                 dist = r["distances"][other_index]
#                 if dist < min_distance:
#                     min_distance = dist
#                     min_requester_index = other_index

#             if min_requester_index != -1:
#                 item = requesters[min_requester_index]
#                 center[0] = (center[0] * len(group) + item["coords"].lat) / (
#                     len(group) + 1
#                 )
#                 center[1] = (center[1] * len(group) + item["coords"].lon) / (
#                     len(group) + 1
#                 )
#                 group.append(min_requester_index)
#                 item["visited"] = True
#         groups.append(group)
#     return groups


# def rate(groups):
#     total_distance = 0
#     for group in groups:
#         avg_lat = 0
#         avg_lon = 0
#         for x in group:
#             avg_lat += requesters[x]["coords"].lat
#             avg_lon += requesters[x]["coords"].lon
#         avg_lat = avg_lat / len(group)
#         avg_lon = avg_lon / len(group)

#         for x in group:
#             lat = requesters[x]["coords"].lat
#             lon = requesters[x]["coords"].lon
#             dist = great_circle([lat, lon], [avg_lat, avg_lon])
#             total_distance += dist.km

#     return total_distance


# # Randomly choose a set of groupings and rate it
# best_groups = None
# min_score = None
# for i in range(ITERATIONS):
#     print("Iteration:", i)
#     groups = group_requesters()
#     if best_groups is None:
#         best_groups = groups
#         min_score = rate(groups)
#     else:
#         score = rate(groups)
#         if score < min_score:
#             print("\tFound new minimum")
#             min_score = score
#             best_groups = groups
#     print("\tMin score: ", min_score)