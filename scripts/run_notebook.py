#!/usr/bin/env python3
"""
Executes the code cells of notebooks/scintillation_interactive_walkthrough.ipynb
to verify full end-to-end execution.
"""

import json
import sys
import traceback

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()

def run_notebook(notebook_path="notebooks/scintillation_interactive_walkthrough.ipynb"):
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    print(f"Executing cells from {notebook_path}...")
    
    # Global environment dictionary for cell execution
    global_env = {}

    for idx, cell in enumerate(nb.get("cells", []), start=1):
        cell_type = cell.get("cell_type")
        if cell_type == "code":
            source = "".join(cell.get("source", []))
            print(f"\n--- Executing Cell {idx} ---")
            try:
                exec(source, global_env)
                print(f"✓ Cell {idx} executed successfully.")
            except Exception as e:
                print(f"❌ Error in Cell {idx}: {e}")
                traceback.print_exc()
                sys.exit(1)

    print("\n🎉 Notebook executed completely without errors!")

if __name__ == "__main__":
    run_notebook()
