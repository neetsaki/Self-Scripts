# molecular_simulator/molecular_simulator/gui/workflow_editor_widget.py
import os 
from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QLabel
)
from ..core.workflow import Workflow, CalculationModule
from .dialogs.scf_params_dialog import ScfParamsDialog 
# Add new dialog and potentially distinguish generator functions if names were identical
from .dialogs.geo_opt_params_dialog import GeoOptParamsDialog
from ..core.generators.vasp_generator import generate_vasp_scf_input, generate_vasp_geo_opt_input
from ase import Atoms 
import traceback # For more detailed error messages

class WorkflowEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_workflow = Workflow(name="MyCalculationWorkflow")
        self.current_atoms_object: Atoms = None 

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Workflow Module Management:"))

        add_module_layout = QHBoxLayout()
        self.add_scf_vasp_button = QPushButton("Add VASP SCF")
        self.add_scf_vasp_button.clicked.connect(self._add_vasp_scf_module)
        add_module_layout.addWidget(self.add_scf_vasp_button)
        
        self.add_geo_opt_vasp_button = QPushButton("Add VASP Geo Opt") # New button
        self.add_geo_opt_vasp_button.clicked.connect(self._add_vasp_geo_opt_module)
        add_module_layout.addWidget(self.add_geo_opt_vasp_button)
        self.layout.addLayout(add_module_layout)

        self.module_list_widget = QListWidget()
        self.module_list_widget.itemDoubleClicked.connect(self._edit_selected_module_parameters)
        self.layout.addWidget(QLabel("Workflow Modules (Double-click to edit):"))
        self.layout.addWidget(self.module_list_widget)
        
        self.generate_files_button = QPushButton("Generate Input Files for Workflow")
        self.generate_files_button.clicked.connect(self._generate_workflow_files)
        self.layout.addWidget(self.generate_files_button)
        # self.setLayout(self.layout) # setLayout is called by the parent, not needed here explicitly

    def set_current_atoms(self, atoms: Atoms): 
        self.current_atoms_object = atoms
        # Optionally, log or update UI based on atoms presence
        if atoms: print(f"WorkflowEditor: Atoms object with {len(atoms)} atoms received.")
        else: print("WorkflowEditor: Atoms object cleared.")


    def _add_vasp_scf_module(self):
        default_scf_params = {"ENCUT": 400, "KPOINTS_TUPLE": (3,3,3), "ISMEAR": 0, "SIGMA": 0.05, "EXTRA_INCAR_PARAMS": {}}
        module_name = f"VASP_SCF_Step_{len(self.current_workflow.modules) + 1}"
        scf_module = CalculationModule(module_type="SCF_VASP", name=module_name, parameters=default_scf_params)
        self.current_workflow.add_module(scf_module)
        self._refresh_module_list()
        print(f"Added module: {scf_module}")

    def _add_vasp_geo_opt_module(self): # New method
        default_geo_opt_params = { 
            "IBRION": 2, "NSW": 200, "EDIFFG": "-0.01", "POTIM": 0.2,
            "ENCUT": 400, "KPOINTS_TUPLE": (3,3,3), "ISMEAR": 0, "SIGMA": 0.05,
            "EXTRA_INCAR_PARAMS": {}
        }
        module_name = f"VASP_GEO_OPT_Step_{len(self.current_workflow.modules) + 1}"
        geo_opt_module = CalculationModule(
            module_type="GEO_OPT_VASP", 
            name=module_name, 
            parameters=default_geo_opt_params
        )
        self.current_workflow.add_module(geo_opt_module)
        self._refresh_module_list()
        print(f"Added module: {geo_opt_module}")

    def _refresh_module_list(self):
        self.module_list_widget.clear()
        for i, module in enumerate(self.current_workflow.modules):
            item_text = f"{i+1}. {module.name} (Type: {module.module_type})"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, i) 
            self.module_list_widget.addItem(list_item)

    def _edit_selected_module_parameters(self, item: QListWidgetItem): # Modified
        module_index = item.data(Qt.ItemDataRole.UserRole)
        if module_index is None or not (0 <= module_index < len(self.current_workflow.modules)): return
        
        module_to_edit = self.current_workflow.modules[module_index]
        updated = False
        if module_to_edit.module_type == "SCF_VASP":
            new_params = ScfParamsDialog.show_dialog(self, initial_params=module_to_edit.parameters)
            if new_params: module_to_edit.parameters = new_params; updated = True
        elif module_to_edit.module_type == "GEO_OPT_VASP": 
            new_params = GeoOptParamsDialog.show_dialog(self, initial_params=module_to_edit.parameters)
            if new_params: module_to_edit.parameters = new_params; updated = True
        else:
            QMessageBox.information(self, "Edit Not Supported", f"Parameter editing for module type '{module_to_edit.module_type}' is not yet implemented.")
        
        if updated:
            print(f"Updated parameters for module '{module_to_edit.name}': {module_to_edit.parameters}")
            QMessageBox.information(self, "Parameters Updated", f"Parameters for '{module_to_edit.name}' updated.")
        else:
            print(f"Parameter editing cancelled or no changes made for module '{module_to_edit.name}'.")


    def _generate_workflow_files(self): # Modified
        if not self.current_atoms_object:
            QMessageBox.warning(self, "No Molecule", "No active molecule. Load/create a molecule first."); return
        if not self.current_workflow.modules:
            QMessageBox.warning(self, "Empty Workflow", "Add calculation modules to the workflow first."); return

        base_output_dir = QFileDialog.getExistingDirectory(self, "Select Base Output Directory for Workflow")
        if not base_output_dir:
            QMessageBox.information(self, "Cancelled", "File generation cancelled."); return

        summary_messages = []
        generated_all_successfully = True

        for i, module in enumerate(self.current_workflow.modules):
            module_folder_name = f"{i+1:02d}_{module.module_type}_{module.name}".replace(" ", "_").replace(":", "_")
            module_output_path = os.path.join(base_output_dir, module_folder_name)
            
            summary_messages.append(f"\nModule: {module.name} (Type: {module.module_type})")
            summary_messages.append(f"  Output Path: {module_output_path}")

            try:
                if not os.path.exists(module_output_path): os.makedirs(module_output_path)

                if module.module_type == "SCF_VASP":
                    files = generate_vasp_scf_input(self.current_atoms_object, module.parameters, output_path=module_output_path)
                    summary_messages.append(f"  Generated files: {', '.join([os.path.basename(f) for f in files])}")
                elif module.module_type == "GEO_OPT_VASP": 
                    files = generate_vasp_geo_opt_input(self.current_atoms_object, module.parameters, output_path=module_output_path)
                    summary_messages.append(f"  Generated files: {', '.join([os.path.basename(f) for f in files])}")
                else:
                    summary_messages.append("  Skipped: Generation for this module type is not implemented yet.")
                    generated_all_successfully = False # Mark as not fully successful if a module is skipped
            except Exception as e:
                summary_messages.append(f"  ERROR generating files: {e}")
                generated_all_successfully = False
                traceback.print_exc() # Print full traceback to console for debugging
        
        final_message_title = "Generation Report"
        final_message_intro = "Workflow Input Generation Complete." if generated_all_successfully else "Workflow Input Generation Encountered Issues."
        final_message = final_message_intro + "\n" + "\n".join(summary_messages)
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(final_message_title)
        msg_box.setText(final_message)
        if not generated_all_successfully: msg_box.setIcon(QMessageBox.Icon.Warning)
        else: msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

        print(final_message) # Also print to console for logging/debugging
