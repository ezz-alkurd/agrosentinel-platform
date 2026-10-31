"""Generate independent Pillow reference tensors for the Dart preprocessing tests."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

OUT = Path(__file__).resolve().parent.parent / "app/test/fixtures"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, width, height, orientation in [
        ("square", 224, 224, None),
        ("portrait", 303, 517, None),
        ("landscape", 97, 65, None),
        ("rotated", 291, 163, 6),
    ]:
        y, x = np.indices((height, width))
        rgb = np.stack(((x*17+y*3)%256, (x*5+y*19)%256, (x*23+y*7)%256), axis=-1).astype(np.uint8)
        if orientation:
            # Distinct smooth horizontal/vertical gradients make rotations observable
            # without coupling the geometry test to high-frequency JPEG IDCT artifacts.
            red = x * 255 // (width - 1)
            green = y * 255 // (height - 1)
            rgb = np.stack((red, green, (2 * red + green) // 3), axis=-1).astype(np.uint8)
        image = Image.fromarray(rgb)
        path = OUT / (name + (".jpg" if orientation else ".png"))
        if orientation:
            exif = Image.Exif(); exif[274] = orientation
            # This fixture isolates EXIF rotation and resize/crop from codec-specific
            # chroma upsampling. Pillow and Dart use different 4:2:0 upsamplers.
            image.save(path, quality=95, subsampling=0, exif=exif)
        else:
            image.save(path)
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        width, height = image.size
        size = (224, int(224*height/width)) if width <= height else (int(224*width/height), 224)
        image = image.resize(size, Image.Resampling.BILINEAR)
        left, top = round((size[0]-224)/2), round((size[1]-224)/2)
        image = image.crop((left, top, left+224, top+224))
        (OUT / (name+".rgb")).write_bytes(np.asarray(image).tobytes())
        print(name, path.stat().st_size)

if __name__ == "__main__": main()
