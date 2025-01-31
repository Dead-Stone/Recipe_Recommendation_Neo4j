# Recipe_Recommendation_Neo4j

A Neo4j-powered recipe recommendation system that uses a custom AI model to generate recipes on-the-fly. The project features a Gradio interface for ease of use, dynamically adds new ingredients to the knowledge graph, and provides step-by-step directions and cooking tips.

## Features
- Neo4j Knowledge Graph storing recipes and ingredients
- Automated recipe generation and recommendations via AI
- Easy ingredient addition on the fly
- User-friendly Gradio interface
- CSV preprocessing for initial data load
- Logging for troubleshooting

## Installation
1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up Neo4j and environment variables in `.env`:
   ```bash
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```
4. (Optional) Run the preprocessing script if you have CSV data:
   ```bash
   python preprocessing.py
   ```
5. Launch the application:
   ```bash
   python app.py
   ```
## Usage
  Open the Gradio interface (default: http://127.0.0.1:7860).
  Add or select ingredients and click "Get recipes" to see a recipe.
  Dynamically adds new ingredients and creates corresponding nodes in Neo4j.
## Credits
  Huge thanks to Kolank for providing free credits to support API usage.
  Built using Python, Cool AI tools, and Neo4j knowledge graph capabilities.

