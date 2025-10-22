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


class BirthdayDealsFinder:
    def __init__(self, api_key: str):
        """
        Initialize the BirthdayDealsFinder with Google Maps API key.
        
        Args:
            api_key (str): Google Maps API key
        """
        self.gmaps = googlemaps.Client(key=api_key)
        self.deals_data = self._load_deals_data()
    
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
                # Search for the store using Google Places API
                places_result = self.gmaps.places(
                    query=store_name,
                    location=(search_lat, search_lng),
                    radius=radius_meters
                )
                
                # Check each result to see if it's within our radius
                for place in places_result.get('results', []):
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    place_coords = (place_lat, place_lng)
                    
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
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Error: Google Maps API key is required!")
        print("Set it as an environment variable: GOOGLE_MAPS_API_KEY=your_key_here")
        print("Or pass it as an argument: --api-key your_key_here")
        sys.exit(1)
    
    # Initialize the finder
    finder = BirthdayDealsFinder(api_key)
    
    # Search for stores
    stores = finder.find_stores_within_radius(args.location, args.radius)
    
    # Print results
    finder.print_results(stores, args.location, args.radius)


if __name__ == "__main__":
    main()
