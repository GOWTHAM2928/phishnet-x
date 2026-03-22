"""
Generate placeholder icons for the PhishNet X extension.
Run this once to create PNG icons in the extension/icons/ folder.
"""

import os

def create_svg_icon(size, color="#dc2626"):
    """Create a simple shield SVG icon."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e293b"/>
      <stop offset="100%" style="stop-color:#334155"/>
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="22" fill="url(#g)"/>
  <path d="M50 15 L78 28 L78 52 C78 66 64 77 50 83 C36 77 22 66 22 52 L22 28 Z"
        fill="{color}" opacity="0.9"/>
  <path d="M42 50 L47 56 L60 43" stroke="white" stroke-width="5"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>'''

def main():
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extension", "icons")
    os.makedirs(icons_dir, exist_ok=True)

    sizes = [16, 32, 48, 128]

    try:
        # Try using cairosvg for proper PNG conversion
        import cairosvg
        for size in sizes:
            svg = create_svg_icon(size)
            output_path = os.path.join(icons_dir, f"icon{size}.png")
            cairosvg.svg2png(bytestring=svg.encode(), write_to=output_path, output_width=size, output_height=size)
            print(f"Created: icon{size}.png")
    except ImportError:
        # Fallback: save as SVG (Chrome also accepts SVG icons)
        print("cairosvg not available. Saving as SVG files.")
        for size in sizes:
            svg = create_svg_icon(size)
            # Save as PNG placeholder using PIL if available
            try:
                from PIL import Image, ImageDraw
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Draw a simple rounded rect background
                margin = size // 8
                draw.rounded_rectangle([margin, margin, size-margin, size-margin],
                                       radius=size//5, fill=(30, 41, 59, 255))
                # Draw shield
                cx, cy = size//2, size//2
                r = size//3
                draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(220, 38, 38, 230))
                output_path = os.path.join(icons_dir, f"icon{size}.png")
                img.save(output_path)
                print(f"Created: icon{size}.png (PIL)")
            except ImportError:
                # Last resort: save SVG with .png extension (won't work in Chrome but allows testing)
                output_path = os.path.join(icons_dir, f"icon{size}.png")
                with open(output_path.replace(".png", ".svg"), "w") as f:
                    f.write(create_svg_icon(max(size, 48)))
                print(f"Saved SVG: icon{size}.svg (rename to .png or install cairosvg/PIL)")

    print(f"\nIcons saved to: {icons_dir}")
    print("Note: For production, use proper PNG icons.")

if __name__ == "__main__":
    main()
