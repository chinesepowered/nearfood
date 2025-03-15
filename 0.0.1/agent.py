import requests
from bs4 import BeautifulSoup
from nearai.agents.environment import Environment
import json
import os
import re
import pprint
import contextlib
# from icalendar import Calendar  # Remove icalendar import
from ical_parser import parse_ical_data # Import the new function

# Configuration variables
ICAL_URL = "https://api.lu.ma/ics/get?entity=discover&id=discplace-BDj7GNbGlsF7Cka"
ICAL_FILE = "ical_data.json"
SUMMARY_FILE = "event_summary.json"  # File to store event summaries
MAX_EVENTS_TO_PROCESS = 5 # Maximum number of events to process

# Define tool for fetching URL content
def fetch_url(url: str) -> str:
    """Fetches the content of a URL."""
    try:
        print("Fetching "+url)
        with contextlib.redirect_stdout(None):
            response = requests.get(url)
            response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"

# Define tool for extracting text from HTML
def extract_text_from_html(html: str) -> str:
    """Extracts text from HTML content."""
    with contextlib.redirect_stdout(None):
        soup = BeautifulSoup(html, 'html.parser')
    result = soup.get_text()
    print(result)
    return result

# Define tool for LLM completion
def llm_completion(env: Environment, messages: list) -> str:
    """Gets an LLM completion from the environment."""
    try:
        return env.completion(messages)
    except Exception as e:
        return f"Error during LLM completion: {e}"

