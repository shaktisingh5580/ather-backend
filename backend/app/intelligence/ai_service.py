import os
import requests
import base64
from openai import OpenAI

# 1. SETUP: OPENROUTER (The Brain)
# Get Key: https://openrouter.ai/keys
OR_CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"), 
)

# 2. SETUP: HUGGING FACE (The Painter)
# Get Key: https://huggingface.co/settings/tokens
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

def analyze_image_context(image_bytes):
    """
    Uses OpenRouter (Gemini Free) to look at an image and describe it.
    Useful for 'Semantic Search' (e.g., finding all 'construction sites').
    """
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    response = OR_CLIENT.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free", # <--- FREE MODEL
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image? Answer in 1 sentence."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content

def generate_inpainting(original_bytes, mask_bytes, prompt):
    """
    Uses Hugging Face Free API to surgically replace the masked area.
    """
    # 1. Encode images for the API
    # Note: HF Inpainting API expects base64 inputs in a specific JSON structure
    # or multipart upload. For stability, we often use the 'inputs' payload format.
    
    encoded_orig = base64.b64encode(original_bytes).decode("utf-8")
    encoded_mask = base64.b64encode(mask_bytes).decode("utf-8")

    payload = {
        "inputs": prompt,
        "image": encoded_orig,
        "mask_image": encoded_mask,
        "parameters": {
            "num_inference_steps": 25, # Fast generation
            "strength": 0.8,           # 80% change, 20% original structure
            "guidance_scale": 7.5
        }
    }

    response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload)
    
    if response.status_code != 200:
        # Fallback: If HF fails, return original (prevents crash)
        print(f"HF Error: {response.text}")
        return original_bytes
        
    return response.content