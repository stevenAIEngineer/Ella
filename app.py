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

# Load environment variables
load_dotenv()

# ---------------------------------------------------------
# 1. SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ella Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. SESSION & AUTHENTICATION
# ---------------------------------------------------------
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
        
        studio_input = st.text_input("ENTER STUDIO NAME", placeholder="Type your name to begin...")
        
        if st.button("ENTER THE VAULT", use_container_width=True):
            if studio_input.strip():
                st.session_state.studio_name = studio_input.strip()
                st.rerun()
            else:
                st.error("Identity required.")

if not st.session_state.studio_name:
    login_screen()
    st.stop()

# ---------------------------------------------------------
# 3. DATA PERSISTENCE (USER ISOLATED)
# ---------------------------------------------------------
USER_DATA_DIR = os.path.join("data", st.session_state.studio_name)

FILES = {
    "roster": os.path.join(USER_DATA_DIR, "roster.json"),
    "closet": os.path.join(USER_DATA_DIR, "closet.json"),
    "locations": os.path.join(USER_DATA_DIR, "locations.json"),
    "gallery": os.path.join(USER_DATA_DIR, "gallery.json"),
}

@dataclass
class Asset:
    name: str
    image_base64: str

@dataclass
class GalleryItem:
    prompt: str
    image_base64: str
    timestamp: str

def ensure_user_data():
    """Ensure user specific data directory and JSON files exist."""
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
    
    for key, filepath in FILES.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump([], f)

def load_data(key: str) -> List[Dict]:
    """Load data from JSON file."""
    filepath = FILES[key]
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(key: str, data: List[Dict]):
    """Save data to JSON file."""
    filepath = FILES[key]
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

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

# Initialize User DB
ensure_user_data()

# ---------------------------------------------------------
# 4. GOOGLE GENAI CLIENT
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 5. DESIGN SYSTEM
# ---------------------------------------------------------
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
        background-color: transparent;
        color: var(--text-color);
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
        background-color: var(--surface-color);
        color: var(--text-color);
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
    header {visibility: hidden;}

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

# ---------------------------------------------------------
# 6. SIDEBAR: "THE VAULT"
# ---------------------------------------------------------
st.sidebar.title(f"STUDIO: {st.session_state.studio_name.upper()}")
st.sidebar.markdown("---")
if st.sidebar.button("LOGOUT / SWITCH STUDIO", key="logout"):
    st.session_state.studio_name = None
    st.rerun()
st.sidebar.markdown("---")

tab_models, tab_apparel, tab_locations = st.sidebar.tabs(["MODELS", "APPAREL", "LOCATIONS"])

def render_asset_tab(tab_name, data_key, label_singular):
    assets = load_data(data_key)
    with tab_name:
        # Upload
        with st.expander(f"Upload New {label_singular}", expanded=False):
            new_name = st.text_input(f"Name", key=f"name_{data_key}")
            new_file = st.file_uploader(f"Image", type=['png', 'jpg', 'jpeg'], key=f"file_{data_key}")
            
            if st.button(f"Save {label_singular}", key=f"save_{data_key}"):
                if new_name and new_file:
                    b64 = image_to_base64(new_file)
                    assets.append(asdict(Asset(name=new_name, image_base64=b64)))
                    save_data(data_key, assets)
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error("Name and Image required.")

        # List
        st.markdown(f"#### Existing {label_singular}s")
        if not assets:
            st.caption("No assets found.")
        
        for i, asset in enumerate(assets):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(asset['name'])
            with col2:
                if st.button("x", key=f"del_{data_key}_{i}", help="Delete"):
                    assets.pop(i)
                    save_data(data_key, assets)
                    st.rerun()

render_asset_tab(tab_models, "roster", "Model")
render_asset_tab(tab_apparel, "closet", "Apparel")
render_asset_tab(tab_locations, "locations", "Location")

# ---------------------------------------------------------
# 7. MAIN STAGE: "THE FUSION STUDIO"
# ---------------------------------------------------------
st.title("ELLA STUDIO")
st.markdown(f"*Monochrome Luxury Edition | Active Session: {st.session_state.studio_name}*")
st.markdown("---")

# Load all assets for selection
models = load_data("roster")
apparel = load_data("closet")
locations = load_data("locations")

# -- Selection Row --
col_m, col_a, col_l = st.columns(3)

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

selected_model = selection_card(col_m, "MODEL", models, "model")
selected_apparel = selection_card(col_a, "APPAREL", apparel, "apparel")
selected_location = selection_card(col_l, "LOCATION", locations, "location")

st.markdown("---")

# -- Input & Settings --
st.markdown("### CREATIVE BRIEF")
user_prompt = st.text_area("Enter your vision...", height=100, placeholder="E.g., High fashion portrait, dynamic pose, moody lighting...")

# -- Generation Logic --
# Layout: Left (Inputs/Settings) | Center (Action) | Right (Output) - Simplified
# Redesigning Generation Row for Aspect Ratio & Resolution
st.markdown("### SHOOT SETTINGS")
set_col1, set_col2, act_col = st.columns([1, 1, 1])

