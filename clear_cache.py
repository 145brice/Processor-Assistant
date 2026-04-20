# Cache clearing helper for Streamlit
import os
import shutil
import streamlit as st

def clear_all_caches():
    """Clear all Streamlit-related caches."""
    cache_dirs = [
        ".streamlit",
        "__pycache__",
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"Cleared {cache_dir}")
            except Exception as e:
                print(f"Could not clear {cache_dir}: {e}")

    # Clear Python cache files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                try:
                    os.remove(os.path.join(root, file))
                except:
                    pass

    print("Cache clearing complete!")

if __name__ == "__main__":
    clear_all_caches()