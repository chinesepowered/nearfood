import requests
import icalendar
from bs4 import BeautifulSoup
from nearai.agents.environment import Environment
import json
import os


def run(env: Environment):
    # Your agent code here
    prompt = {"role": "system", "content": "Crawl events and find food"}
    result = env.completion([prompt] + env.list_messages())
    env.add_reply(result)
    env.request_user_input()

    # File to store iCal data
    ical_file = "ical_data.json"

    # Check if the file exists
    try:
        files = env.list_files_from_thread()
        if any(file.filename == ical_file for file in files):
            # Read from file
            print(f"Reading iCal data from {ical_file}")
            ical_data = env.read_file(ical_file)
            calendar = icalendar.Calendar.from_ical(ical_data.encode('utf-8'))
        else:
            # 1. Fetch iCal data
            ical_url = "https://api.lu.ma/ics/get?entity=discover&id=discplace-BDj7GNbGlsF7Cka"
            try:
                response = requests.get(ical_url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                ical_data = response.text
            except requests.exceptions.RequestException as e:
                print(f"Error fetching iCal data: {e}")
                return

            # 2. Parse iCal data
            try:
                calendar = icalendar.Calendar.from_ical(ical_data)
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
    for event in calendar.walk('VEVENT'):
        summary = event.get('summary')
        description = event.get('description')
        url = event.get('location')  # changed from url = event.get('url')
        # 5. Initial LLM check on description
        system_message_initial = {
            "role": "system",
            "content": "Parse the description and return only true/false and nothing else. true if the event type MAY have free food (tech events, hackathons, tech demos, meetups, etc), false otherwise."
        }
        user_message_initial = {"role": "user", "content": str(description)}
        try:
            llm_response_initial = env.completion([system_message_initial, user_message_initial])
            # print("Debug initial: "+llm_response_initial)
            # Extract the last word from the LLM's response
            last_word = llm_response_initial.split()[-1]
            if last_word.lower() == "true":
                print(f"LLM (initial) says potential free food based on description: {summary}")
                if url and str(url).startswith("https://"):
                    # 6. Fetch event details
                    try:
                        event_response = requests.get(str(url))
                        event_response.raise_for_status()
                        event_html = event_response.text
                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching event details: {e}")
                        continue

                    # 7. Extract text from HTML
                    soup = BeautifulSoup(event_html, 'html.parser')
                    event_text = soup.get_text()

                    # 8. Final LLM check on full event details
                    system_message_final = {
                        "role": "system",
                        "content": "Parse text and return only true/false and nothing else. true if it's free to register and there's a mention of free food (or at least mention of food and no mention of it costing money or buying your own), false otherwise."
                    }
                    user_message_final = {"role": "user", "content": event_text}
                    try:
                        llm_response_final = env.completion([system_message_final, user_message_final])
                        # print("Debug: "+llm_response_final)
                        # Extract the last word from the LLM's response
                        last_word_final = llm_response_final.split()[-1]
                        if last_word_final.lower() == "true":
                            print(f"Confirmed by LLM (final): Free food at: {summary} - {url}")
                            # 9. Sign up for event (implementation needed)
                            # signup(url)
                        else:
                            print(f"LLM (final) says no free food at: {summary} - {url}")
                    except Exception as e:
                        print(f"Error during LLM completion (final): {e}")
                else:
                    print(f"No valid URL found for event: {summary}")
            else:
                print(f"LLM (initial) says no free food in description: {summary}")
        except Exception as e:
            print(f"Error during LLM completion (initial): {e}")


run(env)
