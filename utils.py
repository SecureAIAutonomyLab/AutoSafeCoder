import openai
import random
import string
import types
from copy import deepcopy
import ast
import json
from copy import deepcopy

# Setting API parameters
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = 'YOUR-API-KEY-HERE'
#model="gpt-3.5-turbo-1106"
model="gpt-4o"

prompt_path = "./prompts_fewshot/coder_agent_prompt.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()
        
prompt_path_fuzz= "./prompts_fewshot/initial_inputs_prompt.txt"
with open(prompt_path_fuzz, "r") as f:
    construct_few_shot_prompt_fuzz = f.read()
    
def preprocess_string(input_string, lg):
    if f"```{lg}" in input_string:
        input_string = input_string[input_string.find(f"```{lg}") + len(f"```{lg}"):]
        input_string = input_string[:input_string.find("```")]
    elif "```" in input_string:
        input_string = input_string[input_string.find("```") + 3:]
        input_string = input_string[:input_string.find("```")]
    
    return input_string

def call_chatgpt_programmer(prompt):
    text = f"""
    {construct_few_shot_prompt}

    **Input Code Snippet**:
    ```python
    {prompt}
    ```
    ## Completion 3:
    """
    completions_code = []
    try:
        completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a software programmer."},
        {"role": "user", "content":text},
            ]
        )
        completion = completion.choices[0].message.content.strip()               
        completion = preprocess_string(completion,"python")

    except Exception as e:
        print(e)
        completion = ""
        
    return completion

def call_chatgpt_analyze_static_security(completion):
    
    lg="python"
    gpt_prompt = (
            "Please analyze the following code and detect if it has code vulnerabilities only from the main CWE codes. Answer only with the CWE code and a brief sentence with a suggestion for its fix.\n"+
            "If there are no code vulnerabilities detected answer only with 'no vulnerabilities detected'."
            f"\nCode:\n```{lg}\n" + 
            completion + f"\n```\n\n"
    )
    try:
        new_completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code security analyzer assistant."},
        {"role": "user", "content":gpt_prompt},
            ]
        )
        new_completion = new_completion.choices[0].message.content.strip()               
        new_completion = preprocess_string(new_completion,"python")

    except Exception as e:
        print(e)
        new_completion = ""
        
    return new_completion

def call_chatgpt_programmer_feedback_static(completion,entry, cwe_code, issue_text):
    
    lg="python"
    if issue_text:
        gpt_prompt = (
                "Please modify the code to fix the following security vulnerability. "+
                f"\nHere is the code that has been detected to have a security vulnerability:\n```{lg}\n" + 
                completion + 
                f"\n```\nThe CWE code and details of the vulnerability detected are the following:\n {cwe_code} - {issue_text}" +
                f"\n```\nPlease modify the code so that it does not have any security vulnerability. The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
        )
    else:
        gpt_prompt = (
                "Please modify the code to fix the following security vulnerability. "+
                f"\nHere is the code that has been detected to have a security vulnerability:\n```{lg}\n" + 
                completion + 
                f"\n```\nThe CWE code and details of the vulnerability detected are the following:\n {cwe_code}" +
                f"\n```\nPlease modify the code so that it does not have any security vulnerability but keeps main functionality. The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
        )
    try:
        completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code developer assistant."},
        {"role": "user", "content":gpt_prompt},
            ]
        )
        completion = completion.choices[0].message.content.strip()               
        completion = preprocess_string(completion,"python")

    except Exception as e:
        print(e)
        completion = ""
        
    return completion

def call_chatgpt_programmer_feedback_fuzzing(completion,entry,inputs):
    
    output_string = ""
    for entry in inputs:
        output_string += f"{entry['inputs']}: {entry['result']}\n"
    
    lg="python"
    gpt_prompt = (
            "Please re-completion the code to fix the error message. "+
            f"\nHere is the previous version:\n```{lg}\n" + 
            completion + 
            f"\n```\nWhen calling the function with the following inputs, it raises errors. The inputs and errors are the following:\n" +
            output_string +
            f"\n```\nPlease fix the bugs and return the code. The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
    )
    try:
        completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code developer assistant."},
        {"role": "user", "content":gpt_prompt},
            ]
        )
        completion = completion.choices[0].message.content.strip()               
        completion = preprocess_string(completion,"python")

    except Exception as e:
        print(e)
        completion = ""
        
    return completion