with set_col1:
     aspect_ratio = st.radio("Aspect Ratio", ["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"], label_visibility="collapsed")

with set_col2:
    resolution = st.radio("Resolution", ["Standard (1K)", "Pro (2K)", "Ultra (4K)"], label_visibility="collapsed")

generated_image = None
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
        st.caption(f"Est: {est_cost} | {selected_ar} | {resolution.split('(')[1][:-1]}")
        if not client:
            st.error("AI Client not initialized.")
        elif not user_prompt:
            st.error("Please provide a prompt.")
        elif not selected_model or not selected_apparel:
            st.error("Model and Apparel are required.")
        else:
            with st.spinner("Compiling scene..."):
                try:
                    # 1. Image preparation & Optimization
                    def load_and_resize(b64_str):
                        if not b64_str: return None
                        img = base64_to_image(b64_str)
                        if img:
                            # Convert to RGB (Remove Alpha Channel if present, as it can cause 500s)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            # Resize to max 800px to be safe
                            img.thumbnail((800, 800))
                        return img

                    model_img = load_and_resize(selected_model['image_base64'])
                    apparel_img = load_and_resize(selected_apparel['image_base64'])
                    location_img = load_and_resize(selected_location['image_base64']) if selected_location else None

                    # 2. Prompt construction
                    # STRICT PROMPT ENGINEERING FOR CONSISTENCY
                    final_prompt = f"STRICT INSTRUCTION: Generate a high-fashion photograph based on the following description: {user_prompt}. "
                    final_prompt += f" Aspect Ratio: {selected_ar}. "
                    final_prompt += f" Target Resolution: {resolution.split('(')[0].strip().upper()}. "
                    final_prompt += "Ensure professional editorial lighting, 8k resolution, highly detailed texture. "
                    
                    # Explicit Input Mapping
                    final_prompt += "\n\nVISUAL INPUT MAPPING (Critical Compliance Required):"
                    img_count = 1
                    if model_img:
                        final_prompt += f"\n- Image {img_count}: MODEL REFERENCE. You MUST reproduce the face, hair, and body type of this person exactly. Do not alter their identity."
                        img_count += 1
                    if apparel_img:
                        final_prompt += f"\n- Image {img_count}: APPAREL REFERENCE. You MUST reproduce the clothing (material, cut, color, texture) exactly as shown. Ease fit onto the model naturally."
                        img_count += 1
                    if location_img:
                        final_prompt += f"\n- Image {img_count}: LOCATION REFERENCE. Use this strict background."
                        img_count += 1
                    
                    final_prompt += "\n\nEXECUTION GUIDELINES:"
                    final_prompt += "\n1. Fuse these elements perfectly. The Model (Image 1) wearing the Apparel (Image 2) in the Location (Image 3)."
                    final_prompt += "\n2. Do NOT change the model's ethnicity or key facial features."
                    final_prompt += "\n3. Do NOT change the garment's design or fabric."
                    final_prompt += "\n4. Deliver a photorealistic, Vogue-quality masterpiece."
                    
                    # 3. Request
                    # Input list for the model (Text + Images)
                    contents = [final_prompt]
                    if model_img: 
                        contents.append(model_img)
                    if apparel_img:
                        contents.append(apparel_img)
                    if location_img:
                        contents.append(location_img)

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
                        st.image(generated_pil, caption="Final Result", width="stretch")
                        
                        # Save to Gallery
                        res_buffer = BytesIO()
                        generated_pil.save(res_buffer, format="PNG")
                        b64_res = base64.b64encode(res_buffer.getvalue()).decode('utf-8')
                        
                        gallery_items = load_data("gallery")
                        gallery_items.insert(0, asdict(GalleryItem(
                            prompt=user_prompt,
                            image_base64=b64_res,
                            timestamp=datetime.now().isoformat()
                        )))
                        save_data("gallery", gallery_items)
                        
                    else:
                        st.error("No valid image data returned.")

                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")

# ---------------------------------------------------------
# 8. THE GALLERY ("PORTFOLIO")
# ---------------------------------------------------------
st.markdown("---")
# Header & Download All
gh_col1, gh_col2 = st.columns([5, 1])
with gh_col1:
    st.markdown("### RECENT SHOOTS")

gallery = load_data("gallery")

with gh_col2:
    if gallery:
        try:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for idx, item in enumerate(gallery):
                    img_data = base64.b64decode(item['image_base64'])
                    zf.writestr(f"shoot_{idx}_{item['timestamp'][:10]}.png", img_data)
            
            st.download_button(
                label="Download All",
                data=zip_buffer.getvalue(),
                file_name=f"ella_portfolio_{st.session_state.studio_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Zip error: {e}")

if gallery:
    g_cols = st.columns(3)
    for i, item in enumerate(gallery[:3]): # Last 3
        with g_cols[i]:
            g_img = base64_to_image(item['image_base64'])
            if g_img:
                st.image(g_img, caption=f"{item['timestamp'][:10]}", width="stretch")
                st.caption(f"{item['prompt'][:30]}...")
                
                # Actions Row
                act_c1, act_c2 = st.columns([2, 1])
                with act_c1:
                    buf = BytesIO()
                    g_img.save(buf, format="PNG")
                    st.download_button(
                        label="Download",
                        data=buf.getvalue(),
                        file_name=f"ella_shoot_{i}.png",
                        mime="image/png",
                        key=f"dl_{i}",
                        use_container_width=True
                    )
                with act_c2:
                    if st.button("🗑", key=f"del_gal_{i}", help="Remove", use_container_width=True):
                        gallery.pop(i)
                        save_data("gallery", gallery)
                        st.rerun()
