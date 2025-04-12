import streamlit as st
from PIL import Image
from translations import get_text
from content_generator import call_llm
import os
from database import get_user  # Add this import for render_header and render_login_form

def render_login_form(lang="en", mobile=None, user_exists=True, show_verify=False):
    """
    Renders the login form UI and returns user inputs and button states.
    
    Args:
        lang (str): The selected language ("en", "hi", etc.).
        mobile (str): The mobile number entered by the user (for pre-filling the input).
        user_exists (bool): Whether the user already exists in the database.
        show_verify (bool): Whether to show the OTP verification input.
    
    Returns:
        dict: Contains mobile, first_name, last_name, otp, generate_otp_clicked, verify_clicked.
    """
    st.title(get_text("login_title", lang))
    st.markdown("---")

    # Step 1: Mobile number input
    mobile_input = st.text_input(
        get_text("mobile_placeholder", lang),
        value=mobile if mobile else "",
        placeholder=get_text("mobile_placeholder", lang)
    )

    # Step 2: If user is new, ask for first and last name (we'll handle this later in login_page)
    first_name_input = None
    last_name_input = None
    # This part is now handled in login_page after OTP verification, so we can skip it here

    # Step 3: Generate OTP button
    generate_otp_clicked = st.button(get_text("generate_otp", lang))

    # Step 4: OTP verification
    otp_input = None
    verify_clicked = False
    if show_verify:
        st.markdown("---")
        otp_input = st.text_input(
            get_text("otp_placeholder", lang),
            placeholder=get_text("otp_placeholder", lang)
        )
        verify_clicked = st.button(get_text("verify", lang))

    return {
        "mobile": mobile_input,
        "first_name": first_name_input,
        "last_name": last_name_input,
        "otp": otp_input,
        "generate_otp_clicked": generate_otp_clicked,
        "verify_clicked": verify_clicked
    }



# New function to render the "Your Listings" section with a styled container
def render_listed_products_container(products, delete_product, lang="en"):
    # Add a styled container for "Your Listings"
    st.markdown(
        """
        <div style='border: 1px solid #e6e6e6; border-radius: 5px; padding: 5px; background-color: #f9f9f9; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 5px;'>
            <h2 style='font-size: 24px; font-weight: bold; color: #1E90FF; margin-bottom: 15px;'>
                {title}
            </h2>
        """.format(title=get_text("listed_products_title", lang)),
        unsafe_allow_html=True
    )
    render_listed_products(products, delete_product, lang=lang)
    st.markdown("</div>", unsafe_allow_html=True)


