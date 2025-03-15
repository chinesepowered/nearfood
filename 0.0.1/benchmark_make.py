import requests
import icalendar
from datetime import datetime
import datasets

PATH = "lu_ma_events"  # Changed path to reflect the new dataset

def generate_examples():
    """Fetches and parses ICS data from the Luma API, then yields examples."""
    url = "https://api.lu.ma/ics/get?entity=discover&id=discplace-BDj7GNbGlsF7Cka"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.text
        cal = icalendar.Calendar.from_ical(data)

        for event in cal.walk('VEVENT'):
            summary = str(event.get('summary', ''))
            description = str(event.get('description', ''))
            location = str(event.get('location', ''))
            start = event.get('dtstart').dt
            end = event.get('dtend').dt

            # Format start and end datetimes to strings
            start_str = start.isoformat() if isinstance(start, datetime) else str(start)
            end_str = end.isoformat() if isinstance(end, datetime) else str(end)

            yield {
                "summary": summary,
                "description": description,
                "location": location,
                "start": start_str,
                "end": end_str
            }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from URL: {e}")
    except Exception as e:
        print(f"Error parsing ICS data: {e}")

# Define the features of the dataset
features = datasets.Features({
    "summary": datasets.Value("string"),
    "description": datasets.Value("string"),
    "location": datasets.Value("string"),
    "start": datasets.Value("string"),
    "end": datasets.Value("string")
})

# Create the dataset from the generator function
dataset = datasets.Dataset.from_generator(generate_examples, features=features)

# Save the dataset to disk
dataset.save_to_disk(PATH)