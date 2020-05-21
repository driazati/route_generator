function escapeHtml(unsafe) {
  return unsafe
   .replace(/&/g, "&amp;")
   .replace(/</g, "&lt;")
   .replace(/>/g, "&gt;")
   .replace(/"/g, "&quot;")
   .replace(/'/g, "&#039;");
 }


class RouteGenerator {
  constructor() {
    this.num_bad_addresses = 0;
    this.num_with_recent_deliveries = 0;
    this.num_total = 0;

    this.num_routes_calculated = 0;
  }

  getCache() {
    let address_cache = localStorage.getItem("address_cache");
    if (!address_cache) {
      address_cache =  {};
    } else {
      // address_cache = {};
      address_cache = JSON.parse(address_cache);
    }
    return address_cache;
  }

  setCache(address_cache) {
    localStorage.setItem("address_cache", JSON.stringify(address_cache));
  }

  readCsv(text, filter_fn, state, city) {
    let address_cache = this.getCache();
    let rows = [];
    status.innerText = "reading file";
    d3.csvParse(text, (data) => {
      rows.push(data);
    });

    let promise = new Promise(async (resolve, reject) => {
      let requesters = [];
      for (let i = 0; i < rows.length; i++) {
        status.innerText = `getting address ${i + 1} / ${rows.length}`;
        this.num_total += 1;
        const row = rows[i];
        if (!filter_fn(row)) {
          // Skip people who have had deliveries in the last month
          this.num_with_recent_deliveries +=1 ;
          continue;
        }
        let address = row['Computed Address'];
        address = address.trim();
        address = address.replace(/(,$)/g, "");
        address = address.replace('\n', " ");
        row['Computed Address'] = address;
        let coords = null;
        if (address in address_cache) {
          // Cached entry for this address was found, use it
          coords = address_cache[address];
        } else {
          if (FIX_MISSING_ADDRESSES) {
            console.log("Fetching from bing for ", address);
            try {
              coords = await fetch_coordinates(state, city, address);
            } catch (e) {
              // console.error("Could not fetch", address);
              // console.error(e);
            }
          }
          if (!coords) {
            console.error("Skipped", address);
            this.num_bad_addresses += 1;
            continue;
          }
        }
        address_cache[address] = coords;
        requesters.push({ row: row, coords: coords });
      }

      this.setCache(address_cache);
      resolve(requesters);
    })
    return promise;
  }

  calculateGroups(requesters, target_group_size) {
    status.innerText = 'running calculations';
    const km = new kMeans({
      // Num clusters
      K: requesters.length / target_group_size
    });

    let data = [];
    for (let i = 0; i < requesters.length; i++) {
      data.push([requesters[i].coords[0], requesters[i].coords[1]]);
    }

    km.cluster(data);
    while (km.step()) {
        km.findClosestCentroids();
        km.moveCentroids();

        // console.log(km.centroids);

        if (km.hasConverged()) break;
    }

    let groups = [];
    for (let i = 0; i < km.clusters.length; i++) {
      const cluster = km.clusters[i];
      if (cluster.length > 0) {
        groups.push(cluster);
      }
    }
    return groups;
  }

  printGroups(groups, requesters) {
    const pre = document.getElementById('groups');
    let text = '';
    status.innerText = 'optimizing routes';
    this.numGroups = groups.length;
    for (let i = 0; i < groups.length; i++) {
      const group = groups[i];
      const MAX_GROUP_SIZE = 25;
      if (group.length > MAX_GROUP_SIZE) {
        console.error("too big, skipping");
        continue;
      }

      let waypoints = [];
      for (let j = 0; j < group.length; j++) {
        const requester = requesters[group[j]];
        waypoints.push(requester.coords);
      }

      let routeUrl = 'https://bing.com/maps/default.aspx?rtp=';
      this.drivingTimes = [];

      (function(waypoints, group, obj) {
        drivingDistance(waypoints).then((response) => {
          let text = `<a target="_blank" href="ROUTE_PLACEHOLDER">Total travel time: ${+response.totalTravelTime.toFixed(2)} min</a><br>`;
          obj.drivingTimes.push(response.totalTravelTime);
          for (let j = 0; j < response.waypoints.length; j++) {
            const waypointIndex = response.waypoints[j];
            const requester = requesters[group[waypointIndex]];

            routeUrl += 'adr.' + encodeURIComponent(requester.row['Computed Address']);
            if (j < response.waypoints.length - 1) {
              routeUrl += '~';
            }

            // waypoints.push(requester.coords);
            text += `${j + 1}: ${escapeHtml(requester.row['Computed Address'])}<br>`;
            // text += `${j + 1}: ${escapeHtml(requester.row['Computed Address'])} (${requester.coords})<br>`;
            if (j < group.length - 1) {
              text += `<span class="time">${+response.legs[j].toFixed(2)} min</span><br>`
            }
          }
          obj.num_routes_calculated += 1;
          status.innerText = `calculating route ${obj.num_routes_calculated} / ${groups.length}`
          if (obj.num_routes_calculated == groups.length) {
            status.innerText = `made ${obj.numGroups} groups (mean: ${+math.mean(obj.drivingTimes).toFixed(2)} median: ${+math.median(obj.drivingTimes).toFixed(2)})`;

          }
          text += '<br>';
          text = text.replace('ROUTE_PLACEHOLDER', routeUrl);
          pre.innerHTML += text;
        });
      })(waypoints, group, this);
    }
  }
}