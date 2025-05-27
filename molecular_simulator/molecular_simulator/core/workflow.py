# molecular_simulator/molecular_simulator/core/workflow.py

class CalculationModule:
    def __init__(self, module_type: str, name: str, parameters: dict = None):
        self.module_type = module_type  # e.g., "SCF", "GEO_OPT"
        self.name = name                # User-defined or default name
        self.parameters = parameters if parameters is not None else {}
        # For future: self.connections_to = [] # List of other module names/ids

    def __repr__(self):
        return f"Module(type='{self.module_type}', name='{self.name}', params={self.parameters})"

class Workflow:
    def __init__(self, name: str = "DefaultWorkflow"):
        self.name = name
        self.modules: list[CalculationModule] = []
        # For now, a simple linear list of modules. Later, this could be a graph.

    def add_module(self, module: CalculationModule):
        self.modules.append(module)

    def __repr__(self):
        return f"Workflow(name='{self.name}', modules={self.modules})"
