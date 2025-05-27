# molecular_simulator/molecular_simulator/gui/dialogs/geo_opt_params_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QHBoxLayout # Ensure QHBoxLayout is imported
)

class GeoOptParamsDialog(QDialog):
    def __init__(self, parent=None, initial_params: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Geometry Optimization Parameters (VASP)")
        self.layout = QVBoxLayout(self)
        grid = QGridLayout()

        # IBRION
        grid.addWidget(QLabel("IBRION:"), 0, 0)
        self.ibrion_combo = QComboBox()
        self.ibrion_options = { # Text: Value
            "1 (Ionic relaxation - RMM-DIIS)": 1,
            "2 (Ionic relaxation - CG)": 2, # Often recommended
            "3 (Ionic relaxation - Damped MD)": 3,
        }
        self.ibrion_combo.addItems(self.ibrion_options.keys())
        grid.addWidget(self.ibrion_combo, 0, 1)

        # NSW
        grid.addWidget(QLabel("NSW (Max Ionic Steps):"), 1, 0)
        self.nsw_spinbox = QSpinBox()
        self.nsw_spinbox.setRange(0, 10000)
        self.nsw_spinbox.setSingleStep(10)
        grid.addWidget(self.nsw_spinbox, 1, 1)

        # EDIFFG (Convergence for forces)
        grid.addWidget(QLabel("EDIFFG (e.g., -0.01 eV/Å):"), 2, 0)
        self.ediffg_edit = QLineEdit() # String to allow negative scientific notation
        grid.addWidget(self.ediffg_edit, 2, 1)

        # POTIM (Ionic step size, for IBRION=1,2,3)
        grid.addWidget(QLabel("POTIM (step size for IBRION 1,2,3):"), 3, 0)
        self.potim_spinbox = QDoubleSpinBox()
        self.potim_spinbox.setRange(0.001, 5.0)
        self.potim_spinbox.setSingleStep(0.01)
        self.potim_spinbox.setDecimals(3)
        grid.addWidget(self.potim_spinbox, 3, 1)
        
        # ENCUT, KPOINTS, ISMEAR, SIGMA (can reuse from SCF or set independently)
        grid.addWidget(QLabel("--- Electronic Step Parameters ---"), 4, 0, 1, 2) # Span 2 columns

        grid.addWidget(QLabel("ENCUT (eV):"), 5, 0)
        self.encut_spinbox = QDoubleSpinBox()
        self.encut_spinbox.setRange(100, 2000); self.encut_spinbox.setSingleStep(50)
        grid.addWidget(self.encut_spinbox, 5, 1)

        grid.addWidget(QLabel("K-points (Kx Ky Kz):"), 6, 0)
        self.kx_spin = QSpinBox(); self.kx_spin.setRange(1, 20)
        self.ky_spin = QSpinBox(); self.ky_spin.setRange(1, 20)
        self.kz_spin = QSpinBox(); self.kz_spin.setRange(1, 20)
        k_sub_layout = QHBoxLayout()
        k_sub_layout.addWidget(self.kx_spin); k_sub_layout.addWidget(self.ky_spin); k_sub_layout.addWidget(self.kz_spin)
        grid.addLayout(k_sub_layout, 6, 1)

        grid.addWidget(QLabel("ISMEAR:"), 7, 0)
        self.ismear_combo = QComboBox()
        self.scf_ismear_options = {
            "-5 (Tetrahedron method with Blochl corrections)": -5,
            "0 (Gaussian smearing)": 0, 
            "1 (Methfessel-Paxton order 1)": 1,
        }
        self.ismear_combo.addItems(self.scf_ismear_options.keys())
        grid.addWidget(self.ismear_combo, 7, 1)
        
        grid.addWidget(QLabel("SIGMA (eV):"), 8, 0)
        self.sigma_spinbox = QDoubleSpinBox()
        self.sigma_spinbox.setRange(0.01, 1.0); self.sigma_spinbox.setSingleStep(0.01)
        grid.addWidget(self.sigma_spinbox, 8, 1)

        self._set_initial_params(initial_params) # Call to pre-fill

        self.layout.addLayout(grid)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def _set_initial_params(self, params: dict):
        if not params: params = {}
        
        ibrion_val_to_set = params.get("IBRION", 2) 
        for text, val in self.ibrion_options.items():
            if val == ibrion_val_to_set: self.ibrion_combo.setCurrentText(text); break
        else: self.ibrion_combo.setCurrentIndex(1) 

        self.nsw_spinbox.setValue(params.get("NSW", 200))
        self.ediffg_edit.setText(str(params.get("EDIFFG", "-0.01")))
        self.potim_spinbox.setValue(params.get("POTIM", 0.2))

        self.encut_spinbox.setValue(params.get("ENCUT", 400))
        kpoints = params.get("KPOINTS_TUPLE", (3,3,3))
        self.kx_spin.setValue(kpoints[0]); self.ky_spin.setValue(kpoints[1]); self.kz_spin.setValue(kpoints[2])
        
        scf_ismear_val_to_set = params.get("ISMEAR", 0) 
        for text, val in self.scf_ismear_options.items():
            if val == scf_ismear_val_to_set: self.ismear_combo.setCurrentText(text); break
        else: self.ismear_combo.setCurrentIndex(1)

        self.sigma_spinbox.setValue(params.get("SIGMA", 0.05))


    def get_geo_opt_parameters(self):
        selected_ibrion_text = self.ibrion_combo.currentText()
        ibrion_value = self.ibrion_options.get(selected_ibrion_text, 2) 

        ediffg_str = self.ediffg_edit.text().strip()
        try:
            float(ediffg_str) 
        except ValueError:
            QMessageBox.warning(self, "Input Error", "EDIFFG must be a valid number (e.g., -0.01 or 1e-2).")
            return None
        
        selected_scf_ismear_text = self.ismear_combo.currentText()
        scf_ismear_value = self.scf_ismear_options.get(selected_scf_ismear_text, 0)

        return {
            "IBRION": ibrion_value,
            "NSW": self.nsw_spinbox.value(),
            "EDIFFG": ediffg_str, 
            "POTIM": self.potim_spinbox.value(),
            "ENCUT": self.encut_spinbox.value(),
            "KPOINTS_TUPLE": (self.kx_spin.value(), self.ky_spin.value(), self.kz_spin.value()),
            "ISMEAR": scf_ismear_value, 
            "SIGMA": self.sigma_spinbox.value(),
            "EXTRA_INCAR_PARAMS": {} 
        }

    @staticmethod
    def show_dialog(parent=None, initial_params: dict = None):
        dialog = GeoOptParamsDialog(parent, initial_params)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_geo_opt_parameters()
        return None
