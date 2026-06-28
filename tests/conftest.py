"""
Add src/ to sys.path so tests can import project modules without installing them.
"""
import sys
import os

TESTS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(TESTS_DIR, '..'))
SRC_DIR = os.path.join(REPO_ROOT, 'src')

sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)
