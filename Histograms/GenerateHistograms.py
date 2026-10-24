import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np
import seaborn as sns
import os
import sys

# --- CONFIGURAZIONE ---
CONFIG = {
    'neo4j_csv_path': "Neo4j/ResponseTimes/neo4j_results.csv",
    'basex_csv_path': "BaseX/ResponseTimes/basex_results.csv",
    'dataset_sizes': ['25%', '50%', '75%', '100%'],
    'queries': ['Query 1', 'Query 2', 'Query 3', 'Query 4'],
    'num_executions': 30,
    'color_neo4j': '#8A2BE2',
    'color_basex': '#FF6347',
    'output_folder': 'Histograms'
}

# --- FUNZIONI HELPER ---
def check_input_files():
    for path in [CONFIG['neo4j_csv_path'], CONFIG['basex_csv_path']]:
        if not os.path.isfile(path):
            print(f"ERRORE FATALE: File '{path}' non trovato.", file=sys.stderr)
            sys.exit(1)
        if os.path.getsize(path) < 50:
            print(f"ERRORE FATALE: File '{path}' vuoto o incompleto.", file=sys.stderr)
            sys.exit(1)

def load_data():
    try:
        data_neo4j = pd.read_csv(CONFIG['neo4j_csv_path'])
        data_basex = pd.read_csv(CONFIG['basex_csv_path'])
        data_neo4j['Query'] = data_neo4j['Query'].str.strip()
        data_basex['Query'] = data_basex['Query'].str.strip()
        return data_neo4j, data_basex
    except Exception as e:
        print(f"ERRORE FATALE durante il caricamento dei CSV: {e}", file=sys.stderr)
        sys.exit(1)

def add_labels_to_bars(bars, ax):
    for bar in bars:
        yval = bar.get_height()
        label = f'{yval:.0f}' if yval >= 1 else f'{yval:.2f}'
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval, label, va='bottom', ha='center', fontsize=9, fontweight='bold')

