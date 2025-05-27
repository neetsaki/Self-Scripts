# molecular_simulator/molecular_simulator/gui/main_window.py
import sys
import os 
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QInputDialog,
    QDockWidget 
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt 

from .widgets.molecular_viewer import MolecularViewerWidget
from ..core.io import load_structure, save_structure 
from ase import Atoms 
from .dialogs.add_atom_dialog import AddAtomDialog 
from .dialogs.unit_cell_dialog import UnitCellDialog
from .dialogs.select_by_region_dialog import SelectByRegionDialog
from .dialogs.supercell_dialog import SupercellDialog 
from .dialogs.scf_params_dialog import ScfParamsDialog 
from ..core.generators.vasp_generator import generate_vasp_scf_input
from ..core.workflow import Workflow, CalculationModule
from .workflow_editor_widget import WorkflowEditorWidget 
# Import the new dialogs
from .dialogs.cleave_surface_dialog import CleaveSurfaceDialog
from .dialogs.add_vacuum_dialog import AddVacuumDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Molecular Simulator")
        self.setGeometry(100, 100, 1024, 768)

        self.viewer_widget = MolecularViewerWidget(self)
        self.setCentralWidget(self.viewer_widget) 

        self.current_file_path = None 
        self._create_menus()

        self.workflow_editor_dock = QDockWidget("Workflow Editor", self)
        self.workflow_editor_widget = WorkflowEditorWidget(self.workflow_editor_dock) 
        self.workflow_editor_dock.setWidget(self.workflow_editor_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.workflow_editor_dock)

    def _create_menus(self):
        menu_bar = self.menuBar()

        # File Menu (existing)
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open...", self); open_action.triggered.connect(self._open_file_dialog); file_menu.addAction(open_action)
        save_action = QAction("&Save", self); save_action.setShortcut("Ctrl+S"); save_action.triggered.connect(self._save_file); file_menu.addAction(save_action)
        save_as_action = QAction("Save &As...", self); save_as_action.setShortcut("Ctrl+Shift+S"); save_as_action.triggered.connect(self._save_file_as); file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self); exit_action.triggered.connect(self.close); file_menu.addAction(exit_action)

        # Select Menu (existing)
        select_menu = menu_bar.addMenu("&Select")
        existing_select_actions = select_menu.actions()
        if len(existing_select_actions) == 1 and existing_select_actions[0].text() == "Placeholder Action":
            select_menu.removeAction(existing_select_actions[0])
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

        # Build Menu (Updated)
        build_menu = menu_bar.addMenu("&Build")
        existing_build_actions = build_menu.actions()
        if len(existing_build_actions) == 1 and existing_build_actions[0].text() == "Placeholder Action": build_menu.clear()
        add_atom_action = QAction("&Add Atom...", self); add_atom_action.triggered.connect(self._show_add_atom_dialog); build_menu.addAction(add_atom_action)
        define_cell_action = QAction("&Define/Edit Unit Cell...", self); define_cell_action.triggered.connect(self._show_define_cell_dialog); build_menu.addAction(define_cell_action)
        create_supercell_action = QAction("Create &Supercell...", self); create_supercell_action.triggered.connect(self._show_create_supercell_dialog); build_menu.addAction(create_supercell_action)
        build_menu.addSeparator() # Separator for advanced build features
        cleave_surface_action = QAction("Cleave C&rystal Surface...", self)
        cleave_surface_action.triggered.connect(self._show_cleave_surface_dialog)
        build_menu.addAction(cleave_surface_action)
        add_vacuum_action = QAction("Add &Vacuum Layer...", self)
        add_vacuum_action.triggered.connect(self._show_add_vacuum_dialog)
        build_menu.addAction(add_vacuum_action)
        
        # Generate Menu (existing)
        generate_menu = menu_bar.addMenu("&Generate")
        existing_generate_actions = generate_menu.actions()
        if len(existing_generate_actions) == 1 and existing_generate_actions[0].text() == "Placeholder Action":
             generate_menu.removeAction(existing_generate_actions[0])
        toggle_workflow_editor_action = self.workflow_editor_dock.toggleViewAction()
        toggle_workflow_editor_action.setText("Show/Hide Workflow Editor")
        generate_menu.addAction(toggle_workflow_editor_action)

    def _show_cleave_surface_dialog(self):
        if not self.viewer_widget.current_atoms:
            QMessageBox.information(self, "No Base Structure", "Please load or build a bulk crystal structure first.")
            return
        params = CleaveSurfaceDialog.show_dialog(self)
        if params:
            self.viewer_widget.cleave_surface(params["miller_indices"], params["layers"])
            self.current_file_path = None 
            self.setWindowTitle(f"Molecular Simulator - Modified (Surface Cleaved)")
            self.statusBar().showMessage("Surface cleaved.", 3000)
            if self.workflow_editor_widget and self.viewer_widget.current_atoms:
                 self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
        else:
            self.statusBar().showMessage("Cleave surface cancelled.", 2000)

    def _show_add_vacuum_dialog(self):
        if not self.viewer_widget.current_atoms:
            QMessageBox.information(self, "No Structure", "Please load or build a structure first.")
            return
        if not np.any(self.viewer_widget.current_atoms.cell): 
            QMessageBox.warning(self, "No Unit Cell", "A unit cell must be defined to add vacuum.")
            return
        params = AddVacuumDialog.show_dialog(self)
        if params:
            self.viewer_widget.add_vacuum_layer(params["vacuum"], params["axis"])
            self.current_file_path = None 
            self.setWindowTitle(f"Molecular Simulator - Modified (Vacuum Added)")
            self.statusBar().showMessage("Vacuum layer added.", 3000)
            if self.workflow_editor_widget and self.viewer_widget.current_atoms:
                 self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms)
        else:
            self.statusBar().showMessage("Add vacuum layer cancelled.", 2000)

    # ... (All other existing methods)
    def load_molecule_from_file(self, filepath: str): 
        try:
            atoms = load_structure(filepath)
            self.viewer_widget.show_molecule(atoms)
            self.current_file_path = filepath 
            self.statusBar().showMessage(f"Loaded {filepath}", 5000)
            self.setWindowTitle(f"Molecular Simulator - {os.path.basename(filepath)}")
            self.workflow_editor_widget.set_current_atoms(atoms) 
        except FileNotFoundError:
            self.statusBar().showMessage(f"Error: File not found: {filepath}", 5000)
            self.viewer_widget.clear_view()
            self.current_file_path = None
            self.workflow_editor_widget.set_current_atoms(None) 
        except Exception as e:
            self.statusBar().showMessage(f"Error loading {filepath}: {e}", 5000)
            self.viewer_widget.clear_view()
            self.current_file_path = None
            self.workflow_editor_widget.set_current_atoms(None) 
        if not self.current_file_path: self.setWindowTitle("Molecular Simulator")

    def _show_add_atom_dialog(self): 
        atom_data = AddAtomDialog.show_dialog(self)
        if atom_data:
            self.viewer_widget.add_atom(atom_data["symbol"], (atom_data["x"], atom_data["y"], atom_data["z"])) 
            self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms) 
            self.statusBar().showMessage(f"Added {atom_data['symbol']}", 5000)
            self.current_file_path = None; self.setWindowTitle("Molecular Simulator - Modified*")
        else: self.statusBar().showMessage("Add atom cancelled.", 2000)
    
    def _show_define_cell_dialog(self): 
        params = None
        if self.viewer_widget.current_atoms and np.any(self.viewer_widget.current_atoms.cell):
            try: params = list(self.viewer_widget.current_atoms.cell.cellpar())
            except Exception as e: QMessageBox.warning(self, "Cell Error", f"Could not get cell params: {e}")
        dialog_data = UnitCellDialog.show_dialog(self, params)
        if dialog_data:
            self.viewer_widget.set_unit_cell(dialog_data["cellpar"], dialog_data["pbc"])
            self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms) 
            self.statusBar().showMessage(f"Cell updated. PBC: {dialog_data['pbc']}", 5000)
            self.current_file_path = None; self.setWindowTitle("Molecular Simulator - Modified*")
        else: self.statusBar().showMessage("Define cell cancelled.", 2000)

    def _show_create_supercell_dialog(self): 
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Base Structure", "Load/build a unit cell first."); return
        if not np.any(self.viewer_widget.current_atoms.cell): QMessageBox.warning(self, "Unit Cell Required", "Define unit cell first."); return
        transform_matrix = SupercellDialog.show_dialog(self)
        if transform_matrix is not None:
            self.viewer_widget.create_supercell(transform_matrix) 
            self.workflow_editor_widget.set_current_atoms(self.viewer_widget.current_atoms) 
            self.statusBar().showMessage("Supercell created.", 5000)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Supercell)")
        else: self.statusBar().showMessage("Create supercell cancelled.", 2000)

    def _apply_constraints_to_selected_atoms(self, fix_x: bool, fix_y: bool, fix_z: bool):
        if self.viewer_widget.current_atoms and self.viewer_widget.selected_atom_indices:
            self.viewer_widget.apply_constraints_to_selected(fix_x, fix_y, fix_z)
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Constraints)")
        else: QMessageBox.information(self, "No Selection", "Select atoms before applying constraints.")

    def _release_constraints_on_selected_atoms(self):
        if self.viewer_widget.current_atoms and self.viewer_widget.selected_atom_indices:
            self.viewer_widget.release_constraints_on_selected()
            self.current_file_path = None; self.setWindowTitle(f"Molecular Simulator - Modified (Constraints)")
        else: QMessageBox.information(self, "No Selection", "Select atoms before releasing constraints.")

    def _show_select_by_type_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Molecule", "Load/create molecule first."); return
        symbol, ok = QInputDialog.getText(self, "Select by Atom Type", "Element symbol (e.g., C, Si):")
        if ok and symbol: self.viewer_widget.select_atoms_by_symbol(symbol); self.statusBar().showMessage(f"Selection updated for '{symbol}'.", 3000)
        elif ok: QMessageBox.warning(self, "Input Error", "Symbol cannot be empty.")

    def _show_select_by_region_dialog(self):
        if not self.viewer_widget.current_atoms: QMessageBox.information(self, "No Molecule", "Load/create molecule first."); return
        params = SelectByRegionDialog.show_dialog(self)
        if params: self.viewer_widget.select_atoms_by_sphere(params["center"], params["radius"]); self.statusBar().showMessage(f"Selection updated for region.", 3000)
            
    def _clear_current_selection(self):
        if self.viewer_widget.current_atoms: self.viewer_widget.clear_selection(render_update=True); self.statusBar().showMessage("Selection cleared.", 3000)
        else: self.statusBar().showMessage("No molecule to clear selection from.", 3000)

    def _get_save_file_filter(self):
        fmts = ["XYZ (*.xyz)","CIF (*.cif)","ASE traj (*.traj)","VASP (*.vasp *.poscar *.contcar)","QE (*.pwi *.in)","LAMMPS (*.data *.lammps)","PDB (*.pdb)","All (*.*)"]
        return ";;".join(fmts)

    def _save_file(self):
        if not self.viewer_widget.current_atoms: self.statusBar().showMessage("No molecule to save.", 3000); return
        if self.current_file_path:
            try:
                save_structure(self.viewer_widget.current_atoms, self.current_file_path)
                self.statusBar().showMessage(f"Saved to {self.current_file_path}", 5000)
                self.setWindowTitle(f"Molecular Simulator - {os.path.basename(self.current_file_path)}")
            except Exception as e: QMessageBox.critical(self, "Save Error", f"Could not save file: {e}")
        else: self._save_file_as()

    def _save_file_as(self):
        if not self.viewer_widget.current_atoms: self.statusBar().showMessage("No molecule to save.", 3000); return
        start_dir = os.path.dirname(self.current_file_path) if self.current_file_path else ""
        start_fn = os.path.basename(self.current_file_path) if self.current_file_path else "untitled.xyz"
        if self.viewer_widget.current_atoms and len(self.viewer_widget.current_atoms) > 0 and not self.current_file_path:
            try: start_fn = f"{self.viewer_widget.current_atoms.get_chemical_formula()}.xyz"
            except: pass 
        fp, _ = QFileDialog.getSaveFileName(self, "Save As...", os.path.join(start_dir, start_fn), self._get_save_file_filter())
        if fp:
            try:
                save_structure(self.viewer_widget.current_atoms, fp)
                self.current_file_path = fp 
                self.statusBar().showMessage(f"Saved to {self.current_file_path}", 5000)
                self.setWindowTitle(f"Molecular Simulator - {os.path.basename(self.current_file_path)}")
            except Exception as e: QMessageBox.critical(self, "Save Error", f"Could not save file: {e}")
        else: self.statusBar().showMessage("Save As cancelled.", 2000)

    def _open_file_dialog(self):
        fmts = ["XYZ (*.xyz)","CIF (*.cif)","PDB (*.pdb *.ent)","VASP (*.vasp *.poscar *.contcar)","QE (*.in *.pwi)","All (*.*)"]
        start_dir = os.path.dirname(self.current_file_path) if self.current_file_path else ""
        fp, _ = QFileDialog.getOpenFileName(self, "Open File", start_dir, ";;".join(fmts))
        if fp: self.load_molecule_from_file(fp)
