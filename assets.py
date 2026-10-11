"""assets.py - generates the app icon in code (no image files to ship)."""

from PIL import Image, ImageDraw


def make_icon(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * 0.22)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill="#0B0B0F")
    w = max(2, size // 32)
    d.rounded_rectangle((w, w, size - 1 - w, size - 1 - w), radius=r - w, outline="#D4AF37", width=w)
    # gold check mark
    pts = [(size * 0.26, size * 0.52), (size * 0.43, size * 0.69), (size * 0.75, size * 0.33)]
    d.line(pts, fill="#D4AF37", width=max(3, size // 11), joint="curve")
    return img


def save_ico(path: str):
    make_icon(256).save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
