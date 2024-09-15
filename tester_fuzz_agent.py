import json
from executor_agent_safe import remove_json_prefix
from utils import call_chatgpt_fuzzing_tester

class TesterFuzzAgent:
    def __init__(self, entry):
        self.entry = entry

    def generate_test_inputs(self):
        prompt = self.entry['Prompt']
        result = False
        for i in range(3):
            inputs = call_chatgpt_fuzzing_tester(prompt)
            inputs = remove_json_prefix(inputs)
            try:
                json_inputs = json.loads(inputs)
                result = True
                break
            except:
                continue
        
        if result:
            return json_inputs
        else:
            return {}
