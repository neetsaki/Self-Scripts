# molecular_simulator/molecular_simulator/gui/main_window.py
import sys
import os 
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, 
    QInputDialog, QDockWidget # Ensure QDockWidget is imported
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt # Ensure Qt is imported (for Qt.DockWidgetArea)

from .widgets.molecular_viewer import MolecularViewerWidget
from ..core.io import load_structure, save_structure 
from ase import Atoms 
# import numpy as np # Already imported above

from .dialogs.add_atom_dialog import AddAtomDialog 
from .dialogs.unit_cell_dialog import UnitCellDialog
from .dialogs.select_by_region_dialog import SelectByRegionDialog
from .dialogs.scf_params_dialog import ScfParamsDialog
from .dialogs.supercell_dialog import SupercellDialog
from .dialogs.cleave_surface_dialog import CleaveSurfaceDialog
from .dialogs.add_vacuum_dialog import AddVacuumDialog
from .workflow_editor_widget import WorkflowEditorWidget 
from ..core.workflow import Workflow, CalculationModule 
# The vasp_generator import was removed in the prompt, assuming it's not directly used in MainWindow
# but rather by the WorkflowEditorWidget. If it's needed for _test_generate_vasp_scf (if it were kept),
# it would need to be re-added. However, the prompt implies _test_generate_vasp_scf is removed.
# For now, I will keep the generator imports as they were in the previous version from Turn 79,
# as the prompt doesn't show the full file and they might be used in methods not fully shown.
from ..core.generators.vasp_generator import generate_vasp_scf_input, generate_vasp_geo_opt_input


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Molecular Simulator")
        self.setGeometry(100, 100, 1024, 768) # Default size

        self.viewer_widget = MolecularViewerWidget(self)
        self.setCentralWidget(self.viewer_widget)

        self.current_file_path = None # To store the path of the currently open/saved file

        # Initialize Workflow Editor Dock and Widget BEFORE _create_menus
        self.workflow_editor_dock = QDockWidget("Workflow Editor", self)
        self.workflow_editor_widget = WorkflowEditorWidget(self.workflow_editor_dock)
        self.workflow_editor_dock.setWidget(self.workflow_editor_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.workflow_editor_dock)
        # self.workflow_editor_dock.setVisible(False) # Optionally hide initially

        # Now call _create_menus as it uses workflow_editor_dock
        self._create_menus()
        
        # Initialize current atoms in workflow editor if needed
        if self.viewer_widget.current_atoms:
             self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
        else:
             self.workflow_editor_widget.set_current_atoms(None)


    def _create_menus(self): 
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open...", self); open_action.triggered.connect(self._open_file_dialog); file_menu.addAction(open_action)
        save_action = QAction("&Save", self); save_action.setShortcut("Ctrl+S"); save_action.triggered.connect(self._save_file); file_menu.addAction(save_action)
        save_as_action = QAction("Save &As...", self); save_as_action.setShortcut("Ctrl+Shift+S"); save_as_action.triggered.connect(self._save_file_as); file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self); exit_action.triggered.connect(self.close); file_menu.addAction(exit_action)

        # Select Menu
        select_menu = menu_bar.addMenu("&Select")
        select_by_type_action = QAction("Select by Atom &Type...", self); select_by_type_action.triggered.connect(self._show_select_by_type_dialog); select_menu.addAction(select_by_type_action)
        select_by_region_action = QAction("Select by Spatial &Region (Sphere)...", self); select_by_region_action.triggered.connect(self._show_select_by_region_dialog); select_menu.addAction(select_by_region_action)
        select_menu.addSeparator()
        clear_selection_action = QAction("&Clear Selection", self); clear_selection_action.setShortcut("Esc"); clear_selection_action.triggered.connect(self._clear_current_selection); select_menu.addAction(clear_selection_action)
        select_menu.addSeparator()
        fix_xyz_action = QAction("Fix Selected Atoms (&XYZ)", self); fix_xyz_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(True, True, True)); select_menu.addAction(fix_xyz_action)
        fix_x_action = QAction("Fix Selected Atoms (&X only)", self); fix_x_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(True, False, False)); select_menu.addAction(fix_x_action)
        fix_y_action = QAction("Fix Selected Atoms (&Y only)", self); fix_y_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(False, True, False)); select_menu.addAction(fix_y_action)
        fix_z_action = QAction("Fix Selected Atoms (&Z only)", self); fix_z_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(False, False, True)); select_menu.addAction(fix_z_action)
        fix_xy_action = QAction("Fix Selected Atoms (X&Y)", self); fix_xy_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(True, True, False)); select_menu.addAction(fix_xy_action)
        fix_xz_action = QAction("Fix Selected Atoms (X&Z)", self); fix_xz_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(True, False, True)); select_menu.addAction(fix_xz_action)
        fix_yz_action = QAction("Fix Selected Atoms (Y&Z)", self); fix_yz_action.triggered.connect(lambda: self._apply_constraints_to_selected_atoms(False, True, True)); select_menu.addAction(fix_yz_action)
        select_menu.addSeparator()
        release_constraints_action = QAction("&Release Constraints on Selected", self); release_constraints_action.triggered.connect(self._release_constraints_on_selected_atoms); select_menu.addAction(release_constraints_action)

        # Build Menu
        build_menu = menu_bar.addMenu("&Build")
        add_atom_action = QAction("&Add Atom...", self); add_atom_action.triggered.connect(self._show_add_atom_dialog); build_menu.addAction(add_atom_action)
        define_cell_action = QAction("&Define/Edit Unit Cell...", self); define_cell_action.triggered.connect(self._show_define_cell_dialog); build_menu.addAction(define_cell_action)
        create_supercell_action = QAction("Create &Supercell...", self); create_supercell_action.triggered.connect(self._show_create_supercell_dialog); build_menu.addAction(create_supercell_action)
        build_menu.addSeparator()
        cleave_surface_action = QAction("Cleave C&rystal Surface...", self); cleave_surface_action.triggered.connect(self._show_cleave_surface_dialog); build_menu.addAction(cleave_surface_action)
        add_vacuum_action = QAction("Add &Vacuum Layer...", self); add_vacuum_action.triggered.connect(self._show_add_vacuum_dialog); build_menu.addAction(add_vacuum_action)
        
        # Generate Menu
        generate_menu = menu_bar.addMenu("&Generate")
        toggle_workflow_editor_action = self.workflow_editor_dock.toggleViewAction() 
        toggle_workflow_editor_action.setText("Show/Hide Workflow Editor")
        generate_menu.addAction(toggle_workflow_editor_action)

    def _get_save_file_filter(self):
        supported_formats = [
            "XYZ files (*.xyz)", "CIF files (*.cif)", "ASE trajectory files (*.traj)",
            "VASP POSCAR/CONTCAR (*.vasp *.poscar *.contcar)", 
            "Quantum Espresso Input (*.pwi *.in)", "LAMMPS data files (*.data *.lammps)",
            "PDB files (*.pdb)", "All files (*.*)"
        ]
        return ";;".join(supported_formats)

    def _save_file(self):
        if not self.viewer_widget.current_atoms:
            self.statusBar().showMessage("No molecule to save.", 3000); return
        if self.current_file_path:
            try:
                save_structure(self.viewer_widget.current_atoms, self.current_file_path)
                self.statusBar().showMessage(f"File saved to {self.current_file_path}", 5000)
                self.setWindowTitle(f"Molecular Simulator - {os.path.basename(self.current_file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save file to {self.current_file_path}:\n{e}")
        else: self._save_file_as()

    def _save_file_as(self):
        if not self.viewer_widget.current_atoms:
            self.statusBar().showMessage("No molecule to save.", 3000); return
        
        start_dir = os.path.dirname(self.current_file_path) if self.current_file_path else ""
        start_filename = os.path.basename(self.current_file_path) if self.current_file_path else "untitled.xyz"
        if self.viewer_widget.current_atoms and len(self.viewer_widget.current_atoms) > 0 and not self.current_file_path:
            try: start_filename = f"{self.viewer_widget.current_atoms.get_chemical_formula()}.xyz"
            except: pass 

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As...", os.path.join(start_dir, start_filename), self._get_save_file_filter()
        )
        if file_path:
            try:
                save_structure(self.viewer_widget.current_atoms, file_path)
                self.current_file_path = file_path
                self.statusBar().showMessage(f"File saved to {self.current_file_path}", 5000)
                self.setWindowTitle(f"Molecular Simulator - {os.path.basename(self.current_file_path)}")
            except Exception as e: QMessageBox.critical(self, "Save Error", f"Could not save file to {file_path}:\n{e}")
        else: self.statusBar().showMessage("Save As cancelled.", 2000)

    def _open_file_dialog(self):
        supported_formats = [
            "XYZ files (*.xyz)", "CIF files (*.cif)", "PDB files (*.pdb *.ent)",
            "VASP POSCAR/CONTCAR (*.vasp *.poscar *.contcar)",
            "Quantum Espresso Input (*.in *.pwi)", "All files (*.*)"
        ]
        filter_string = ";;".join(supported_formats)
        start_dir = os.path.dirname(self.current_file_path) if self.current_file_path else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Molecular File", start_dir, filter_string)
        if file_path: self.load_molecule_from_file(file_path)

    def load_molecule_from_file(self, filepath: str):
        try:
            atoms = load_structure(filepath)
            self.viewer_widget.show_molecule(atoms)
            self.current_file_path = filepath 
            self.statusBar().showMessage(f"Loaded {filepath}", 5000)
            self.setWindowTitle(f"Molecular Simulator - {os.path.basename(filepath)}")
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(atoms)
        except FileNotFoundError:
            self.statusBar().showMessage(f"Error: File not found: {filepath}", 5000)
            self.viewer_widget.clear_view(); self.current_file_path = None
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(None)
        except Exception as e:
            self.statusBar().showMessage(f"Error loading {filepath}: {e}", 5000)
            self.viewer_widget.clear_view(); self.current_file_path = None
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(None)
        if not self.current_file_path: self.setWindowTitle("Molecular Simulator")

    def _show_add_atom_dialog(self):
        atom_data = AddAtomDialog.show_dialog(self)
        if atom_data:
            symbol = atom_data["symbol"]; position = (atom_data["x"], atom_data["y"], atom_data["z"])
            self.viewer_widget.add_atom(symbol, position)
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
            self.current_file_path = None; self.setWindowTitle("Molecular Simulator - Modified")
            self.statusBar().showMessage(f"Added atom {symbol} at {position}", 5000)
        else: self.statusBar().showMessage("Add atom cancelled.", 2000)

    def _show_define_cell_dialog(self):
        current_cell_params = None
        if self.viewer_widget.current_atoms and np.any(self.viewer_widget.current_atoms.cell):
            try: current_cell_params = list(self.viewer_widget.current_atoms.cell.cellpar())
            except Exception as e: print(f"Could not get current cell parameters: {e}")
        dialog_data = UnitCellDialog.show_dialog(self, current_cell_params)
        if dialog_data:
            cellpar = dialog_data["cellpar"]; pbc = dialog_data["pbc"]
            self.viewer_widget.set_unit_cell(cellpar, pbc)
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
            self.current_file_path = None; self.setWindowTitle("Molecular Simulator - Modified")
            self.statusBar().showMessage(f"Unit cell defined/updated. PBC: {pbc}", 5000)
        else: self.statusBar().showMessage("Define unit cell cancelled.", 2000)

    def _show_create_supercell_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Base Structure", "Please load or build a unit cell structure first."); return
        if not np.any(self.viewer_widget.current_atoms.cell): QMessageBox.warning(self, "Unit Cell Required", "A unit cell must be defined before creating a supercell."); return
        transform_matrix = SupercellDialog.show_dialog(self)
        if transform_matrix is not None:
            self.viewer_widget.create_supercell(transform_matrix)
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Supercell)")
            self.statusBar().showMessage("Supercell created.", 5000)
        else: self.statusBar().showMessage("Create supercell cancelled.", 2000)

    def _show_cleave_surface_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Base Structure", "Please load or build a bulk crystal structure first."); return
        params = CleaveSurfaceDialog.show_dialog(self)
        if params:
            self.viewer_widget.cleave_surface(params["miller_indices"], params["layers"])
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Surface Cleaved)")
            self.statusBar().showMessage("Surface cleaved.", 3000)
        else: self.statusBar().showMessage("Cleave surface cancelled.", 2000)

    def _show_add_vacuum_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Structure", "Please load or build a structure first."); return
        if not np.any(self.viewer_widget.current_atoms.cell): QMessageBox.warning(self, "No Unit Cell", "A unit cell must be defined to add vacuum."); return
        params = AddVacuumDialog.show_dialog(self)
        if params:
            self.viewer_widget.add_vacuum_layer(params["vacuum"], params["axis"])
            if self.workflow_editor_widget: self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Vacuum Added)")
            self.statusBar().showMessage("Vacuum layer added.", 3000)
        else: self.statusBar().showMessage("Add vacuum layer cancelled.", 2000)

    def _show_select_by_type_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Molecule", "Load or create a molecule first."); return
        symbol, ok = QInputDialog.getText(self, "Select by Atom Type", "Enter element symbol (e.g., C, Si):")
        if ok and symbol: self.viewer_widget.select_atoms_by_symbol(symbol); self.statusBar().showMessage(f"Selection updated for symbol '{symbol}'.", 3000)
        elif ok: QMessageBox.warning(self, "Input Error", "Element symbol cannot be empty.")

    def _show_select_by_region_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Molecule", "Load or create a molecule first."); return
        params = SelectByRegionDialog.show_dialog(self)
        if params: self.viewer_widget.select_atoms_by_sphere(params["center"], params["radius"]); self.statusBar().showMessage(f"Selection updated for region.", 3000)
            
    def _clear_current_selection(self):
        if self.viewer_widget.current_atoms: self.viewer_widget.clear_selection(render_update=True); self.statusBar().showMessage("Selection cleared.", 3000)
        else: self.statusBar().showMessage("No molecule loaded to clear selection from.", 3000)


    def _apply_constraints_to_selected_atoms(self, fix_x: bool, fix_y: bool, fix_z: bool):
        if self.viewer_widget.current_atoms and self.viewer_widget.selected_atom_indices:
            self.viewer_widget.apply_constraints_to_selected(fix_x, fix_y, fix_z)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Constraints)")
        else: QMessageBox.information(self, "No Selection", "Please select atoms before applying constraints.")

    def _release_constraints_on_selected_atoms(self):
        if self.viewer_widget.current_atoms and self.viewer_widget.selected_atom_indices:
            self.viewer_widget.release_constraints_on_selected()
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Constraints)")
        else: QMessageBox.information(self, "No Selection", "Please select atoms before releasing constraints.")

# The _test_generate_vasp_scf method was removed as per the prompt in Turn 70,
# but it was present in Turn 67 (the last full version shown before the prompt).
# If it should indeed be gone, this is fine. If it was an oversight in the prompt,
# it would be missing here. Assuming it should be gone as per the prompt's direction
# when WorkflowEditorWidget was introduced.
```
