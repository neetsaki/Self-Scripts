# molecular_simulator/molecular_simulator/gui/widgets/molecular_viewer.py
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt
from pyvistaqt import QtInteractor
import pyvista as pv
from ase import Atoms, Atom 
import numpy as np
from ase.cell import Cell 
from ase.constraints import FixCartesian
from ase.build import make_supercell
# Add new imports for surface building
from ase.build import surface as ase_surface
from ase.build import sort as ase_sort # To sort atoms after cleaving, good practice
import traceback # For detailed error logging

class MolecularViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.plotter = QtInteractor(self)
        self.layout.addWidget(self.plotter.interactor)
        
        self.plotter.background_color = 'lightgrey'
        
        self.current_atoms: Atoms = None
        self.atom_actors = [] 
        self.selected_atom_indices: list[int] = [] 
        self.cell_actor = None
        
        self.plotter.enable_element_picking(callback=self._handle_pick, show_message=False) 
        self.plotter.iren.add_observer("KeyPressEvent", self._handle_key_press)

    def _get_atom_color(self, symbol: str, selected: bool = False) -> str:
        if selected: return 'lime' 
        colors = {'H': 'white', 'C': '#787878', 'O': '#FF0000', 'N': '#0000FF', 'Si': '#DAA520', 'default': '#FF1493'} # Simplified
        return colors.get(symbol, colors['default'])

    def _get_atom_radius(self, symbol: str) -> float:
        radii = {'H': 0.37, 'C': 0.77, 'O': 0.73, 'N': 0.75, 'Si': 1.11, 'default': 0.7} # Simplified
        return radii.get(symbol, radii['default'])

    def show_molecule(self, atoms_object: Atoms = None):
        self.plotter.clear() 
        self.atom_actors.clear()
        if self.cell_actor:
            self.plotter.remove_actor(self.cell_actor, render=False)
            self.cell_actor = None
        self.current_atoms = atoms_object
        self.selected_atom_indices = [] 
        if self.current_atoms and len(self.current_atoms) > 0:
            if not self.plotter.renderer.lights: self.plotter.add_light(pv.Light())
            for i, atom in enumerate(self.current_atoms):
                actor = self.plotter.add_mesh(
                    pv.Sphere(radius=self._get_atom_radius(atom.symbol), center=atom.position),
                    color=self._get_atom_color(atom.symbol, selected=False), name=f"atom_{i}"
                )
                self.atom_actors.append(actor)
            if self.plotter.picker: self.plotter.picker.pickable_actors = self.atom_actors
            if self.current_atoms.cell is not None and np.any(self.current_atoms.cell.array):
                self._draw_unit_cell(self.current_atoms.cell)
            self.plotter.reset_camera()
        self.plotter.render()

    def _handle_pick(self, picked_actor, *args):
        if picked_actor is None or not self.current_atoms or not self.atom_actors:
            if self.selected_atom_indices: self.clear_selection(render_update=True)
            return
        try:
            atom_idx = self.atom_actors.index(picked_actor)
        except ValueError: 
            if self.selected_atom_indices: self.clear_selection(render_update=True)
            return
        if atom_idx in self.selected_atom_indices:
            self.selected_atom_indices.remove(atom_idx)
            self._update_atom_appearance(atom_idx, selected=False)
        else:
            self.clear_selection(render_update=False) 
            self.selected_atom_indices.append(atom_idx)
            self._update_atom_appearance(atom_idx, selected=True)
        self.plotter.render()

    def _update_atom_appearance(self, atom_idx: int, selected: bool):
        if not self.current_atoms or not (0 <= atom_idx < len(self.atom_actors)): return
        actor_to_update = self.atom_actors[atom_idx]
        atom_symbol = self.current_atoms[atom_idx].symbol
        actor_to_update.prop.color = pv.Color(self._get_atom_color(atom_symbol, selected=selected))

    def _refresh_selected_atoms_appearance(self):
        if not self.atom_actors or not self.current_atoms : return
        for i in range(len(self.current_atoms)):
            self._update_atom_appearance(i, selected=(i in self.selected_atom_indices))
        self.plotter.render()

    def clear_selection(self, render_update=True):
        if self.current_atoms and self.atom_actors:
            for idx in self.selected_atom_indices:
                if 0 <= idx < len(self.atom_actors): self._update_atom_appearance(idx, selected=False)
        self.selected_atom_indices = []
        if render_update: self.plotter.render()
        print("Selection cleared.")

    def select_atoms_by_symbol(self, symbol: str):
        if not self.current_atoms: return
        self.clear_selection(render_update=False)
        symbol_to_match = symbol.strip()
        if len(symbol_to_match) == 1: symbol_to_match = symbol_to_match.upper()
        elif len(symbol_to_match) > 1: symbol_to_match = symbol_to_match[0].upper() + symbol_to_match[1:].lower()
        for i, atom in enumerate(self.current_atoms):
            if atom.symbol == symbol_to_match: self.selected_atom_indices.append(i)
        self._refresh_selected_atoms_appearance()

    def select_atoms_by_sphere(self, center: tuple[float, float, float], radius: float):
        if not self.current_atoms: return
        self.clear_selection(render_update=False)
        center_np, radius_sq = np.array(center), radius * radius
        for i, atom in enumerate(self.current_atoms):
            if np.sum((atom.position - center_np)**2) <= radius_sq: self.selected_atom_indices.append(i)
        self._refresh_selected_atoms_appearance()

    def apply_constraints_to_selected(self, fix_x: bool, fix_y: bool, fix_z: bool):
        if not self.current_atoms or not self.selected_atom_indices:
            QMessageBox.information(self, "No Selection", "No atoms selected to apply constraints.")
            return
        constraint_mask = [fix_x, fix_y, fix_z]
        new_constraints_for_selected = [FixCartesian(idx, constraint_mask) for idx in self.selected_atom_indices]
        
        existing_constraints = self.current_atoms.constraints or []
        final_constraints = []
        for constr in existing_constraints:
            if isinstance(constr, FixCartesian):
                if constr.a not in self.selected_atom_indices: final_constraints.append(constr)
            else: final_constraints.append(constr)
        final_constraints.extend(new_constraints_for_selected)
        self.current_atoms.set_constraints(final_constraints)
        print(f"Applied constraints. Total constraints: {len(self.current_atoms.constraints)}")
        QMessageBox.information(self, "Constraints Applied", 
                                f"Applied constraints ({fix_x=}, {fix_y=}, {fix_z=}) to {len(self.selected_atom_indices)} selected atoms.")

    def release_constraints_on_selected(self):
        if not self.current_atoms or not self.selected_atom_indices:
            QMessageBox.information(self, "No Selection", "No atoms selected to release constraints from.")
            return
        if not self.current_atoms.constraints:
            QMessageBox.information(self, "No Constraints", "No constraints are set on any atom in the system.")
            return
        new_constraints_list = []
        released_count = 0
        for constr in self.current_atoms.constraints:
            if isinstance(constr, FixCartesian) and constr.a in self.selected_atom_indices:
                released_count +=1
            else: new_constraints_list.append(constr)
        if released_count > 0:
            self.current_atoms.set_constraints(new_constraints_list if new_constraints_list else None)
            QMessageBox.information(self, "Constraints Released", f"Released Cartesian constraints from {released_count} selected atoms.")
        else:
            QMessageBox.information(self, "No Constraints Found", "No Cartesian constraints found for the selected atoms.")

    def create_supercell(self, transformation_matrix: np.ndarray):
        if self.current_atoms is None: QMessageBox.information(self, "No Molecule", "Load or create a base molecule first."); return
        if not np.any(self.current_atoms.cell): QMessageBox.warning(self, "No Unit Cell", "A unit cell must be defined to create a supercell."); return
        try:
            original_atoms = self.current_atoms.copy() 
            if original_atoms.constraints: print("Note: Existing constraints are not automatically propagated by this operation."); original_atoms.set_constraints(None) 
            supercell_atoms = make_supercell(original_atoms, transformation_matrix, wrap=True)
            self.show_molecule(supercell_atoms) 
            QMessageBox.information(self, "Supercell Created", f"Supercell created. New atom count: {len(supercell_atoms)}.")
        except Exception as e: QMessageBox.critical(self, "Supercell Error", f"Could not create supercell: {e}"); traceback.print_exc()

    def cleave_surface(self, miller_indices: tuple[int, int, int], layers: int):
        """Cleaves a surface from the current_atoms and updates the view."""
        if self.current_atoms is None:
            QMessageBox.information(self, "No Molecule", "Load or create a bulk crystal structure first.")
            return
        if not np.any(self.current_atoms.cell) or not np.all(self.current_atoms.pbc):
            QMessageBox.warning(self, "Bulk Crystal Required", 
                                "A periodic bulk crystal (with defined cell and PBC True in all directions) is required to cleave a surface.")
            return
        try:
            bulk_atoms = self.current_atoms.copy()
            if bulk_atoms.constraints:
                print("Note: Existing constraints are cleared before cleaving surface.")
                bulk_atoms.set_constraints(None)
            slab_atoms = ase_surface(bulk_atoms, miller_indices, layers, vacuum=None) 
            slab_atoms = ase_sort(slab_atoms) 
            self.show_molecule(slab_atoms)
            print(f"Created surface with Miller indices {miller_indices}, {layers} layers. Atom count: {len(slab_atoms)}")
            QMessageBox.information(self, "Surface Cleaved", 
                                    f"Surface ({miller_indices[0]}{miller_indices[1]}{miller_indices[2]}) with {layers} layers created. Atom count: {len(slab_atoms)}.\nUse 'Add Vacuum Layer' to adjust vacuum if needed.")
        except Exception as e:
            QMessageBox.critical(self, "Surface Cleave Error", f"Could not cleave surface: {e}\nEnsure the Miller indices are valid for the crystal structure and that the structure is a 3D periodic bulk crystal.")
            traceback.print_exc()

    def add_vacuum_layer(self, vacuum_thickness: float, axis_idx: int):
        """Adds a vacuum layer to the current structure along the specified axis."""
        if self.current_atoms is None:
            QMessageBox.information(self, "No Molecule", "Load or create a structure first.")
            return
        if not np.any(self.current_atoms.cell):
            QMessageBox.warning(self, "No Unit Cell", "A unit cell must be defined to add a vacuum layer.")
            return
        try:
            atoms_with_vacuum = self.current_atoms.copy()
            atoms_with_vacuum.center(vacuum=vacuum_thickness, axis=axis_idx)
            new_pbc = list(atoms_with_vacuum.pbc) 
            if 0 <= axis_idx < 3: new_pbc[axis_idx] = False 
            atoms_with_vacuum.set_pbc(new_pbc)
            self.show_molecule(atoms_with_vacuum)
            print(f"Added {vacuum_thickness} Å vacuum along axis {axis_idx}. New cell: {atoms_with_vacuum.cell.cellpar()}, PBC: {atoms_with_vacuum.pbc}")
            QMessageBox.information(self, "Vacuum Layer Added", f"Added {vacuum_thickness} Å vacuum along axis {axis_idx}.")
        except Exception as e:
            QMessageBox.critical(self, "Add Vacuum Error", f"Could not add vacuum layer: {e}")
            traceback.print_exc()

    def _handle_key_press(self, interactor, event_name): 
        key = interactor.GetKeySym().lower() 
        if key == "c": 
            if self.selected_atom_indices and self.current_atoms: self._change_selected_atom_type_dialog(self.selected_atom_indices[0]) 
            elif not self.selected_atom_indices: QMessageBox.information(self, "No Atom Selected", "Select an atom first to change its type.")
        elif key == "escape": self.clear_selection(render_update=True)
        elif key == "v": 
            if self.current_atoms and np.any(self.current_atoms.cell): 
                if self.cell_actor and self.cell_actor in self.plotter.renderer.actors: self.plotter.remove_actor(self.cell_actor, render=True); self.cell_actor = None
                else: self._draw_unit_cell(self.current_atoms.cell); self.plotter.render()
            else: print("No cell defined to toggle, or cell is all zeros.")

    def _change_selected_atom_type_dialog(self, atom_idx_to_change: int):
        if not self.current_atoms or not (0 <= atom_idx_to_change < len(self.current_atoms)): return
        current_symbol = self.current_atoms[atom_idx_to_change].symbol
        new_symbol, ok = QInputDialog.getText(self, "Change Atom Type", f"Index: {atom_idx_to_change}, Symbol: {current_symbol}\nEnter new symbol:", text=current_symbol)
        if ok and new_symbol:
            new_symbol = new_symbol.strip()
            if not new_symbol: QMessageBox.warning(self, "Invalid Input", "Symbol cannot be empty."); return
            if len(new_symbol) == 1: new_symbol = new_symbol.upper()
            elif len(new_symbol) > 1: new_symbol = new_symbol[0].upper() + new_symbol[1:].lower()
            try:
                _ = Atom(new_symbol) 
                self.current_atoms[atom_idx_to_change].symbol = new_symbol
                actor_to_update = self.atom_actors[atom_idx_to_change]
                actor_to_update.mapper.input_data = pv.Sphere(radius=self._get_atom_radius(new_symbol), center=self.current_atoms[atom_idx_to_change].position)
                actor_to_update.prop.color = pv.Color(self._get_atom_color(new_symbol, selected=False))
                self.clear_selection(render_update=True) 
            except Exception as e: QMessageBox.warning(self, "Error", f"Symbol '{new_symbol}' not valid: {e}")

    def clear_view(self): 
        self.plotter.clear()
        if self.cell_actor: self.cell_actor = None
        self.current_atoms = None
        self.atom_actors.clear()
        self.selected_atom_indices = [] 
        self.plotter.render()
        
    def _draw_unit_cell(self, cell: Cell):
        if self.cell_actor: self.plotter.remove_actor(self.cell_actor, render=False); self.cell_actor = None
        if cell is None or not np.any(cell.array): return
        v = cell.array; o = np.array([0.,0.,0.])
        pts = np.array([o,v[0],v[1],v[2],v[0]+v[1],v[0]+v[2],v[1]+v[2],v[0]+v[1]+v[2]])
        ln_idx = [[0,1],[0,2],[0,3],[1,4],[1,5],[2,4],[2,6],[3,5],[3,6],[4,7],[5,7],[6,7]]
        ln_pv = [[2,s,e] for s,e in ln_idx]
        self.cell_actor = self.plotter.add_mesh(pv.PolyData(pts, lines=np.array(ln_pv).ravel()), color='black', line_width=2)

    def set_unit_cell(self, cell_params: list[float], pbc: bool):
        if self.current_atoms is None: self.current_atoms = Atoms() 
        try:
            cell_obj = Cell.fromcellpar(cell_params)
            self.current_atoms.set_cell(cell_obj); self.current_atoms.set_pbc(pbc)
            self._draw_unit_cell(self.current_atoms.cell); self.plotter.render()
        except Exception as e: QMessageBox.warning(self, "Cell Error", f"Could not set unit cell: {e}")
            
    def add_atom(self, symbol: str, position: tuple[float, float, float]):
        new_atom = Atom(symbol, position=position)
        if self.current_atoms is None: self.current_atoms = Atoms([new_atom])
        else: self.current_atoms.append(new_atom)
        self.show_molecule(self.current_atoms)
