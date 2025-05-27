# molecular_simulator/molecular_simulator/gui/dialogs/cleave_surface_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox, QSpinBox
)
from PyQt6.QtGui import QIntValidator

class CleaveSurfaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cleave Crystal Surface")
        self.layout = QVBoxLayout(self)
        grid = QGridLayout()

        # Miller Indices (h, k, l)
        grid.addWidget(QLabel("Miller Index h:"), 0, 0)
        self.h_edit = QLineEdit("1")
        self.h_edit.setValidator(QIntValidator(-20, 20)) # Allow negative indices
        grid.addWidget(self.h_edit, 0, 1)

        grid.addWidget(QLabel("Miller Index k:"), 1, 0)
        self.k_edit = QLineEdit("0")
        self.k_edit.setValidator(QIntValidator(-20, 20))
        grid.addWidget(self.k_edit, 1, 1)

        grid.addWidget(QLabel("Miller Index l:"), 2, 0)
        self.l_edit = QLineEdit("0")
        self.l_edit.setValidator(QIntValidator(-20, 20))
        grid.addWidget(self.l_edit, 2, 1)

        # Number of layers for the slab
        grid.addWidget(QLabel("Number of Layers:"), 3, 0)
        self.layers_spinbox = QSpinBox()
        self.layers_spinbox.setRange(1, 100) # Min 1 layer, Max 100 layers
        self.layers_spinbox.setValue(4) # Default to 4 layers
        grid.addWidget(self.layers_spinbox, 3, 1)
        
        self.layout.addLayout(grid)
        self.layout.addWidget(QLabel("Note: Vacuum will be minimal. Use 'Add Vacuum Layer' to adjust."))

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_cleave_parameters(self):
        try:
            h = int(self.h_edit.text())
            k = int(self.k_edit.text())
            l = int(self.l_edit.text())
            layers = self.layers_spinbox.value()

            if h == 0 and k == 0 and l == 0:
                QMessageBox.warning(self, "Input Error", "Miller indices (h,k,l) cannot all be zero.")
                return None
            if layers <= 0:
                QMessageBox.warning(self, "Input Error", "Number of layers must be positive.")
                return None
                
            return {"miller_indices": (h, k, l), "layers": layers}
        except ValueError:
            QMessageBox.warning(self, "Input Error", "All parameters must be valid integers.")
            return None

    @staticmethod
    def show_dialog(parent=None):
        dialog = CleaveSurfaceDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_cleave_parameters()
        return None