def generate_graphs():
    check_input_files()
    data_neo4j, data_basex = load_data()
    sns.set_theme(style="whitegrid")
    os.makedirs(CONFIG['output_folder'], exist_ok=True)
    
    avg_col_name = f"Average of {CONFIG['num_executions']} Executions (ms)"
    
    for query_name in CONFIG['queries']:
        print(f"Generating graphs for {query_name}...")

        try:
            # --- Preparazione dati per la query corrente ---
            df_neo4j_q = data_neo4j[data_neo4j['Query'] == query_name]
            df_basex_q = data_basex[data_basex['Query'] == query_name]
            if df_neo4j_q.empty or df_basex_q.empty:
                raise ValueError(f"Dati non trovati per '{query_name}'.")

            first_exec_neo4j = {size: df_neo4j_q[df_neo4j_q['Dataset'] == size]['First Execution Time (ms)'].iloc[0] for size in CONFIG['dataset_sizes']}
            first_exec_basex = {size: df_basex_q[df_basex_q['Dataset'] == size]['First Execution Time (ms)'].iloc[0] for size in CONFIG['dataset_sizes']}
            
            avg_exec_neo4j = {size: df_neo4j_q[df_neo4j_q['Dataset'] == size][avg_col_name].iloc[0] for size in CONFIG['dataset_sizes']}
            avg_exec_basex = {size: df_basex_q[df_basex_q['Dataset'] == size][avg_col_name].iloc[0] for size in CONFIG['dataset_sizes']}
            
            def extract_ci(ci_str):
                matches = re.findall(r'[\d\.]+', ci_str)
                return float(matches[0]), float(matches[1])

            ci_neo4j = {size: extract_ci(df_neo4j_q[df_neo4j_q['Dataset'] == size]['Confidence Interval (Min, Max)'].iloc[0]) for size in CONFIG['dataset_sizes']}
            ci_basex = {size: extract_ci(df_basex_q[df_basex_q['Dataset'] == size]['Confidence Interval (Min, Max)'].iloc[0]) for size in CONFIG['dataset_sizes']}

            y_err_neo4j = np.array([[avg_exec_neo4j[s] - ci_neo4j[s][0], ci_neo4j[s][1] - avg_exec_neo4j[s]] for s in CONFIG['dataset_sizes']]).T
            y_err_basex = np.array([[avg_exec_basex[s] - ci_basex[s][0], ci_basex[s][1] - avg_exec_basex[s]] for s in CONFIG['dataset_sizes']]).T

        except (KeyError, IndexError, ValueError) as e:
            print(f"  ERRORE: Dati mancanti o malformati per '{query_name}'. Impossibile generare grafici. Dettagli: {e}", file=sys.stderr)
            continue

        index = np.arange(len(CONFIG['dataset_sizes']))
        bar_width = 0.35

        # --- Grafico 1: Prima Esecuzione ---
        fig_first, ax_first = plt.subplots(figsize=(14, 8))
        bars1_neo4j = ax_first.bar(index - bar_width/2, first_exec_neo4j.values(), bar_width, label='Neo4j', color=CONFIG['color_neo4j'], edgecolor='black')
        bars1_basex = ax_first.bar(index + bar_width/2, first_exec_basex.values(), bar_width, label='BaseX', color=CONFIG['color_basex'], edgecolor='black')
        ax_first.set_title(f'Tempo di Prima Esecuzione (a freddo) - {query_name}', fontsize=16, fontweight='bold')
        ax_first.set_ylabel('Tempo di Esecuzione (ms)', fontweight='bold')
        ax_first.set_xlabel('Dimensione del Dataset', fontweight='bold')
        ax_first.set_xticks(index, CONFIG['dataset_sizes'])
        ax_first.legend()
        add_labels_to_bars(bars1_neo4j, ax_first)
        add_labels_to_bars(bars1_basex, ax_first)
        ax_first.set_ylim(0, max(list(first_exec_neo4j.values()) + list(first_exec_basex.values())) * 1.2)
        fig_first.tight_layout()
        plt.savefig(os.path.join(CONFIG['output_folder'], f'First_Execution_{query_name.replace(" ", "_")}.png'), dpi=300)
        plt.close(fig_first)

        # --- Grafico 2: Tempo Medio ---
        fig_avg, ax_avg = plt.subplots(figsize=(14, 8))
        bars2_neo4j = ax_avg.bar(index - bar_width/2, avg_exec_neo4j.values(), bar_width, yerr=y_err_neo4j, capsize=5, label='Neo4j', color=CONFIG['color_neo4j'], edgecolor='black')
        bars2_basex = ax_avg.bar(index + bar_width/2, avg_exec_basex.values(), bar_width, yerr=y_err_basex, capsize=5, label='BaseX', color=CONFIG['color_basex'], edgecolor='black')
        ax_avg.set_title(f"Tempo Medio di {CONFIG['num_executions']} Esecuzioni (a caldo) - {query_name}", fontsize=16, fontweight='bold')
        ax_avg.set_ylabel('Tempo Medio di Esecuzione (ms)', fontweight='bold')
        ax_avg.set_xlabel('Dimensione del Dataset', fontweight='bold')
        ax_avg.set_xticks(index, CONFIG['dataset_sizes'])
        ax_avg.legend()
        add_labels_to_bars(bars2_neo4j, ax_avg)
        add_labels_to_bars(bars2_basex, ax_avg)
        ax_avg.set_ylim(0, max(list(avg_exec_neo4j.values()) + list(avg_exec_basex.values())) * 1.2)
        fig_avg.tight_layout()
        plt.savefig(os.path.join(CONFIG['output_folder'], f'Average_Execution_{query_name.replace(" ", "_")}.png'), dpi=300)
        plt.close(fig_avg)

def main():
    """Punto di ingresso principale dello script."""
    generate_graphs()
    print("\nProcesso di generazione degli istogrammi completato.")
    print(f"I grafici sono stati salvati nella cartella '{os.path.abspath(CONFIG['output_folder'])}'")

if __name__ == "__main__":
    main()