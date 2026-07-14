import logging
import ollama

def query_local_assistant(system_prompt: str, user_content: str, model_name: str = "llama3") -> str:
    """Executes a structured chat completion request to a local Ollama instance."""
    
    logging.info(f"Initiating inference request to local model: {model_name}")
    
    response = ollama.chat(
        model=model_name,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content},
        ],
        options={
            'temperature': 0.2,  # Constrain decoding temperature to minimize hallucination
            'num_predict': 5000,  # Allow longer outputs
        }
    )
    
    logging.info("Successfully generated inference response.")
    
    return response['message']['content']