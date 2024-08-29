# knowledge_graph.py 

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Import the updated parse_ingredient function
from data_processing import parse_ingredient

# Load environment variables from the .env file
load_dotenv()

# Neo4j credentials from environment variables
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USER", "neo4j")  # Default to 'neo4j' if NEO4J_USER is not set
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Initialize the driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

# Initialize Neo4j driver (replace with your actual connection setup)
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

# Function to create a knowledge graph entry for a new recipe
def create_knowledge_graph(title, ingredients, directions):
    with driver.session() as session:
        session.write_transaction(_create_recipe, title, ingredients, directions)

def _create_recipe(tx, title, ingredients, directions):
    # Create recipe node
    tx.run("CREATE (r:Recipe {title: $title, directions: $directions})",
           title=title, directions=directions)
    # Create and link ingredient nodes
    for ingredient in ingredients:
        tx.run("MATCH (r:Recipe {title: $title}) "
               "MERGE (i:Ingredient {name: $ingredient}) "
               "MERGE (i)-[:USED_IN]->(r)",
               title=title, ingredient=ingredient['ingredient'])

# Function to check if a recipe exists in the KG
def check_recipe_exists(title, ingredients):
    with driver.session() as session:
        result = session.run(
            "MATCH (r:Recipe {title: $title})-[:USED_IN]->(i:Ingredient) "
            "WHERE i.name IN $ingredients "
            "RETURN r.title, collect(i.name) as ingredients",
            title=title,
            ingredients=ingredients
        )
        return result.single() is not None

# Function to get recipe details from KG if it exists
def get_recipe_from_kg(title, ingredients):
    with driver.session() as session:
        result = session.run(
            "MATCH (r:Recipe {title: $title})-[:USED_IN]->(i:Ingredient) "
            "WHERE i.name IN $ingredients "
            "RETURN r.title as title, r.directions as directions, collect(i.name) as ingredients",
            title=title,
            ingredients=ingredients
        )
        record = result.single()
        if record:
            return {
                'title': record['title'],
                'Ingredients': [{'ingredient': ing} for ing in record['ingredients']],
                'directions': record['directions']
            }
        return None
    
    
def create_knowledge_graph(recipe_title, ingredients, directions):
    
    with driver.session() as session:
        if ingredients == [] and directions == []:
            return session.write_transaction(_create_ingredient_node, recipe_title)
        # Create a Product node with title and directions properties
        session.write_transaction(_create_product_node, recipe_title, directions)
        
        for ingredient in ingredients:
            quantity = ingredient.get("quantity", "")
            ingredient_name = ingredient.get("ingredient", "")
            
            # Create an Ingredient node
            session.write_transaction(_create_ingredient_node, ingredient_name)
            
            # Create a relationship from Ingredient to Product
            session.write_transaction(_create_used_in_relationship, ingredient_name, recipe_title, quantity)
        
        for i, step in enumerate(directions, start=1):
            # Create a Direction node
            session.write_transaction(_create_direction_node, recipe_title, i, step)

def _create_product_node(tx, title, directions):
    query = """
    MERGE (p:Product {title: $title})
    SET p.directions = $directions
    """
    tx.run(query, title=title, directions=directions)

def _create_ingredient_node(tx, name):
    query = """
    MERGE (i:Ingredient {name: $name})
    """
    tx.run(query, name=name)

def _create_used_in_relationship(tx, ingredient_name, product_title, quantity):
    query = """
    MATCH (i:Ingredient {name: $ingredient_name})
    MATCH (p:Product {title: $product_title})
    MERGE (i)-[r:USED_IN {quantity: $quantity}]->(p)
    """
    tx.run(query, ingredient_name=ingredient_name, product_title=product_title, quantity=quantity)

def _create_direction_node(tx, product_title, order, description):
    query = """
    MATCH (p:Product {title: $product_title})
    CREATE (d:Direction {order: $order, description: $description})
    CREATE (p)-[:HAS_STEP {order: $order}]->(d)
    """
    tx.run(query, product_title=product_title, order=order, description=description)

# Don't forget to close the driver when you're done
def close_driver():
    driver.close()

# Example usage (remove this part in production)
# create_knowledge_graph("Sample Recipe", [{"quantity": "1 cup", "ingredient": "Sugar"}], ["Step 1: Mix ingredients."])
# close_driver()
