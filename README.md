# Ella Studio

**Ella Studio** is a high-fashion, AI-powered virtual photography studio. It allows users to fuse models, apparel, and locations into professional-grade editorial shots using advanced multimodal AI.

## The Idea
The goal of Ella is to bridge the gap between creative direction and AI generation. Instead of just typing prompts, users can manage a visual asset library ("The Vault") containing their own models, clothes, and backgrounds. The application then intelligently fuses these assets into a cohesive final image.

## How It Works
1.  **The Vault**: A persistent local database (JSON) where users upload and store their assets.
2.  **The Fusion Studio**: The main interface where users combine a Model + Apparel + Location and write a creative brief.
3.  **The Engine**: Beneath the hood, Ella uses an advanced **Multimodal Reasoning Engine**. It interprets the *actual pixel data* of the selected assets alongside the prompt, ensuring the final result respects the visual identity of the inputs.
4.  **Ella (The Persona)**: A context-aware Creative Director who can "see" the current selection and offer tailored advice or prompts.

## Project Structure
*   `app.py`: The main monolithic application file containing the UI, logic, and persistence layer.
*   `data/`: Directory storing the JSON databases for models, apparel, locations, and the gallery.
*   `requirements.txt`: Python dependencies.

## Key Features
*   **Monochrome Luxury UI**: A custom-styled dark interface focusing on the content.
*   **Multimodal Input**: Images are passed directly to the context window for high-fidelity reasoning.
*   **Persistent Gallery**: Automatically saves shoots and allows batch downloading.
*   **Context-Aware**: Ella knows what you are working on and sees what you see.

## Credits
**Developed by Steven Lansangan.**
*Full Stack Developer*
