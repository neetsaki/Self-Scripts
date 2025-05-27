# molecular_simulator/molecular_simulator/gui/dialogs/supercell_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QIntValidator
import numpy as np

class SupercellDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Supercell")

        self.layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        # For simple PxQxR supercells along lattice vectors
        self.p_edit = QLineEdit("1")
        self.q_edit = QLineEdit("1")
        self.r_edit = QLineEdit("1")

        int_validator = QIntValidator(1, 100) # Multipliers from 1 to 100
        self.p_edit.setValidator(int_validator)
        self.q_edit.setValidator(int_validator)
        self.r_edit.setValidator(int_validator)

        grid_layout.addWidget(QLabel("Repeat P (along a1):"), 0, 0)
        grid_layout.addWidget(self.p_edit, 0, 1)
        grid_layout.addWidget(QLabel("Repeat Q (along a2):"), 1, 0)
        grid_layout.addWidget(self.q_edit, 1, 1)
        grid_layout.addWidget(QLabel("Repeat R (along a3):"), 2, 0)
        grid_layout.addWidget(self.r_edit, 2, 1)
        
        self.layout.addLayout(grid_layout)
        self.layout.addWidget(QLabel("Note: This creates a diagonal supercell matrix [P,0,0; 0,Q,0; 0,0,R]."))


        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_supercell_matrix(self):
        try:
            p = int(self.p_edit.text())
            q = int(self.q_edit.text())
            r = int(self.r_edit.text())

            if p <= 0 or q <= 0 or r <= 0:
                QMessageBox.warning(self, "Input Error", "Repeat factors must be positive integers.")
                return None
            
            # Create a diagonal transformation matrix
            # P, Q, R correspond to multiples of the lattice vectors a1, a2, a3
            matrix = np.diag([p, q, r])
            return matrix
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Repeat factors must be valid integers.")
            return None

    @staticmethod
    def show_dialog(parent=None):
        dialog = SupercellDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_supercell_matrix()
        return None
