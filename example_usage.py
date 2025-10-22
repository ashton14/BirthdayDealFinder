#!/usr/bin/env python3
"""
Example usage of the Birthday Deals Finder

This script demonstrates how to use the BirthdayDealsFinder class programmatically.
"""

import os
from birthday_deals_finder import BirthdayDealsFinder


def main():
    """Example usage of the BirthdayDealsFinder."""
    
    # Get API key from environment variable
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Please set your Google Maps API key as an environment variable:")
        print("set GOOGLE_MAPS_API_KEY=your_api_key_here")
        return
    
    # Initialize the finder with concurrent processing
    finder = BirthdayDealsFinder(api_key, max_workers=10)
    
    # Example searches
    locations = [
        ("New York, NY", 5.0),
        ("Los Angeles, CA", 10.0),
        ("Chicago, IL", 3.0),
        ("Miami, FL", 15.0)
    ]
    
    for location, radius in locations:
        print(f"\n{'='*80}")
        print(f"Searching for birthday deals within {radius} miles of {location}")
        print('='*80)
        
        # Time the search
        import time
        start_time = time.time()
        
        # Use concurrent method for better performance
        stores = finder.find_stores_within_radius_concurrent(location, radius)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        finder.print_results(stores, location, radius)
        print(f"\nSearch completed in {search_time:.2f} seconds")


if __name__ == "__main__":
    main()
