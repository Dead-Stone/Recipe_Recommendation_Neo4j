# app.py

import gradio as gr
import json
import logging
from knowledge_graph import create_knowledge_graph, check_recipe_exists, get_recipe_from_kg  # Updated import
from model_call import call_kolank_api
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

from preprocessing import add_new_ingredient, load_and_preprocess_data

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Neo4j connection setup
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD")
print(':::::::::::::::::::::::::::::::::::::::::::',neo4j_uri, neo4j_username, neo4j_password)
# Initialize Neo4j driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

def get_all_ingredients():
    with driver.session() as session:
        result = session.run("MATCH (i:Ingredient) RETURN i.name AS name")
        all_ingredients = [record["name"] for record in result]
    return sorted(all_ingredients)

df, tmp_ingredients = load_and_preprocess_data()

# Get all ingredients from the knowledge graph
all_ingredients = get_all_ingredients()

# Function to prompt the AI model for structured JSON response
def get_recipe_suggestion(ingredients):
    ingredient_text = ', '.join(ingredients) 

    logger.debug(f"Prompting model with ingredients: {ingredients}")
    messages = [
        {"role": "system", "content": "You are a culinary expert. Provide the full recipe details including title, ingredients, directions, and tips in JSON format."},
        {"role": "user", "content": f"Provide the recipe details in the specified JSON format using only these ingredients: {ingredient_text}."}
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

    response = call_kolank_api(messages, response_format)
    if response:
        return response  # Parse JSON response
    else:
        return "Error generating recipe. Please try again."

# Function to check if a recipe exists in the KG
def check_recipe_in_kg(title, ingredients):
    with driver.session() as session:
        result = session.run(
            "MATCH (r:Product {title: $title})-[:USES]->(i:Ingredient) "
            "WHERE i.name IN $ingredients "
            "RETURN r.title, collect(i.name) as ingredients",
            title=title,
            ingredients=ingredients
        )
        return result.single() is not None

# Function to process the recipe data and create nodes/edges in the graph
def process_recipe_data(recipe_data):
    logger.debug(f"Processing recipe data: {recipe_data}")
    
    if isinstance(recipe_data, dict):
        title = recipe_data.get('title', 'Untitled Recipe')
        ingredients = recipe_data.get('Ingredients', [])
        ingredient_names = [ing.get('ingredient', '') for ing in ingredients]
        
        if check_recipe_in_kg(title, ingredient_names):
            logger.info(f"Recipe '{title}' already exists in the KG.")
            return get_recipe_from_kg(title, ingredient_names)
        else:
            directions = recipe_data.get('directions', [])
            tips = recipe_data.get('tips', "")

            # Save the new recipe to the graph
            create_knowledge_graph(title, ingredients, directions)
            
            # Format the output for display
            result = f"**New Recipe Generated:**\n\n"
            result += f"**Title:** {title}\n\n"
            result += "**Ingredients:**\n" + "\n".join(
                f"- {ingredient.get('quantity', 'to taste')} {ingredient.get('ingredient', '')}".strip()
                for ingredient in ingredients
            ) + "\n\n"
            result += "**Directions:**\n" + "\n".join(f"**Step {i+1}:** {step}" for i, step in enumerate(directions)) + "\n\n"
            if tips:
                result += f"**Tips:** {tips}\n"  # Join the tips into a single string
            
            return result
    else:
        logger.error("Recipe data does not have the expected structure.")
        return "Error generating recipe. Please try again."

# # Function to get recipes based on selected ingredients
# def get_recipes(selected_ingredients, new_ingredient):
#     logger.debug(f"Selected ingredients: {selected_ingredients}, New ingredient: {new_ingredient}")
#     global all_ingredients  # Declare the variable as global
#     if new_ingredient and new_ingredient not in all_ingredients:
#         try:
#             all_ingredients = add_new_ingredient(new_ingredient, all_ingredients)
#             logger.debug(f"Ingredient list after adding: {all_ingredients}")
#         except Exception as e:
#             logger.error(f"Error adding new ingredient: {e}")
#             return "Error adding new ingredient. Please try again."

#     logger.debug(f"Final set of ingredients: {set(selected_ingredients)}")
#     recipe_data = get_recipe_suggestion(list(set(selected_ingredients)))
    
#     return process_recipe_data(recipe_data)
def get_recipes(selected_ingredients, new_ingredient):
    logger.debug(f"Selected ingredients: {selected_ingredients}, New ingredient: {new_ingredient}")
    ingredients_to_use = set(selected_ingredients or [])
    
    if new_ingredient:
        new_ingredient = new_ingredient.strip()
        if new_ingredient and new_ingredient not in ingredients_to_use:
            ingredients_to_use.add(new_ingredient)
            try:
                all_ingredients = add_new_ingredient(new_ingredient, all_ingredients)
            except Exception as e:
                logger.error(f"Error adding new ingredient: {e}")
    
    if not ingredients_to_use:
        return "Please select at least one ingredient"
        
    try:
        recipe_data = get_recipe_suggestion(list(ingredients_to_use))
        return process_recipe_data(recipe_data)
    except Exception as e:
        logger.error(f"Error generating recipe: {e}")
        return "Error generating recipe. Please try again."
# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# Recipe Recommendation System")
    
    search_input = gr.Textbox(
        label="Search or Add Ingredient",
        placeholder="Type an ingredient and press Enter to add if not found"
    )
    
    ingredients_input = gr.CheckboxGroup(
        choices=all_ingredients,
        label="Select Available Ingredients",
        interactive=True,
        elem_id="ingredients-selection"
    )
    
    generate_button = gr.Button("Get recipes")
    output = gr.Markdown(label="Recommended Recipes")
    
    def update_ingredient_list(search_input_value):
        logger.debug(f"Search input received: {search_input_value}")
        global all_ingredients
        
        if not search_input_value:
            return gr.update(choices=all_ingredients)
            
        # Clean the input
        search_input_value = search_input_value.strip()
        print("values::::::::",search_input_value,all_ingredients)
        if search_input_value and search_input_value not in all_ingredients:
            try:
                # Add new ingredient
                all_ingredients = add_new_ingredient(search_input_value, all_ingredients)
                logger.debug(f"Updated ingredient list: {all_ingredients}")
                return gr.update(choices=all_ingredients, value=[search_input_value])
            except Exception as e:
                logger.error(f"Error updating ingredient list: {e}")
                return gr.update(choices=all_ingredients)
                
        return gr.update(choices=all_ingredients)

    search_input.submit(
        update_ingredient_list, 
        inputs=search_input, 
        outputs=ingredients_input
    )
    
    generate_button.click(
        get_recipes, 
        inputs=[ingredients_input, search_input], 
        outputs=output
    )

# Launch Gradio app
if __name__ == "__main__":
    logger.info("Starting Gradio application...")
    demo.launch(share=True)
