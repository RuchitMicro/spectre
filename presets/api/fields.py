# fields.py
import io
import os
import uuid
from io                             import BytesIO
from PIL                            import Image, ImageSequence
from django.db                      import models
from django.db.models.fields.files  import FileField, FieldFile, ImageFieldFile, ImageField
from django.core.files.base         import ContentFile
from django.core.files.uploadedfile import UploadedFile

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "tiff", "bmp", "gif"}

def _random_name(original_name):
    ext = os.path.splitext(original_name)[1].lower() or ''
    return f"{uuid.uuid4().hex}{ext}"

def _is_image_name(name):
    ext = os.path.splitext(name)[1].lstrip('.').lower()
    return ext in IMAGE_EXTS


def _compress_image_file(uploaded_file, max_width=1920, quality=70):
    """
    Compress/resize uploaded_file (file-like) and return a ContentFile of the result.
    - Preserves animation for GIF / animated WebP when Pillow supports it.
    - Skips compression for vector formats (svg) or if Pillow cannot open the file.
    - Falls back to original bytes on any error.
    """
    uploaded_file.seek(0)
    try:
        img = Image.open(uploaded_file)
    except Exception:
        # Not an image Pillow can handle (SVG, corrupt, etc.) — return original bytes
        uploaded_file.seek(0)
        return ContentFile(uploaded_file.read())

    fmt = (img.format or "").upper()
    if fmt == "SVG":
        # Vector image — don't rasterize or compress (could alter appearance)
        uploaded_file.seek(0)
        return ContentFile(uploaded_file.read())

    # Helper to resize a frame while preserving mode
    def _resize_frame(frame):
        if max_width and getattr(frame, "width", None) and frame.width > max_width:
            ratio = max_width / float(frame.width)
            new_h = int(frame.height * ratio)
            return frame.resize((max_width, new_h), Image.LANCZOS)
        return frame

    buf = BytesIO()

    try:
        # Animated image handling
        is_animated = getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1

        if is_animated:
            frames = []
            durations = []
            disposals = []
            # collect frames (convert palettes to RGBA/RGB carefully)
            for frame in ImageSequence.Iterator(img):
                frame = frame.convert("RGBA") if frame.mode in ("P", "RGBA", "LA") else frame.convert("RGB") if frame.mode != "RGB" else frame
                frame = _resize_frame(frame)
                frames.append(frame)
                durations.append(frame.info.get("duration", img.info.get("duration", 100)))
                disposals.append(frame.info.get("disposal", 2))

            # Save animated GIF
            if fmt == "GIF":
                save_kwargs = dict(format="GIF", save_all=True, append_images=frames[1:], loop=img.info.get("loop", 0),
                                   duration=img.info.get("duration", durations[0] if durations else 100), optimize=True, disposal=2)
                frames[0].save(buf, **save_kwargs)

            # Animated WebP (if Pillow supports): preserve frames
            elif fmt == "WEBP":
                save_kwargs = dict(format="WEBP", save_all=True, append_images=frames[1:], loop=img.info.get("loop", 0),
                                   duration=img.info.get("duration", durations[0] if durations else 100), quality=quality, method=6)
                frames[0].save(buf, **save_kwargs)

            else:
                # Unknown animated format — fall back to saving first frame (still resized)
                first = frames[0]
                if first.mode in ("RGBA", "LA") and fmt in ("JPEG", "JPG"):
                    first = first.convert("RGB")
                if fmt in ("JPEG", "JPG"):
                    first.save(buf, format="JPEG", quality=quality, optimize=True)
                elif fmt == "PNG":
                    first.save(buf, format="PNG", optimize=True)
                else:
                    first.save(buf, format=fmt)
        else:
            # Single-frame images
            frame = img
            # Convert paletted/alpha to appropriate mode for target format
            if frame.mode in ("P",):
                frame = frame.convert("RGBA")
            # Resize
            frame = _resize_frame(frame)

            # Convert RGBA->RGB if saving to JPEG
            if fmt in ("JPEG", "JPG") and frame.mode in ("RGBA", "LA", "P"):
                frame = frame.convert("RGB")

            if fmt in ("JPEG", "JPG"):
                frame.save(buf, format="JPEG", quality=quality, optimize=True)
            elif fmt == "PNG":
                # PNG: keep alpha if present
                save_kwargs = dict(format="PNG", optimize=True)
                frame.save(buf, **save_kwargs)
            elif fmt == "WEBP":
                # WebP: Pillow may or may not support; try to use lossy WebP
                try:
                    frame.save(buf, format="WEBP", quality=quality, method=6)
                except Exception:
                    # Fallback to PNG/JPEG depending on alpha
                    if frame.mode in ("RGBA",):
                        frame.save(buf, format="PNG", optimize=True)
                    else:
                        frame.save(buf, format="JPEG", quality=quality, optimize=True)
            else:
                # TIFF, BMP, ICO, etc. — try saving in original format; if that fails, fallback to PNG
                try:
                    frame.save(buf, format=fmt)
                except Exception:
                    try:
                        frame.save(buf, format="PNG", optimize=True)
                    except Exception:
                        # final fallback: return original bytes
                        uploaded_file.seek(0)
                        return ContentFile(uploaded_file.read())

        buf.seek(0)
        return ContentFile(buf.read())

    except Exception:
        # Any unexpected processing error — safe fallback to original bytes
        uploaded_file.seek(0)
        return ContentFile(uploaded_file.read())

