import streamlit as st
import sqlite3
import random
import requests
from voice_processor import get_product_description
from content_generator import get_structured_content
from database import init_db, add_user, get_user_products, get_user
from dotenv import load_dotenv
from PIL import Image, ImageEnhance
import os
import io
from translations import LANGUAGES, get_text  # Import from translations.py
from ui_components import (
    render_header, render_image_upload, render_record_description,
    render_generated_listing, render_listed_products, #render_share_listings,
    render_manage_listings, render_listed_products_container, render_login_form, 
)

load_dotenv()
# Load the .env file from the credentials folder
load_dotenv(dotenv_path=os.path.expanduser("~/Desktop/credentials/voice_listing/.env"))

# Initialize database
init_db()

# Custom function to add a product and get its ID
def add_product_with_id(user_mobile, product_details, image_paths):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO products (user_mobile, product_name, product_name_en, material, material_en, 
                             description, description_en, price, price_en, tags, tags_en, image_paths)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_mobile, product_details["product_name"], product_details["product_name_en"],
          product_details["material"], product_details["material_en"],
          product_details["description"], product_details["description_en"],
          product_details["price"], product_details["price_en"],
          product_details["tags"], product_details["tags_en"],
          ",".join(image_paths)))
    product_id = c.lastrowid
    conn.commit()
    conn.close()
    return product_id

# Custom function to update a product
def update_product(product_id, product_details, image_paths):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    existing_product = c.fetchone()
    
    updated_values = {
        "product_name": product_details.get("product_name", existing_product[2]),
        "product_name_en": product_details.get("product_name_en", existing_product[3]),
        "material": product_details.get("material", existing_product[4]),
        "material_en": product_details.get("material_en", existing_product[5]),
        "description": product_details.get("description", existing_product[6]),
        "description_en": product_details.get("description_en", existing_product[7]),
        "price": product_details.get("price", existing_product[8]),
        "price_en": product_details.get("price_en", existing_product[9]),
        "tags": product_details.get("tags", existing_product[10]),
        "tags_en": product_details.get("tags_en", existing_product[11]),
        "image_paths": ",".join(image_paths) if image_paths else existing_product[12],
        "created_at": existing_product[13]  # Preserve created_at
    }
    
    c.execute("""
        UPDATE products
        SET product_name = ?, product_name_en = ?, material = ?, material_en = ?, 
            description = ?, description_en = ?, price = ?, price_en = ?, tags = ?, tags_en = ?, 
            image_paths = ?, created_at = ?
        WHERE id = ?
    """, (updated_values["product_name"], updated_values["product_name_en"],
          updated_values["material"], updated_values["material_en"],
          updated_values["description"], updated_values["description_en"],
          updated_values["price"], updated_values["price_en"],
          updated_values["tags"], updated_values["tags_en"],
          updated_values["image_paths"], updated_values["created_at"], product_id))
    conn.commit()
    conn.close()

# Custom function to delete a product
def delete_product(product_id):
    conn = sqlite3.connect("listings.db")
    c = conn.cursor()
    # Get image paths to delete files
    c.execute("SELECT image_paths FROM products WHERE id = ?", (product_id,))
    image_paths = c.fetchone()[0].split(",")
    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)
    # Delete product from database
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

# Function to refine images
def refine_images(uploaded_files, user_mobile, product_counter):
    lang = st.session_state.get("selected_language", "en")
    refined_image_paths = []
    # Retrieve the API key from the environment variable
    api_key = os.getenv("REMOVE_BG_API_KEY")
    for i, uploaded_file in enumerate(uploaded_files):
        input_image = Image.open(uploaded_file)
        api_url = "https://api.remove.bg/v1.0/removebg"
        headers = {"X-Api-Key": api_key}
        files = {"image_file": uploaded_file.getvalue()}

        response = requests.post(api_url, headers=headers, files=files)
        if response.status_code == 200:
            refined_image = Image.open(io.BytesIO(response.content))
            brightness_enhancer = ImageEnhance.Brightness(refined_image)
            refined_image = brightness_enhancer.enhance(1.2)
            contrast_enhancer = ImageEnhance.Contrast(refined_image)
            refined_image = contrast_enhancer.enhance(1.3)
            if refined_image.mode == "RGBA":
                refined_image = refined_image.convert("RGB")

            output_dir = f"output/{user_mobile}/{product_counter}"
            os.makedirs(output_dir, exist_ok=True)
            final_path = os.path.join(output_dir, f"product_{product_counter}_image_{i}.jpg")
            refined_image.save(final_path, "JPEG")
            refined_image_paths.append(final_path)
        else:
            st.error(get_text("api_error", lang, index=i+1, status=response.status_code, text=response.text))
            return []
    return refined_image_paths

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "mobile" not in st.session_state:
    st.session_state.mobile = None
