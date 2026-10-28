import io
import base64
from typing import Optional

def process_avatar_image(file_storage, max_size=(400, 400), quality=85) -> Optional[str]:
    """
    Process an uploaded avatar image in memory:
    - Resizes to max 400x400 maintaining aspect ratio
    - Optimizes and compresses to JPEG
    - Returns a Data URI string: 'data:image/jpeg;base64,...'
    
    Why this is essential:
    On serverless platforms like Vercel (AWS Lambda), the container filesystem is
    strictly read-only ('/var/task' [Errno 30]). In-memory Base64 Data URI stores
    directly into MongoDB, requires zero disk writes, and persists permanently.
    """
    if not file_storage or not getattr(file_storage, 'filename', None) or file_storage.filename == '':
        return None

    try:
        file_bytes = file_storage.read()
        if not file_bytes:
            return None
        
        # Reset pointer in case file is read again
        if hasattr(file_storage, 'seek'):
            try:
                file_storage.seek(0)
            except Exception:
                pass

        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            
            # Convert transparency / RGBA to RGB with white background
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as pil_err:
            print(f"[Image Processing - PIL Fallback] {pil_err}")
            # If PIL resize fails, fallback to encoding raw file bytes directly
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            ext = file_storage.filename.rsplit('.', 1)[1].lower() if '.' in file_storage.filename else 'png'
            mime = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
            return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"[Image Processing Error] {e}")
        return None
