# content_generator.py
import base64
import requests
import os
from openai import OpenAI

def encode_image(image_path):
    """Encode an image file to base64 for API requests."""
    print(f"Attempting to encode image: {image_path}")
    print(f"Does image file exist? {os.path.exists(image_path)}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def call_llm(prompt):
    client = OpenAI(api_key="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")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

def get_structured_content(description, image_paths, lang="en"):
    """
    Generate structured content for a product listing using the description and images.ca
    Returns listing in the specified language and includes English translations for all fields.
    """
    language_map = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "mr": "Marathi",
        "bn": "Bengali",
        "gu": "Gujarati"
    }
    target_language = language_map.get(lang, "English")

    prompt = f"""
    You are an expert in generating product listings. Based on the following product description and images, create a structured product listing with the following fields:
    - Product Name
    - Material
    - Description
    - Price
    - Tags

    The description provided is: "{description}"

    The product has {len(image_paths)} images associated with it.

    **Important**: 
    1. Generate the response in {target_language}. Ensure all text (including field names and values) is in {target_language}.
    2. Provide English translations for all fields, labeled as '<Field> (English)' (e.g., 'Product Name (English)').

    Format the response as:
    Product Name: <name>
    Product Name (English): <name_en>
    Material: <material>
    Material (English): <material_en>
    Description: <description>
    Description (English): <description_en>
    Price: <price>
    Price (English): <price_en>
    Tags: <tags>
    Tags (English): <tags_en>
    """

    response = call_llm(prompt)
    print(response)

    listing = {}
    for line in response.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            listing[key.strip()] = value.strip()

    return {
        "product_name": listing.get("Product Name", ""),
        "product_name_en": listing.get("Product Name (English)", listing.get("Product Name", "")),
        "material": listing.get("Material", ""),
        "material_en": listing.get("Material (English)", listing.get("Material", "")),
        "description": listing.get("Description", ""),
        "description_en": listing.get("Description (English)", listing.get("Description", "")),
        "price": listing.get("Price", ""),
        "price_en": listing.get("Price (English)", listing.get("Price", "")),
        "tags": listing.get("Tags", ""),
        "tags_en": listing.get("Tags (English)", listing.get("Tags", ""))
    }