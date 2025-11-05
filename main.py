
"""
Main Entry Point for Warehouse Automation System
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from simulations.run_integrated import main

if __name__ == "__main__":
    main()

