#!/usr/bin/env python3
"""
Performance comparison between sequential and concurrent API calls
"""

import os
import time
from birthday_deals_finder import BirthdayDealsFinder


def main():
    """Compare performance between sequential and concurrent methods."""
    
    # Get API key from environment variable
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Please set your Google Maps API key as an environment variable:")
        print("set GOOGLE_MAPS_API_KEY=your_api_key_here")
        return
    
    # Test parameters
    test_location = "New York, NY"
    test_radius = 5.0
    
    print(f"Performance Test: Birthday Deals Finder")
    print(f"Location: {test_location}")
    print(f"Radius: {test_radius} miles")
    print("=" * 60)
    
    # Test sequential method
    print("\n1. Testing Sequential Method...")
    finder_seq = BirthdayDealsFinder(api_key, max_workers=1)
    
    start_time = time.time()
    stores_seq = finder_seq.find_stores_within_radius(test_location, test_radius)
    seq_time = time.time() - start_time
    
    print(f"Sequential method completed in {seq_time:.2f} seconds")
    print(f"Found {len(stores_seq)} stores")
    
    # Test concurrent method
    print("\n2. Testing Concurrent Method...")
    finder_concurrent = BirthdayDealsFinder(api_key, max_workers=10)
    
    start_time = time.time()
    stores_concurrent = finder_concurrent.find_stores_within_radius_concurrent(test_location, test_radius)
    concurrent_time = time.time() - start_time
    
    print(f"Concurrent method completed in {concurrent_time:.2f} seconds")
    print(f"Found {len(stores_concurrent)} stores")
    
    # Calculate improvement
    if seq_time > 0:
        speedup = seq_time / concurrent_time
        improvement = ((seq_time - concurrent_time) / seq_time) * 100
        print(f"\nPerformance Improvement:")
        print(f"Speedup: {speedup:.2f}x faster")
        print(f"Time saved: {improvement:.1f}%")
        print(f"Time reduction: {seq_time - concurrent_time:.2f} seconds")
    
    # Verify results are the same
    if len(stores_seq) == len(stores_concurrent):
        print(f"\n✓ Both methods found the same number of stores ({len(stores_seq)})")
    else:
        print(f"\n⚠ Different results: Sequential={len(stores_seq)}, Concurrent={len(stores_concurrent)}")


if __name__ == "__main__":
    main()
