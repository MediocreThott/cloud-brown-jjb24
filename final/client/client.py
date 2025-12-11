import os
import requests
import json
import google.generativeai as genai

# --- CONFIGURATION ---
GOOGLE_API_KEY = ***REMOVED***
SERVER_BASE_URL = 'https://fantasy-server-780966768163.us-central1.run.app'
FANTASY_API_KEY = 'super-secret-key-12345'
HEADERS = {'X-API-Key': FANTASY_API_KEY}

# --- TOOL DEFINITIONS ---
def get_leagues():
    """Returns a list of all fantasy basketball league IDs for the user."""
    print("... Calling get_leagues tool ...")
    try:
        response = requests.get(f"{SERVER_BASE_URL}/leagues", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error connecting to server: {e}"

def get_teams(league_id: str):
    """Returns a list of all teams and their managers for a given league ID."""
    print(f"... Calling get_teams tool for league: {league_id} ...")
    try:
        response = requests.get(f"{SERVER_BASE_URL}/league/{league_id}/teams", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error connecting to server: {e}"

# --- MAIN CLIENT LOGIC ---
def main():
    print("--- Fantasy Basketball LLM Client ---")
    genai.configure(api_key=GOOGLE_API_KEY)
    system_instruction = (
        "You are a helpful and knowledgeable fantasy basketball assistant. "
        "Your goal is to answer the user's questions by using the available tools. "
        "If you need to know the user's league ID before answering a question, "
        "you must first use the get_leagues() tool to find it."
    )
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        tools=[get_leagues, get_teams],
        system_instruction=system_instruction
    )
    chat = model.start_chat(enable_automatic_function_calling=True)
    print("Ready! Ask a question about your fantasy leagues.\n")
    while True:
        try:
            query = input("You: ")
            if query.lower() in ['exit', 'quit']: break
            response = chat.send_message(query)
            print(f"LLM: {response.text}\n")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()