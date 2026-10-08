import os
from PIL import Image, ImageDraw, ImageFont
from app.core.config import settings

def generate_certificate(
    recipient_name: str,
    event_name: str,
    event_date: str,
    certificate_id: str,
    job_id: str
) -> str:
    template_path = os.path.join(os.getcwd(), "assets", "aereo_hackathon_certificate_template_updated.png")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")
        
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 25)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    img_w, img_h = img.size
    
    # --- 1. Replace Event Name ---
    event_y = img_h * 0.23
    draw.rectangle(
        [img_w * 0.1, event_y - 20, img_w * 0.9, event_y + 45],
        fill="white"
    )
    event_text = event_name.upper()
    evt_bbox = draw.textbbox((0, 0), event_text, font=font_small)
    evt_w = evt_bbox[2] - evt_bbox[0]
    draw.text(((img_w - evt_w) / 2, event_y), event_text, fill="#3498db", font=font_small)
    
    # --- 2. Replace [RECIPIENT NAME] ---
    rect_width = 800
    rect_height = 80
    center_x = img_w / 2
    center_y = img_h * 0.350
    draw.rectangle(
        [center_x - rect_width/2, center_y - rect_height/2, center_x + rect_width/2, center_y + rect_height/2],
        fill="white"
    )
    bbox = draw.textbbox((0, 0), recipient_name, font=font_large)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (img_w - text_w) / 2
    y = center_y - (text_h / 2) - 15
    draw.text((x, y), recipient_name, fill="#1c4873", font=font_large)
    
    # --- 3. Replace the "for participating..." sentence ---
    sentence_y = img_h * 0.42
    draw.rectangle(
        [img_w * 0.1, sentence_y - 13, img_w * 0.9, sentence_y + 28],
        fill="white"
    )
    sentence_text = f"for participating in the {event_name} held on {event_date}."
    sent_bbox = draw.textbbox((0, 0), sentence_text, font=font_small)
    sent_w = sent_bbox[2] - sent_bbox[0]
    draw.text(((img_w - sent_w) / 2, sentence_y), sentence_text, fill="#5a6872", font=font_small)
    
    # --- 4. Replace Certificate ID at bottom left ---
    id_x = img_w * 0.08
    id_y = img_h * 0.92
    draw.rectangle(
        [img_w * 0.03, id_y - 15, id_x + 600, id_y + 40],
        fill="white"
    )
    cert_text = f"Certificate ID: {certificate_id}"
    draw.text((id_x, id_y), cert_text, fill="#5a6872", font=font_small)
    
    # --- 5. Replace "Issued: ..." at bottom right ---
    issued_x = img_w * 0.60
    draw.rectangle(
        [issued_x, id_y - 15, img_w * 0.97, id_y + 40],
        fill="white"
    )
    issued_text = f"Issued: {event_date}"
    draw.text((issued_x + 60, id_y), issued_text, fill="#5a6872", font=font_small)
    
    # Ensure storage path exists
    output_dir = os.path.join(settings.CERTIFICATE_STORAGE_PATH, job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{certificate_id}.pdf")
    img.save(output_path, "PDF", resolution=100.0)
    
    return output_path