class RandomizedFieldFile(FieldFile):
    """
    Base FieldFile that supports random-name behavior defined by the parent field.
    """
    def _final_name(self, original_name):
        if getattr(self.field, "random_name", True):
            return _random_name(original_name)
        return original_name

    def save(self, name, content, save=True):
        final_name = self._final_name(name)
        # delegate to parent implementation; subclasses may override further
        return super().save(final_name, content, save=save)

class CustomFileField(FileField):
    """
    Use in place of models.FileField.
    Params:
      - random_name (bool): default True. If True uploaded files are renamed to UUID.ext
    """
    attr_class = RandomizedFieldFile

    def __init__(self, *args, random_name=True, **kwargs):
        self.random_name = bool(random_name)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # persist the option for migrations
        if self.random_name is not True:
            kwargs['random_name'] = self.random_name
        return name, path, args, kwargs

class RandomizedImageFieldFile(ImageFieldFile, RandomizedFieldFile):
    """
    Handles randomization + compression for image uploads.
    Only compresses when `content` looks like an UploadedFile (i.e. a new upload).
    """

    def save(self, name, content, save=True):
        # If randomization requested - compute final name here (extension preserved)
        final_name = self._final_name(name)

        # Only process images and only for new uploads (UploadedFile)
        is_uploaded = isinstance(content, UploadedFile)
        looks_like_image = _is_image_name(final_name) or getattr(content, "content_type", "").startswith("image/")

        if is_uploaded and looks_like_image and getattr(self.field, "do_compress", True):
            max_w = getattr(self.field, "max_width", 1920)
            quality = getattr(self.field, "quality", 75)
            try:
                compressed = _compress_image_file(content, max_width=max_w, quality=quality)
                compressed.name = final_name
                return super(ImageFieldFile, self).save(final_name, compressed, save=save)
            except Exception:
                # On any failure, fall back to original content (but with randomized name)
                content.seek(0)

        # Either not uploaded, not image, or compression disabled -> just save (with randomized name if set)
        return super().save(final_name, content, save=save)

class CustomImageField(ImageField):
    """
    Use in place of models.ImageField.
    Params:
      - random_name (bool): default True
      - max_width (int|None): default 1920. If None no resizing by width.
      - quality (int): default 75. JPEG quality used when applicable.
      - do_compress (bool): default True. If False no compression/resizing will be applied.
    """
    attr_class = RandomizedImageFieldFile

    def __init__(self, *args, random_name=True, max_width=1920, quality=75, do_compress=True, **kwargs):
        self.random_name = bool(random_name)
        self.max_width = None if max_width is None else int(max_width)
        self.quality = int(quality)
        self.do_compress = bool(do_compress)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.random_name is not True:
            kwargs['random_name'] = self.random_name
        if self.max_width is not None and self.max_width != 1920:
            kwargs['max_width'] = self.max_width
        if self.quality != 75:
            kwargs['quality'] = self.quality
        if self.do_compress is not True:
            kwargs['do_compress'] = self.do_compress
        return name, path, args, kwargs