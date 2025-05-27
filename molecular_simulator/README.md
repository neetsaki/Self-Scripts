# Molecular Simulator (Work In Progress)

A Python-based graphical tool for setting up and managing molecular and crystal structures for computational chemistry and materials science simulations.

## Core Features Implemented:

*   **3D Molecular Visualization**: Interactive viewing of atomic structures using PyVista.
*   **File I/O**:
    *   Supports opening various common formats (XYZ, CIF, PDB, POSCAR, etc.) via ASE.
    *   Save and Save As functionality for structures.
*   **Structure Editing & Building**:
    *   Select atoms by clicking, by type, or by spatial region.
    *   Change atom types of selected atoms.
    *   Add new atoms at specified coordinates.
    *   Define and edit unit cells for crystalline structures.
    *   Create supercells from existing unit cells.
    *   Cleave crystal surfaces using Miller indices.
    *   Add vacuum layers to surface slabs.
*   **Coordinate Constraints**:
    *   Apply Cartesian constraints (fix X, Y, Z, or combinations) to selected atoms.
    *   Release constraints from selected atoms.
*   **Input File Generation (Conceptual & Basic VASP)**:
    *   A workflow manager UI (dock widget) to define a sequence of calculations.
    *   Currently supports adding VASP SCF and VASP Geometry Optimization modules.
    *   Dialogs for setting parameters for these calculation modules.
    *   Generates basic VASP input files (`POSCAR`, `INCAR`, `KPOINTS`, `POTCAR_README.txt`) in structured output directories.
*   **UI**:
    *   Graphical user interface built with PyQt6.
    *   Styled with QSS for a modern look and feel.
    *   Menu-driven operations and dialogs for parameter input.

## Installation

1.  **Prerequisites**:
    *   Python 3.8+
    *   `pip` (Python package installer)

2.  **Setup Environment (Recommended)**:
    Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    Navigate to the project root directory (where `requirements.txt` is located) and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install PyQt6, PyVista, ASE, NumPy, and other necessary packages.

## Basic Usage

1.  **Launch the Application**:
    Navigate to the project root directory and run:
    ```bash
    python -m molecular_simulator.main
    ```
    Alternatively, you can pass a path to a molecular file as a command-line argument to load it on startup:
    ```bash
    python -m molecular_simulator.main path/to/your/molecule.xyz
    ```

2.  **Overview**:
    *   **File Menu**: Open, save, or export molecular structures.
    *   **Select Menu**: Tools for selecting atoms and applying/releasing coordinate constraints.
    *   **Build Menu**: Tools for adding atoms, defining unit cells, creating supercells, cleaving surfaces, and adding vacuum.
    *   **Generate Menu**: Access the Workflow Editor to set up calculation steps (e.g., VASP SCF, VASP Geometry Optimization) and generate input files.
    *   **3D Viewer**: Interact with the molecule using mouse controls (left-click drag to rotate, middle-click drag or Shift+Left-click drag to pan, scroll wheel or Right-click drag to zoom).
    *   **Workflow Editor (Dock)**: Add calculation modules, edit their parameters (double-click), and generate input files for the entire workflow.

## Testing

Thorough manual testing is required for all implemented features. This includes:
*   Loading and saving various file formats.
*   All structure building and modification tools.
*   Selection mechanisms and constraint applications.
*   Input file generation for VASP SCF and Geometry Optimization modules.
*   UI interactions, dialogs, and error handling.

(See internal testing plan for more details.)

## Known Issues / Future Work (Examples)

*   **Undo/Redo**: Not currently implemented.
*   **Advanced Workflow Editor**: The current workflow editor is list-based. A full node-based graphical editor is a future goal.
*   **Expanded DFT/MD Code Support**: Add generators for more codes (Quantum Espresso, CP2K, OpenMX, SIESTA, LAMMPS etc.) and more calculation types (MD, NEB, Phonons, etc.).
*   **POTCAR Generation**: Actual POTCAR file generation is not supported due_to licensing; only a `POTCAR_README.txt` is created.
*   **Constraint Visualization**: No specific visual markers for constrained atoms yet.
*   **More Robust Error Handling and Input Validation**.
*   **Comprehensive Unit and Integration Tests**.
*   **Detailed User and Developer Documentation**.

## Contribution

(Placeholder for contribution guidelines if this were an open-source project)
```
