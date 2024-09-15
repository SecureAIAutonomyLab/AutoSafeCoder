from utils import call_chatgpt_programmer, call_chatgpt_programmer_feedback_fuzzing, call_chatgpt_programmer_feedback_static

class ProgrammerAgent:
    def __init__(self, entry):
        self.entry = entry

    def write_code(self):
        prompt = f"Create a python function that follows the following code requirements: {self.entry['Prompt']}"
        code = call_chatgpt_programmer(prompt)
        return code
    def write_code_feedback_static(self,completion,cwe_code, issue_text):
        code = call_chatgpt_programmer_feedback_static(completion,self.entry, cwe_code, issue_text)
        return code
    def write_code_feedback_fuzz(self,completion,inputs):
        code = call_chatgpt_programmer_feedback_fuzzing(completion,self.entry,inputs)
        return code
