import os
import base64
from flask import Flask, render_template_string
from database import get_user_products
#from dotenv import load_dotenv

#load_dotenv()

app = Flask(__name__)

@app.route("/public/<mobile>")
def public_page(mobile):
    products = get_user_products(mobile)
    html = f"<h1>Products by {mobile}</h1>"
    for product in products:
        html += f"""
            <h2>{product['product_name_en'] or product['product_name']}</h2>
            <p>Material: {product['material_en'] or product['material']}</p>
            <p>Description: {product['description_en'] or product['description']}</p>
            <p>Price: {product['price_en'] or product['price']}</p>
            <p>Tags: {product['tags_en'] or product['tags']}</p>
        """
        for img_path in product['image_paths']:
            if os.path.exists(img_path):
                with open(img_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode("utf-8")
                    html += f'<img src="data:image/jpeg;base64,{img_data}" width="200"><br>'
            else:
                html += f"<p>Error: Image not found at {img_path}</p>"
        html += "<hr>"
    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True, port=5000)