export const STEP_METERS = 3;

export function haversine(lat1, lon1, lat2, lon2) {
  const earthRadiusMeters = 6371000;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(deltaPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
  return 2 * earthRadiusMeters * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function escXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function fmtTime(value) {
  const date = normalizeDate(value);
  return date ? date.toISOString().replace('.000Z', 'Z') : '';
}

function normalizeDate(value) {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }
  return null;
}

function clonePoint(point, time = null) {
  return {
    lat: point.lat,
    lon: point.lon,
    ele: point.ele ?? null,
    time,
  };
}

function sampleRoadPoints(segmentPoints, stepMeters) {
  if (!Array.isArray(segmentPoints) || segmentPoints.length < 2) {
    return [];
  }

  const cumulativeDistances = [0];
  for (let index = 1; index < segmentPoints.length; index += 1) {
    const previous = segmentPoints[index - 1];
    const current = segmentPoints[index];
    cumulativeDistances.push(
      cumulativeDistances[index - 1] +
        haversine(previous.lat, previous.lon, current.lat, current.lon)
    );
  }

  const totalDistance = cumulativeDistances[cumulativeDistances.length - 1];
  const sampled = [];

  // Keep road-derived exports dense enough for Fog of World without exploding file size.
  for (let target = 0; target <= totalDistance; target = Math.min(target + stepMeters, totalDistance)) {
    let segmentIndex = 0;
    while (
      segmentIndex < segmentPoints.length - 2 &&
      cumulativeDistances[segmentIndex + 1] < target
    ) {
      segmentIndex += 1;
    }

    const start = segmentPoints[segmentIndex];
    const end = segmentPoints[Math.min(segmentIndex + 1, segmentPoints.length - 1)];
    const startDistance = cumulativeDistances[segmentIndex];
    const endDistance = cumulativeDistances[Math.min(segmentIndex + 1, cumulativeDistances.length - 1)];

    if (endDistance === startDistance) {
      sampled.push({
        lat: start.lat,
        lon: start.lon,
        ele: start.ele ?? null,
        cumDist: target,
      });
    } else {
      const ratio = (target - startDistance) / (endDistance - startDistance);
      sampled.push({
        lat: start.lat + (end.lat - start.lat) * ratio,
        lon: start.lon + (end.lon - start.lon) * ratio,
        ele: start.ele ?? null,
        cumDist: target,
      });
    }

    if (target === totalDistance) {
      break;
    }
  }

  return sampled;
}

function buildTimeAnchors(waypoints, cumulativePath) {
  const anchors = [];
  for (let index = 0; index < waypoints.length; index += 1) {
    const time = normalizeDate(waypoints[index].time);
    if (!time) {
      continue;
    }
    anchors.push({ distance: cumulativePath[index], timeMs: time.getTime() });
  }
  return anchors;
}

function assignTimes(points, anchors) {
  if (anchors.length === 0) {
    return points.map((point) => clonePoint(point, null));
  }

  return points.map((point) => {
    let before = anchors[0];
    let after = anchors[anchors.length - 1];

    for (let index = 0; index < anchors.length - 1; index += 1) {
      if (
        anchors[index].distance <= point.cumDist &&
        anchors[index + 1].distance >= point.cumDist
      ) {
        before = anchors[index];
        after = anchors[index + 1];
        break;
      }
    }

    const timeMs =
      before.distance === after.distance
        ? before.timeMs
        : before.timeMs +
          ((point.cumDist - before.distance) / (after.distance - before.distance)) *
            (after.timeMs - before.timeMs);

    return clonePoint(point, new Date(timeMs));
  });
}

export function buildExportPath(waypoints, segments, stepMeters = STEP_METERS) {
  if (!Array.isArray(waypoints) || waypoints.length === 0) {
    return [];
  }
  if (waypoints.length === 1) {
    return [clonePoint(waypoints[0], normalizeDate(waypoints[0].time))];
  }

  const pathPoints = [];
  const cumulativeWaypointDistances = [0];
  let currentDistance = 0;

  pathPoints.push({
    lat: waypoints[0].lat,
    lon: waypoints[0].lon,
    ele: waypoints[0].ele ?? null,
    cumDist: 0,
  });

  for (let index = 0; index < waypoints.length - 1; index += 1) {
    const start = waypoints[index];
    const end = waypoints[index + 1];
    const segment = Array.isArray(segments) ? segments[index] : null;

    if (segment?.type === 'road' && Array.isArray(segment.pts) && segment.pts.length > 1) {
      const sampledRoadPoints = sampleRoadPoints(segment.pts, stepMeters);
      for (let sampleIndex = 1; sampleIndex < sampledRoadPoints.length; sampleIndex += 1) {
        const sample = sampledRoadPoints[sampleIndex];
        pathPoints.push({
          lat: sample.lat,
          lon: sample.lon,
          ele: sample.ele,
          cumDist: currentDistance + sample.cumDist,
        });
      }
      currentDistance += sampledRoadPoints[sampledRoadPoints.length - 1]?.cumDist ?? 0;
    } else {
      currentDistance += haversine(start.lat, start.lon, end.lat, end.lon);
      pathPoints.push({
        lat: end.lat,
        lon: end.lon,
        ele: end.ele ?? null,
        cumDist: currentDistance,
      });
    }

    cumulativeWaypointDistances.push(currentDistance);
  }

  return assignTimes(pathPoints, buildTimeAnchors(waypoints, cumulativeWaypointDistances));
}
