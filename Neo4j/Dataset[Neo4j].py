import pandas as pd
from py2neo import Graph, Node, Relationship
from tqdm import tqdm
import os
import configparser

def create_graph(graph, users, bank_accounts, devices, ip_addresses, device_ip, device_account, transactions, dataset_name):
    print(f"Starting to load data into {dataset_name}...")

    # Crea nodi per gli utenti
    user_nodes = {}
    for _, row in tqdm(users.iterrows(), total=len(users), desc=f"Loading Users into {dataset_name}"):
        user_node = Node("User", id=row['id'], name=row['name'], surname=row['surname'], birthdate=row['birthdate'], email=row['email'], phone_number=row['phone_number'])
        graph.create(user_node)
        user_nodes[row['id']] = user_node

    # Crea nodi per i conti bancari e collega i conti ai rispettivi utenti
    bank_account_nodes = {}
    for _, row in tqdm(bank_accounts.iterrows(), total=len(bank_accounts), desc=f"Loading Bank Accounts into {dataset_name}"):
        bank_account_node = Node("BankAccount", id=row['id'], user_id=row['user_id'], account_number=row['account_number'], balance=row['balance'])
        graph.create(bank_account_node)
        bank_account_nodes[row['id']] = bank_account_node
        
        # Relazione OWNS tra User e BankAccount
        user_id = row['user_id']
        if user_id in user_nodes:
            owns_relationship = Relationship(user_nodes[user_id], "OWNS", bank_account_node)
            graph.create(owns_relationship)

    # Crea nodi per i dispositivi e collega ai rispettivi utenti
    device_nodes = {}
    for _, row in tqdm(devices.iterrows(), total=len(devices), desc=f"Loading Devices into {dataset_name}"):
        device_node = Node("Device", id=row['id'], user_id=row['user_id'], device_type=row['device_type'], device_name=row['device_name'])
        graph.create(device_node)
        device_nodes[row['id']] = device_node

        # Relazione OWNS_DEVICE tra User e Device
        user_id = row['user_id']
        if user_id in user_nodes:
            owns_device_relationship = Relationship(user_nodes[user_id], "OWNS_DEVICE", device_node)
            graph.create(owns_device_relationship)

    # Crea nodi per gli indirizzi IP
    ip_address_nodes = {}
    for _, row in tqdm(ip_addresses.iterrows(), total=len(ip_addresses), desc=f"Loading IP Addresses into {dataset_name}"):
        ip_address_node = Node("IPAddress", id=row['id'], ip_address=row['ip_address'])
        graph.create(ip_address_node)
        ip_address_nodes[row['id']] = ip_address_node

    # Relazione DEVICE_HAS_IP (1:1)
    for _, row in tqdm(device_ip.iterrows(), total=len(device_ip), desc=f"Creating Device to IP relationships in {dataset_name}"):
        device_id = row['device_id']
        ip_id = row['ip_id']
        if device_id in device_nodes and ip_id in ip_address_nodes:
            has_ip_relationship = Relationship(device_nodes[device_id], "HAS_IP", ip_address_nodes[ip_id])
            graph.create(has_ip_relationship)

    # Relazione DEVICE_ACCOUNT (N:M)
    for _, row in tqdm(device_account.iterrows(), total=len(device_account), desc=f"Creating Device to Account relationships in {dataset_name}"):
        device_id = row['device_id']
        account_id = row['account_id']
        if device_id in device_nodes and account_id in bank_account_nodes:
            uses_account_relationship = Relationship(device_nodes[device_id], "USES_ACCOUNT", bank_account_nodes[account_id])
            graph.create(uses_account_relationship)

    # Crea nodi per le transazioni e relazioni con altri nodi
    for _, row in tqdm(transactions.iterrows(), total=len(transactions), desc=f"Loading Transactions and Relationships into {dataset_name}"):
        transaction_node = Node("Transaction", id=row['id'], date_time=row['date_time'], description=row['description'], amount=row['amount'])
        graph.create(transaction_node)

        # Relazione tra transazione e conto sorgente
        if row['source_account_id'] in bank_account_nodes:
            rel_source_account = Relationship(transaction_node, "FROM_ACCOUNT", bank_account_nodes[row['source_account_id']])
            graph.create(rel_source_account)

        # Relazione tra transazione e conto destinatario
        if row['recipient_account_id'] in bank_account_nodes:
            rel_recipient_account = Relationship(transaction_node, "TO_ACCOUNT", bank_account_nodes[row['recipient_account_id']])
            graph.create(rel_recipient_account)

    print(f"Finished loading data into {dataset_name}.")

def load_csvs_from_folder(folder):
    users = pd.read_csv(os.path.join(folder, 'users.csv'), encoding='utf-8')
    bank_accounts = pd.read_csv(os.path.join(folder, 'bank_accounts.csv'), encoding='utf-8')
    devices = pd.read_csv(os.path.join(folder, 'devices.csv'), encoding='utf-8')
    ip_addresses = pd.read_csv(os.path.join(folder, 'ip_addresses.csv'), encoding='utf-8')
    device_ip = pd.read_csv(os.path.join(folder, 'device_ip.csv'), encoding='utf-8')
    device_account = pd.read_csv(os.path.join(folder, 'device_account.csv'), encoding='utf-8')
    transactions = pd.read_csv(os.path.join(folder, 'transactions.csv'), encoding='utf-8')
    return users, bank_accounts, devices, ip_addresses, device_ip, device_account, transactions

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)
    
    neo4j_config = config['Neo4j']
    uri = neo4j_config['uri']
    user = neo4j_config['user']
    password = neo4j_config['password']

    base_dir = os.path.dirname(os.path.abspath(__file__))
    datasets = [
        ("dataset25", os.path.join(base_dir, '..', 'Dataset', 'CSV', 'Dataset_25')),
        ("dataset50", os.path.join(base_dir, '..', 'Dataset', 'CSV', 'Dataset_50')),
        ("dataset75", os.path.join(base_dir, '..', 'Dataset', 'CSV', 'Dataset_75')),
        ("dataset100", os.path.join(base_dir, '..', 'Dataset', 'CSV', 'Dataset_100')),
    ]

    for db_name, folder in datasets:
        print(f"\nLoading data for {db_name} from {folder}")
        users, bank_accounts, devices, ip_addresses, device_ip, device_account, transactions = load_csvs_from_folder(folder)
        graph = Graph(uri, user=user, password=password, name=db_name)
        create_graph(graph, users, bank_accounts, devices, ip_addresses, device_ip, device_account, transactions, db_name)

    print("\nData successfully loaded into all Neo4j databases.")