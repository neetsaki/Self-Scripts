# molecular_simulator/molecular_simulator/main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from .gui.main_window import MainWindow
from ase.build import molecule as ase_molecule_builder 

# Function to load stylesheet
def load_stylesheet(app_root_dir):
    # Path assumes style.qss is in molecular_simulator/gui/
    # Relative to the 'molecular_simulator' package directory, which is 'package_dir' in main()
    # Correct path construction should be based on the location of the gui package.
    # If main.py is in molecular_simulator/molecular_simulator/main.py
    # and style.qss is in molecular_simulator/molecular_simulator/gui/style.qss
    # then the path from package_dir (which is molecular_simulator/molecular_simulator/) is just "gui/style.qss"

    # Let's adjust path based on where main.py is and where style.qss is.
    # main.py is in project_root/molecular_simulator/molecular_simulator/main.py
    # style.qss is in project_root/molecular_simulator/molecular_simulator/gui/style.qss
    # So, from script_dir (which is project_root/molecular_simulator/molecular_simulator/), it's "gui/style.qss"
    
    script_dir = os.path.dirname(os.path.abspath(__file__)) # dir of main.py
    style_file_path = os.path.join(script_dir, "gui", "style.qss")
    
    try:
        with open(style_file_path, "r") as f:
            print(f"Loading stylesheet from: {style_file_path}")
            return f.read()
    except FileNotFoundError:
        print(f"Stylesheet {style_file_path} not found. Using default style.")
        # Try an alternative path if project_root was meant differently
        # package_dir = os.path.dirname(script_dir) # molecular_simulator/
        # project_root = os.path.dirname(package_dir) # project_root_level/
        # alt_style_path = os.path.join(project_root, "molecular_simulator", "gui", "style.qss")
        # print(f"Attempting alternative stylesheet path: {alt_style_path}")
        # try:
        #     with open(alt_style_path, "r") as f:
        #         print(f"Loading stylesheet from: {alt_style_path}")
        #         return f.read()
        # except FileNotFoundError:
        #     print(f"Alternative stylesheet {alt_style_path} also not found.")
        return "" # Return empty string if not found
    except Exception as e:
        print(f"Error loading stylesheet {style_file_path}: {e}")
        return ""


def main():
    app = QApplication(sys.argv)
    
    # Determine project root directory to reliably find other files
    script_path = os.path.abspath(__file__) 
    script_dir = os.path.dirname(script_path) 
    # package_dir = os.path.dirname(script_dir) 
    # project_root = os.path.dirname(package_dir)

    # Load and apply stylesheet (using script_dir as base for gui/style.qss)
    stylesheet = load_stylesheet(script_dir) # Pass script_dir
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        print("No stylesheet loaded, application will use default Qt styling.")


    window = MainWindow() # MainWindow initialization AFTER stylesheet is set
    
    # --- File loading logic from previous steps ---
    file_to_load = None
    # project_root is needed for resolving relative paths from project root for input files
    # For data/H2O.xyz, it's project_root/data/H2O.xyz
    # Let's define project_root relative to script_dir
    # script_dir = .../molecular_simulator/molecular_simulator
    # package_dir (parent of molecular_simulator module) = .../molecular_simulator
    # project_root_for_data = parent of package_dir = .../ (the top level dir)
    # This matches the previous project_root calculation.
    true_package_dir = os.path.dirname(script_dir) 
    project_root_for_data = os.path.dirname(true_package_dir)


    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.isabs(input_path):
            if os.path.exists(input_path): file_to_load = input_path
            else: print(f"Error: Absolute path specified but file not found: {input_path}")
        else: 
            if os.path.exists(input_path): file_to_load = input_path # Relative to CWD
            else: # Try relative to project root
                path_from_root = os.path.join(project_root_for_data, input_path)
                if os.path.exists(path_from_root): file_to_load = path_from_root
                else: print(f"Error: Relative path '{input_path}' not found in CWD or project root '{project_root_for_data}'.")
    else: 
        default_file_path = os.path.join(project_root_for_data, "data", "H2O.xyz")
        print(f"No file argument, attempting to load default: {default_file_path}")
        if os.path.exists(default_file_path): file_to_load = default_file_path
        else: print(f"Default file '{default_file_path}' not found.")

    if file_to_load:
        print(f"Loading molecule from: {file_to_load}")
        window.load_molecule_from_file(file_to_load)
    else:
        print("No file loaded. Showing a default H2O molecule built with ASE.")
        fallback_molecule = ase_molecule_builder('H2O')
        if window.viewer_widget: 
             window.viewer_widget.show_molecule(fallback_molecule)
        else: 
             print("Error: viewer_widget not initialized in MainWindow before showing molecule.")


    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
