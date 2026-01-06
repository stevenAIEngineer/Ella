import os
import base64
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

from dotenv import load_dotenv

# Load env structure
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version="v1alpha")
)

# Create 3 dummy images (800x800)
def make_img(color):
    img = Image.new('RGB', (800, 800), color=color)
    return img

img1 = make_img('red')
img2 = make_img('green')
img3 = make_img('blue')

prompt = "STRICT INSTRUCTION: Generate a high-fashion photograph. Image 1 is model, Image 2 is apparel, Image 3 is location."

print("\n--- Test 3: Text + 3 Large Images ---")
try:
    contents = [prompt, img1, img2, img3]
    response = client.models.generate_content(
        model='gemini-3-pro-image-preview',
        contents=contents
    )
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