def call_chatgpt_fuzzing_tester(prompt):
    text = f"""
    {construct_few_shot_prompt_fuzz}

    ## Prompt 2:
    ```python
    {prompt}
    ```
    ## Completion 2:
    """
    try:
        completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code tester specialized in fuzzing."},
        {"role": "user", "content":text},
            ]
        )
        completion = completion.choices[0].message.content.strip()               
        completion = preprocess_string(completion,"python")

    except Exception as e:
        print(e)
        completion = ""
        
    return completion

def call_chatgpt_fuzzer(prompt):
    try:
        text = f"""
    **Role**: As a tester, your task is to create mutated inputs for fuzzing testing. 

    **Instructions**:
    - Please create a mutated inputs that modifies the previous input generation
    - The format should only be a JSON string.For example:{"input1": [1.0], "input2": 1.0}
    
    ## Previous Input Generation: 
    {prompt}
    """
    
        completion = openai.chat.completions.create(
            model=model,
            stream=False,
            messages=[
        {"role": "system", "content": "You are a code tester specialized in fuzzing."},
        {"role": "user", "content":text},
            ]
        )
        completion = completion.choices[0].message.content.strip()               
        completion = preprocess_string(completion,"python")

    except Exception as e:
        print(e)
        completion = ""
        
    return completion

def mutate_value(value):
    """Mutates a single value based on its type."""
    if isinstance(value, bool):
        # Randomly flip the boolean value with a 50% chance
        return value if random.random() > 0.5 else not value
    if isinstance(value, int):
        # Mutate integers by adding or subtracting a random number
        return value + random.randint(-1000, 1000)
    elif isinstance(value, float):
        # Mutate floats by adding or subtracting a random float
        return value + random.uniform(-1000.0, 1000.0)
    elif isinstance(value, str):
        # Mutate strings by shuffling, adding random characters, or removing characters
        if len(value) == 0:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 20)))
        mutation_type = random.choice(['shuffle', 'add', 'remove'])
        if mutation_type == 'shuffle':
            return ''.join(random.sample(value, len(value)))
        elif mutation_type == 'add':
            position = random.randint(0, len(value))
            return value[:position] + random.choice(string.ascii_letters + string.digits) + value[position:]
        elif mutation_type == 'remove' and len(value) > 1:
            position = random.randint(0, len(value)-1)
            return value[:position] + value[position+1:]
        else:
            return value
    elif isinstance(value, list):
        # Mutate all elements in the list
        return [mutate_value(element) for element in value]
    elif isinstance(value, dict):
        # Mutate dictionaries by mutating keys or values, adding or removing key-value pairs
        if len(value) == 0:
            return {mutate_value(''): mutate_value('')}  # Add a new random key-value pair if dict is empty
        mutation_type = random.choice(['mutate_key', 'mutate_value', 'add', 'remove'])
        if mutation_type == 'mutate_key':
            old_key = random.choice(list(value.keys()))
            new_key = mutate_value(old_key)
            value[new_key] = value.pop(old_key)
        elif mutation_type == 'mutate_value':
            key = random.choice(list(value.keys()))
            value[key] = mutate_value(value[key])
        elif mutation_type == 'add':
            value[mutate_value('')] = mutate_value('')
        elif mutation_type == 'remove' and len(value) > 1:
            key = random.choice(list(value.keys()))
            del value[key]
        return value
    else:
        return value  # For unsupported types, return the value as is

def mutate_inputs(inputs):
    """Mutates the contents of the dynamic `inputs` object."""
    mutated_inputs = {}
    try: 
        
        for key, value in inputs.items():
            mutated_inputs[key] = mutate_value(deepcopy(value))
        
    except AttributeError as e:
        print(f"Error: {e}. The `inputs` object is not a dictionary.")
        if isinstance(inputs, list):
            inputs = {i: item for i, item in enumerate(inputs)}
            for key, value in inputs.items():
                mutated_inputs[key] = mutate_value(deepcopy(value))

    return mutated_inputs

def fuzz_function(inputs,code,funname, num_tests=1):
    """Generates fuzzed inputs and runs the function with them."""
     # Extract and mutate the inputs
    return mutate_inputs(inputs)