if "otp" not in st.session_state:
    st.session_state.otp = None
if "show_verify" not in st.session_state:
    st.session_state.show_verify = False
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "description" not in st.session_state:
    st.session_state.description = None
if "product_counter" not in st.session_state:
    st.session_state.product_counter = 0
if "edit_product_id" not in st.session_state:
    st.session_state.edit_product_id = None
if "generated_listing" not in st.session_state:
    st.session_state.generated_listing = None
if "refined_image_paths" not in st.session_state:
    st.session_state.refined_image_paths = []
if "page" not in st.session_state:
    st.session_state.page = "main"
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "en"  # Default to English
if "previous_uploaded_files" not in st.session_state:
    st.session_state.previous_uploaded_files = None

def login_page():
    lang = st.session_state.selected_language

    # Initialize session state variables
    if "language_proceeded" not in st.session_state:
        st.session_state.language_proceeded = False
    if "otp_generated" not in st.session_state:
        st.session_state.otp_generated = False
    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False
    if "name_input_step" not in st.session_state:
        st.session_state.name_input_step = False
    if "temp_first_name" not in st.session_state:
        st.session_state.temp_first_name = ""
    if "temp_last_name" not in st.session_state:
        st.session_state.temp_last_name = ""

    # Language selection
    st.subheader(get_text("select_language", lang))
    current_language = [k for k, v in LANGUAGES.items() if v == lang][0]
    selected_language = st.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(current_language),
        key="language_selectbox"
    )

    if selected_language and LANGUAGES[selected_language] != st.session_state.selected_language:
        st.session_state.selected_language = LANGUAGES[selected_language]
        st.rerun()

    lang = st.session_state.selected_language

    if not st.session_state.language_proceeded:
        if st.button(get_text("proceed", lang)):
            st.session_state.language_proceeded = True
            st.rerun()
    else:
        # Skip login form if already logged in
        if st.session_state.logged_in:
            return

        # If we're in the name input step, skip the login form and go straight to name input
        if st.session_state.name_input_step:
            st.markdown("---")
            st.markdown(
                f"<h3 style='font-size: 20px; font-weight: bold; color: #1E90FF;'>{get_text('new_user_info', lang)}</h3>",
                unsafe_allow_html=True
            )
            with st.form(key="name_input_form"):
                st.session_state.temp_first_name = st.text_input(
                    get_text("first_name_label", lang),
                    value=st.session_state.temp_first_name,
                    placeholder=get_text("first_name_placeholder", lang)
                )
                st.session_state.temp_last_name = st.text_input(
                    get_text("last_name_label", lang),
                    value=st.session_state.temp_last_name,
                    placeholder=get_text("last_name_placeholder", lang)
                )
                submit_names_clicked = st.form_submit_button(get_text("submit_names", lang))

                if submit_names_clicked:
                    if st.session_state.temp_first_name and st.session_state.temp_last_name:
                        add_user(st.session_state.mobile, st.session_state.temp_first_name, st.session_state.temp_last_name)
                        st.session_state.logged_in = True
                        st.session_state.show_verify = False
                        st.session_state.otp_generated = False
                        st.session_state.otp_verified = False
                        st.session_state.name_input_step = False
                        st.session_state.temp_first_name = ""
                        st.session_state.temp_last_name = ""
                        st.success(get_text("logged_in_success", lang))
                        st.rerun()
                    else:
                        st.error(get_text("name_required", lang))
            return

        # Render the login form and get user inputs
        form_data = render_login_form(
            lang=lang,
            mobile=st.session_state.get("mobile", None),
            user_exists=True,  # We'll check existence later, after OTP verification
            show_verify=st.session_state.get("show_verify", False)
        )

        # Extract form data
        mobile_input = form_data["mobile"]
        otp_input = form_data["otp"]
        generate_otp_clicked = form_data["generate_otp_clicked"]
        verify_clicked = form_data["verify_clicked"]

        # Logic for generating OTP
        if generate_otp_clicked and not st.session_state.otp_generated:
            if mobile_input and mobile_input.isdigit() and len(mobile_input) == 10:
                st.session_state.mobile = mobile_input
                st.session_state.otp = str(random.randint(100000, 999999))
                st.session_state.show_verify = True
                st.session_state.otp_generated = True
                st.rerun()  # Force a rerun to ensure the form updates with the OTP input field
            else:
                st.error(get_text("enter_mobile_error", lang))

        # Display OTP if generated
        if st.session_state.otp_generated:
            st.write(f"Your OTP is: **{st.session_state.otp}**")

        # Logic for verifying OTP
        if verify_clicked and otp_input:
            if otp_input == st.session_state.otp:
                st.session_state.otp_verified = True
                # Check if user exists after OTP verification
                user = get_user(mobile_input)
                if not user:  # New user
                    st.session_state.name_input_step = True
                    st.rerun()  # Rerun to show the name input form
                else:  # Existing user
                    st.session_state.logged_in = True
                    st.session_state.show_verify = False
                    st.session_state.otp_generated = False
                    st.session_state.otp_verified = False
                    st.session_state.name_input_step = False
                    st.success(get_text("logged_in_success", lang))
                    st.rerun()
            else:
                st.error(get_text("invalid_otp", lang))

