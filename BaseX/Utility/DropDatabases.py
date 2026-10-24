import sys
import os
import configparser
from BaseXClient import BaseXClient

# Aggiungi la root del progetto al path per importare config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def drop_all_datasets(session):
    """Cancella tutti i database che iniziano con 'dataset'."""
    try:
        # Il comando LIST restituisce i nomi dei database
        db_list_str = session.execute("LIST")
        databases = db_list_str.split()
        
        dropped_count = 0
        for db in databases:
            if db.startswith("dataset"):
                try:
                    session.execute(f"DROP DATABASE {db}")
                    print(f"Database '{db}' has been dropped.")
                    dropped_count += 1
                except IOError as e:
                    print(f"Error dropping database '{db}': {e}")
        
        if dropped_count == 0:
            print("No 'dataset' databases found to drop.")

    except IOError as e:
        print(f"Error listing databases: {e}")

def main():
    """Connette a BaseX e cancella i database dei dataset."""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'))

    host = config['BaseX']['host']
    port = int(config['BaseX']['port'])
    user = config['BaseX']['user']
    password = config['BaseX']['password']

    try:
        session = BaseXClient.Session(host, port, user, password)
        print("Connected to BaseX.")
        drop_all_datasets(session)
        session.close()
        print("Process completed.")
    except Exception as e:
        print(f"Failed to connect or execute operation: {e}")

if __name__ == "__main__":
    main()