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
    # Base prompt with 50mm lens setup
    MASTER_BASE_PROMPT = (
        "Professional e-commerce fashion photography, wide shot, rule of thirds composition. "
        "Framing: Model is centered with visible headroom above and floor space below. "
        "Anatomy: Anatomically correct proportions, natural human height, realistic body structure. "
        "Camera: Shot on Phase One XF IQ4, 100MP, 50mm lens (eye-level angle), f/8 aperture. "
        "Quality: 4k native resolution, hyper-realistic, uncompressed, sharp details."
    )

    NEGATIVE_PROMPT = (
        "elongated body, stretched torso, long neck, unnatural height, distorted proportions, alien anatomy, "
        "cinematic lighting, dramatic shadows, artistic blur, bokeh, messy background, illustration, painting, "
        "3d render, low contrast, grain, noise, watermark, text."
    )

    @staticmethod
    def generate_payload(user_input: str, style: BrandStyle, aspect_ratio: str, use_custom_location: bool) -> str:
        # If custom location is used, we only take the Lighting/Pose from the style, not the Environment.
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
