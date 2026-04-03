#!/usr/bin/env python3
"""Generate a KDP-ready ebook cover (1600x2560px) using Pillow.

Usage: python3 generate-cover.py <output_path> <title> <subtitle> <author> [gradient_top] [gradient_bottom] [accent_color]

Produces a professional-looking gradient cover with typography.
KDP spec: 1600x2560 pixels, 10:16 aspect ratio, sRGB, JPEG or TIFF.
"""

import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip3 install Pillow")
    sys.exit(1)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient(width, height, top_color, bottom_color):
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = top_color
    r2, g2, b2 = bottom_color
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def find_font(preferred_names, size):
    """Try to find a system font, fall back to default."""
    font_dirs = [
        "/System/Library/Fonts/Supplemental/",
        "/System/Library/Fonts/",
        "/Library/Fonts/",
        os.path.expanduser("~/Library/Fonts/"),
        "/usr/share/fonts/truetype/",
    ]
    for font_dir in font_dirs:
        for name in preferred_names:
            for ext in ['.ttf', '.otf', '.ttc']:
                path = os.path.join(font_dir, name + ext)
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines


def generate_cover(output_path, title, subtitle, author,
                   gradient_top='#1a1a2e', gradient_bottom='#16213e',
                   accent_color='#e2b97f'):
    WIDTH = 1600
    HEIGHT = 2560
    MARGIN = 120

    top_rgb = hex_to_rgb(gradient_top)
    bottom_rgb = hex_to_rgb(gradient_bottom)
    accent_rgb = hex_to_rgb(accent_color)

    # Create gradient background
    img = create_gradient(WIDTH, HEIGHT, top_rgb, bottom_rgb)
    draw = ImageDraw.Draw(img)

    # Accent line near top
    line_y = 380
    draw.line([(MARGIN + 200, line_y), (WIDTH - MARGIN - 200, line_y)],
              fill=accent_rgb, width=3)

    # Title
    title_font = find_font(['Georgia', 'Times New Roman', 'Palatino', 'Baskerville'], 120)
    title_lines = wrap_text(title.upper(), title_font, WIDTH - MARGIN * 2, draw)
    title_y = 450
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        # Shadow
        draw.text((x + 3, title_y + 3), line, font=title_font, fill=(0, 0, 0, 128))
        draw.text((x, title_y), line, font=title_font, fill=accent_rgb)
        title_y += bbox[3] - bbox[1] + 30

    # Accent line below title
    line_y2 = title_y + 40
    draw.line([(MARGIN + 200, line_y2), (WIDTH - MARGIN - 200, line_y2)],
              fill=accent_rgb, width=3)

    # Subtitle
    if subtitle and subtitle.strip():
        subtitle_font = find_font(['Georgia', 'Times New Roman', 'Palatino'], 60)
        sub_lines = wrap_text(subtitle, subtitle_font, WIDTH - MARGIN * 2, draw)
        sub_y = line_y2 + 60
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (WIDTH - text_width) // 2
            draw.text((x, sub_y), line, font=subtitle_font, fill=(220, 220, 220))
            sub_y += bbox[3] - bbox[1] + 15

    # Series label (if "Book N" or similar in subtitle)
    # Decorative element in middle area
    mid_y = HEIGHT // 2
    draw.ellipse([(WIDTH // 2 - 80, mid_y - 80), (WIDTH // 2 + 80, mid_y + 80)],
                 outline=accent_rgb, width=2)
    draw.ellipse([(WIDTH // 2 - 60, mid_y - 60), (WIDTH // 2 + 60, mid_y + 60)],
                 outline=accent_rgb, width=1)

    # Author name at bottom
    author_font = find_font(['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'], 72)
    bbox = draw.textbbox((0, 0), author.upper(), font=author_font)
    text_width = bbox[2] - bbox[0]
    author_y = HEIGHT - 300
    x = (WIDTH - text_width) // 2

    # Author accent line above
    draw.line([(MARGIN + 200, author_y - 40), (WIDTH - MARGIN - 200, author_y - 40)],
              fill=accent_rgb, width=2)

    draw.text((x, author_y), author.upper(), font=author_font, fill=(255, 255, 255))

    # Save
    img.save(output_path, 'JPEG', quality=95, subsampling=0)
    file_size = os.path.getsize(output_path)
    print(f"Cover generated: {output_path}")
    print(f"  Dimensions: {WIDTH}x{HEIGHT}px")
    print(f"  File size:  {file_size / 1024:.0f} KB")


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: generate-cover.py <output> <title> <subtitle> <author> [top_color] [bottom_color] [accent]")
        sys.exit(1)

    output = sys.argv[1]
    title = sys.argv[2]
    subtitle = sys.argv[3]
    author = sys.argv[4]
    top = sys.argv[5] if len(sys.argv) > 5 else '#1a1a2e'
    bottom = sys.argv[6] if len(sys.argv) > 6 else '#16213e'
    accent = sys.argv[7] if len(sys.argv) > 7 else '#e2b97f'

    generate_cover(output, title, subtitle, author, top, bottom, accent)
