import requests
import json
import os
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Union
import icalendar
from datetime import datetime

# Maximum number of events to process
MAX_EVENTS_TO_PROCESS = 15

def parse_ical_data(ical_data: str) -> List[Dict[str, Any]]:
    """Parse iCal data using icalendar library"""
    try:
        cal = icalendar.Calendar.from_ical(ical_data)
        events = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {
                    'SUMMARY': str(component.get('summary', 'No Title')),
                    'DESCRIPTION': str(component.get('description', 'No Description')),
                    'URL': str(component.get('url', '')),
                    'DTSTART': component.get('dtstart').dt.isoformat() if component.get('dtstart') else None,
                    'DTEND': component.get('dtend').dt.isoformat() if component.get('dtend') else None,
                    'LOCATION': str(component.get('location', 'No Location'))
                }
                events.append(event)
        
        return events
    except Exception as e:
        raise Exception(f"Error parsing iCal data: {str(e)}")

def fetch_url(url: str) -> str:
    """Fetch content from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching URL: {str(e)}")

def extract_text_from_html(html: str) -> str:
    """Extract text from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    
    # Get text
    text = soup.get_text(separator="\n")
    
    # Remove extra whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

def get_event_summaries(summary_path: str) -> List[Dict[str, Any]]:
    """Read event summaries from file"""
    if not os.path.exists(summary_path):
        return []
    
    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading summaries: {e}")
        return []

def process_ical_data(
    ical_url: str,
    ical_data_path: str,
    summary_path: str,
    inference_provider: Any
) -> Dict[str, Any]:
    """Process iCal data, analyze events, and save results"""
    
    # Fetch and save iCal data
    try:
        ical_data = fetch_url(ical_url)
        
        # Save raw iCal data
        with open(ical_data_path, 'w') as f:
            f.write(ical_data)
        
        # Parse iCal data
        events = parse_ical_data(ical_data)
        print(f"Parsed {len(events)} events from iCal data")
        
        # Process events
        processed_events = []
        events_processed_count = 0
        
        for event in events:
            if events_processed_count >= MAX_EVENTS_TO_PROCESS:
                break
                
            summary = event.get('SUMMARY')
            description = event.get('DESCRIPTION')
            url = event.get('URL')
            
            print(f"Processing event: {summary}")
            
            # Initial check for free food potential
            initial_prompt = f"""Parse the event name and description and return only true/false and nothing else. 
            true if the description suggests there's a good chance of free food, false otherwise. 
            Event description doesn't need to mention food, still return true if the type of events may have free food.
            
            Event: {summary}
            Description: {description}
            """
            
            initial_response = inference_provider.get_completion(initial_prompt)
            initial_has_food = initial_response.lower().strip() == "true"
            
            event_data = {
                "name": summary,
                "url": url,
                "date": event.get('DTSTART'),
                "location": event.get('LOCATION')
            }
            
            if initial_has_food and url and url.startswith("http"):
                try:
                    # Fetch and process event page
                    event_html = fetch_url(url)
                    event_text = extract_text_from_html(event_html)
                    
                    # Final check with full event details
                    final_prompt = f"""Return how likely (very likely, likely, unlikely, very unlikely) followed by a summarization 
                    of the event details mentioning food.
                    
                    Event: {summary}
                    Full Event Details: {event_text[:3000]}  # Limit text length
                    """
                    
                    final_response = inference_provider.get_completion(final_prompt)
                    
                    # Parse response
                    parts = final_response.split(',', 1)
                    likelihood = parts[0].strip()
                    event_summary = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Add to event data
                    event_data.update({
                        "food_description": event_summary,
                        "initial_llm_response": initial_response,
                        "final_llm_response": final_response,
                        "likelihood": likelihood
                    })
                    
                except Exception as e:
                    print(f"Error processing URL for event {summary}: {e}")
                    event_data.update({
                        "food_description": "Error processing URL",
                        "initial_llm_response": initial_response,
                        "final_llm_response": "Error",
                        "likelihood": "Unknown"
                    })
            else:
                # No URL or not likely to have food
                event_data.update({
                    "food_description": "No food in description" if not initial_has_food else "No URL to check",
                    "initial_llm_response": initial_response,
                    "final_llm_response": "No URL" if initial_has_food else "No food in description",
                    "likelihood": "No URL" if initial_has_food else "No food in description"
                })
            
            processed_events.append(event_data)
            events_processed_count += 1
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        # Save processed events
        with open(summary_path, 'w') as f:
            json.dump(processed_events, f, indent=2)
        
        print(f"Processed {events_processed_count} events")
        
        # Generate final summary using LLM
        if processed_events:
            context = json.dumps(processed_events, indent=2)
            final_prompt = f"""Here are the event summaries:
            {context}
            
            Based on these summaries, provide a final summary of potential free food opportunities 
            and their likelihood. Also, suggest some specific events to consider attending.
            """
            
            final_summary = inference_provider.get_completion(final_prompt)
            
            # Add final summary to processed events
            result = {
                "events": processed_events,
                "summary": final_summary,
                "processed_at": datetime.now().isoformat()
            }
            
            # Save final result
            with open(summary_path, 'w') as f:
                json.dump(result, f, indent=2)
                
            return result
        
        return {"status": "error", "message": "No events processed"}