# molecular_simulator/molecular_simulator/gui/dialogs/select_by_region_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator

class SelectByRegionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Atoms in Spherical Region")
        self.layout = QVBoxLayout(self)
        grid = QGridLayout()

        self.x_edit = QLineEdit("0.0")
        self.y_edit = QLineEdit("0.0")
        self.z_edit = QLineEdit("0.0")
        self.radius_edit = QLineEdit("2.0") # Default radius

        validator = QDoubleValidator()
        validator.setDecimals(4)
        self.x_edit.setValidator(validator)
        self.y_edit.setValidator(validator)
        self.z_edit.setValidator(validator)
        
        radius_validator = QDoubleValidator()
        radius_validator.setDecimals(4)
        radius_validator.setBottom(0.0001) # Radius must be positive
        self.radius_edit.setValidator(radius_validator)

        grid.addWidget(QLabel("Center X:"), 0, 0)
        grid.addWidget(self.x_edit, 0, 1)
        grid.addWidget(QLabel("Y:"), 1, 0)
        grid.addWidget(self.y_edit, 1, 1)
        grid.addWidget(QLabel("Z:"), 2, 0)
        grid.addWidget(self.z_edit, 2, 1)
        grid.addWidget(QLabel("Radius (Å):"), 3, 0)
        grid.addWidget(self.radius_edit, 3, 1)
        self.layout.addLayout(grid)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selection_parameters(self):
        try:
            x = float(self.x_edit.text())
            y = float(self.y_edit.text())
            z = float(self.z_edit.text())
            radius = float(self.radius_edit.text())
            if radius <= 0:
                QMessageBox.warning(self, "Input Error", "Radius must be a positive number.")
                return None
            return {"center": (x, y, z), "radius": radius}
        except ValueError:
            QMessageBox.warning(self, "Input Error", "All parameters must be valid numbers.")
            return None

    @staticmethod
    def show_dialog(parent=None):
        dialog = SelectByRegionDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selection_parameters()
        return None
