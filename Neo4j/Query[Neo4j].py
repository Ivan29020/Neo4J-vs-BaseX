import time
import csv
import os
import configparser
import numpy as np
from scipy import stats
from neo4j import GraphDatabase
import logging

logging.getLogger("neo4j").setLevel(logging.ERROR)

# --- CONFIGURAZIONE ---
NUM_EXECUTIONS = 30
WARMUP_RUNS = 2

# --- CLASSE DI CONNESSIONE ---
class Neo4jConnection:
    def __init__(self, uri, user, password, database_name):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database_name = database_name

    def close(self):
        self._driver.close()

    def run_query(self, query):
        with self._driver.session(database=self.database_name) as session:
            return session.run(query).consume()
    
    def measure_query_time(self, query):
        start_time = time.perf_counter()
        self.run_query(query)
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000

# --- PROCESSO PRINCIPALE ---
def process_datasets():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)
    neo4j_config = config['Neo4j']

    database_mappings = {
        "25%": "dataset25", "50%": "dataset50",
        "75%": "dataset75", "100%": "dataset100"
    }

    # Query ordinate per complessità crescente
    queries = {
        'Query 1': """
            MATCH (u:User {id: 1})-[:OWNS]->(a:BankAccount)
            RETURN a.id, a.account_number, a.balance
        """,
        'Query 2': """
            MATCH (d:Device)-[:USES_ACCOUNT]->(a:BankAccount)
            WITH a, count(d) AS device_count
            WHERE device_count >= 7
            RETURN a.id AS account_id, device_count AS device_count 
        """,
        'Query 3': """
            MATCH (t:Transaction)
            WITH max(t.amount) AS max_amount
            MATCH (t:Transaction {amount: max_amount})-[:TO_ACCOUNT]->(a:BankAccount)<-[:OWNS]-(u:User)
            WITH u LIMIT 1

            MATCH (u)-[:OWNS_DEVICE]->(d:Device)
            MATCH (d)-[:HAS_IP]->(ip:IPAddress)

            RETURN u.name AS user_name, count(DISTINCT d) AS device_count, count(DISTINCT ip) AS distinct_ip_count
        """,
        'Query 4': """
            MATCH (t:Transaction)
            WITH max(t.amount) AS max_amount
            MATCH (su:User)-[:OWNS]->(:BankAccount)<-[:FROM_ACCOUNT]-(t:Transaction {amount: max_amount})-[:TO_ACCOUNT]->(:BankAccount)<-[:OWNS]-(ru:User)
            LIMIT 1

            OPTIONAL MATCH (su)-[:OWNS_DEVICE]->(sd:Device)-[:HAS_IP]->(si:IPAddress)
            WITH su, ru, t, count(DISTINCT sd) as source_device_count, count(DISTINCT si) as source_ip_count

            OPTIONAL MATCH (ru)-[:OWNS_DEVICE]->(rd:Device)-[:HAS_IP]->(ri:IPAddress)
            WITH su, ru, t, source_device_count, source_ip_count, count(DISTINCT rd) as recipient_device_count, count(DISTINCT ri) as recipient_ip_count

            RETURN t.amount as transaction_amount, 
                su.name as from_user, source_device_count, source_ip_count,
                ru.name as to_user, recipient_device_count, recipient_ip_count
        """
    }
    
    output_directory = os.path.join(os.path.dirname(__file__), 'ResponseTimes')
    os.makedirs(output_directory, exist_ok=True)
    
    results_data = []

    for percent, db_name in database_mappings.items():
        print(f"\n--- Pre-warming cache for database: {db_name} ---")
        try:
            prewarm_conn = Neo4jConnection(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'], db_name)
            prewarm_conn.run_query("MATCH (n) RETURN count(n)")
            prewarm_conn.close()
            print(f"--- Cache for {db_name} is now warm. ---")
        except Exception as e:
            print(f"  !!! WARNING: Could not pre-warm cache for {db_name}. Timings may be skewed. Error: {e}")

        for query_name, query in queries.items():
            print(f"\n--- Running Neo4j: {percent} Dataset - {query_name} ---")
            
            try:
                # Esecuzione a freddo 
                print("Running 'first' execution (on warm cache)...")
                db_conn_cold = Neo4jConnection(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'], db_name)
                first_execution_time = db_conn_cold.measure_query_time(query)
                db_conn_cold.close()
                print(f"First execution time: {first_execution_time:.2f} ms")

                # Esecuzioni a caldo
                print(f"Running {NUM_EXECUTIONS} hot executions (after {WARMUP_RUNS} warm-up runs)...")
                times = []
                db_conn_hot = Neo4jConnection(neo4j_config['uri'], neo4j_config['user'], neo4j_config['password'], db_name)
                for _ in range(WARMUP_RUNS):
                    db_conn_hot.run_query(query)
                for i in range(NUM_EXECUTIONS):
                    elapsed_time = db_conn_hot.measure_query_time(query)
                    times.append(elapsed_time)
                    print(f"  Execution {i+1}/{NUM_EXECUTIONS}: {elapsed_time:.2f} ms", end='\r')
                print("\n")
                db_conn_hot.close()
                
                # Calcoli statistici
                avg_time = np.mean(times)
                std_dev = np.std(times)
                conf_interval = stats.t.interval(0.95, len(times)-1, loc=avg_time, scale=stats.sem(times))
                print(f"Average time: {avg_time:.2f} ms")

                results_data.append({
                    'Query': query_name,
                    'Dataset': percent,
                    'First Execution Time (ms)': first_execution_time,
                    f'Average of {NUM_EXECUTIONS} Executions (ms)': avg_time,
                    'Standard Deviation (ms)': std_dev,
                    'Confidence Interval (Min, Max)': f"({conf_interval[0]:.2f}, {conf_interval[1]:.2f})"
                })
            except Exception as e:
                print(f"  !!! ERROR during execution for {query_name} on {db_name}: {e}")
                continue

    # Scrittura dei risultati aggregati
    output_file = os.path.join(output_directory, "neo4j_results.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = results_data[0].keys() if results_data else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_data)

    print(f"\nNeo4j benchmark completed. Results saved to {output_file}")

if __name__ == "__main__":
    process_datasets()