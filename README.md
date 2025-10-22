# Birthday Deals Finder

A Python script that uses the Google Maps API to find stores with birthday deals within a specified radius of any location.

## Features

- 🔍 Search for stores with birthday deals within a specified radius
- 📍 Uses Google Maps API for accurate location data
- 📏 Calculates precise distances using geodesic calculations
- ⭐ Includes store ratings and review counts
- 🎁 Shows the specific birthday deal for each store
- 📊 Sorts results by distance (closest first)
- ⚡ **Concurrent processing for 3-5x faster API calls**
- 🎛️ Configurable worker threads for optimal performance

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Google Maps API key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Places API
     - Places API(New)
     - Geocoding API
   - Create credentials (API key)
   - Restrict the API key to your applications for security

3. **Set your API key:**
   
   **Option A: Using .env file (Recommended)**
   Create a `.env` file in the project directory:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   
   **Option B: Environment variable**
   ```bash
   # Windows
   set GOOGLE_MAPS_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

## Usage

### Command Line Interface

```bash
python birthday_deals_finder.py "New York, NY" 5.0
```

Arguments:
- `location`: Address or coordinates to search from
- `radius`: Search radius in miles
- `--api-key`: Google Maps API key (optional if set as environment variable)
- `--concurrent`: Use concurrent processing (default: True)
- `--sequential`: Use sequential processing (slower but more reliable for API rate limits)
- `--max-workers`: Maximum number of concurrent workers (default: 10)

### Examples

```bash
# Search within 5 miles of New York City
python birthday_deals_finder.py "New York, NY" 5.0

# Search within 10 miles using coordinates
python birthday_deals_finder.py "40.7128,-74.0060" 10.0

# Search with custom API key
python birthday_deals_finder.py "Los Angeles, CA" 15.0 --api-key your_key_here

# Use sequential processing (slower but more reliable)
python birthday_deals_finder.py "Chicago, IL" 10.0 --sequential

# Use concurrent processing with custom worker count
python birthday_deals_finder.py "Miami, FL" 8.0 --max-workers 15
```

### Programmatic Usage

```python
from birthday_deals_finder import BirthdayDealsFinder

# Initialize with API key and concurrent processing
finder = BirthdayDealsFinder("your_api_key_here", max_workers=10)

# Search for stores using concurrent method (faster)
stores = finder.find_stores_within_radius_concurrent("Chicago, IL", 5.0)

# Or use sequential method (slower but more reliable)
# stores = finder.find_stores_within_radius("Chicago, IL", 5.0)

# Print results
finder.print_results(stores, "Chicago, IL", 5.0)
```

### Performance Testing

Run the performance comparison script to see the speed improvement:

```bash
python performance_test.py
```

This will compare sequential vs concurrent processing and show the performance improvement.

## Sample Output

```
🎂 Birthday Deals within 5.0 miles of New York, NY
============================================================
Found 12 stores with birthday deals:

1. Starbucks
   🎁 Deal: free drink
   📍 Address: 123 Broadway, New York, NY 10001
   📏 Distance: 0.3 miles
   ⭐ Rating: 4.2/5 (150 reviews)

2. McDonald's
   🎁 Deal: free fries
   📍 Address: 456 5th Ave, New York, NY 10018
   📏 Distance: 0.8 miles
   ⭐ Rating: 3.8/5 (89 reviews)

...
```

## Data Source

The script uses the `birthday_deals.csv` file which contains over 200 stores and their corresponding birthday deals. The CSV has two columns:
- `store`: Store name
- `deal`: Birthday deal description

## Requirements

- Python 3.7+
- Google Maps API key with Places and Geocoding APIs enabled
- Internet connection for API calls

## Dependencies

- `googlemaps`: Google Maps API client
- `geopy`: Geodesic distance calculations
- `pandas`: Data manipulation (optional, for future enhancements)

## Error Handling

The script includes comprehensive error handling for:
- Missing API key
- Invalid locations
- Network connectivity issues
- API rate limiting
- Missing CSV file

## Performance

The script now uses concurrent processing to significantly improve performance:

- **Concurrent processing**: 3-5x faster than sequential processing
- **Configurable workers**: Adjust `--max-workers` based on your API quota and system resources
- **Rate limiting friendly**: Built-in error handling for API rate limits
- **Timing information**: Shows search completion time

### Performance Tips

1. **API Quotas**: Google Maps API has rate limits. Start with 5-10 workers and adjust based on your quota
2. **Network**: Concurrent processing works best with stable internet connections
3. **Memory**: More workers use more memory, but the default 10 workers is usually optimal

## Notes

- The script searches for exact store name matches from the CSV file
- Results are sorted by distance (closest first)
- Only the first (closest) location is returned for each store
- Concurrent processing makes API calls much faster while respecting rate limits
