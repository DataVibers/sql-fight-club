# run_app.py
import os
import sys

# Ensure project root is on sys.path (this file IS in the root)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.ui.streamlit_app import main  # import the Streamlit app's main()

if __name__ == "__main__":
    main()
