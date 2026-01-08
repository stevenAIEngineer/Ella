# ELLA STUDIO: Technical Architecture & Vision Document

## 1. Mission & Vision
**ELLA STUDIO** is a "Virtual Fashion Studio" designed to democratize high-end e-commerce photography. 
*   **Vision:** To eliminate the need for physical photoshoots by allowing users to virtually dress any model in any garment with photorealistic, commercial-grade results.
*   **Mission:** Empower fashion brands and creators with an AI-driven "Creative Director" (Cruella) and a "Virtual Photographer" (Nano Banana Pro) that prioritizes specific apparel details, natural anatomical blending, and consistent brand aesthetics over generic AI art.

## 2. Core Logic & Workflow
The application operates on a linear, user-centric pipeline:

### A. The Vault (Asset Management)
*   **Data Structure:** User-specific JSON databases (`roster.json`, `closet.json`, `locations.json`) store Base64-encoded assets.
*   **Dual-Reference Models:** 
    *   Models are defined by TWO images: a **Face Reference (Close-Up)** for identity preservation and a **Body Reference (Full Shot)** for pose/proportions.
    *   This "Head/Body" split is critical for the "Anatomical Integration" logic.

### B. The Fusion Studio (Scene Composition)
*   **Selection:** Users select a Model, Apparel, and Location (optional) from their Vault.
*   **Brand Styles (The "Banana Split" Logic):** 
    *   Users choose a vibe (e.g., "Zara Minimalist" vs. "Vogue Luxury").
    *   **Smart Injection:** If no location is uploaded, the style injects a detailed environment description. If a location *is* uploaded, the style strictly overrides the environment prompt to force the custom background while keeping the lighting vibe.

### C. The Generation Pipeline (Nano Banana Pro)
The core engine uses `gemini-3-pro-image-preview` (codenamed "Nano Banana Pro") with a sophisticated 3-stage mental prompt:
1.  **Phase 1: Anatomical Integration:** The AI is instructed to first build a coherent human by blending the selected Face onto the Body reference seamlessly at the neck.
2.  **Phase 2: Virtual Try-On:** The Apparel is "mentally draped" onto this new cohesive human figure, respecting gravity and fabric physics.
3.  **Phase 3: Compositing:** The dressed figure is placed into the Location with matching lighting.

### D. Cruella (The AI Creative Director)
*   **Persona:** A haughty, demanding, high-fashion critic.
*   **Function:** She analyzes the *visual* inputs (images) alongside the user's text prompt.
*   **Output:** She provides a single, copy-pasteable "VISION" code block, stripped of technical jargon, focusing purely on widely descriptive visual excellence.

## 3. Technical Architecture
*   **Frontend:** Streamlit (Python).
*   **Backend Logic:** Python `google-genai` SDK.
*   **Model:** Google Gemini 3 Pro Experimental (Multimodal).
*   **State Management:** Local JSON files (simulating a database) + Streamlit Session State.
*   **Deployment:** Railway (Dockerized via `Procfile`).

## 4. Key Features
*   **Monochrome Luxury UI:** Custom CSS variables enforce a strict black/white/grey aesthetic with high-end typography (Jost, Cormorant Garamond).
*   **Background Consistency:** "Smart Environment Injection" ensures styles don't conflict with custom uploaded backgrounds.
*   **Anatomical Priority:** Prompt engineering specifically targets "neck connection" and "floating head" issues.
*   **Portfolio Archive:** A persistent, scrollable gallery of past shoots with "Download All" (Zip) and "Clear All" functionality.

## 5. Future Roadmap
*   **Video Generation:** Expanding the pipeline to animated runway walks.
*   **Specific Brand Fine-Tuning:** Training LoRA adapters for specific clothing brands.
