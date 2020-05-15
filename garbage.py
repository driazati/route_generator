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
