import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv("env.env")

client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    token=os.getenv("HF_TOKEN")
)

async def ask_llama_validator(system_prompt: str, user_message: str):
    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error en Hugging Face: {e}")
        return "ERROR"