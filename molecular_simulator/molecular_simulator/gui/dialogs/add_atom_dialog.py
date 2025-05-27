# molecular_simulator/molecular_simulator/gui/dialogs/add_atom_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator
from ase import Atom # For symbol validation

class AddAtomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Atom")

        self.layout = QVBoxLayout(self)

        # Element Symbol
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Element Symbol:"))
        self.symbol_edit = QLineEdit("C") # Default to Carbon
        symbol_layout.addWidget(self.symbol_edit)
        self.layout.addLayout(symbol_layout)

        # Coordinates
        coord_layout = QHBoxLayout()
        self.x_edit = QLineEdit("0.0")
        self.y_edit = QLineEdit("0.0")
        self.z_edit = QLineEdit("0.0")
        
        # Validators for coordinates to accept doubles
        double_validator = QDoubleValidator()
        double_validator.setDecimals(4) # Allow up to 4 decimal places
        self.x_edit.setValidator(double_validator)
        self.y_edit.setValidator(double_validator)
        self.z_edit.setValidator(double_validator)

        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.x_edit)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.y_edit)
        coord_layout.addWidget(QLabel("Z:"))
        coord_layout.addWidget(self.z_edit)
        self.layout.addLayout(coord_layout)

        # Dialog buttons (OK, Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_atom_data(self):
        symbol = self.symbol_edit.text().strip()
        try:
            x = float(self.x_edit.text())
            y = float(self.y_edit.text())
            z = float(self.z_edit.text())
        except ValueError:
            # This should ideally be caught by validators, but good to have a fallback
            QMessageBox.warning(self, "Input Error", "Coordinates must be valid numbers.")
            return None

        # Validate symbol
        if not symbol:
            QMessageBox.warning(self, "Input Error", "Element symbol cannot be empty.")
            return None
        
        # Capitalize symbol correctly
        if len(symbol) == 1:
            symbol = symbol.upper()
        elif len(symbol) > 1:
            symbol = symbol[0].upper() + symbol[1:].lower()
        
        try:
            # Check if ASE recognizes the symbol by trying to create a dummy atom
            _ = Atom(symbol) 
        except Exception as e:
            QMessageBox.warning(self, "Input Error", f"Invalid element symbol '{symbol}': {e}")
            return None
            
        return {"symbol": symbol, "x": x, "y": y, "z": z}

    @staticmethod
    def show_dialog(parent=None):
        dialog = AddAtomDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_atom_data()
        return None
