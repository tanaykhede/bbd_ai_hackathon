from .step import Step

class Workflow:
    """
    Represents a workflow.
    """
    def __init__(self, name):
        self.name = name
        self.steps = []

    def add_step(self, step: Step):
        """
        Adds a step to the workflow.
        """
        self.steps.append(step)
