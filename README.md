GraphRAG Football Chatbot ⚽🤖
GraphRAG Football Chatbot is an AI-powered chatbot that integrates Neo4j, OpenAI embeddings, and LLMs to provide structured football knowledge retrieval using GraphRAG (Graph + Retrieval-Augmented Generation).

🚀 Features
✅ Neo4j Knowledge Graph: Stores players, clubs, leagues, and performance stats.
✅ Graph-Based Retrieval: Converts queries into Cypher for structured retrieval.
✅ OpenAI Embeddings: Enables similarity search for player comparisons.
✅ Streamlit Chatbot UI: User-friendly interface for football-related queries.

📂 Project Structure
bash
Copy
Edit
📁 graphrag-football-chatbot
 ├── football_kg_loader.py         # Loads football data into Neo4j
 ├── football_kg_embeddings.py     # Generates and stores OpenAI embeddings in Neo4j
 ├── football_kg_chatbot.py        # Streamlit chatbot for football queries
 ├── requirements.txt              # Required dependencies
 ├── .env                          # API keys (not shared for security reasons)
🔧 Setup & Installation
1️⃣ Clone the Repository

bash
Copy
Edit
git clone https://github.com/YOUR_USERNAME/graphrag-football-chatbot.git
cd graphrag-football-chatbot
2️⃣ Install Dependencies

bash
Copy
Edit
pip install -r requirements.txt
3️⃣ Set Up API Keys
Create a .env file and add your OpenAI & Neo4j credentials:

ini
Copy
Edit
OPENAI_API_KEY=your_openai_api_key
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_username
NEO4J_PASSWORD=your_password
4️⃣ Run the Chatbot

bash
Copy
Edit
streamlit run football_kg_chatbot.py
🎯 Example Queries
"What are Erling Haaland's stats?"
