#!/usr/bin/env python3
"""Overlay title, series line, and author name onto a DALL-E artwork image.

Usage: python3 overlay-cover-text.py <input_image> <output_path> <title> <series_line> <author> [accent_hex]

Resizes to 1600x2560 (KDP spec), adds gradient overlays for text readability,
and renders title/series/author with proper typography.
"""

import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip3 install Pillow")
    sys.exit(1)

TARGET_W, TARGET_H = 1600, 2560

def hex_to_rgba(hex_color, alpha=255):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)

def find_font(names, size):
    font_dirs = [
        "/System/Library/Fonts/Supplemental/",
        "/System/Library/Fonts/",
        "/Library/Fonts/",
        os.path.expanduser("~/Library/Fonts/"),
        "/usr/share/fonts/truetype/",
    ]
    for d in font_dirs:
        for name in names:
            for ext in ['.ttf', '.otf', '.ttc']:
                path = os.path.join(d, name + ext)
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

def overlay_text(input_path, output_path, title, series_line, author, accent='#e6c391'):
    img = Image.open(input_path).convert('RGBA')
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    # Gradient overlays for text readability
    overlay = Image.new('RGBA', (TARGET_W, TARGET_H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    # Top band
    for y in range(0, 550):
        alpha = int(190 * (1 - y / 550))
        odraw.line([(0, y), (TARGET_W, y)], fill=(0, 0, 0, alpha))
    # Bottom band
    for y in range(TARGET_H - 350, TARGET_H):
        alpha = int(190 * ((y - (TARGET_H - 350)) / 350))
        odraw.line([(0, y), (TARGET_W, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    accent_rgba = hex_to_rgba(accent)
    accent_rgb = accent_rgba[:3]

    # Fonts
    title_font = find_font(['Georgia', 'Times New Roman', 'Palatino', 'Baskerville'], 110)
    series_font = find_font(['Georgia', 'Times New Roman', 'Palatino'], 46)
    author_font = find_font(['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'], 62)

    # Title (top area)
    title_upper = title.upper()
    title_lines = wrap_text(title_upper, title_font, TARGET_W - 200, draw)
    y = 100
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (TARGET_W - w) // 2
        draw.text((x + 3, y + 3), line, font=title_font, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=title_font, fill=accent_rgb)
        y += bbox[3] - bbox[1] + 15

    # Accent line below title
    draw.line([(350, y + 15), (TARGET_W - 350, y + 15)], fill=accent_rgb, width=2)

    # Series line
    if series_line and series_line.strip():
        bbox = draw.textbbox((0, 0), series_line, font=series_font)
        w = bbox[2] - bbox[0]
        sx = (TARGET_W - w) // 2
        sy = y + 35
        draw.text((sx + 2, sy + 2), series_line, font=series_font, fill=(0, 0, 0, 180))
        draw.text((sx, sy), series_line, font=series_font, fill=(210, 210, 210))

    # Accent line above author
    ay = TARGET_H - 180
    draw.line([(350, ay - 30), (TARGET_W - 350, ay - 30)], fill=accent_rgb, width=2)

    # Author (bottom area)
    author_upper = author.upper()
    bbox = draw.textbbox((0, 0), author_upper, font=author_font)
    w = bbox[2] - bbox[0]
    ax = (TARGET_W - w) // 2
    draw.text((ax + 2, ay + 2), author_upper, font=author_font, fill=(0, 0, 0, 200))
    draw.text((ax, ay), author_upper, font=author_font, fill=(255, 255, 255))

    # Save
    img = img.convert('RGB')
    img.save(output_path, 'JPEG', quality=95, subsampling=0)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Cover saved: {output_path}")
    print(f"  {TARGET_W}x{TARGET_H}px | {size_kb:.0f} KB")

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print("Usage: overlay-cover-text.py <input> <output> <title> <series_line> <author> [accent_hex]")
        sys.exit(1)
    accent = sys.argv[6] if len(sys.argv) > 6 else '#e6c391'
    overlay_text(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], accent)
