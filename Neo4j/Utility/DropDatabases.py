import sys
import os
import configparser
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def clear_database_content(driver, database_name, batch_size=50000):
    """Cancella tutti i nodi e le relazioni in un database specifico."""
    with driver.session(database=database_name) as session:
        while True:
            # Controlla se ci sono nodi rimasti
            result = session.run("MATCH (n) RETURN count(n) AS count").single()
            node_count = result["count"] if result else 0
            
            if node_count == 0:
                print(f"Database '{database_name}' is already empty.")
                break

            print(f"Found {node_count} nodes in '{database_name}'. Deleting in batches...")
            
            # Esegui la cancellazione in batch
            query = f"MATCH (n) WITH n LIMIT {batch_size} DETACH DELETE n RETURN count(n) AS deleted_count"
            summary = session.run(query).consume()
            
            print(f"Deleted a batch of nodes. Checking remaining...")
            # Dopo l'esecuzione, il loop verificherà di nuovo il conteggio
    
    print(f"All nodes and relationships have been dropped in database '{database_name}'.")


def main():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'))
    
    uri = config['Neo4j']['uri']
    user = config['Neo4j']['user']
    password = config['Neo4j']['password']
    
    databases = ["dataset100", "dataset75", "dataset50", "dataset25"]
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Connected to Neo4j.")
        
        for db_name in databases:
            print(f"\nProcessing database: {db_name}")
            clear_database_content(driver, db_name)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("\nConnection to Neo4j closed.")

if __name__ == "__main__":
    main()