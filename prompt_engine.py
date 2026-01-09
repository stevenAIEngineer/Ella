"""
Author: Steven Lansangan
"""
from enum import Enum

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
    def parse_campaign_briefs(user_input: str) -> list[str]:
        """
        Returns a list of 3 raw shot descriptions (Subject/Pose only) for the UI editors.
        Uses regex to find specific 'Shot X' blocks to ensure correct slotting.
        """
        import re
        briefs = ["", "", ""] # Fixed size 3
        
        # Check if basic markers exist
        has_structure = bool(re.search(r'Shot \d', user_input, re.IGNORECASE))
        
        if has_structure:
            # Robust Extraction: Find text for specific shots indepedently
            # Pattern: "Shot X" ... (content) ... (Next "Shot" or End of String)
            
            # Shot 1
            m1 = re.search(r'Shot 1[:\s\.]+(.*?)(?=Shot \d|$)', user_input, re.IGNORECASE | re.DOTALL)
            if m1: briefs[0] = m1.group(1).strip()
            
            # Shot 2
            m2 = re.search(r'Shot 2[:\s\.]+(.*?)(?=Shot \d|$)', user_input, re.IGNORECASE | re.DOTALL)
            if m2: briefs[1] = m2.group(1).strip()
            
            # Shot 3
            m3 = re.search(r'Shot 3[:\s\.]+(.*?)(?=Shot \d|$)', user_input, re.IGNORECASE | re.DOTALL)
            if m3: briefs[2] = m3.group(1).strip()
            
            # Fallback for "Shot 1" only cases where others might be implied or mis-numbered?
            # For now, strict mapping is safer as requested.
            
            # If we found at least one structured shot, return the list.
            # Even if Shot 2 is empty, it stays empty in the UI.
            if any(briefs):
                return briefs

        # FALLBACK: Standard Auto-Variation
        base = user_input
        briefs[0] = f"{base}"
        briefs[1] = f"{base}. DYNAMIC VARIATION: Side profile, walking motion, or active stance. Distinct difference."
        briefs[2] = f"{base}. DETAIL SHOT: Close-up, alternative angle, or artistic crop. Focus on texture/mood."
        
        return briefs

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
