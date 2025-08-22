from abc import ABC, abstractmethod

class Step(ABC):
    """
    Represents a single step in a workflow.
    """
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def execute(self, context):
        """
        Executes the step.
        """
        pass
