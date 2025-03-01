import csv
import os
from neo4j import GraphDatabase

# Neo4j Credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

# Function to connect and run a Cypher query
def execute_query(driver, cypher_query, parameters=None):
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.run(cypher_query, parameters)
    except Exception as e:
        print(f"Error: {e}")

# Function to create nodes
def create_player_node(driver, player, matches, goals, xG, shots, year):
    query = """
    MERGE (p:Player {name: $player, matches: $matches, goals: $goals, xG: $xG, shots: $shots, year: $year})
    """
    parameters = {"player": player, "matches": matches, "goals": goals, "xG": xG, "shots": shots, "year": year}
    execute_query(driver, query, parameters)

def create_club_node(driver, club):
    query = "MERGE (c:Club {name: $club})"
    parameters = {"club": club}
    execute_query(driver, query, parameters)

def create_league_node(driver, league):
    query = "MERGE (l:League {name: $league})"
    parameters = {"league": league}
    execute_query(driver, query, parameters)

def create_country_node(driver, country):
    query = "MERGE (c:Country {name: $country})"
    parameters = {"country": country}
    execute_query(driver, query, parameters)

# Function to create relationships
def create_relationships(driver, player, club, league, country):
    query = """
    MATCH (p:Player {name: $player}), (c:Club {name: $club})
    MERGE (p)-[:PLAYS_FOR]->(c)
    WITH c
    MATCH (c), (l:League {name: $league})
    MERGE (c)-[:PART_OF]->(l)
    WITH l
    MATCH (l), (cn:Country {name: $country})
    MERGE (l)-[:IN_COUNTRY]->(cn)
    """
    parameters = {"player": player, "club": club, "league": league, "country": country}
    execute_query(driver, query, parameters)

# Main function to read the CSV file and populate the graph
def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

    with open("data/football_Data.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        print("Reading CSV file...")

        for row in reader:
            country = row["Country"]
            league = row["League"]
            club = row["Club"]
            player = row["Player Names"]
            matches = int(row["Matches_Played"])
            goals = int(row["Goals"])
            xG = float(row["xG"])  # Expected Goals
            shots = int(row["Shots"])
            year = int(row["Year"])

            create_player_node(driver, player, matches, goals, xG, shots, year)
            create_club_node(driver, club)
            create_league_node(driver, league)
            create_country_node(driver, country)
            create_relationships(driver, player, club, league, country)

    driver.close()
    print("Football graph populated successfully!")

# Run the main function
if __name__ == "__main__":
    main()
