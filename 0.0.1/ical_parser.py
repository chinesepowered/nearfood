# ical_parser.py
import re
from typing import List, Dict

def parse_ical_data(ical_data: str) -> List[Dict]:
    """
    Parses iCal data and extracts event information, handling multi-line descriptions.

    Args:
        ical_data (str): The iCal data as a string.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents an event
                      and contains the summary, description, and location.
    """
    events = []
    event = {}
    in_event = False
    description_ongoing = False
    current_key = None
    description_buffer = ""

    key_indicators = ["LOCATION:", "DTSTART:", "SUMMARY:", "ORGANIZER:"] # Add other known keys

    for line in ical_data.splitlines():
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_event = True
            event = {}
            description_buffer = ""
        elif line == "END:VEVENT":
            in_event = False
            if description_ongoing and current_key:
                event[current_key] = description_buffer.strip()
            description_ongoing = False
            current_key = None
            events.append(event)
        elif in_event:
            if ":" in line and not description_ongoing:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "DESCRIPTION":
                    description_buffer = value
                    description_ongoing = True
                    current_key = key
                else:
                    event[key] = value
            elif description_ongoing and current_key:
                if any(line.startswith(k) for k in key_indicators):
                    description_ongoing = False
                    event[current_key] = description_buffer.strip()
                    # Parse the new key-value pair
                    key, value = line.split(":", 1)
                    event[key.strip()] = value.strip()

                else:
                    description_buffer += line  # Append without any extras

    # Extract URL from description in a separate loop
    for event in events:
        if "DESCRIPTION" in event:
            url = extract_url_from_description(event["DESCRIPTION"])
            if url:
                event["URL"] = url

    # Filter out events with missing summary, description, or location
    filtered_events = []
    for event in events:
        if ("SUMMARY" in event and event["SUMMARY"] and
            "DESCRIPTION" in event and event["DESCRIPTION"] and
            "LOCATION" in event and event["LOCATION"]):
            filtered_events.append(event)
    print(filtered_events)
    return filtered_events

def extract_url_from_description(description: str) -> str:
    """Extracts the URL from the description string."""
    # Updated regex pattern to extract only the URL without trailing characters
    match = re.search(r"Get up-to-date information at:\s*(https?://[^\s\\]+)", description)
    if match:
        return match.group(1).strip()
    return None