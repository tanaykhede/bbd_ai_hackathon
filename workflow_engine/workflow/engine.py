from .workflow import Workflow

class Engine:
    """
    The workflow engine.
    """
    def __init__(self):
        pass

    def run(self, workflow: Workflow):
        """
        Runs the workflow.
        """
        context = {}
        for step in workflow.steps:
            print(f"Executing step: {step.name}")
            step.execute(context)
        return context
