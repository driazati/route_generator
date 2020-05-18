const FIX_MISSING_ADDRESSES = true;
const GROUP_SIZE = 5;
const MAX_GROUP_SIZE = 25;

const print = console.log

let file = null;

const status = document.getElementById('status');
document.getElementById('clipboard').addEventListener('click', e => {
  navigator.clipboard.writeText(document.getElementById('groups').innerText);
});



document.getElementById('file').addEventListener('change',  (e) =>{
  document.getElementById('calculate').disabled = false;
  status.innerText = 'waiting to calculate';
  file = e.target.files[0];
});

document.getElementById('calculate').addEventListener('click', (e) => {
  document.getElementById('groups').innerText = '';
  var reader = new FileReader();
  
  reader.onload = function (evt) {
    generator = new RouteGenerator(30)
    generator.readCsv(evt.target.result, 'GA', 'atlanta').then((requesters) => {
      const groups = generator.calculateGroups(requesters);
      generator.printGroups(groups, requesters);
    });

  };

  reader.onerror = function (evt) {
    alert("Could not read file");

  };

  reader.readAsText(file, "UTF-8");
});


let BING_API_KEY = null;


function CallRestService(request, data, callback, error_callback) {
  data['key'] = BING_API_KEY;
  $.ajax({
    url: request,
    dataType: "jsonp",
    data: data,
    jsonp: "jsonp",
    success: function (r) {
      callback(r);
    },
    error: function (e) {
      error_callback(e);
    }
  });
}

const api_key_input = document.getElementById('bing_api_key');

let api_key = localStorage.getItem('bing_api_key');
if (api_key) {
  api_key_input.value = api_key;
  document.getElementById('file').disabled = false;
  BING_API_KEY = api_key;
}
api_key_input.addEventListener('input', (e) => {
  if (api_key_input.value == '') {
    document.getElementById('file').disabled = true;
  } else {
    document.getElementById('file').disabled = false;
  }
  BING_API_KEY = api_key_input.value;
  localStorage.setItem('bing_api_key', BING_API_KEY);
});


const BING_URL_BASE = "http://dev.virtualearth.net/REST/v1";
let request = `${BING_URL_BASE}/Locations/US/GA/atlanta/${encodeURIComponent("98 ardmore place nw 30309 atlanta ga")}`;


function fetch_coordinates(state, city, address) {
  state = encodeURIComponent(state);
  city = encodeURIComponent(city);
  address = encodeURIComponent(address);
  const request = `${BING_URL_BASE}/Locations/US/${state}/${city}/${address}`;


  return new Promise((resolve, reject) => {
      CallRestService(request, {}, (data) => {
        resolve(data.resourceSets[0].resources[0].point.coordinates);
      }, (e) => { reject(e); });      
  })
}

function drivingDistance(waypoints) {
  if (waypoints.length == 1) {
    return new Promise((resolve, reject) => {
      resolve({
        totalTravelTime: 0,
        waypoints: [0],
        legs: []
      });
    })
  }
  let urlParams = {
    'optimizeWaypoints': true,
    'optimize': 'timeWithTraffic'
  };
  for (let i = 0; i < waypoints.length; i++) {
    urlParams[`waypoint.${i}`] = `${waypoints[i][0]},${waypoints[i][1]}`;
  }
  const request = `${BING_URL_BASE}/Routes/Driving`;

  return new Promise((resolve, reject) => {
    CallRestService(request, urlParams, (data) => {
      const resource = data.resourceSets[0].resources[0];
      const response = {
        totalTravelTime: resource.travelDurationTraffic / 60,
        waypoints: [],
        legs: []
      };

      for (let i = 0; i < resource.routeLegs.length; i++) {
        response.legs.push(resource.routeLegs[i].travelDuration / 60);
      }

      if (waypoints.length > 2) {
        for (let i = 0; i < resource.waypointsOrder.length; i++) {
          const waypoint = resource.waypointsOrder[i];
          response.waypoints.push(parseInt(waypoint.replace('wp.', '')));
        }
      }

      resolve(response);
    }, (e) => { reject(e); });      
  });
}

class RouteGenerator {
  constructor(min_delivery_window_days) {
    this.min_delivery_window_days = min_delivery_window_days;

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

  readCsv(text, state, city) {
    let address_cache = this.getCache();
    let rows = [];
    status.innerText = "reading file";
    d3.csvParse(text, (data) => {
      rows.push(data);
    });

    let promise = new Promise((resolve, reject) => {
      let requesters = [];
      for (let i = 0; i < rows.length; i++) {
        status.innerText = `getting address ${i + 1} / ${rows.length}`;
        this.num_total += 1;
        const row = rows[i];
        if (row['Days since delivery'] < this.min_delivery_window_days) {
          // Skip people who have had deliveries in the last month
          this.num_with_recent_deliveries +=1 ;
          continue;
        }
        const address = row['Computed Address'];
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
              console.error("Could not fetch", address);
              console.error(e);
            }
          }
          if (!coords) {
            // console.error("Skipped", address);
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

  calculateGroups(requesters) {
    status.innerText = 'running calculations';
    const km = new kMeans({
      // Num clusters
      K: requesters.length / GROUP_SIZE
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
    for (let i = 0; i < groups.length; i++) {
      const group = groups[i];
      if (group.length > MAX_GROUP_SIZE) {
        console.error("too big, skipping");
        continue;
      }

      let waypoints = [];
      for (let j = 0; j < group.length; j++) {
        const requester = requesters[group[j]];
        waypoints.push(requester.coords);
      }

      (function(waypoints, group, obj) {
        drivingDistance(waypoints).then((response) => {
          let text = `Total travel time: ${+response.totalTravelTime.toFixed(2)} min\n`;
          for (let j = 0; j < response.waypoints.length; j++) {
            const waypointIndex = response.waypoints[j];
            const requester = requesters[group[waypointIndex]];
            // waypoints.push(requester.coords);
            text += `${j + 1}: ${requester.row['Computed Address']} (${requester.coords})\n`;
            if (j < group.length - 1) {
              text += `\t${+response.legs[j].toFixed(2)} min\n`
            }
          }
          obj.num_routes_calculated += 1;
          status.innerText = `calculating route ${obj.num_routes_calculated} / ${groups.length}`
          if (obj.num_routes_calculated == groups.length) {
            status.innerText = 'done';
          }
          text += '\n';
          pre.innerText += text;
        });
      })(waypoints, group, this);
    }
  }
}

