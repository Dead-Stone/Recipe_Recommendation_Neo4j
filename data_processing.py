# data_processing.py

import pandas as pd
import json
import logging
from model_call import call_kolank_api, call_openai_api
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_data(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Check if 'ingredients' column exists and process it
    if 'ingredients' not in df.columns:
        raise KeyError("The CSV file does not contain an 'ingredients' column.")

    # Define a function to call the model for parsing the full recipe details
    def get_full_recipe_details(recipe_title, ingredient_list):
        # Convert the list to a single string if it's not already
        ingredient_text = ', '.join(ingredient_list) if isinstance(ingredient_list, list) else ingredient_list

        # Define the messages to send to the model
        messages = [
            {"role": "system", "content": "You are a culinary expert. Provide the full recipe details including title, ingredients, directions, and tips in JSON format."},
            {"role": "user", "content": f"Title: {recipe_title}. Ingredients: {ingredient_text}. Provide the recipe details in the specified JSON format."}
        ]

        # Define the JSON schema with the corrected format
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "Ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "quantity": {"type": "string"},
                            "ingredient": {"type": "string"}
                        },
                        "required": ["quantity", "ingredient"],
                        "additionalProperties": False
                    }
                },
                "directions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "tips": {"type": "string"}
            },
            "required": ["title", "Ingredients", "directions", "tips"],
            "additionalProperties": False
        }

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "recipe_response",
                "strict": True,
                "schema": schema
            }
        }

        return call_kolank_api(messages, response_format=response_format)

    # Apply the function to each row's 'ingredients' column and store the results in 'parsed_ingredients'
    df['parsed_ingredients'] = df.apply(lambda row: get_full_recipe_details(row['title'], row['ingredients'])['Ingredients'], axis=1)

    return df

def parse_ingredients_list(ingredients_str):
    try:
        # Evaluate the string to a list
        ingredients_list = eval(ingredients_str)
        # Convert each ingredient string to a dictionary
        return [parse_ingredient(ingredient) for ingredient in ingredients_list]
    except Exception as e:
        print(f"Error parsing ingredients: {e}")
        return []

def parse_ingredient(ingredient):
    # Assuming the ingredient is in the form "quantity ingredient_name"
    parts = ingredient.split(maxsplit=1)
    if len(parts) == 2:
        quantity, ingredient_name = parts
        return {"quantity": quantity, "ingredient": ingredient_name}
    else:
        return {"quantity": "", "ingredient": ingredient}

