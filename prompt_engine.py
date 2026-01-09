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
    def generate_payload(user_input: str, style: BrandStyle, aspect_ratio: str, use_custom_location: bool) -> str:
        # Override environment if custom loc
        style_text = style.prompt_modifier
        if use_custom_location:
            # Simple heuristic to strip environment text if needed, or rely on the model to prioritize the image input.
            # For now, we append the full style but add a strong override instruction.
            style_text += " IGNORE STYLE ENVIRONMENT. USE LOCATION IMAGE BACKGROUND."

        return (
            f"STRICT INSTRUCTION: {PromptGenerator.MASTER_BASE_PROMPT} "
            f"Aspect Ratio: {aspect_ratio}. "
            f"Subject: {user_input}. "
            f"Style Guide: {style_text} "
            f"Exclude: {PromptGenerator.NEGATIVE_PROMPT}"
        )

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
