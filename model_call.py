#model_call.py

import openai
import json
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables from the .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# API Keys and URLs from environment variables
KOLANK_API_KEY = os.getenv("KOLANK_API_KEY")
KOLANK_URL = os.getenv("KOLANK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Log setup information
logging.info(f"KOLANK_API_KEY: {KOLANK_API_KEY}")
logging.info(f"KOLANK_URL: {KOLANK_URL}")
logging.info(f"OPENAI_API_KEY: {OPENAI_API_KEY}")

# Function for calling Kolank API using OpenAI
def call_kolank_api(messages, response_format={ "type": "json_object" }):
    try:
        client = OpenAI(base_url=KOLANK_URL, api_key=KOLANK_API_KEY)
        response = client.chat.completions.create(
            model="Openai/gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
            response_format=response_format
        )
        json_response = response.choices[0].message.content
        logger.debug(f"Kolank Model response: {json_response}")

        data = json.loads(json_response)  # Parse the JSON response

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        data = None
    except Exception as e:
        logger.error(f"Error calling Kolank API: {e}")
        data = None

    return data

# Function for calling OpenAI API directly
def call_openai_api(messages, response_format={ "type": "json_object" }, max_tokens=1024, temperature=0.2):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Specify the appropriate model name here
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format
        )

        # Extract the message content from the response
        json_response = response.choices[0].message.content
        logger.debug(f"OpenAI Model response: {json_response}")

        # Parse the JSON response
        data = json.loads(json_response)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        data = None
    

    return data
