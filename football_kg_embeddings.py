from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI

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
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT_EMBEDDINGS")

# Initialize Chat Model
chat = ChatOpenAI(api_key=OPENAI_API_KEY)

# Initialize Neo4j Graph Connection
kg = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)

# Create a vector index for football player embeddings
kg.query(
    """
    CREATE VECTOR INDEX football_players_embeddings IF NOT EXISTS
    FOR (p:Player) ON (p.embedding)
    OPTIONS {
      indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
      }
    }
    """
)

# Test if the index was created
res = kg.query("SHOW VECTOR INDEXES")
print(res)

# Generate embeddings for player descriptions
kg.query(
    """
    MATCH (p:Player)
    WHERE p.name IS NOT NULL
    WITH p, genai.vector.encode(
        p.name + ' played ' + toString(p.matches) + ' matches and scored ' + toString(p.goals) + ' goals.',
        "OpenAI",
        {
          token: $openAiApiKey,
          endpoint: $openAiEndpoint
        }) AS vector
    WITH p, vector
    WHERE vector IS NOT NULL
    CALL db.create.setNodeVectorProperty(p, "embedding", vector)
    """,
    params={
        "openAiApiKey": OPENAI_API_KEY,
        "openAiEndpoint": OPENAI_ENDPOINT,
    },
)

# Query the graph using vector search for similar players
question = "Who are the top goal scorers similar to Messi?"

result = kg.query(
    """
    WITH genai.vector.encode(
        $question,
        "OpenAI",
        {
          token: $openAiApiKey,
          endpoint: $openAiEndpoint
        }) AS question_embedding
    CALL db.index.vector.queryNodes(
        'football_players_embeddings',
        $top_k,
        question_embedding
    ) YIELD node AS player, score
    RETURN player.name, player.goals, player.matches, score
    """,
    params={
        "openAiApiKey": OPENAI_API_KEY,
        "openAiEndpoint": OPENAI_ENDPOINT,
        "question": question,
        "top_k": 5,
    },
)

# Print results
for record in result:
    print(f"Name: {record['player.name']}")
    print(f"Goals: {record['player.goals']}")
    print(f"Matches: {record['player.matches']}")
    print(f"Score: {record['score']}")
    print("---")
