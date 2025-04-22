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
                return response_text
        logging.warning("The response contains no candidates.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing the JSON response: {e}")
        return None

def get_prompt(text):
    """Extracts all prompts from the text using the original pattern."""
    pattern = r'\b_prompt\b(.*?)\b_prompt\b'
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]

def get_answers(text):
    """Extracts all answers from the text."""
    pattern = r'_answer ---------\s*\n\n(.*?)\n ----------------'
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]

def build_chat_data(prompts, answers):
    """Builds the chat data from prompts and answers."""
    chat_data = []
    
    # Add complete prompt-answer pairs
    for i in range(min(len(prompts), len(answers))):
        chat_data.append({"parts": [{"text": prompts[i]}], "role": "user"})
        chat_data.append({"parts": [{"text": answers[i]}], "role": "model"})
    
    # Add the last prompt if there's one more prompt than answers
    if len(prompts) > len(answers):
        chat_data.append({"parts": [{"text": prompts[-1]}], "role": "user"})
        
    return chat_data

def process_file(file_path, file_data):
    """Reads the file, processes the prompt, and writes the response back."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cur_content = f.read()
        
        # Extract all prompts and answers
        all_prompts = get_prompt(cur_content)
        all_answers = get_answers(cur_content)
        
        # Build the chat data
        chat_data = build_chat_data(all_prompts, all_answers)
        
        # Check if there's a prompt without an answer
        if len(all_prompts) > len(all_answers):
            latest_prompt = all_prompts[-1]
            logging.info(f"Found new prompt to process: {latest_prompt}")
            
            # Get response from API
            answer = post_prompt(chat_data, file_data["api_key"])
            
            if answer:
                logging.info(f"Received response: {answer}")
                
                # Append the answer to the file
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n_answer ---------\n\n{answer}\n ----------------")
                
                # Update file data with the new chat
                file_data["chat_data"] = chat_data + [{"parts": [{"text": answer}], "role": "model"}]
                return True
        else:
            logging.info(f"No new prompt to process for file: {file_path}")
            file_data["chat_data"] = chat_data
            
    except Exception as e:
        logging.error(f"An error occurred while processing {file_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return False

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
        if file_name.startswith(prefix):
            data = {
                "path": os.path.join(folder_path, file_name),
                "name": file_name,
                "chat_data": [],
                "api_key": API_KEY
            }
            text_files.append(data)
    return text_files

if __name__ == "__main__":
    folder_path = select_folder()
    if folder_path:
        prefix = "np_ai"
        files_data = {}

        while True:
            text_files = find_text_files(folder_path, prefix)
            if not text_files:
                logging.info("No matching files found. Waiting...")
                time.sleep(2)  
                continue

            # Process each file
            for file in text_files:
                file_path = file["path"]
                
                # Initialize file_data if its a new file
                if file_path not in files_data:
                    files_data[file_path] = file
                
                if os.path.exists(file_path):
                    process_file(file_path, files_data[file_path])
                else:
                    logging.warning(f"File {file_path} does not exist. Skipping.")
            
            time.sleep(2)  # Wait before checking files again