def main_app():
    lang = st.session_state.selected_language
    user_mobile = st.session_state.mobile
    render_header(user_mobile, lang=lang)

    # Display Listed Products 
    if not st.session_state.generated_listing:
        products = get_user_products(user_mobile)
        render_listed_products_container(products, delete_product, lang=lang)

    # Step 1: Image Upload (Collapsible after completion)
    step1_expanded = not bool(st.session_state.uploaded_images)  # Expanded only if no images uploaded
    with st.expander(get_text("upload_images_title", lang), expanded=step1_expanded):
        render_image_upload(lang=lang)

    # Step 2: Record Description (Visible after Step 1)
    if st.session_state.uploaded_images and len(st.session_state.uploaded_images) <= 3 and not st.session_state.generated_listing:
        with st.expander(get_text("record_description_title", lang), expanded=True):
            selected_language, language_options, record_clicked, create_clicked = render_record_description(lang=lang)

            if record_clicked:
                st.write(get_text("recording_message", lang, language=selected_language))
                with st.spinner(get_text("processing_voice", lang)):
                    description = get_product_description(language_options[selected_language])
                    st.session_state.description = description
                    st.write("Generated Description:", description)
                    st.rerun()

            if create_clicked:
                with st.spinner(get_text("processing_voice", lang)):
                    st.session_state.product_counter += 1
                    refined_image_paths = refine_images(st.session_state.uploaded_images, user_mobile, st.session_state.product_counter)
                    if not refined_image_paths:
                        st.session_state.description = None
                        st.rerun()
                        return
                    st.session_state.refined_image_paths = refined_image_paths
                    st.session_state.generated_listing = get_structured_content(st.session_state.description, refined_image_paths, lang=lang)
                    st.rerun()

    # Step 3: Review and Edit Listing
    if st.session_state.generated_listing:
        submit_clicked, edited_listing = render_generated_listing(lang=lang)
        if submit_clicked:
            if st.session_state.edit_product_id:
                update_product(st.session_state.edit_product_id, edited_listing, st.session_state.refined_image_paths)
                st.session_state.edit_product_id = None
            else:
                add_product_with_id(user_mobile, edited_listing, st.session_state.refined_image_paths)
            st.success(get_text("product_saved", lang))
            st.session_state.uploaded_images = []
            st.session_state.description = None
            st.session_state.generated_listing = None
            st.session_state.refined_image_paths = []
            st.rerun()

def manage_listings_page():
    lang = st.session_state.selected_language
    user_mobile = st.session_state.mobile
    products = get_user_products(user_mobile)
    
    # Render manage listings
    render_manage_listings(products, delete_product, lang=lang)

# Main logic
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "main":
        main_app()
    elif st.session_state.page == "manage_listings":
        manage_listings_page()