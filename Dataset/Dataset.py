import random
import csv
import os
from faker import Faker
import xml.etree.ElementTree as ET

fake = Faker()

PERC_LIST = [0.25, 0.50, 0.75, 1.00]
FOLDER_LIST = ['Dataset_25', 'Dataset_50', 'Dataset_75', 'Dataset_100']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NUM_USERS = 40000
NUM_BANK_ACCOUNTS = 75000
NUM_DEVICES = 90000
NUM_IP_ADDRESSES = NUM_DEVICES
NUM_TRANSACTIONS = 130000

device_types = ['smartphone', 'tablet', 'laptop', 'desktop', 'smartwatch']

def generate_users(start_id, end_id):
    return [{
        'id': user_id,
        'name': fake.first_name(),
        'surname': fake.last_name(),
        'birthdate': fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d'),
        'email': fake.email(),
        'phone_number': fake.phone_number()
    } for user_id in range(start_id, end_id + 1)]

def generate_bank_accounts(start_id, end_id, user_id_range):
    return [{
        'id': account_id,
        'user_id': random.randint(user_id_range[0], user_id_range[1]),
        'account_number': fake.iban(),
        'balance': round(random.uniform(500.0, 50000.0), 2)
    } for account_id in range(start_id, end_id + 1)]

def generate_devices(start_id, end_id, user_id_range):
    return [{
        'id': device_id,
        'user_id': random.randint(user_id_range[0], user_id_range[1]),
        'device_type': random.choice(device_types),
        'device_name': fake.word() + "-" + str(device_id)
    } for device_id in range(start_id, end_id + 1)]

def generate_ip_addresses(start_id, end_id):
    return [{
        'id': ip_id,
        'ip_address': fake.ipv4()
    } for ip_id in range(start_id, end_id + 1)]

def generate_device_ip(start_id, end_id):
    return [{
        'device_id': device_id,
        'ip_id': device_id
    } for device_id in range(start_id, end_id + 1)]

def generate_device_account(num, device_id_range, account_id_range):
    return [{
        'device_id': random.randint(device_id_range[0], device_id_range[1]),
        'account_id': random.randint(account_id_range[0], account_id_range[1])
    } for _ in range(num)]

def generate_transactions(start_id, end_id, account_id_range):
    return [{
        'id': transaction_id,
        'date_time': fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
        'description': fake.sentence(nb_words=5),
        'amount': round(random.uniform(100.0, 10000.0), 2),
        'source_account_id': random.randint(account_id_range[0], account_id_range[1]),
        'recipient_account_id': random.randint(account_id_range[0], account_id_range[1])
    } for transaction_id in range(start_id, end_id + 1)]

