#!/usr/bin/env python3
"""
Birthday Deals Finder using Google Maps API

This script finds stores from birthday_deals.csv within a specified radius
and returns their corresponding birthday deals.
"""

import csv
import os
import sys
import argparse
from typing import List, Dict, Tuple
import googlemaps
from geopy.distance import geodesic
import pandas as pd
from dotenv import load_dotenv
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests


PLACES_TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'
PLACES_FIELD_MASK = ','.join([
    'places.id',
    'places.formattedAddress',
    'places.location',
    'places.rating',
    'places.userRatingCount',
])


class BirthdayDealsFinder:
    def __init__(self, api_key: str, max_workers: int = 10):
        """
        Initialize the BirthdayDealsFinder with Google Maps API key.
        
        Args:
            api_key (str): Google Maps API key
            max_workers (int): Maximum number of concurrent workers for parallel processing
        """
        self.api_key = api_key
        self.gmaps = googlemaps.Client(key=api_key)
        self.deals_data = self._load_deals_data()
        self.max_workers = max_workers
        self._lock = threading.Lock()

    def _text_search(self, query: str, lat: float, lng: float, radius_meters: float) -> List[Dict]:
        """
        Search for places using the Places API (New) Text Search endpoint.

        Args:
            query (str): Text to search for (e.g. store name)
            lat (float): Latitude to bias results toward
            lng (float): Longitude to bias results toward
            radius_meters (float): Bias radius in meters (API max is 50,000)

        Returns:
            List[Dict]: Places with name, address, lat/lng, place_id, rating and rating count
        """
        response = requests.post(
            PLACES_TEXT_SEARCH_URL,
            headers={
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': PLACES_FIELD_MASK,
            },
            json={
                'textQuery': query,
                'locationBias': {
                    'circle': {
                        'center': {'latitude': lat, 'longitude': lng},
                        'radius': min(radius_meters, 50000.0),
                    }
                },
            },
            timeout=10,
        )
        if response.status_code != 200:
            try:
                error = response.json().get('error', {})
                message = f"{error.get('status', response.status_code)} ({error.get('message', '')})"
            except ValueError:
                message = f"HTTP {response.status_code}"
            raise RuntimeError(message)

        places = []
        for place in response.json().get('places', []):
            location = place.get('location', {})
            places.append({
                'lat': location.get('latitude'),
                'lng': location.get('longitude'),
                'formatted_address': place.get('formattedAddress', 'Address not available'),
                'place_id': place.get('id', ''),
                'rating': place.get('rating', 'N/A'),
                'user_ratings_total': place.get('userRatingCount', 'N/A'),
            })
        return places

    def _load_deals_data(self) -> Dict[str, str]:
        """
        Load birthday deals data from CSV file.
        
        Returns:
            Dict[str, str]: Dictionary mapping store names to their deals
        """
        deals = {}
        try:
            with open('birthday_deals.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    store_name = row['store'].strip()
                    deal = row['deal'].strip()
                    deals[store_name] = deal
        except FileNotFoundError:
            print("Error: birthday_deals.csv file not found!")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            sys.exit(1)
        
        return deals
    
    def _search_single_store(self, store_name: str, deal: str, search_lat: float, 
                           search_lng: float, radius_meters: float, 
                           search_coords: Tuple[float, float], radius_miles: float) -> List[Dict[str, str]]:
        """
        Search for a single store within the radius.
        
        Args:
            store_name (str): Name of the store to search for
            deal (str): Birthday deal for this store
            search_lat (float): Search latitude
            search_lng (float): Search longitude
            radius_meters (float): Search radius in meters
            search_coords (Tuple[float, float]): Search coordinates for distance calculation
            radius_miles (float): Search radius in miles
            
        Returns:
            List[Dict[str, str]]: List of found stores (usually 0 or 1)
        """
        found_stores = []
        try:
            # Search for the store using Google Places API (New)
            places = self._text_search(store_name, search_lat, search_lng, radius_meters)

            # Check each result to see if it's within our radius
            for place in places:
                place_coords = (place['lat'], place['lng'])
                
                # Calculate actual distance
                distance_miles = geodesic(search_coords, place_coords).miles
                
                if distance_miles <= radius_miles:
                    found_stores.append({
                        'store_name': store_name,
                        'deal': deal,
                        'address': place.get('formatted_address', 'Address not available'),
                        'distance_miles': round(distance_miles, 2),
                        'place_id': place.get('place_id', ''),
                        'rating': place.get('rating', 'N/A'),
                        'user_ratings_total': place.get('user_ratings_total', 'N/A')
                    })
                    break  # Only take the first (closest) result for each store
                    
        except Exception as e:
            print(f"Error searching for {store_name}: {e}")
        
        return found_stores
    
    def find_stores_within_radius_concurrent(self, location: str, radius_miles: float) -> List[Dict[str, str]]:
        """
        Find stores within the specified radius using concurrent processing for better performance.
        
        Args:
            location (str): Address or coordinates to search from
            radius_miles (float): Search radius in miles
            
        Returns:
            List[Dict[str, str]]: List of stores with their deals and distances
        """
        # Convert miles to meters for Google Maps API
        radius_meters = radius_miles * 1609.34
        
        # Geocode the search location
        try:
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                print(f"Error: Could not find location '{location}'")
                return []
            
            search_lat = geocode_result[0]['geometry']['location']['lat']
            search_lng = geocode_result[0]['geometry']['location']['lng']
            search_coords = (search_lat, search_lng)
            
        except Exception as e:
            print(f"Error geocoding location: {e}")
            return []
        
        found_stores = []
        
        # Use ThreadPoolExecutor for concurrent API calls
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all store searches concurrently
            future_to_store = {
                executor.submit(
                    self._search_single_store,
                    store_name,
                    deal,
                    search_lat,
                    search_lng,
                    radius_meters,
                    search_coords,
                    radius_miles
                ): store_name for store_name, deal in self.deals_data.items()
            }
            
            # Collect results as they complete
            total = len(future_to_store)
            for completed, future in enumerate(as_completed(future_to_store), 1):
                print(f"\rSearched {completed}/{total} stores...", end='', flush=True)
                store_name = future_to_store[future]
                try:
                    result = future.result()
                    if result:  # If stores were found
                        found_stores.extend(result)
                except Exception as e:
                    print(f"\nError processing {store_name}: {e}")
            print()

        # Sort by distance
        found_stores.sort(key=lambda x: x['distance_miles'])
        return found_stores
    
    def find_stores_within_radius(self, location: str, radius_miles: float) -> List[Dict[str, str]]:
        """
        Find stores within the specified radius that have birthday deals.
        
        Args:
            location (str): Address or coordinates to search from
            radius_miles (float): Search radius in miles
            
        Returns:
            List[Dict[str, str]]: List of stores with their deals and distances
        """
        # Convert miles to meters for Google Maps API
        radius_meters = radius_miles * 1609.34
        
        # Geocode the search location
        try:
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                print(f"Error: Could not find location '{location}'")
                return []
            
            search_lat = geocode_result[0]['geometry']['location']['lat']
            search_lng = geocode_result[0]['geometry']['location']['lng']
            search_coords = (search_lat, search_lng)
            
        except Exception as e:
            print(f"Error geocoding location: {e}")
            return []
        
        found_stores = []
        
        # Search for each store in our deals database
        for store_name, deal in self.deals_data.items():
            try:
                # Search for the store using Google Places API (New)
                places = self._text_search(store_name, search_lat, search_lng, radius_meters)

                # Check each result to see if it's within our radius
                for place in places:
                    place_coords = (place['lat'], place['lng'])
                    
                    # Calculate actual distance
                    distance_miles = geodesic(search_coords, place_coords).miles
                    
                    if distance_miles <= radius_miles:
                        found_stores.append({
                            'store_name': store_name,
                            'deal': deal,
                            'address': place.get('formatted_address', 'Address not available'),
                            'distance_miles': round(distance_miles, 2),
                            'place_id': place.get('place_id', ''),
                            'rating': place.get('rating', 'N/A'),
                            'user_ratings_total': place.get('user_ratings_total', 'N/A')
                        })
                        break  # Only take the first (closest) result for each store
                        
            except Exception as e:
                print(f"Error searching for {store_name}: {e}")
                continue
        
        # Sort by distance
        found_stores.sort(key=lambda x: x['distance_miles'])
        return found_stores
    
    def print_results(self, stores: List[Dict[str, str]], location: str, radius: float):
        """
        Print the search results in a formatted way.
        
        Args:
            stores (List[Dict[str, str]]): List of found stores
            location (str): Search location
            radius (float): Search radius
        """
        print(f"\nBirthday Deals within {radius} miles of {location}")
        print("=" * 60)
        
        if not stores:
            print("No stores with birthday deals found in the specified radius.")
            return
        
        print(f"Found {len(stores)} stores with birthday deals:\n")
        
        for i, store in enumerate(stores, 1):
            print(f"{i}. {store['store_name']}")
            print(f"   Deal: {store['deal']}")
            print(f"   Address: {store['address']}")
            print(f"   Distance: {store['distance_miles']} miles")
            if store['rating'] != 'N/A':
                print(f"   Rating: {store['rating']}/5 ({store['user_ratings_total']} reviews)")
            print()


def main():
    """Main function to run the birthday deals finder."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Find birthday deals within a specified radius using Google Maps API"
    )
    parser.add_argument(
        "location",
        help="Address or coordinates to search from (e.g., 'New York, NY' or '40.7128,-74.0060')"
    )
    parser.add_argument(
        "radius",
        type=float,
        help="Search radius in miles"
    )
    parser.add_argument(
        "--api-key",
        help="Google Maps API key (or set GOOGLE_MAPS_API_KEY environment variable)"
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        default=True,
        help="Use concurrent processing for faster API calls (default: True)"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Use sequential processing (slower but more reliable for API rate limits)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of concurrent workers (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Error: Google Maps API key is required!")
        print("Set it as an environment variable: GOOGLE_MAPS_API_KEY=your_key_here")
        print("Or pass it as an argument: --api-key your_key_here")
        sys.exit(1)
    
    # Initialize the finder
    finder = BirthdayDealsFinder(api_key, max_workers=args.max_workers)
    
    # Determine which method to use
    use_concurrent = args.concurrent and not args.sequential
    
    # Search for stores with timing
    start_time = time.time()
    
    if use_concurrent:
        print(f"Searching with concurrent processing (max {args.max_workers} workers)...")
        stores = finder.find_stores_within_radius_concurrent(args.location, args.radius)
    else:
        print("Searching with sequential processing...")
        stores = finder.find_stores_within_radius(args.location, args.radius)
    
    end_time = time.time()
    search_time = end_time - start_time
    
    # Print results
    finder.print_results(stores, args.location, args.radius)
    print(f"\nSearch completed in {search_time:.2f} seconds")


if __name__ == "__main__":
    main()
