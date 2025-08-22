import unittest
from workflow_engine.workflow.workflow import Workflow
from workflow_engine.workflow.step import Step
from workflow_engine.workflow.engine import Engine

class PrintStep(Step):
    def __init__(self, name, message):
        super().__init__(name)
        self.message = message

    def execute(self, context):
        print(self.message)
        context[self.name] = self.message

class TestWorkflow(unittest.TestCase):
    def test_workflow(self):
        # Create a workflow
        workflow = Workflow("Test Workflow")

        # Add steps to the workflow
        workflow.add_step(PrintStep("step1", "Hello from step 1"))
        workflow.add_step(PrintStep("step2", "Hello from step 2"))

        # Run the workflow
        engine = Engine()
        context = engine.run(workflow)

        # Check the context
        self.assertEqual(context["step1"], "Hello from step 1")
        self.assertEqual(context["step2"], "Hello from step 2")

if __name__ == '__main__':
    unittest.main()
