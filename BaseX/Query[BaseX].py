import time
import csv
import os
import configparser
import numpy as np
from scipy import stats
from BaseXClient import BaseXClient

# --- CONFIGURAZIONE ---
NUM_EXECUTIONS = 30
WARMUP_RUNS = 2

# --- FUNZIONI DI SUPPORTO ---
def get_db_connection(config):
    return BaseXClient.Session(
        config['host'], int(config['port']), config['user'], config['password']
    )

def measure_query_time(session, query):
    query_obj = session.query(query)
    start_time = time.perf_counter()
    results = list(query_obj.iter())
    end_time = time.perf_counter()
    query_obj.close()
    return (end_time - start_time) * 1000

# --- PROCESSO PRINCIPALE ---
def process_datasets():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)
    basex_config = config['BaseX']

    database_mappings = {
        "25%": "dataset25", "50%": "dataset50",
        "75%": "dataset75", "100%": "dataset100"
    }

    queries = {
        'Query 1': """
            let $user-id := "1"
            for $account in collection()/bank_accounts/bank_account[user_id=$user-id]
            return <result>
                <account_id>{$account/id/text()}</account_id>
                <account_number>{$account/account_number/text()}</account_number>
                <balance>{$account/balance/text()}</balance>
            </result>
        """,
        'Query 2': """
            for $group in collection()/device_accounts/device_account
            group by $id := $group/account_id/text()
            let $device-count := count($group)
            where $device-count >= 7
            return <result>
                <account_id>{$id}</account_id>
                <device_count>{$device-count}</device_count>
            </result>
        """,
        'Query 3': """
            let $max-amount := max(collection()/transactions/transaction/amount)
            let $top-transaction := (collection()/transactions/transaction[amount = $max-amount])[1]
            let $recipient-account-id := $top-transaction/recipient_account_id/text()
            let $recipient-user-id := collection()/bank_accounts/bank_account[id/text() = $recipient-account-id]/user_id/text()
            let $recipient-user := collection()/users/user[id/text() = $recipient-user-id]
            
            let $user-devices := collection()/devices/device[user_id/text() = $recipient-user-id]
            let $user-device-ids := $user-devices/id/text()
            
            let $used-ip-ids := collection()/device_ip/device_ip[device_id/text() = $user-device-ids]/ip_id/text()
            let $distinct-ip-count := count(distinct-values($used-ip-ids))
            
            return <result>
                <user_name>{$recipient-user/name/text()}</user_name>
                <device_count>{count($user-devices)}</device_count>
                <distinct_ip_count>{$distinct-ip-count}</distinct_ip_count>
            </result>           
        """,
        'Query 4': """
            let $max-amount := max(collection()/transactions/transaction/amount)
            let $top-transaction := (collection()/transactions/transaction[amount = $max-amount])[1]
            
            let $source-account := collection()/bank_accounts/bank_account[id/text() = $top-transaction/source_account_id/text()]
            let $recipient-account := collection()/bank_accounts/bank_account[id/text() = $top-transaction/recipient_account_id/text()]
            
            let $source-user := collection()/users/user[id/text() = $source-account/user_id/text()]
            let $recipient-user := collection()/users/user[id/text() = $recipient-account/user_id/text()]

            let $source-devices := collection()/devices/device[user_id/text() = $source-user/id/text()]
            let $source-ips := collection()/ip_addresses/ip_address[id/text() = collection()/device_ip/device_ip[device_id/text() = $source-devices/id/text()]/ip_id/text()]
            
            let $recipient-devices := collection()/devices/device[user_id/text() = $recipient-user/id/text()]
            let $recipient-ips := collection()/ip_addresses/ip_address[id/text() = collection()/device_ip/device_ip[device_id/text() = $recipient-devices/id/text()]/ip_id/text()]
            
            return <result>
                <transaction_amount>{$top-transaction/amount/text()}</transaction_amount>
                <from_user name="{$source-user/name/text()}" device_count="{count($source-devices)}" distinct_ip_count="{count(distinct-values($source-ips))}" />
                <to_user name="{$recipient-user/name/text()}" device_count="{count($recipient-devices)}" distinct_ip_count="{count(distinct-values($recipient-ips))}" />
            </result>
        """
    }

    output_directory = os.path.join(os.path.dirname(__file__), 'ResponseTimes')
    os.makedirs(output_directory, exist_ok=True)
    
    results_data = []

    for percent, db_name in database_mappings.items():
        for query_name, query_to_run in queries.items():
            print(f"\n--- Running BaseX: {percent} Dataset - {query_name} ---")
            
            try:
                # Esecuzione a freddo
                print("Running cold execution...")
                session_cold = get_db_connection(basex_config)
                session_cold.execute(f"OPEN {db_name}")
                first_execution_time = measure_query_time(session_cold, query_to_run)
                session_cold.close()
                print(f"Cold execution time: {first_execution_time:.2f} ms")

                # Esecuzioni a caldo
                print(f"Running {NUM_EXECUTIONS} hot executions (after {WARMUP_RUNS} warm-up runs)...")
                times = []
                session_hot = get_db_connection(basex_config)
                session_hot.execute(f"OPEN {db_name}")
                for _ in range(WARMUP_RUNS):
                    list(session_hot.query(query_to_run).iter())
                for i in range(NUM_EXECUTIONS):
                    elapsed_time = measure_query_time(session_hot, query_to_run)
                    times.append(elapsed_time)
                    print(f"  Execution {i+1}/{NUM_EXECUTIONS}: {elapsed_time:.2f} ms", end='\r')
                print("\n")
                session_hot.close()

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
    output_file = os.path.join(output_directory, "basex_results.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = results_data[0].keys() if results_data else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_data)

    print(f"\nBaseX benchmark completed. Results saved to {output_file}")

if __name__ == "__main__":
    process_datasets()