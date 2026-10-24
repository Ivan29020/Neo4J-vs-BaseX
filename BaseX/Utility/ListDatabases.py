import sys
import os
import configparser
from BaseXClient import BaseXClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def list_databases(session):
    """Elenca tutti i database presenti in BaseX."""
    try:
        db_list_str = session.execute("LIST")
        databases = db_list_str.split()
        if databases:
            print("Available databases:")
            for db in databases:
                print(f"- {db}")
        else:
            print("No databases found.")
    except IOError as e:
        print(f"Error listing databases: {e}")

def main():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'))

    host = config['BaseX']['host']
    port = int(config['BaseX']['port'])
    user = config['BaseX']['user']
    password = config['BaseX']['password']

    try:
        session = BaseXClient.Session(host, port, user, password)
        list_databases(session)
        session.close()
    except Exception as e:
        print(f"Failed to connect or execute operation: {e}")

if __name__ == "__main__":
    main()