import requests
import json
import time
import re
import logging
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askdirectory
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_KEY = "AIzaSyCOTWK12YPwattWYvn1QGxaXyISxK4PpI0"
CHAT_DATA = []

def post_prompt(chat_data, api_key):
    """Sends a request to the API and returns the response."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": chat_data}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        response_json = response.json()

        if 'candidates' in response_json and response_json['candidates']:
            first_candidate = response_json['candidates'][0]
            if 'content' in first_candidate and 'parts' in first_candidate['content'] and first_candidate['content']['parts']:
                response_text = first_candidate['content']['parts'][0].get('text', '')
                chat_data.append({"parts": [{"text": response_text}], "role": "model"})
                return response_text
        logging.warning("The response contains no candidates.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing the JSON response: {e}")
        return None

def get_prompt(text, keyword):
    """Extracts the text between two keywords."""
    pattern = r'\b' + re.escape(keyword) + r'\b(.*?)\b' + re.escape(keyword) + r'\b'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def process_file(file_path, prev_prompt, chat_data, api_key):
    """Reads the file, processes the prompt, and writes the response back."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cur_content = f.read()

        prompts = get_prompt(cur_content, "_prompt")
        if prompts:
            latest_prompt = prompts[-1].strip()

            if latest_prompt != prev_prompt:
                logging.info(f"Sending prompt: {latest_prompt}")
                chat_data.append({"parts": [{"text": latest_prompt}], "role": "user"})

                answer = post_prompt(chat_data, api_key)
                if answer:
                    logging.info(f"Received response: {answer}")
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(f"\n\n_answer --------- \n\n{answer}\n ----------------")
                    return latest_prompt
    except FileNotFoundError:
        logging.error(f"The file {file_path} was not found.")
    except re.error as e:
        logging.error(f"Regex error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return prev_prompt

def select_folder():
    """Opens a GUI to select a folder and returns the selected path."""
    Tk().withdraw()  
    folder_path = askdirectory(title="Select a Folder")
    if folder_path:
        logging.info(f"Selected folder: {folder_path}")
    else:
        logging.warning("No folder selected.")
    return folder_path

def find_text_files(folder_path, prefix):
    """Finds all .txt files in the folder with the specified prefix."""
    text_files = []
    for file_name in os.listdir(folder_path):
        if file_name.startswith(prefix) and file_name.endswith(".txt"):
            text_files.append(os.path.join(folder_path, file_name))
    return text_files

if __name__ == "__main__":
    folder_path = select_folder()
    if folder_path:
        prefix = "_ai" 

        while True:
            text_files = find_text_files(folder_path, prefix)
            if not text_files:
                logging.info("No matching text files found. Waiting...")
                time.sleep(2)  # Wait before checking again
                continue

            # Process the first matching file
            file_path = text_files[0]
            logging.info(f"Using file for chat: {file_path}")

            prev_prompt = ""
            while True:
                prev_prompt = process_file(file_path, prev_prompt, CHAT_DATA, API_KEY)
                time.sleep(1)  # Reduce CPU usage