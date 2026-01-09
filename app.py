"""
Ella Studio
Developer: Steven Lansangan
"""
import streamlit as st
import os
import json
import base64
import zipfile
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import prompt_engine
import importlib
importlib.reload(prompt_engine) # Force reload
from prompt_engine import PromptGenerator, BrandStyle, ShotListGenerator
import db_manager as db

# Initialize DB
db.init_db()

# Load environment variables
load_dotenv()

# Config
st.set_page_config(
    page_title="Ella Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sessions
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "studio_name" not in st.session_state:
    st.session_state.studio_name = None

def login_screen():
    st.markdown("""
    <style>
        .stTextInput > div > div > input {
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 50px;'>ELLA STUDIO</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #888;'>Monochrome Luxury Edition</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        tab_login, tab_reg = st.tabs(["LOGIN", "REGISTER"])
        
        with tab_login:
            l_user = st.text_input("Username", key="l_u")
            l_pass = st.text_input("Password", type="password", key="l_p")
            if st.button("ENTER VAULT", use_container_width=True):
                uid = db.login_user(l_user, l_pass)
                if uid:
                    st.session_state.user_id = uid
                    st.session_state.studio_name = l_user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            
            # Forgot Password Logic
            if st.button("Forgot Password?", type="tertiary"):
                if l_user:
                    hint = db.get_user_hint(l_user)
                    if hint:
                        st.info(f"💡 HINT: {hint}")
                    else:
                        st.warning("No user found or no hint set.")
                else:
                    st.warning("Enter username first.")
        
        with tab_reg:
            r_user = st.text_input("Choose Username", key="r_u")
            r_pass = st.text_input("Choose Password", type="password", key="r_p")
            r_hint = st.text_input("Password Hint (Optional)", key="r_h", placeholder="Something to help you remember...")
            
            if st.button("CREATE STUDIO", use_container_width=True):
                if r_user and r_pass:
                    success, msg = db.create_user(r_user, r_pass, r_hint)
                    if success:
                        st.success("Studio created! Please login.")
                    else:
                        st.error(msg)
                else:
                    st.error("Fields required.")

if not st.session_state.user_id:
    login_screen()
    st.stop()


def image_to_base64(uploaded_file) -> str:
    """Convert uploaded file to base64 string."""
    try:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode('utf-8')
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

def base64_to_image(base64_string: str) -> Optional[Image.Image]:
    """Convert base64 string to PIL Image."""
    try:
        if not base64_string:
            return None
        # Handle data:image/png;base64, prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        return Image.open(BytesIO(image_data))
    except Exception:
        return None

def load_and_resize(b64_str, max_size=None):
    """Load base64 image and optionally resize it."""
    if not b64_str: return None
    img = base64_to_image(b64_str)
    if img:
        # Convert to RGB to ensure compatibility
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Resize if max_size is provided (tuple)
        if max_size:
            img.thumbnail(max_size)
    return img

@st.dialog("High Resolution Preview")
def show_image_preview(image, prompt):
    st.image(image, use_container_width=True)
    st.caption(prompt)

@st.dialog("Magic Editor")
def render_edit_dialog(image, original_prompt, category_type='apparel'):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(image, caption="base", use_container_width=True)
    with col2:
        st.caption(f"Original: {original_prompt[:100]}...")
    
    st.markdown("#### Remix Instructions")
    edit_instr = st.text_input("What should we change?", placeholder="E.g., Change background to a beach, Make the dress red...")
    
    st.markdown("#### Additional Context (Optional)")
    ref_file = st.file_uploader("Texture/Style Ref", type=['png', 'jpg', 'jpeg'], key="edit_ref")
    
    if st.button("GENERATE REMIX", use_container_width=True):
        if not edit_instr:
            st.error("Please describe your edit.")
            return

        with st.spinner("Applying magic..."):
             try:
                # payload
                final_prompt = PromptGenerator.generate_edit_payload(
                    base_desc=original_prompt,
                    edit_instruction=edit_instr
                )
                
                contents = [final_prompt, image]
                if ref_file:
                    ref_img = Image.open(ref_file)
                    contents.append(ref_img)
                    
                # Call API
                if client:
                    response = client.models.generate_content(
                        model='gemini-3-pro-image-preview',
                        contents=contents,
                         config=types.GenerateContentConfig(
                            safety_settings=[types.SafetySetting(
                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="BLOCK_ONLY_HIGH"
                            )]
                        )
                    )
                    
                    # Decode
                    generated_pil = None
                    if response.parts:
                         for part in response.parts:
                              if part.inline_data:
                                   if isinstance(part.inline_data.data, bytes):
                                        generated_pil = Image.open(BytesIO(part.inline_data.data))
                                   else:
                                        generated_pil = Image.open(BytesIO(base64.b64decode(part.inline_data.data)))
                                   break
                    
                    if generated_pil:
                         # Save
                         res_buffer = BytesIO()
                         generated_pil.save(res_buffer, format="PNG")
                         b64_res = base64.b64encode(res_buffer.getvalue()).decode('utf-8')
                         
                         db.add_gallery_item(st.session_state.user_id, category_type, f"Remix: {edit_instr}", b64_res)
                         st.success("Saved to Gallery!")
                         st.rerun()
                    else:
                        st.error("No image returned.")
                else:
                    st.error("Client error.")

             except Exception as e:
                st.error(f"Error: {e}")

# Init DB


# GenAI Client
api_key = os.getenv("GOOGLE_API_KEY") 

try:
    from google import genai
    from google.genai import types
    from google.genai.types import HttpOptions
    
    if api_key:
        client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1alpha")
        )
    else:
        st.warning("GOOGLE_API_KEY not found in environment variables.")
        client = None

except ImportError:
    st.error("`google-genai` library not installed. Please install it.")
    client = None

# Styles
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Jost:wght@300;400;500&display=swap');

    /* GLOBAL VARIABLES */
    :root {
        --bg-color: #0a0a0a;
        --surface-color: #111111;
        --text-color: #e5e5e5;
        --accent-color: #cfcfcf;
        --border-color: #333333;
    }

    /* BASE STYLES */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Jost', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #ffffff;
    }
    
    p, label, .stMarkdown {
        font-family: 'Jost', sans-serif;
        color: var(--text-color);
    }

    /* CUSTOM COMPONENTS */
    .stButton > button {
        background-color: transparent;
        color: var(--text-color);
        border: 1px solid var(--accent-color);
        border-radius: 0px;
        font-family: 'Jost', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: var(--accent-color);
        color: var(--bg-color);
        border-color: var(--accent-color);
    }
    
    /* INPUT FIELDS */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        caret-color: var(--text-color);
        border: none;
        border-bottom: 1px solid var(--accent-color);
        border-radius: 0;
        font-family: 'Jost', sans-serif;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-bottom: 1px solid white;
        box-shadow: none;
    }
    
    /* SELECTION BOXES */
    .stSelectbox > div > div {
        background-color: var(--surface-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color);
        font-family: 'Jost', sans-serif;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: var(--surface-color);
        border-right: 1px solid var(--border-color);
    }

    /* HIDE DEFAULT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;}  <-- Removed to show Sidebar Toggle */

    /* CUSTOM CONTAINERS */
    .asset-card {
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        padding: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .asset-img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        margin-bottom: 5px;
        opacity: 0.8;
        transition: opacity 0.3s;
    }
    .asset-img:hover {
        opacity: 1;
    }
    
    /* CHAT STYLES */
    .chat-container {
        border-top: 1px solid var(--border-color);
        padding-top: 20px;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar logic
st.sidebar.title(f"STUDIO: {st.session_state.studio_name.upper()}")
st.sidebar.markdown("---")
if st.sidebar.button("LOGOUT / SWITCH STUDIO", key="logout"):
    st.session_state.user_id = None
    st.session_state.studio_name = None
    st.rerun()
st.sidebar.markdown("---")

# Admin Console
with st.sidebar.expander("ADMIN CONSOLE", expanded=False):
    st.caption("User Roster (Passwords Encrypted)")
    all_users = db.get_all_users()
    if all_users:
        # Simple table
        for u in all_users:
            st.markdown(f"**{u['username']}**")
            st.caption(f"Hint: {u['password_hint'] if u['password_hint'] else 'None'}")
            st.markdown("---")
    else:
        st.info("No users yet.")

st.sidebar.markdown("---")
st.sidebar.caption("© 2025 Steven Lansangan")

tab_models, tab_apparel, tab_locations = st.sidebar.tabs(["MODELS", "APPAREL", "LOCATIONS"])

def render_model_tab(tab_name):
    assets = db.get_models(st.session_state.user_id)
    with tab_name:
        # Upload
        with st.expander("Upload New Model", expanded=False):
            new_name = st.text_input("Model Name", key="name_roster")
            st.caption("📷 Best: 1024x1024px. Square crop for Face. Portrait for Body.")
            face_file = st.file_uploader("Face Ref (Close-up)", type=['png', 'jpg', 'jpeg'], key="file_face_roster")
            body_file = st.file_uploader("Body Ref (Full Shot)", type=['png', 'jpg', 'jpeg'], key="file_body_roster")
            
            if st.button("Save Model", key="save_roster"):
                if new_name and face_file and body_file:
                    face_b64 = image_to_base64(face_file)
                    body_b64 = image_to_base64(body_file)
                    
                    db.add_model(st.session_state.user_id, new_name, face_b64, body_b64)
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error("Name, Face, and Body images required.")

        # List
        st.markdown("#### Existing Models")
        if not assets:
            st.caption("No models found.")
        
        for asset in assets:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(asset['name'])
            with col2:
                if st.button("x", key=f"del_roster_{asset['id']}", help="Delete"):
                    db.delete_model(asset['id'])
                    st.rerun()

def render_asset_tab(tab_name, category_code, label_singular):
    assets = db.get_assets(st.session_state.user_id, category_code)
    with tab_name:
        # Upload
        with st.expander(f"Upload New {label_singular}", expanded=False):
            new_name = st.text_input(f"Name", key=f"name_{category_code}")
            st.caption("📷 Best: ~1000px on longest side. Avoid 4K uploads.")
            new_file = st.file_uploader(f"Image", type=['png', 'jpg', 'jpeg'], key=f"file_{category_code}")
            
            if st.button(f"Save {label_singular}", key=f"save_{category_code}"):
                if new_name and new_file:
                    b64 = image_to_base64(new_file)
                    db.add_asset(st.session_state.user_id, category_code, new_name, b64)
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error("Name and Image required.")

        # List
        st.markdown(f"#### Existing {label_singular}s")
        if not assets:
            st.caption("No assets found.")
        
        for asset in assets:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(asset['name'])
            with col2:
                if st.button("x", key=f"del_{category_code}_{asset['id']}", help="Delete"):
                    db.delete_asset(asset['id'])
                    st.rerun()

render_model_tab(tab_models)
render_asset_tab(tab_apparel, "closet", "Apparel")
render_asset_tab(tab_locations, "location", "Location")

# Main Interface
st.title("ELLA STUDIO")
st.markdown(f"*Monochrome Luxury Edition | Active Session: {st.session_state.studio_name}*")
st.markdown("---")

# Load all assets for selection
models = db.get_models(st.session_state.user_id)
apparel = db.get_assets(st.session_state.user_id, "closet")
locations = db.get_assets(st.session_state.user_id, "location")

def selection_card(col, title, assets, key_prefix):
    selected = None
    with col:
        st.markdown(f"### {title}")
        options = ["None"] + [a['name'] for a in assets]
        choice = st.selectbox(f"Select {title}", options, label_visibility="collapsed", key=f"sel_{key_prefix}")
        
        if choice != "None":
            # get asset
            asset_data = next((a for a in assets if a['name'] == choice), None)
            if asset_data:
                selected = asset_data
                img = base64_to_image(asset_data['image_base64'])
                if img:
                    st.image(img, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="height:200px; border:1px dashed #333; display:flex; align-items:center; justify-content:center; color:#555;">
                Select {title}
            </div>
            """, unsafe_allow_html=True)
            
    return selected

def selection_card_model(col, title, assets):
    selected = None
    with col:
        st.markdown(f"### {title}")
        options = ["None"] + [a['name'] for a in assets]
        choice = st.selectbox(f"Select {title}", options, label_visibility="collapsed", key=f"sel_model")
        
        if choice != "None":
            # get asset
            asset_data = next((a for a in assets if a['name'] == choice), None)
            if asset_data:
                selected = asset_data
                # Display logic: Prefer Face Ref, fallback to old image_base64
                img_key = 'face_base64' if 'face_base64' in asset_data else 'image_base64'
                if img_key in asset_data:
                    img = base64_to_image(asset_data[img_key])
                    if img:
                        st.image(img, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="height:200px; border:1px dashed #333; display:flex; align-items:center; justify-content:center; color:#555;">
                Select {title}
            </div>
            """, unsafe_allow_html=True)
    return selected

# TABS
main_tab1, main_tab2 = st.tabs(["Apparel Shoot", "Accessories"])

with main_tab1:
    # -- Selection Row --
    col_m, col_a, col_l = st.columns(3)
    selected_model = selection_card_model(col_m, "MODEL", models)
    selected_apparel = selection_card(col_a, "APPAREL", apparel, "apparel")
    selected_location = selection_card(col_l, "LOCATION", locations, "location")

    st.markdown("---")

    # -- Input & Settings --
    st.markdown("### CREATIVE BRIEF")
    user_prompt = st.text_area("Enter your vision...", height=100, placeholder="E.g., High fashion portrait, dynamic pose, moody lighting...")
    ref_image = st.file_uploader("Moodboard (Optional)", type=['png', 'jpg', 'jpeg'], key="cruella_ref")
    
    # Session State for Planned Shots
    if "shot_plan" not in st.session_state:
        st.session_state.shot_plan = ["", "", ""]

    if st.button("✨ AUTO-PLAN CAMPAIGN (Cruella Mode)", help="Let Cruella analyze your brief & moodboard", use_container_width=True):
        if not user_prompt and not ref_image:
             st.error("Please enter a vision or upload a moodboard.")
        else:
             with st.status("Cruella is analyzing your vision...", expanded=True) as status:
                  st.write("Reading brief & analyzing visuals...")
                  st.write("Designing high-fashion campaign structure...")
                  
                  # Handle Image
                  pil_image = None
                  if ref_image:
                      pil_image = Image.open(ref_image)
                  
                  # New ShotListGenerator Logic
                  try:
                      generated_shots = ShotListGenerator.generate_shot_list(client, user_prompt, image=pil_image, min_count=3)
                  except Exception as e:
                      st.error(f"Chunking Error: {e}")
                      generated_shots = [{"description": user_prompt}] # Fallback
                  
                  # Extract descriptions for the text areas
                  briefs = [shot['description'] for shot in generated_shots]
                  
                  # Update Main Plan (Dynamic List)
                  st.session_state.shot_plan = briefs
                  
                  status.update(label="Campaign Plan Created!", state="complete", expanded=False)
                  st.rerun()
    
    # Editable Planner UI (Dynamic Grid)
    st.markdown(f"#### SHOOT PLANNER ({len(st.session_state.shot_plan)} Shots)")
    
    # Render inputs in rows of 3
    plan_cols = st.columns(3)
    for i, shot_text in enumerate(st.session_state.shot_plan):
        col_idx = i % 3
        with plan_cols[col_idx]:
             # We use a key based on index to fetch value. 
             # If key exists, it overrides 'value', so we rely on session state persistence normally.
             # But here we want to update the LIST when the TEXT AREA changes.
             new_val = st.text_area(f"Shot {i+1}", value=shot_text, key=f"shot_input_{i}", height=120)
             st.session_state.shot_plan[i] = new_val

    # No longer need final_shot_inputs list, we use st.session_state.shot_plan directly

    # -- Generation Logic --
    st.markdown("### SHOOT SETTINGS")
    set_col1, set_col2, set_col3, act_col = st.columns([1, 1, 1, 1])

    with set_col1:
         brand_style_name = st.selectbox("Brand Style", [s.value for s in BrandStyle], label_visibility="collapsed")
         selected_style = next(s for s in BrandStyle if s.value == brand_style_name)

    with set_col2:
         aspect_ratio = st.radio("Aspect Ratio", ["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"], label_visibility="collapsed")

    with set_col2:
        resolution = st.radio("Resolution", ["Standard (1K)", "Pro (2K)", "Ultra (4K)"], label_visibility="collapsed")

    ar_map = {
        "1:1 (Square)": "1:1",
        "16:9 (Landscape)": "16:9",
        "9:16 (Portrait)": "9:16"
    }
    selected_ar = ar_map[aspect_ratio]

    # Cost Calculation
    cost_map = {
        "Standard (1K)": "~$0.14",
        "Pro (2K)": "~$0.14", 
        "Ultra (4K)": "~$0.25"
    }
    est_cost = cost_map[resolution]

    with act_col:
        st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True) # Spacer
        if st.button("INITIATE SHOOT", use_container_width=True):
            st.caption(f"Est: {est_cost}x3 | {selected_ar} | {resolution.split('(')[1][:-1]}")
            if not client:
                st.error("AI Client not initialized.")
            elif not user_prompt:
                st.error("Please provide a prompt.")
            elif not selected_model or not selected_apparel:
                st.error("Model and Apparel are required.")
            else:
                with st.spinner("Compiling scene..."):
                    try:
                        # Prep Images
                        # Using global load_and_resize
                        model_face_img = None
                        model_body_img = None
                        
                        if selected_model:
                            if 'face_base64' in selected_model and 'body_base64' in selected_model:
                                 # Generation needs slightly larger limits (800 or 1024)
                                 model_face_img = load_and_resize(selected_model['face_base64'], (800, 800))
                                 model_body_img = load_and_resize(selected_model['body_base64'], (800, 800))
                            elif 'image_base64' in selected_model:
                                 # Legacy fallback
                                 model_body_img = load_and_resize(selected_model['image_base64'], (800, 800))
                        
                        
                        apparel_img = load_and_resize(selected_apparel['image_base64'], (800, 800))
                        location_img = load_and_resize(selected_location['image_base64'], (800, 800)) if selected_location else None

                        # Results Grid
                        st.markdown("### SERIES RESULTS")
                        
                        # Dynamic Results Grid
                        # We'll create columns dynamically or use a wrapping logic?
                        # Streamlit columns are fixed width row.
                        # Let's do rows of 3.
                        
                        total_shots = len(st.session_state.shot_plan)
                        cols_per_row = 3
                        
                        # Loop through all planned shots
                        for i in range(total_shots):
                            # Start a new row if needed
                            if i % cols_per_row == 0:
                                current_row_cols = st.columns(cols_per_row)
                            
                            col_idx = i % cols_per_row
                            
                            with current_row_cols[col_idx]:
                                st.markdown(f"**Shot {i+1}**")
                                with st.spinner(f"Generating..."):
                                    # Select Payload
                                    current_brief = st.session_state.shot_plan[i]
                                    
                                    # Skip if empty
                                    if not current_brief:
                                        st.warning("Skipped (Empty)")
                                        continue

                                    # Construct Payload manually using the brief as Subject
                                    # We disable auto-variation since the brief is now explicit
                                    style_text = selected_style.prompt_modifier
                                    if selected_location:
                                         style_text += " IGNORE STYLE ENVIRONMENT. USE LOCATION IMAGE BACKGROUND."
                                    
                                    final_prompt_optimized = (
                                        f"STRICT INSTRUCTION: {PromptGenerator.MASTER_BASE_PROMPT} "
                                        f"Aspect Ratio: {selected_ar}. "
                                        f"Subject: {current_brief}. "
                                        f"Style Guide: {style_text} "
                                        f"Exclude: {PromptGenerator.NEGATIVE_PROMPT}"
                                    )
                        
                                    # Fidelity checks
                                    final_prompt_optimized += "\\n\\nVISUAL MAPPING:"
                                    img_count = 1
                                    
                                    if model_face_img:
                                        final_prompt_optimized += f"\\n- Image {img_count}: MODEL FACE REF. PRIORITY: CRITICAL IDENTITY PRESERVATION. The output face must be indistinguishable from this reference. strict Carbon-Copy. Do NOT 'beautify', 'optimize', or 'average' the features. Maintain exact eye shape, nose structure, and facial landmarks."
                                        img_count += 1
                                    
                                    if model_body_img:
                                        final_prompt_optimized += f"\\n- Image {img_count}: MODEL BODY REF. Use this for body proportions and pose. Ensure natural anatomical connection to the head."
                                        img_count += 1
                                        
                                    if apparel_img:
                                        final_prompt_optimized += f"\\n- Image {img_count}: APPAREL REF. PRIORITY: TEXTURE & CUT FIDELITY. However, the FIT must be realistic. The fabric should fold, crease, and hang according to the model's pose and gravity. Do not make it look like a sticker. It must wrap around the 3D form."
                                        img_count += 1
                                    if location_img:
                                        final_prompt_optimized += f"\\n- Image {img_count}: LOCATION REF. Use this background. Integrate the subject with matching lighting and shadows."
                                        img_count += 1
                                    
                                    final_prompt_optimized += "\\n\\nFINAL INSTRUCTION: NATURAL CONSISTENCY ALL THE TIME."
                                    final_prompt_optimized += "\\n1. The Reference Face MUST match the Output Face."
                                    final_prompt_optimized += "\\n2. The Reference Apparel MUST match the Output Apparel."
                                    final_prompt_optimized += "\\n3. Lighting must be coherent across Model, Clothes, and Background."

                                    # Request
                                    # Input list for the model (Text + Images)
                                    contents = [final_prompt_optimized]
                                    if model_face_img: contents.append(model_face_img)
                                    if model_body_img: contents.append(model_body_img)
                                    if apparel_img: contents.append(apparel_img)
                                    if location_img: contents.append(location_img)

                                    # Call API
                                    response = client.models.generate_content(
                                        model='gemini-3-pro-image-preview',
                                        contents=contents,
                                        config=types.GenerateContentConfig(
                                            safety_settings=[types.SafetySetting(
                                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                                threshold="BLOCK_ONLY_HIGH"
                                            )]
                                        )
                                    )
                                    
                                    # Process response (Gemini 3 returns image in parts)
                                    generated_pil = None
                                    
                                    if response.parts:
                                        for part in response.parts:
                                            if part.inline_data:
                                                try:
                                                    if isinstance(part.inline_data.data, bytes):
                                                        generated_pil = Image.open(BytesIO(part.inline_data.data))
                                                    else:
                                                        # Decode base64 if needed
                                                        image_data = base64.b64decode(part.inline_data.data)
                                                        generated_pil = Image.open(BytesIO(image_data))
                                                    break
                                                except Exception as img_err:
                                                     st.error(f"Failed to decode output: {img_err}")
                                            elif hasattr(part, 'text') and part.text and "http" in part.text:
                                                st.warning("Received link instead of image: " + part.text)
                                    
                                    if generated_pil:
                                        st.success("SHOOT COMPLETE")
                                        st.image(generated_pil, caption=f"Shot {i+1}", use_container_width=True)
                                        
                                        # Save to Gallery
                                        res_buffer = BytesIO()
                                        generated_pil.save(res_buffer, format="PNG")
                                        b64_res = base64.b64encode(res_buffer.getvalue()).decode('utf-8')
                                        
                                        db.add_gallery_item(st.session_state.user_id, 'apparel', f"{current_brief[:100]}", b64_res)
                                        
                                    else:
                                        st.error("Frame failed.")
    
                    except Exception as e:
                        st.error(f"Generation failed: {str(e)}")

    # Gallery
    st.markdown("---")
    # Header & Download All
    gh_col1, gh_col2 = st.columns([3, 2])
    with gh_col1:
        st.markdown("### PORTFOLIO ARCHIVE")

    gallery = db.get_gallery(st.session_state.user_id, 'apparel')

    with gh_col2:
        if gallery:
            try:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for idx, item in enumerate(gallery):
                        img_data = base64.b64decode(item['image_base64'])
                        zf.writestr(f"shoot_{idx}_{item['timestamp'][:10]}.png", img_data)
                
                # Action Buttons Layout (Side by Side)
                st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True) # visual alignment
                dl_col, clr_col = st.columns([1, 1])
                with dl_col:
                    st.download_button(
                        label="Download All",
                        data=zip_buffer.getvalue(),
                        file_name=f"ella_portfolio_{st.session_state.studio_name}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                with clr_col:
                    if st.button("CLEAR", help="Wipe Archive", use_container_width=True):
                        db.clear_gallery(st.session_state.user_id, 'apparel')
                        st.rerun()

            except Exception as e:
                st.error(f"Zip error: {e}")

    if gallery:
        # SCROLLABLE GALLERY CONTAINER
        with st.container(height=600):
            # Grid Layout: Iterate in batches of 3
            for i in range(0, len(gallery), 3):
                cols = st.columns(3)
                batch = gallery[i:i+3]
                for j, item in enumerate(batch):
                    idx = i + j
                    with cols[j]:
                        g_img = base64_to_image(item['image_base64'])
                        if g_img:
                            st.image(g_img, caption=f"{item['timestamp'][:10]}", use_container_width=True)
                            st.caption(f"{item['prompt'][:30]}...")
                            
                            # Actions Row
                            act_c1, act_c2, act_c3, act_c4 = st.columns([1, 1, 2, 1])
                            with act_c1:
                                if st.button("🔍", key=f"view_{item['id']}", help="Maximize"):
                                    show_image_preview(g_img, item['prompt'])
                            with act_c2:
                                if st.button("✏️", key=f"edit_{item['id']}", help="Remix"):
                                    render_edit_dialog(g_img, item['prompt'], 'apparel')
                            with act_c3:
                                buf = BytesIO()
                                g_img.save(buf, format="PNG")
                                st.download_button(
                                    label="Download",
                                    data=buf.getvalue(),
                                    file_name=f"ella_shoot_{idx}.png",
                                    mime="image/png",
                                    key=f"dl_{idx}",
                                    use_container_width=True
                                )
                            with act_c3:
                                if st.button("🗑", key=f"del_gal_{item['id']}", help="Remove", use_container_width=True):
                                    db.delete_gallery_item(item['id'])
                                    st.rerun()
    else:
        st.info("No shoots in portfolio yet.")



with main_tab2:
    st.markdown("### ACCESSORY STUDIO")
    st.markdown("Add Jewelry, Bags, or Shoes to your generated shoots.")
    
    # 1. Select Base from Main Gallery
    main_gallery = db.get_gallery(st.session_state.user_id, 'apparel')
    
    col_base, col_acc = st.columns(2)
    
    selected_shoot_base64 = None
    
    with col_base:
        st.markdown("#### 1. Select Base Shoot")
        if not main_gallery:
            st.info("No shoots available. Go to Apparel Shoot tab first.")
        else:
            # Create friendly labels
            shoot_options = {f"Shoot {i+1} ({item['timestamp'][:10]})": i for i, item in enumerate(main_gallery)}
            selected_option = st.selectbox("Choose Image", list(shoot_options.keys()))
            
            if selected_option:
                idx = shoot_options[selected_option]
                selected_shoot = main_gallery[idx]
                selected_shoot_base64 = selected_shoot['image_base64']
                
                # Preview
                base_img = base64_to_image(selected_shoot_base64)
                if base_img:
                    st.image(base_img, caption="Base Image", use_container_width=True)

    with col_acc:
        st.markdown("#### 2. Add Accessory")
        acc_desc = st.text_input("Accessory Name/Description", placeholder="E.g., Gold chunky necklace, Leather handbag")
        st.caption("📷 Best: Transparent PNG or White Background. High res (1000px+).")
        acc_file = st.file_uploader("Upload Item", type=['png', 'jpg', 'jpeg'], key="acc_upload")
        
        acc_image = None
        if acc_file:
            acc_image = Image.open(acc_file)
            st.image(acc_image, caption="Accessory Ref", width=200)

    st.markdown("---")
    
    if st.button("APPLY ACCESSORY", use_container_width=True):
        if not selected_shoot_base64 or not acc_image or not acc_desc:
            st.error("Missing inputs. Select a shoot, upload an accessory, and describe it.")
        elif not client:
             st.error("AI Client not initialized.")
        else:
            with st.spinner(" fusing accessory..."):
                try:
                    # Prepare inputs
                    base_pil = base64_to_image(selected_shoot_base64)
                    
                    # Construct Prompt via Engine
                    acc_prompt = PromptGenerator.generate_accessory_payload(
                        base_desc="Existing fashion shoot",
                        accessory_desc=acc_desc
                    )
                    
                    contents = [acc_prompt, base_pil, acc_image]
                    
                    response = client.models.generate_content(
                        model='gemini-3-pro-image-preview',
                        contents=contents,
                         config=types.GenerateContentConfig(
                            safety_settings=[types.SafetySetting(
                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="BLOCK_ONLY_HIGH"
                            )]
                        )
                    )
                    
                    # Handle Response
                    final_acc_pil = None
                    if response.parts:
                         for part in response.parts:
                              if part.inline_data:
                                   if isinstance(part.inline_data.data, bytes):
                                        final_acc_pil = Image.open(BytesIO(part.inline_data.data))
                                   else:
                                        final_acc_pil = Image.open(BytesIO(base64.b64decode(part.inline_data.data)))
                                   break
                    
                    if final_acc_pil:
                        st.success("ACCESSORY ADDED")
                        st.image(final_acc_pil, caption="Final Result", use_container_width=True)
                        
                        # Save to ACCESSORIES Gallery
                        buf = BytesIO()
                        final_acc_pil.save(buf, format="PNG")
                        b64_new = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        db.add_gallery_item(st.session_state.user_id, 'accessory', f"Accessory Add: {acc_desc}", b64_new)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Failed: {e}")
    
    # ---------------------------------------------------------
    # ACCESSORY PORTFOLIO
    # ---------------------------------------------------------
    st.markdown("---")
    gh_col1, gh_col2 = st.columns([3, 2])
    with gh_col1:
        st.markdown("### ACCESSORY ARCHIVE")

    acc_portfolio = db.get_gallery(st.session_state.user_id, 'accessory')

    with gh_col2:
        if acc_portfolio:
            try:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for idx, item in enumerate(acc_portfolio):
                        img_data = base64.b64decode(item['image_base64'])
                        zf.writestr(f"accessory_{idx}_{item['timestamp'][:10]}.png", img_data)
                
                # Action Buttons
                st.markdown("<div style='height: 5px'></div>", unsafe_allow_html=True) 
                dl_col, clr_col = st.columns([1, 1])
                with dl_col:
                    st.download_button(
                        label="Download All",
                        data=zip_buffer.getvalue(),
                        file_name=f"ella_accessories_{st.session_state.studio_name}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="dl_all_acc"
                    )
                with clr_col:
                    if st.button("CLEAR", help="Wipe Accessories", use_container_width=True, key="clr_acc"):
                        db.clear_gallery(st.session_state.user_id, 'accessory')
                        st.rerun()

            except Exception as e:
                st.error(f"Zip error: {e}")

    if acc_portfolio:
        # Gallery Grid
        with st.container(height=600):
            for i in range(0, len(acc_portfolio), 3):
                cols = st.columns(3)
                batch = acc_portfolio[i:i+3]
                for j, item in enumerate(batch):
                    idx = i + j
                    with cols[j]:
                        g_img = base64_to_image(item['image_base64'])
                        if g_img:
                            st.image(g_img, caption=f"{item['timestamp'][:10]}", use_container_width=True)
                            st.caption(f"{item['prompt'][:30]}...")
                            
                            
                            # Actions
                            act_a1, act_a2, act_a3, act_a4 = st.columns([1, 1, 2, 1])
                            with act_a1:
                                if st.button("🔍", key=f"view_acc_{item['id']}", help="Maximize"):
                                    show_image_preview(g_img, item['prompt'])
                            with act_a2:
                                if st.button("✏️", key=f"edit_acc_{item['id']}", help="Remix"):
                                    render_edit_dialog(g_img, item['prompt'], 'accessory')

                            with act_a3:
                                buf = BytesIO()
                                g_img.save(buf, format="PNG")
                                st.download_button(
                                    label="Download",
                                    data=buf.getvalue(),
                                    file_name=f"ella_acc_{idx}.png",
                                    mime="image/png",
                                    key=f"dl_acc_{idx}",
                                    use_container_width=True
                                )
                            with act_a4:
                                if st.button("🗑", key=f"del_acc_{item['id']}", help="Remove", use_container_width=True):
                                    db.delete_gallery_item(item['id'])
                                    st.rerun()

    else:
        st.info("No accessory shoots yet.")
