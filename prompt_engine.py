"""
Author: Steven Lansangan
"""
from enum import Enum
import json
from typing import List, Dict

class BrandStyle(Enum):
    MINIMALIST = "Minimalist / Zara (Clean)"
    URBAN = "Urban / Streetwear (Hype)"
    LUXURY = "Luxury / Editorial (Vogue)"
    POP = "Pop / Fast Fashion (Bright)"

    @property
    def prompt_modifier(self):
        if self == BrandStyle.MINIMALIST:
            return "Environment: Infinite white cyclorama background, clean studio floor. Lighting: Softbox studio lighting, even illumination, neutral white balance, no harsh shadows. Pose: Neutral standing pose, arms relaxed, looking at camera, bored expression."
        elif self == BrandStyle.URBAN:
            return "Environment: Concrete wall, outdoor city street daytime, blurred depth. Lighting: Natural sunlight, slight hard shadow, high contrast. Pose: Candid walking motion, looking away, dynamic angle, streetwear aesthetic."
        elif self == BrandStyle.LUXURY:
            return "Environment: Dark grey textured backdrop, moody studio atmosphere. Lighting: Single spotlight, rim lighting on silhouette, dramatic contrast, warm tones. Pose: Sharp angular high-fashion pose, intense gaze, confident, elegant."
        elif self == BrandStyle.POP:
            return "Environment: Solid bright pastel color background (pink or yellow). Lighting: High-key lighting, overexposed brightness, vibrant colors. Pose: Cheerful, smiling, playful movement, hand on hip, energetic."
        return ""

