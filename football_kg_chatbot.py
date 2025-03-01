import streamlit as st
from dotenv import load_dotenv
import os
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

# Load environment variables
load_dotenv()

# Get Neo4j credentials from environment
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

# Get OpenAI credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Football Knowledge Graph Chatbot",
    page_icon="⚽",
    layout="wide",
)

# Streamlit app header
st.title("⚽ Football Knowledge Graph Chatbot")
st.markdown("Ask questions about football players, clubs, leagues, and more!")

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_example" not in st.session_state:
    st.session_state.selected_example = None

# Function to initialize LLM and Knowledge Graph
@st.cache_resource
def initialize_chain():
    # Initialize OpenAI Chat Model
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    )

    # Initialize Neo4j Graph Connection
    kg = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )
    
    # Define Few-Shot Prompt Template for Cypher Generation
    CYPHER_GENERATION_TEMPLATE = """
    You are an expert Neo4j Developer translating user questions into Cypher queries for a football knowledge graph.
    Convert the user's question based on the schema.

    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.

    Do not return entire nodes or embedding properties.

    Example Cypher Statements:

    1. To find top goal scorers in a league:
    ```
    MATCH (p:Player)-[:PLAYS_FOR]->(c:Club)-[:PART_OF]->(l:League {{name: "La Liga"}})
    RETURN p.name, p.goals ORDER BY p.goals DESC LIMIT 5
    ```

    2. To find which players played for a club:
    ```
    MATCH (p:Player)-[:PLAYS_FOR]->(c:Club {{name: "Barcelona"}})
    RETURN p.name, p.matches ORDER BY p.matches DESC
    ```

    3. To find similar players based on embeddings:
    ```
    WITH genai.vector.encode(
        "Find players similar to Lionel Messi",
        "OpenAI",
        {{
          token: "{openai_api_key}",
          endpoint: "{openai_endpoint}"
        }}) AS query_embedding
    CALL db.index.vector.queryNodes(
        'football_players_embeddings',
        5,
        query_embedding
    ) YIELD node AS player, score
    RETURN player.name, player.goals, score
    ```

    Schema:
    {schema}

    Question:
    {question}
    """

    # Define QA Prompt Template for detailed responses
    QA_TEMPLATE = """
    You are a football statistics expert providing detailed information from a football knowledge graph.
    Always provide comprehensive, well-formatted answers that include ALL the data points from the query results.
    
    For statistical queries, include:
    - The player's full name
    - The specific statistic values (goals, matches, etc.)
    - The year/season of the statistic
    - Any club or league affiliations if available
    - Sort or group data in a meaningful way if appropriate
    
    Include contextual insights when possible, such as notable achievements, records, or comparisons.
    When presenting multiple players, use appropriate formatting like bullet points or tables in markdown.
    
    Context from the knowledge graph:
    {context}
    
    Question: {question}
    
    Detailed Answer:
    """

    # Get schema information from the database
    schema = kg.get_schema
    st.session_state.schema = schema

    # Set up prompt templates
    cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
    qa_prompt = PromptTemplate.from_template(QA_TEMPLATE)

    # Create a GraphRAG Chatbot using Few-Shot Cypher Query Generation
    cypher_qa = GraphCypherQAChain.from_llm(
        llm,
        graph=kg,
        verbose=True,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
        allow_dangerous_requests=True
    )
    
    return cypher_qa, schema

# Initialize the chain
chain, schema = initialize_chain()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Add a connection status indicator
if NEO4J_URI and OPENAI_API_KEY:
    st.sidebar.success("✅ Connected to Neo4j and OpenAI")
else:
    st.sidebar.error("❌ Missing connection details. Check .env file.")

# Display schema information in the sidebar
with st.sidebar.expander("Database Schema", expanded=False):
    st.code(schema, language="json")

# Define function to process a question (used for both chat input and examples)
def process_question(prompt):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            message_placeholder = st.empty()
            
            try:
                # Query the knowledge graph
                response = chain.invoke({
                    "query": prompt,
                    "question": prompt,
                    "schema": schema,
                    "openai_api_key": OPENAI_API_KEY,
                    "openai_endpoint": OPENAI_ENDPOINT
                })
                
                # Get the answer from the response
                answer = response.get('result', 'No answer found.')
                
                # Display the Cypher query used (if available)
                if 'intermediate_steps' in response:
                    with st.expander("View Cypher Query"):
                        cypher_query = response['intermediate_steps'][0]['query']
                        st.code(cypher_query, language="cypher")
                
                # Display the answer
                message_placeholder.markdown(answer)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Process selected example if there is one
if st.session_state.selected_example:
    prompt = st.session_state.selected_example
    st.session_state.selected_example = None  # Reset after using it
    process_question(prompt)

# Accept user input
if prompt := st.chat_input("Ask about football..."):
    process_question(prompt)

# Add example questions in the sidebar
st.sidebar.header("Example Questions")
example_questions = [
    "Who was the top goal scorer in La Liga in 2018?",
    "Who has played the most matches in the Bundesliga?",
    "Which players have similar goal-scoring stats to Mohamed Salah?",
    "Which players scored more than 30 goals in a season?",
    "What are the stats for Erling Haaland?"
]

# Function to set the selected example
def set_example(question):
    st.session_state.selected_example = question

# Create buttons for each example question
for question in example_questions:
    st.sidebar.button(question, on_click=set_example, args=(question,))

# Add app information
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This app uses Neo4j Graph Database and OpenAI to answer questions about football. "
    "It translates natural language questions into Cypher queries and returns results "
    "from the knowledge graph."
)