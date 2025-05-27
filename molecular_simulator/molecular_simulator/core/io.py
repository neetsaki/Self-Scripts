# molecular_simulator/molecular_simulator/core/io.py
from ase import Atoms
from ase.io import read, write

def load_structure(filepath: str) -> Atoms:
    """Loads a structure from a file using ASE."""
    return read(filepath)

def save_structure(atoms: Atoms, filepath: str):
    """Saves a structure to a file using ASE."""
    write(filepath, atoms)
