import os
import configparser
from BaseXClient import BaseXClient

def create_database(session, database_name):
    """Crea il database se non esiste, cancellandolo prima se presente."""
    try:
        session.execute(f"DROP DATABASE {database_name}")
        print(f"Dropped existing database '{database_name}' to ensure it's clean.")
    except IOError:
        pass
    session.execute(f"CREATE DATABASE {database_name}")
    print(f"Database '{database_name}' created.")

def insert_xml_files(session, database_name, xml_folder):
    """Carica tutti i file XML dalla cartella specificata nel database BaseX."""
    # Apri il DB per il contesto di inserimento
    session.execute(f"OPEN {database_name}")
    
    for filename in os.listdir(xml_folder):
        if filename.endswith('.xml'):
            file_path = os.path.join(xml_folder, filename)
            # Il "path" all'interno del DB sarà semplicemente il nome del file.
            # Questo è cruciale per la funzione doc() che useremo dopo.
            db_path_in_db = filename  

            with open(file_path, 'r', encoding='utf-8') as xml_file:
                xml_content = xml_file.read()
            
            # Aggiungi il contenuto al database con il nome del file come percorso
            session.add(db_path_in_db, xml_content)
            print(f"File {filename} caricato in '{database_name}' come risorsa '{db_path_in_db}'.")

def main():
    """Connette a BaseX e carica i file XML nei database."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    basex_config = config['BaseX']
    session = BaseXClient.Session(
        basex_config['host'],
        int(basex_config['port']),
        basex_config['user'],
        basex_config['password']
    )
    
    try:
        percentages = [25, 50, 75, 100]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for pct in percentages:
            database_name = f"dataset{pct}"
            xml_folder = os.path.join(base_dir, '..', 'Dataset', 'XML', f'Dataset_{pct}')
            
            print(f"\nProcessing database '{database_name}' from folder '{xml_folder}'...")
            create_database(session, database_name)
            insert_xml_files(session, database_name, xml_folder)
            print(f"Database '{database_name}' created and populated successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()