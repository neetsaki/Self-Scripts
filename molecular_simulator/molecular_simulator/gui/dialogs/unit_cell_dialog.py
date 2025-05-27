# molecular_simulator/molecular_simulator/gui/dialogs/unit_cell_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, 
    QDialogButtonBox, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QDoubleValidator
from ase.cell import Cell

class UnitCellDialog(QDialog):
    def __init__(self, parent=None, current_cell_params=None):
        super().__init__(parent)
        self.setWindowTitle("Define/Edit Unit Cell")

        self.layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        # Labels and LineEdits for a, b, c, alpha, beta, gamma
        self.param_edits = {}
        params = ["a", "b", "c", "alpha", "beta", "gamma"]
        defaults = ["10.0", "10.0", "10.0", "90.0", "90.0", "90.0"] # Default to a cubic cell
        
        if current_cell_params: # If existing cell, use its parameters
            # current_cell_params expected to be [a, b, c, alpha, beta, gamma]
            defaults = [f"{p:.4f}" for p in current_cell_params]

        double_validator = QDoubleValidator()
        double_validator.setDecimals(4)
        double_validator.setBottom(0.0001) # Lengths and angles should be positive

        for i, param_name in enumerate(params):
            grid_layout.addWidget(QLabel(f"{param_name.capitalize()}:"), i, 0)
            self.param_edits[param_name] = QLineEdit(defaults[i])
            self.param_edits[param_name].setValidator(double_validator)
            grid_layout.addWidget(self.param_edits[param_name], i, 1)
            # Units
            unit = " (Å)" if i < 3 else " (°)"
            grid_layout.addWidget(QLabel(unit), i, 2)

        self.layout.addLayout(grid_layout)

        # Checkbox for PBC
        self.pbc_checkbox = QCheckBox("Enable Periodic Boundary Conditions (PBC)")
        # If a cell is defined, typically PBC is true.
        # If current_cell_params were passed, it implies a cell exists.
        self.pbc_checkbox.setChecked(bool(current_cell_params)) 
        self.layout.addWidget(self.pbc_checkbox)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_cell_parameters(self):
        try:
            params_values = [float(self.param_edits[p].text()) for p in ["a", "b", "c", "alpha", "beta", "gamma"]]
            pbc_enabled = self.pbc_checkbox.isChecked()
            
            # Basic validation for cell parameters (e.g., lengths > 0)
            if not all(p > 0 for p in params_values[:3]): # a, b, c must be > 0
                QMessageBox.warning(self, "Input Error", "Cell lengths (a, b, c) must be positive.")
                return None
            if not all(0 < p <= 180 for p in params_values[3:]): # angles typically > 0 and <= 180
                 # ASE's Cell.fromcellpar handles more complex validation, but basic check here.
                 # e.g. sum of angles in a triangle, etc.
                 # Allowing 180 for flat structures, though ASE might be stricter.
                 QMessageBox.warning(self, "Input Error", "Angles (alpha, beta, gamma) must be between 0 and 180 degrees.")
                 return None


            return {"cellpar": params_values, "pbc": pbc_enabled}
        except ValueError:
            QMessageBox.warning(self, "Input Error", "All cell parameters must be valid numbers.")
            return None

    @staticmethod
    def show_dialog(parent=None, current_cell_params=None):
        dialog = UnitCellDialog(parent, current_cell_params)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_cell_parameters()
        return None