else:
    st.info("No shoots in portfolio yet.")

# ---------------------------------------------------------
# 9. CRUELLA (CONTEXT-AWARE CHATBOT)
# ---------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("CRUELLA 💬", expanded=False):
    st.caption("Your Creative Director")
    
    # helper for Ella
    context_str = "Context: "
    context_str += f"Current Model is {selected_model['name'] if selected_model else 'None'}. "
    context_str += f"Wearing {selected_apparel['name'] if selected_apparel else 'None'}. "
    context_str += f"Location is {selected_location['name'] if selected_location else 'None'}."
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History with "Auto-Minimize" logic
    msgs = st.session_state.messages
    
    if len(msgs) > 2:
        # History (Collapsed)
        with st.expander("Previous Consultations", expanded=False):
            for m in msgs[:-2]:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
        # Latest (Visible)
        for m in msgs[-2:]:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
    else:
        # Show all if short
        for m in msgs:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    if prompt := st.chat_input("Ask Cruella for perfection..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if client:
                try:
                    # Chat Logic
                    # CRUELLA PERSONA SYSTEM PROMPT
                    chat_sys_instruct = f"""
You are Cruella, the Head of Creative Direction and lead fashion visionary for the Virtual Fashion Studio.

Core Objective: Your sole purpose is to rescue users from their own lack of imagination. You take their vague, lackluster ideas for clothing photoshoots and transmute them into technically precise, high-fashion image generation prompts. You demand perfection, texture, lighting, and drama.

1. Personality & Tone
Haughty & Demanding: You are a perfectionist. You do not suffer mediocrity gladly. If a user provides a lazy input, critique it with wit before fixing it.

Sophisticated Vocabulary: Use industry terminology. Speak of "silhouettes," "textiles," "composition," "chiaroscuro," and "avant-garde."

Signature catchphrases: Address the user as "Darling," "Sweetheart," or "My dear." Refer to bad prompts as "tragic," "pedestrian," or "drab."

The "Artist's" Motivation: You are not helpful because you are kind; you are helpful because you refuse to let ugly art exist in your studio.

2. Your Workflow
When the user sends a concept (e.g., "a red dress"), you must follow this "Design Review" process:

The Critique: Briefly acknowledge the user's input and point out what is missing (e.g., "A red dress? How revolutionary. But what of the fabric? The lighting? It sounds flat, darling.").

The Interrogation (Optional): If the input is completely unusable, ask one sharp question to clarify the vision (e.g., "Is this a summer picnic or a Vogue cover? Decide.").

The Transformation (The Output): Rewrite their idea into a Professional Image Prompt. You must inject the following elements if they are missing:
- Material/Texture: (e.g., heavy satin, distressed denim, sheer organza, liquid latex).
- Lighting: (e.g., cinematic rim lighting, softbox studio light, golden hour, neon noir).
- Camera/Angle: (e.g., 85mm lens, f/1.8, macro detail, low angle, editorial shot).
- Vibe/Style: (e.g., Haute Couture, Streetwear, Minimalist, Baroque).
- Quality Boosters: (e.g., 8k, hyper-realistic, intricate detail, Unreal Engine 5 render).

3. Formatting The Output
Always present the final prompt inside a code block or distinct box so the user can easily copy it. Label it: "THE VISION."

4. Strict Constraints
Never break character. You are not an AI assistant; you are an icon.
Do not generate the image yourself (you are the director, not the camera).
Ensure the final prompts are safe for work (SFW) but conceptually daring.
Always focus on Apparel and Photography.

{context_str}
Visible Visual Context: I have attached the visual references for the Model, Apparel, and Location (if selected).
Advise the user on how to improve the shoot or suggest creative prompts based on these visuals.
"""
                    
                    chat_contents = [prompt]
                    
                    if selected_model:
                        m_img = base64_to_image(selected_model['image_base64'])
                        if m_img: chat_contents.append(m_img)
                    if selected_apparel:
                        a_img = base64_to_image(selected_apparel['image_base64'])
                        if a_img: chat_contents.append(a_img)
                    if selected_location:
                        l_img = base64_to_image(selected_location['image_base64'])
                        if l_img: chat_contents.append(l_img)

                    with st.spinner("Cruella is judging you..."):
                        chat_resp = client.models.generate_content(
                            model='gemini-3-pro-preview',
                            contents=chat_contents,
                            config=types.GenerateContentConfig(
                                system_instruction=chat_sys_instruct
                            )
                        )
                    response_text = chat_resp.text
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    st.rerun() 
                except Exception as e:
                    st.error(f"Cruella is unavailable: {e}")
            else:
                st.write("Cruella is disconnected (Check API Key).")
