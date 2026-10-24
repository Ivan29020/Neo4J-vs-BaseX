import subprocess
import sys
import os

def run_python(script_path):
    print(f"\nEseguo: {script_path}")
    # Usiamo Popen e leggiamo l'output in tempo reale per non perdere nulla
    process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    
    # Leggi stdout e stderr
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    stderr = process.communicate()[1]
    
    if process.returncode != 0:
        print(f"--- ERRORE nell'esecuzione di {script_path} ---")
        if stderr:
            print(stderr.strip())
        sys.exit(process.returncode)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Genera i dataset
    run_python(os.path.join(base_dir, "Dataset", "Dataset.py"))

    # 2. Carica i dati in BaseX
    run_python(os.path.join(base_dir, "BaseX", "Dataset[BaseX].py"))
    
    # 3. IMPOSTA GLI INDICI SU NEO4J (NUOVO PASSAGGIO)
    run_python(os.path.join(base_dir, "Neo4j", "Utility", "SetupIndexes.py"))

    # 4. Carica i dati in Neo4j (ora con gli indici già presenti)
    run_python(os.path.join(base_dir, "Neo4j", "Dataset[Neo4j].py"))

    # 5. Esegui le query e misura i tempi su BaseX
    run_python(os.path.join(base_dir, "BaseX", "Query[BaseX].py"))

    # 6. Esegui le query e misura i tempi su Neo4j
    run_python(os.path.join(base_dir, "Neo4j", "Query[Neo4j].py"))

    # 7. Genera gli istogrammi
    run_python(os.path.join(base_dir, "Histograms", "GenerateHistograms.py"))

    print("\nTutto il processo è stato completato con successo!")

if __name__ == "__main__":
    main()