def run(env: Environment):
    # Register tools
    env.get_tool_registry().register_tool(fetch_url)
    env.get_tool_registry().register_tool(extract_text_from_html)
    env.get_tool_registry().register_tool(llm_completion)

    # Initialize variables
    processed_events = []

    # Load existing summaries if they exist
    try:
        files = env.list_files_from_thread()
        if any(file.filename == SUMMARY_FILE for file in files):
            print(f"Reading existing summaries from {SUMMARY_FILE}")
            summary_data = env.read_file(SUMMARY_FILE)
            processed_events = json.loads(summary_data)
    except Exception as e:
        print(f"Error loading existing summaries: {e}")

    # Your agent code here
    prompt = {"role": "system", "content": "You are an agent processing publicly available events to see if there's free food at these events and how likely."}

    # File to store iCal data
    ical_file = ICAL_FILE

    # Check if the file exists
    try:
        files = env.list_files_from_thread()
        if any(file.filename == ical_file for file in files):
            # Read from file
            print(f"Reading iCal data from {ical_file}")
            ical_data = env.read_file(ical_file)
            events = parse_ical_data(ical_data)
        else:
            # 1. Fetch iCal data
            ical_url = ICAL_URL
            try:
                ical_data = fetch_url(ical_url)
                if "Error" in ical_data:
                    print(ical_data)
                    return
            except requests.exceptions.RequestException as e:
                print(f"Error fetching iCal data: {e}")
                return

            # 2. Parse iCal data
            try:
                events = parse_ical_data(ical_data)
            except Exception as e:
                print(f"Error parsing iCal data: {e}")
                return

            # 3. Store iCal data to file
            print(f"Writing iCal data to {ical_file}")
            env.write_file(ical_file, ical_data)

    except Exception as e:
        print(f"Error handling file: {e}")
        return

    # 4. Filter events
    num_events = len(events)
    start_index = 0
    events_processed_count = 0 #Counter to track total events processed

    while start_index < num_events and events_processed_count < MAX_EVENTS_TO_PROCESS:
        print(f"Processing events {start_index + 1} to {min(start_index + (MAX_EVENTS_TO_PROCESS - events_processed_count), num_events)} of {num_events}")

        for i in range(start_index, min(start_index + (MAX_EVENTS_TO_PROCESS - events_processed_count), num_events)):
            if i >= num_events:
                break #Break inner loop if max events are processed

            print("\n" + "=" * 40)  # Section separator
            event = events[i]
            summary = event.get('SUMMARY')
            description = event.get('DESCRIPTION')
            url = event.get('URL')
            print(f"Event: {summary}")
            print(f"URL: {url}")
            #print(f"Description: {description}")

            # 5. Initial LLM check on description
            system_message_initial = {
                "role": "system",
                "content": "Parse the event name and description and return only true/false and nothing else. true if the description suggests there's a good chance of free food, false otherwise. event description doesn't need to mention food, still return true if the type of events may have free food."
            }
            user_message_initial = {"role": "user", "content": str(summary)+str(description)}
            
            llm_response_initial = llm_completion(env, [system_message_initial, user_message_initial])
            print("Initial LLM Response:")
            pprint.pp(llm_response_initial)

            if llm_response_initial.lower() == "true":
                print(f"LLM (initial) says potential free food based on description: {summary}")
                if url and str(url).startswith("https://"):
                    # 6. Fetch event details
                    event_html = fetch_url(str(url))
                    if "Error" in event_html:
                        print(event_html)
                        continue

                    # 7. Extract text from HTML
                    with contextlib.redirect_stdout(None):
                        event_text = extract_text_from_html(event_html)

                    # 8. Final LLM check on full event details
                    system_message_final = {
                        "role": "system",
                        "content": "Return how likely (very likely, likely, unlikely, very unlikely) followed by a summarization of the event details mentioning food."
                    }
                    user_message_final = {"role": "user", "content": event_text}
                    
                    llm_response_final = llm_completion(env, [system_message_final, user_message_final])
                    print("Final LLM Response:")
                    pprint.pp(llm_response_final)

                    # Parse the LLM response
                    parts = llm_response_final.split(',', 1)
                    likelihood = parts[0].strip()
                    event_summary = parts[1].strip() if len(parts) > 1 else ""

                    print(f"Likelihood: {likelihood}")
                    print(f"Summary: {event_summary}")

                    #Create event summary
                    event_data = {
                        "name": summary,
                        "url": str(url),
                        "food_description": event_summary,
                        "initial_llm_response": llm_response_initial,
                        "final_llm_response": llm_response_final,
                        "likelihood": likelihood
                    }
                    processed_events.append(event_data)
                else:
                    print(f"No valid URL found for event: {summary}")
                    #Create event summary
                    event_data = {
                        "name": summary,
                        "url": "No URL",
                        "food_description": "No URL",
                        "initial_llm_response": llm_response_initial,
                        "final_llm_response": "No URL",
                        "likelihood": "No URL"
                    }
                    processed_events.append(event_data)
            else:
                print(f"LLM (initial) says unlikely to have free food at: {summary}")
                event_data = {
                        "name": summary,
                        "url": str(url),
                        "food_description": "No food in description",
                        "initial_llm_response": llm_response_initial,
                        "final_llm_response": "No food in description",
                        "likelihood": "No food in description"
                    }
                processed_events.append(event_data)
            
            events_processed_count += 1 #Increment event counter
        start_index += 1

    # Save the updated summaries
    try:
        print(f"Writing updated summaries to {SUMMARY_FILE}")
        env.write_file(SUMMARY_FILE, json.dumps(processed_events))
    except Exception as e:
        print(f"Error saving summaries: {e}")

    # Prepare context for final LLM call
    try:
        summary_data = env.read_file(SUMMARY_FILE)
        event_summaries = json.loads(summary_data)
        context = json.dumps(event_summaries, indent=2)  # Format for readability
    except Exception as e:
        context = f"Error reading or parsing {SUMMARY_FILE}: {e}"

    final_prompt = {
        "role": "system",
        "content": f"Here are the event summaries from {SUMMARY_FILE}:\n{context}\n\nBased on these summaries, provide a final summary of potential free food opportunities and their likelihood.  Also, suggest some specific events to consider attending."
    }

    # Make the final LLM call
    final_llm_response = llm_completion(env, [prompt, final_prompt] + env.list_messages())
    print("Final LLM Response:")
    pprint.pp(final_llm_response)
    env.add_reply(final_llm_response)
    env.request_user_input()


run(env)
