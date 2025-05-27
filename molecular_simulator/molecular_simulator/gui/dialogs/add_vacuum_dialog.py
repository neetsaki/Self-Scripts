# molecular_simulator/molecular_simulator/gui/dialogs/add_vacuum_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox, QComboBox
)
from PyQt6.QtGui import QDoubleValidator

class AddVacuumDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Vacuum Layer")
        self.layout = QVBoxLayout(self)
        grid = QGridLayout()

        grid.addWidget(QLabel("Vacuum Thickness (Å):"), 0, 0)
        self.vacuum_edit = QLineEdit("10.0")
        validator = QDoubleValidator(0.1, 1000.0, 2) # Min 0.1A, Max 1000A, 2 decimals
        self.vacuum_edit.setValidator(validator)
        grid.addWidget(self.vacuum_edit, 0, 1)

        grid.addWidget(QLabel("Axis for Vacuum:"), 1, 0)
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(["Z (axis 2)", "Y (axis 1)", "X (axis 0)"])
        self.axis_combo.setCurrentIndex(0) # Default to Z-axis
        grid.addWidget(self.axis_combo, 1, 1)
        
        self.layout.addLayout(grid)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_vacuum_parameters(self):
        try:
            vacuum = float(self.vacuum_edit.text())
            axis_text = self.axis_combo.currentText() # "Z (axis 2)"
            axis = int(axis_text.split("axis ")[1].replace(")", "")) # Extract 2, 1, or 0

            if vacuum <= 0:
                QMessageBox.warning(self, "Input Error", "Vacuum thickness must be positive.")
                return None
            return {"vacuum": vacuum, "axis": axis}
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Vacuum thickness must be a valid number.")
            return None
        except Exception as e: # Catch parsing error for axis if text changes
            QMessageBox.warning(self, "Internal Error", f"Could not parse axis: {e}")
            return None


    @staticmethod
    def show_dialog(parent=None):
        dialog = AddVacuumDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_vacuum_parameters()
        return None
