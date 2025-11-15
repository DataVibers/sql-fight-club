# tests/__init__.py
import os
import sys

# Project root: the folder that contains 'app' and 'tests'
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
