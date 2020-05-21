let BING_API_KEY = null;

function setBingAPIKey(key) {
  BING_API_KEY = key;
}


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


const BING_URL_BASE = "https://dev.virtualearth.net/REST/v1";
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

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
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
    CallRestService(request, urlParams, async (data) => {
      if (data.statusCode && data.statusCode == 429) {
        // too many requests error, wait a bit and try again
        console.log("Too many requests, retrying...")
        await timeout(2000 + Math.floor(Math.random() * 10000));
        drivingDistance(waypoints).then((data) => {
          resolve(data);
        });
        return;
      }
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
      } else if (waypoints.length == 2) {
        response.waypoints.push(0);
        response.waypoints.push(1);
      }

      resolve(response);
    }, (e) => { reject(e); });      
  });
}