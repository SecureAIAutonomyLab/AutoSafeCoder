from utils import call_chatgpt_fuzzer,fuzz_function

class InputMutatorAgent:
    def __init__(self, inputs, funname, code):
        self.inputs = inputs
        self.code = code
        self.funname = funname

    def mutate_inputs(self):
        
        mutated_inputs = fuzz_function(self.inputs,self.code,self.funname)
        return mutated_inputs
