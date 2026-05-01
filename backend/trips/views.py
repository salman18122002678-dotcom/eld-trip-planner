"""API views for trip planning."""
import json
import math
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .hos_engine import calculate_trip

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def _fetch_json(url, retries=2):
        """Fetch JSON from a URL using urllib. Works on Railway/cloud."""
        for attempt in range(retries + 1):
                    try:
                                    req = urllib.request.Request(url, headers={
                                                        'User-Agent': 'ELDTripPlanner/1.0'
                                    })
                                    ctx = ssl.create_default_context()
                                    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                                                        data = resp.read().decode()
                                                        return json.loads(data)
                    except Exception as e:
                                    print(f"Fetch attempt {attempt+1} error: {e}")
                                if attempt < retries:
                                                time.sleep(0.5)
                                        return None


def geocode_location(query):
        """Geocode a location string to coordinates using Nominatim."""
        params = {
            'q': query,
            'format': 'json',
            'limit': 1
        }
        url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
        data = _fetch_json(url)
        if data and len(data) > 0:
                    return {
                                    'lat': float(data[0]['lat']),
                                    'lon': float(data[0]['lon']),
                                    'display_name': data[0]['display_name']
                    }
                return None


def get_route(waypoints):
        """Get route between waypoints using OSRM."""
    coords = ";".join([f"{w['lon']},{w['lat']}" for w in waypoints])
    url = f"{OSRM_URL}/{coords}?overview=full&geometries=geojson"
    data = _fetch_json(url)
    if data and data.get('code') == 'Ok':
                route = data['routes'][0]
                return {
                    'geometry': route['geometry'],
                    'total_distance': route['distance'] / 1609.34,  # meters to miles
                    'total_duration': route['duration'] / 3600  # seconds to hours
                }
            return None


@api_view(['POST'])
def plan_trip(request):
        """Plan a trip with HOS compliance."""
    pickup_location = request.data.get('pickup_location')
    dropoff_location = request.data.get('dropoff_location')
    current_location = request.data.get('current_location')
    cycle_hours_used = float(request.data.get('cycle_hours_used', 0))

    if not all([pickup_location, dropoff_location, current_location]):
                return Response({'error': 'Missing required locations'}, status=status.HTTP_400_BAD_REQUEST)

    # Geocode locations
    pickup_geo = geocode_location(pickup_location)
    dropoff_geo = geocode_location(dropoff_location)
    current_geo = geocode_location(current_location)

    if not current_geo:
                return Response({'error': f'Could not find location: {current_location}'}, status=status.HTTP_404_NOT_FOUND)
            if not pickup_geo:
                        return Response({'error': f'Could not find location: {pickup_location}'}, status=status.HTTP_404_NOT_FOUND)
                    if not dropoff_geo:
                                return Response({'error': f'Could not find location: {dropoff_location}'}, status=status.HTTP_404_NOT_FOUND)

    # Get route (with fallback)
    route = get_route([current_geo, pickup_geo, dropoff_geo])
    if not route:
                return Response({'error': 'Could not calculate route. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    route['start_name'] = current_geo['display_name'].split(',')[0]
    route['pickup_name'] = pickup_geo['display_name'].split(',')[0]
    route['dropoff_name'] = dropoff_geo['display_name'].split(',')[0]

    # Calculate HOS-compliant trip
    trip_result = calculate_trip(route, cycle_hours_used)

    return Response({
                'route': {
                                'geometry': route['geometry'],
                                'total_distance': round(route['total_distance'], 1),
                                'total_duration': round(route['total_duration'], 1),
                },
                'locations': {
                                'current': {'name': current_geo['display_name'], 'coords': [current_geo['lon'], current_geo['lat']]},
                                'pickup': {'name': pickup_geo['display_name'], 'coords': [pickup_geo['lon'], pickup_geo['lat']]},
                                'dropoff': {'name': dropoff_geo['display_name'], 'coords': [dropoff_geo['lon'], dropoff_geo['lat']]},
                },
                'stops': trip_result['stops'],
                'daily_logs': trip_result['daily_logs'],
                'summary': trip_result['summary']
    })