class PromptGenerator:
    # Standard Setup
    MASTER_BASE_PROMPT = (
        "Professional e-commerce fashion photography, wide shot, rule of thirds composition. "
        "Framing: Model is centered with visible headroom above and floor space below. "
        "Anatomy: Anatomically correct proportions, natural human height, realistic body structure. "
        "Camera: Shot on Phase One XF IQ4, 100MP, 50mm lens (eye-level angle), f/8 aperture. "
        "Quality: 4k native resolution, hyper-realistic, uncompressed, sharp details. "
        "Cloth Physics: Clothing must drape naturally over the body, respecting gravity and fabric weight. Avoid rigid or floating textures. Realistic seam interaction with the pose."
    )

    NEGATIVE_PROMPT = (
        "elongated body, stretched torso, long neck, unnatural height, distorted proportions, alien anatomy, "
        "cinematic lighting, dramatic shadows, artistic blur, bokeh, messy background, illustration, painting, "
        "3d render, low contrast, grain, noise, watermark, text."
    )

    @staticmethod
    def generate_payload(user_input: str, style: BrandStyle, aspect_ratio: str, use_custom_location: bool, variation_idx: int = 0) -> str:
        # Override environment if custom loc
        style_text = style.prompt_modifier
        if use_custom_location:
            # Simple heuristic
            style_text += " IGNORE STYLE ENVIRONMENT. USE LOCATION IMAGE BACKGROUND."

        # Variation Logic
        pose_instruction = "Standard Pose: As described in prompt."
        if variation_idx == 1:
            pose_instruction = "Variation 2: DYNAMIC POSE. Distinctly different from the first shot. Side profile, walking motion, or active stance. Avoid static standing."
        elif variation_idx == 2:
            pose_instruction = "Variation 3: ALTERNATIVE ANGLE. Close-up detail, sitting, or artistic crop. Focus on mood and texture detail."

        return (
            f"STRICT INSTRUCTION: {PromptGenerator.MASTER_BASE_PROMPT} "
            f"Aspect Ratio: {aspect_ratio}. "
            f"Subject: {user_input}. "
            f"Pose Directive: {pose_instruction}. "
            f"Style Guide: {style_text} "
            f"Exclude: {PromptGenerator.NEGATIVE_PROMPT}"
        )

    @staticmethod
    def generate_campaign_payloads(user_input: str, style: BrandStyle, aspect_ratio: str, use_custom_location: bool) -> list[str]:
        """
        Parses user_input to see if it contains structured "Shot 1", "Shot 2" etc.
        Returns a list of 3 full prompts.
        """
        prompt_list = []
        
        # Check for structured input
        if "Shot 1" in user_input and "Shot 2" in user_input:
            # Simple parsing: Split by 'Shot '
            # Note: This relies on the user format "Shot 1:", "### Shot 2", etc.
            # We will split case-insensitive
            import re
            parts = re.split(r'Shot \d[:\.]?', user_input, flags=re.IGNORECASE)
            # parts[0] might be title or empty. parts[1] is shot 1, etc.
            
            clean_parts = [p.strip() for p in parts if len(p.strip()) > 20] # Filter out short noise
            
            # If parsing fails to get at least 2 distinct parts, fallback
            if len(clean_parts) >= 2:
                # We aim for 3. If only 2 found, we reuse the last one.
                for i in range(3):
                    # Get specific brief or fallback to last known
                    brief = clean_parts[i] if i < len(clean_parts) else clean_parts[-1]
                    
                    # Construct specific payload (No automatic variation injection)
                    # We reuse generate_payload logic but bypassing the pose variation key
                    style_text = style.prompt_modifier
                    if use_custom_location:
                         style_text += " IGNORE STYLE ENVIRONMENT. USE LOCATION IMAGE BACKGROUND."
                    
                    final = (
                        f"STRICT INSTRUCTION: {PromptGenerator.MASTER_BASE_PROMPT} "
                        f"Aspect Ratio: {aspect_ratio}. "
                        f"Subject: {brief}. "
                        f"Style Guide: {style_text} "
                        f"Exclude: {PromptGenerator.NEGATIVE_PROMPT}"
                    )
                    prompt_list.append(final)
                return prompt_list

        # FALLBACK: Standard Auto-Variation
        for i in range(3):
            prompt_list.append(PromptGenerator.generate_payload(user_input, style, aspect_ratio, use_custom_location, variation_idx=i))
        
        return prompt_list

    @staticmethod
    def parse_campaign_briefs(user_input: str, client) -> list[str]:
        """
        Uses Gemini 1.5 Pro to intelligently deconstruct the user's brief into 3 distinct shots.
        Returns a list of 3 raw shot descriptions.
        """
        import json
        import google.generativeai as genai

        # If no client provided or client error, fallback
        if not client:
             return [user_input, f"{user_input} (Variant)", f"{user_input} (Detail)"]

        try:
            # User Change: Explicit request for gemini-3-pro-preview
            model = client.GenerativeModel('gemini-3-pro-preview') 
            
            system_instruction = (
                "You are Cruella, a High-Fashion Creative Director. "
                "Your Task: Analyze the user's creative brief execution plan. "
                "Output Requirement: BREAK IT DOWN into exactly 3 distinct fashion shots (Hero, Dynamic, Detail). "
                "Rules:"
                "1. If the user provided specific 'Shot 1/2/3' instructions, extract them exactly."
                "2. If the user provided a vague theme, YOU MUST INVENT 3 distinct variations (Wide/Standard, Motion/Action, Close-up/Detail)."
                "3. Output MUST be a raw JSON list of 3 strings. No markdown formatting."
                "Example Output: [\"Shot 1 description...\", \"Shot 2 description...\", \"Shot 3 description...\"]"
            )
            
            response = model.generate_content(
                f"{system_instruction}\n\nUser Brief: {user_input}\n\nOutput the JSON list of 3 shots:",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            
            # Clean response (Strip Markdown if present)
            raw_text = response.text
            if "```json" in raw_text:
                raw_text = raw_text.replace("```json", "").replace("```", "")
            elif "```" in raw_text:
                 raw_text = raw_text.replace("```", "")

            # Parse JSON
            if raw_text:
                shots = json.loads(raw_text.strip())
                if isinstance(shots, list) and len(shots) >= 3:
                    return shots[:3] # Ensure exactly 3
                
        except Exception as e:
            print(f"AI Chunking Error: {e}")
        
        # Fallback if AI fails
        return [
            f"{user_input}",
            f"{user_input}. DYNAMIC VARIATION: Side profile, walking motion, or active stance.",
            f"{user_input}. DETAIL SHOT: Close-up, alternative angle, focus on texture/mood."
        ]

    @staticmethod
    def generate_accessory_payload(base_desc: str, accessory_desc: str) -> str:
        return (
            f"STRICT INSTRUCTION: Image Editing / Object Insertion. "
            f"Base Context: {base_desc}. "
            f"Task: Add the following accessory to the model: {accessory_desc}. "
            f"Requirements: 1. The accessory must look photorealistic and chemically bonded to the image (lighting, shadows, reflections). "
            f"2. DO NOT change the Model's face or the original dress. "
            f"3. High Fidelity Texture: Ensure gold looks like gold, leather looks like leather. "
            f"Output: A final composited e-commerce shot."
        )

    @staticmethod
    def generate_edit_payload(base_desc: str, edit_instruction: str) -> str:
        return (
            f"STRICT INSTRUCTION: Image Editing / Remix. "
            f"Base Context: {base_desc}. "
            f"User Edit Request: {edit_instruction}. "
            f"Constraints: 1. KEEP the original Pose, Composition, and Lighting structure unless explicitly told to change it. "
            f"2. Apply the user's edit naturally into the scene. "
            f"3. Maintain high photorealism and 4k quality. "
            f"Output: A final composited e-commerce shot."
        )

class ShotListGenerator:
    """
    Analyzes a user prompt and breaks it down into distinct, varied shots (poses/angles).
    """
    
    @staticmethod
    def generate_shot_list(client, user_prompt: str, min_count: int = 3) -> List[Dict[str, str]]:
        """
        Uses Gemini text model to create a JSON list of shots.
        Dynamically determines the number of shots based on user intent (min_count to ~6).
        """
        system_instruction = (
            "You are an expert Fashion Photographer producing a 'Shot List'.\n"
            "Task: Break the user's concept into a complete fashion campaign.\n"
            "Requirements:\n"
            f"1. QUANTITY: Generate AT LEAST {min_count} shots. If the user's brief contains more specific ideas/scenes, generate a shot for EACH one (up to 8).\n"
            "2. Variety: Vary the camera angles (Wide, Medium, Close-up, Low angle).\n"
            "3. Poses: Ensure each shot has a distinct, active pose (Walking, Sitting, Leaning, Dynamic).\n"
            "4. Consistency: Keep the same model and clothing description, just change the action/framing.\n\n"
            "Output: Strictly valid JSON list of objects. No markdown formatting.\n"
            "Format:\n"
            "[\n    {\"title\": \"The Walk\", \"description\": \"Full body shot...\"},\n    {\"title\": \"The Detail\", \"description\": \"Close-up shot...\"}\n]"
        )
        
        try:
            # Note: client is likely the Google GenAI Module or Client object
            # Adapting to standard Google GenAI SDK usage if client = genai
            if hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
                 # Vertex AI style or specific wrapper
                 response = client.models.generate_content(
                    model='gemini-3-pro-preview',
                    contents=f"User Concept: {user_prompt}\nTarget: Dynamic Campaign (Min {min_count} shots)",
                    config={'response_mime_type': 'application/json', 'system_instruction': system_instruction}
                )
            else:
                # Standard Google Generative AI SDK style
                # model = client.GenerativeModel(...)
                model = client.GenerativeModel(
                    model_name='gemini-1.5-pro', # Fallback
                    system_instruction=system_instruction
                )
                try: 
                    model = client.GenerativeModel('gemini-3-pro-preview', system_instruction=system_instruction)
                except:
                    model = client.GenerativeModel('gemini-1.5-pro', system_instruction=system_instruction)

                response = model.generate_content(
                    f"User Concept: {user_prompt}\nTarget: Dynamic Campaign (Min {min_count} shots)",
                    generation_config={'response_mime_type': 'application/json'}
                )

            # Parse
            raw = response.text
            if "```json" in raw: raw = raw.replace("```json", "").replace("```", "")
            elif "```" in raw: raw = raw.replace("```", "")
            
            return json.loads(raw)
            
        except Exception as e:
            print(f"Chunking failed: {e}")
            # Fallback
            return [
                {"title": "Standard Front", "description": f"Standard front view. {user_prompt}"},
                {"title": "Side Profile", "description": f"Side profile view. {user_prompt}"},
                {"title": "Detail Shot", "description": f"Close up detail shot. {user_prompt}"}
            ][:min_count]