def write_csv(folder, filename, data, fieldnames):
    with open(os.path.join(folder, filename), 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def csv_to_xml(csv_path, xml_path, root_tag, row_tag):
    root = ET.Element(root_tag)
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item = ET.SubElement(root, row_tag)
            for key, val in row.items():
                child = ET.SubElement(item, key)
                child.text = val
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

# Inizializza i dati vuoti
users, bank_accounts, devices, ip_addresses, device_ip, device_account, transactions = [], [], [], [], [], [], []

user_id = 1
account_id = 1
device_id = 1
ip_id = 1
transaction_id = 1

# Prepara cartelle principali
for main_folder in ['CSV', 'XML']:
    main_folder_path = os.path.join(BASE_DIR, main_folder)
    if not os.path.exists(main_folder_path):
        os.makedirs(main_folder_path)
    for sub_folder in FOLDER_LIST:
        path = os.path.join(main_folder_path, sub_folder)
        if not os.path.exists(path):
            os.makedirs(path)

for perc, folder in zip(PERC_LIST, FOLDER_LIST):
    csv_folder = os.path.join(BASE_DIR, 'CSV', folder)
    xml_folder = os.path.join(BASE_DIR, 'XML', folder)

    prev_user_id = user_id
    prev_account_id = account_id
    prev_device_id = device_id
    prev_ip_id = ip_id
    prev_transaction_id = transaction_id

    n_users = int(NUM_USERS * perc)
    n_accounts = int(NUM_BANK_ACCOUNTS * perc)
    n_devices = int(NUM_DEVICES * perc)
    n_ips = n_devices
    n_transactions = int(NUM_TRANSACTIONS * perc)
    n_device_account = int(n_accounts * 2)

    # USERS
    if len(users) < n_users:
        users += generate_users(user_id, n_users)
        user_id = n_users + 1
    write_csv(csv_folder, 'users.csv', users, ['id', 'name', 'surname', 'birthdate', 'email', 'phone_number'])

    # BANK ACCOUNTS
    if len(bank_accounts) < n_accounts:
        bank_accounts += generate_bank_accounts(account_id, n_accounts, (1, n_users))
        account_id = n_accounts + 1
    write_csv(csv_folder, 'bank_accounts.csv', bank_accounts, ['id', 'user_id', 'account_number', 'balance'])

    # DEVICES
    if len(devices) < n_devices:
        devices += generate_devices(device_id, n_devices, (1, n_users))
        device_id = n_devices + 1
    write_csv(csv_folder, 'devices.csv', devices, ['id', 'user_id', 'device_type', 'device_name'])

    # IP ADDRESSES
    if len(ip_addresses) < n_ips:
        ip_addresses += generate_ip_addresses(ip_id, n_ips)
        ip_id = n_ips + 1
    write_csv(csv_folder, 'ip_addresses.csv', ip_addresses, ['id', 'ip_address'])

    # DEVICE-IP
    if len(device_ip) < n_devices:
        device_ip += generate_device_ip(prev_device_id, n_devices)
    write_csv(csv_folder, 'device_ip.csv', device_ip, ['device_id', 'ip_id'])

    # DEVICE-ACCOUNT
    if len(device_account) < n_device_account:
        device_account += generate_device_account(n_device_account - len(device_account), (1, n_devices), (1, n_accounts))
    write_csv(csv_folder, 'device_account.csv', device_account, ['device_id', 'account_id'])

    # TRANSACTIONS
    if len(transactions) < n_transactions:
        transactions += generate_transactions(transaction_id, n_transactions, (1, n_accounts))
        transaction_id = n_transactions + 1
    write_csv(csv_folder, 'transactions.csv', transactions, ['id', 'date_time', 'description', 'amount', 'source_account_id', 'recipient_account_id'])

    # Conversione CSV -> XML
    csv_to_xml(os.path.join(csv_folder, 'users.csv'), os.path.join(xml_folder, 'users.xml'), 'users', 'user')
    csv_to_xml(os.path.join(csv_folder, 'bank_accounts.csv'), os.path.join(xml_folder, 'bank_accounts.xml'), 'bank_accounts', 'bank_account')
    csv_to_xml(os.path.join(csv_folder, 'devices.csv'), os.path.join(xml_folder, 'devices.xml'), 'devices', 'device')
    csv_to_xml(os.path.join(csv_folder, 'ip_addresses.csv'), os.path.join(xml_folder, 'ip_addresses.xml'), 'ip_addresses', 'ip_address')
    csv_to_xml(os.path.join(csv_folder, 'device_ip.csv'), os.path.join(xml_folder, 'device_ip.xml'), 'device_ips', 'device_ip')
    csv_to_xml(os.path.join(csv_folder, 'device_account.csv'), os.path.join(xml_folder, 'device_account.xml'), 'device_accounts', 'device_account')
    csv_to_xml(os.path.join(csv_folder, 'transactions.csv'), os.path.join(xml_folder, 'transactions.xml'), 'transactions', 'transaction')

    print(f"Dataset {int(perc*100)}% creato in CSV e XML nelle rispettive cartelle.")

print("Tutti i dataset incrementali sono stati generati con successo in CSV e XML.")