import nbformat

# Name of your notebook file
notebook_path = "notebooks/shark_Foraging_LongTerm.ipynb"

try:
    # 1. Read the notebook (ignores minor formatting errors)
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    # 2. Clean the metadata
    # This removes the '.venv' link that might be confusing GitHub
    nb['metadata']['kernelspec'] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }

    # 3. Write it back out perfectly formatted
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
        
    print("✅ Notebook fixed and cleaned! Try pushing to GitHub again.")

except Exception as e:
    print(f"❌ Error fixing notebook: {e}")