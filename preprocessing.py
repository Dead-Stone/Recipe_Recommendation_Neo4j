# preprocessing.py

import pandas as pd
import logging
from data_processing import parse_ingredient
from knowledge_graph import create_knowledge_graph
from dotenv import load_dotenv
import os

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Path to your CSV file
data_path = 'receipes.csv'

# Function to parse ingredients list from a string representation
def parse_ingredients_list(ingredients_str):
    try:
        ingredients_list = eval(ingredients_str)
        # print(':::::::::::::::::::::::::::::::::::::::::::',ingredients_list)
        return [parse_ingredient(ingredient) for ingredient in ingredients_list]
    except Exception as e:
        logger.error(f"Error parsing ingredients: {e}")
        return []

# Function to add a new ingredient to the knowledge graph if it doesn't exist
def add_new_ingredient(ingredient_name, all_ingredients):
    """
    Add a new ingredient to the knowledge graph and ingredient list
    Args:
        ingredient_name (str): Name of the ingredient to add
        all_ingredients (list): Current list of all ingredients
    Returns:
        list: Updated list of ingredients
    """
    # print("inside add_new_ingredient before if")
    print(all_ingredients,":::",ingredient_name)
    if isinstance(all_ingredients, list) and ingredient_name not in all_ingredients:
        # Create ingredient node in knowledge graph
        print("inside add_new_ingredient")
        create_knowledge_graph(ingredient_name, [], [])
        # Add to list and sort
        all_ingredients.append(ingredient_name)
        all_ingredients.sort()
        logger.info(f"Added new ingredient: {ingredient_name}")
    return all_ingredients

def load_and_preprocess_data():
    # Load the CSV file
    df = pd.read_csv(data_path)

    # Parse ingredients and add parsed ingredients column
    df['parsed_ingredients'] = df['ingredients'].apply(parse_ingredients_list)
    # print('::::::::::::::::::::::::::----------------------:::::::::::::::::',df['parsed_ingredients'])
    # Extract individual ingredients from the parsed ingredients
    all_ingredients = set()
    for ingredients in df['parsed_ingredients']:
        for ingredient in ingredients:
            all_ingredients.add(ingredient['ingredient'])

    # Convert set to list and sort
    all_ingredients = sorted(list(all_ingredients))
    
    # Update the knowledge graph with all ingredients
    for ingredient in all_ingredients:
        print("inside for loop",ingredient,all_ingredients)
        add_new_ingredient(ingredient, all_ingredients)
    
    return df, all_ingredients



if __name__ == "__main__":
    logger.info("Starting data preprocessing...")
    df, all_ingredients = load_and_preprocess_data()
    logger.info("Data preprocessing completed.")