def render_header(user_mobile, lang="en"):
    col1, col2 = st.columns([4,2])
    with col1:
        st.markdown(f"<h1 style='font-size: 36px; font-weight: bold;'>{get_text('title', lang)}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size: 20px; color: #666;'>{get_text('welcome', lang)}</h3>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        col2_1, col2_2 = st.columns([1, 1])
        with col2_2:
            if st.button(get_text("logout", lang)):
                st.session_state.logged_in = False
                st.session_state.mobile = None
                st.session_state.otp = None
                st.session_state.show_verify = False
                st.session_state.uploaded_images = []
                st.session_state.description = None
                st.session_state.product_counter = 0
                st.session_state.edit_product_id = None
                st.session_state.generated_listing = None
                st.success(get_text("logged_in_success", lang))
                st.rerun()
        with col2_1:
            if st.button(get_text("manage_listings", lang)):
                st.session_state.page = "manage_listings"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

def render_image_upload(lang="en"):
    st.subheader(get_text("upload_images_title", lang))
    with st.container():
        st.markdown(
            """
            <div style='border: 1px solid #e6e6e6; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
            """,
            unsafe_allow_html=True
        )
        uploaded_files = st.file_uploader(get_text("upload_label", lang), type=["jpg", "png", "jpeg"], accept_multiple_files=True)

        # Track previous upload state to avoid infinite rerun
        if "previous_uploaded_files" not in st.session_state:
            st.session_state.previous_uploaded_files = None

        # Update session state and check if the uploaded files have changed
        if uploaded_files and uploaded_files != st.session_state.previous_uploaded_files:
            st.session_state.uploaded_images = uploaded_files
            st.session_state.previous_uploaded_files = uploaded_files
            if len(uploaded_files) > 3:
                st.error(get_text("max_images_error", lang))
                st.session_state.uploaded_images = uploaded_files[:3]
                st.session_state.previous_uploaded_files = uploaded_files[:3]
            st.rerun()

        # Display uploaded images
        if st.session_state.uploaded_images:
            st.subheader(get_text("uploaded_images", lang))
            cols = st.columns(3)
            for i, uploaded_file in enumerate(st.session_state.uploaded_images):
                input_image = Image.open(uploaded_file)
                cols[i % 3].image(input_image, caption=get_text("image_caption", lang, index=i+1), width=200)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    return uploaded_files

def render_record_description(lang="en"):
    st.subheader(get_text("record_description_title", lang))
    language_options = {
        "Hindi": "hi-IN",
        "Tamil": "ta-IN",
        "Telugu": "te-IN",
        "Marathi": "mr-IN",
        "Bengali": "bn-IN",
        "Gujarati": "gu-IN"
    }
    selected_language = st.radio(get_text("choose_language", lang), list(language_options.keys()), horizontal=True)

    # Display current description if it exists and is not empty
    if st.session_state.description and st.session_state.description.strip():
        st.subheader(f"{get_text('description', lang)} ({selected_language})")
        st.write(st.session_state.description)
    elif st.session_state.description is not None:
        st.subheader(f"{get_text('description', lang)} ({selected_language})")
        st.write(get_text("no_description", lang))

    # Buttons for recording or re-recording
    record_button_label = get_text("rerecord_button", lang) if st.session_state.description is not None else get_text("record_button", lang)
    record_clicked = st.button(record_button_label)
    create_clicked = st.session_state.description and st.session_state.description.strip() and st.button(get_text("create_listing", lang))
    
    return selected_language, language_options, record_clicked, create_clicked

# render generated list in user language and update edits in english as well for the public url
def render_generated_listing(lang="en"):
    st.subheader(get_text("review_edit_title", lang))

    field_map = {
        "product_name": get_text("product_name", lang),
        "material": get_text("material", lang),
        "description": get_text("description", lang),
        "price": get_text("price", lang),
        "tags": get_text("tags", lang)
    }

    with st.form(key="edit_listing_form"):
        product_name = st.text_input(field_map["product_name"], value=st.session_state.generated_listing["product_name"])
        material = st.text_input(field_map["material"], value=st.session_state.generated_listing["material"])
        description = st.text_area(field_map["description"], value=st.session_state.generated_listing["description"])
        price = st.text_input(field_map["price"], value=st.session_state.generated_listing["price"])
        tags = st.text_input(field_map["tags"], value=st.session_state.generated_listing["tags"])
        submit_clicked = st.form_submit_button(get_text("submit_listing", lang))

        edited_listing = {
            "product_name": product_name,
            "material": material,
            "description": description,
            "price": price,
            "tags": tags
        }
        if lang != "en" and submit_clicked:
            prompt = f"""
            Translate the following product listing fields from {lang} to English:
            Product Name: {product_name}
            Material: {material}
            Description: {description}
            Price: {price}
            Tags: {tags}
            Format the response as:
            Product Name (English): <name_en>
            Material (English): <material_en>
            Description (English): <description_en>
            Price (English): <price_en>
            Tags (English): <tags_en>
            """
            response = call_llm(prompt)
            english_listing = {}
            for line in response.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    english_listing[key.strip()] = value.strip()
            edited_listing.update({
                "product_name_en": english_listing.get("Product Name (English)", product_name),
                "material_en": english_listing.get("Material (English)", material),
                "description_en": english_listing.get("Description (English)", description),
                "price_en": english_listing.get("Price (English)", price),
                "tags_en": english_listing.get("Tags (English)", tags)
            })
        elif lang == "en":
            edited_listing.update({
                "product_name_en": product_name,
                "material_en": material,
                "description_en": description,
                "price_en": price,
                "tags_en": tags
            })

    st.subheader(get_text("refined_images", lang))
    cols = st.columns(3)
    for i, refined_path in enumerate(st.session_state.refined_image_paths):
        if os.path.exists(refined_path):  # Validate path
            cols[i % 3].image(refined_path, caption=get_text("image_caption", lang, index=i+1), width=200)
        else:
            st.error(f"Image path invalid: {refined_path}")
    st.markdown("---")
    
    return submit_clicked, edited_listing

def render_listed_products(products, delete_product, lang="en"):
    #st.subheader(get_text("listed_products_title", lang))
    if not products:
        st.write(get_text("no_products", lang))
    else:
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(
                        """
                        <div style='border: 1px solid #e6e6e6; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        """,
                        unsafe_allow_html=True
                    )
                    if product['image_paths']:
                        st.image(product['image_paths'][0], width=150)
                    st.write(f"**{product['product_name']}**")
                    st.write(f"{get_text('price', lang)}: {product['price']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ {get_text('edit', lang)}", key=f"edit_{product['id']}"):
                            st.session_state.edit_product_id = product['id']
                            st.session_state.uploaded_images = []
                            st.session_state.description = product['description']
                            st.session_state.generated_listing = {
                                "product_name": product['product_name'],
                                "material": product['material'],
                                "description": product['description'],
                                "price": product['price'],
                                "tags": product['tags'],
                                "product_name_en": product['product_name_en'],
                                "material_en": product['material_en'],
                                "description_en": product['description_en'],
                                "price_en": product['price_en'],
                                "tags_en": product['tags_en']
                            }
                            st.session_state.refined_image_paths = product['image_paths']  # Preserve existing image paths
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ {get_text('delete', lang)}", key=f"delete_{product['id']}"):
                            delete_product(product['id'])
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

'''
def render_share_listings(user_mobile, lang="en"):
    st.subheader(get_text("share_listings_title", lang))
    public_url = f"http://127.0.0.1:5000/public/{user_mobile}"
    with st.container():
        st.markdown(
            """
            <div style='border: 1px solid #e6e6e6; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
            """,
            unsafe_allow_html=True
        )
        st.write(get_text("share_url_message", lang))
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"<a href='{public_url}' style='font-size: 16px; color: #1a73e8;'>{public_url}</a>", unsafe_allow_html=True)
        with col2:
            if st.button(get_text("copy_link", lang)):
                st.write(get_text("link_copied", lang))
                st.markdown(
                    f"""
                    <script>navigator.clipboard.writeText("{public_url}");</script>
                    """,
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)
'''


def render_header(user_mobile, lang="en"):
    # Fetch user details to get the first name
    user = get_user(user_mobile)
    if user:
        user_name = user[1]  # First name (index 1 in the users table)
    else:
        user_name = user_mobile  # Fallback to mobile number if user not found

    col1, col2 = st.columns([4, 2])
    with col1:
        st.markdown(
            f"<h1 style='font-size: 36px; font-weight: bold;'>{get_text('title', lang)}</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h3 style='font-size: 20px; color: #666;'>{get_text('welcome', lang)} {user_name}</h3>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        col2_1, col2_2 = st.columns([1, 1])
        with col2_2:
            if st.button(get_text("logout", lang)):
                st.session_state.logged_in = False
                st.session_state.mobile = None
                st.session_state.otp = None
                st.session_state.show_verify = False
                st.session_state.uploaded_images = []
                st.session_state.description = None
                st.session_state.product_counter = 0
                st.session_state.edit_product_id = None
                st.session_state.generated_listing = None
                st.success(get_text("logged_in_success", lang))
                st.rerun()
        with col2_1:
            if st.button(get_text("manage_listings", lang)):
                st.session_state.page = "manage_listings"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")


#render manage listings page
def render_manage_listings(products, delete_product, lang="en"):
    st.markdown(f"<h1 style='font-size: 36px; font-weight: bold;'>{get_text('manage_listings_title', lang)}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not products:
        st.write(get_text("no_products_manage", lang))
    else:
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(
                        """
                        <div style='border: 1px solid #e6e6e6; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                        """,
                        unsafe_allow_html=True
                    )
                    if product['image_paths']:
                        if os.path.exists(product['image_paths'][0]):
                            st.image(product['image_paths'][0], width=150)
                        else:
                            st.error(f"Invalid image path: {product['image_paths'][0]}")
                    st.write(f"**{product['product_name']}**")
                    st.write(f"{get_text('material', lang)}: {product['material']}")
                    st.write(f"{get_text('description', lang)}: {product['description']}")
                    st.write(f"{get_text('price', lang)}: {product['price']}")
                    st.write(f"{get_text('tags', lang)}: {product['tags']}")
                    if st.button(f"🗑️ {get_text('delete', lang)}", key=f"delete_{product['id']}"):
                        delete_product(product['id'])
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(get_text("back_to_main", lang)):
        st.session_state.page = "main"
        st.rerun()