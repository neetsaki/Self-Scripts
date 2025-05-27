# molecular_simulator/molecular_simulator/gui/dialogs/scf_params_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QHBoxLayout # Import QHBoxLayout
)

class ScfParamsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SCF Parameters (VASP)")
        self.layout = QVBoxLayout(self)
        grid = QGridLayout()

        # ENCUT
        grid.addWidget(QLabel("ENCUT (eV):"), 0, 0)
        self.encut_spinbox = QDoubleSpinBox()
        self.encut_spinbox.setRange(100, 2000)
        self.encut_spinbox.setValue(400)
        self.encut_spinbox.setSingleStep(50)
        grid.addWidget(self.encut_spinbox, 0, 1)

        # KPOINTS (Kx, Ky, Kz)
        grid.addWidget(QLabel("K-points (Kx Ky Kz):"), 1, 0)
        self.kx_spin = QSpinBox(); self.kx_spin.setRange(1, 20); self.kx_spin.setValue(3)
        self.ky_spin = QSpinBox(); self.ky_spin.setRange(1, 20); self.ky_spin.setValue(3)
        self.kz_spin = QSpinBox(); self.kz_spin.setRange(1, 20); self.kz_spin.setValue(3)
        
        k_sub_layout = QHBoxLayout() # Use QHBoxLayout for side-by-side
        k_sub_layout.addWidget(self.kx_spin)
        k_sub_layout.addWidget(self.ky_spin)
        k_sub_layout.addWidget(self.kz_spin)
        grid.addLayout(k_sub_layout, 1, 1) # Add the QHBoxLayout to the grid


        # ISMEAR
        grid.addWidget(QLabel("ISMEAR:"), 2, 0)
        self.ismear_combo = QComboBox()
        self.ismear_combo.addItems([
            "-5 (Tetrahedron method with Blochl corrections)",
            "0 (Gaussian smearing)", 
            "1 (Methfessel-Paxton order 1)",
            "2 (Methfessel-Paxton order 2)"
        ])
        self.ismear_combo.setCurrentIndex(1) # Default to Gaussian
        grid.addWidget(self.ismear_combo, 2, 1)
        
        # SIGMA
        grid.addWidget(QLabel("SIGMA (eV):"), 3, 0)
        self.sigma_spinbox = QDoubleSpinBox()
        self.sigma_spinbox.setRange(0.01, 1.0)
        self.sigma_spinbox.setValue(0.05)
        self.sigma_spinbox.setSingleStep(0.01)
        grid.addWidget(self.sigma_spinbox, 3, 1)

        self.layout.addLayout(grid)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_scf_parameters(self):
        ismear_text = self.ismear_combo.currentText()
        ismear_value = int(ismear_text.split(" ")[0]) # Extract the numeric value

        return {
            "ENCUT": self.encut_spinbox.value(),
            "KPOINTS_TUPLE": (self.kx_spin.value(), self.ky_spin.value(), self.kz_spin.value()),
            "ISMEAR": ismear_value,
            "SIGMA": self.sigma_spinbox.value(),
            "EXTRA_INCAR_PARAMS": { 
                # "NSW": 0, # Already set in generator for SCF
                # "IBRION": -1, # Already set in generator for SCF
            }
        }

    @staticmethod
    def show_dialog(parent=None):
        dialog = ScfParamsDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_scf_parameters()
        return None
