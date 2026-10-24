import configparser
import os
import sys
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def create_constraints_and_indexes(driver, db_name):
    """Crea vincoli di unicità e indici per un dato database."""
    print(f"--- Applying schema for database: {db_name} ---")
    
    queries = {
        "User ID Constraint": "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "BankAccount ID Constraint": "CREATE CONSTRAINT bank_account_id_unique IF NOT EXISTS FOR (a:BankAccount) REQUIRE a.id IS UNIQUE",
        "Device ID Constraint": "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE",
        "IPAddress ID Constraint": "CREATE CONSTRAINT ip_address_id_unique IF NOT EXISTS FOR (ip:IPAddress) REQUIRE ip.id IS UNIQUE",
        "Transaction ID Constraint": "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE",
    }
    
    with driver.session(database=db_name) as session:
        for name, query in queries.items():
            try:
                print(f"Applying: {name}...")
                session.run(query)
            except Exception as e:
                print(f"  Error applying '{name}': {e}")
    
    print(f"Schema setup for {db_name} completed.")


def main():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')
    config.read(config_path)
    
    uri = config['Neo4j']['uri']
    user = config['Neo4j']['user']
    password = config['Neo4j']['password']
    
    databases = ["dataset25", "dataset50", "dataset75", "dataset100"]
    
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Connected to Neo4j.")
        
        for db_name in databases:
            create_constraints_and_indexes(driver, db_name)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("\nConnection to Neo4j closed.")

if __name__ == "__main__":
    main()