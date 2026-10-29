import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def make_gravitui_icon():
    # Supersampled 1024x1024 canvas for ultra-crisp downsampling
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base Squircle / Rounded App Tile
    margin = 48
    r = 200
    bbox = [margin, margin, S - margin, S - margin]
    
    # Background radial gradient
    bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    bg_draw.rounded_rectangle(bbox, radius=r, fill=(12, 10, 24, 255))
    
    # Subtle inner glow / radial light in upper half
    light = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    light_draw = ImageDraw.Draw(light)
    light_draw.ellipse([200, 100, S - 200, 700], fill=(80, 50, 160, 70))
    light = light.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, light)

    # Outer border: Neon Violet to Amber gradient border
    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(bbox, radius=r, outline=(140, 90, 240, 200), width=12)
    
    # 2. Mini Terminal Title Bar at the top of the squircle
    title_bar = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    tb_draw = ImageDraw.Draw(title_bar)
    # 3 colored terminal traffic light dots: red, yellow, green
    tb_y = margin + 65
    dots = [
        (margin + 80, tb_y, (255, 95, 86, 230)),
        (margin + 120, tb_y, (255, 189, 46, 230)),
        (margin + 160, tb_y, (39, 201, 63, 230))
    ]
    for dx, dy, col in dots:
        tb_draw.ellipse([dx - 12, dy - 12, dx + 12, dy + 12], fill=col)
    
    # Terminal title text "[GraviTUI]"
    # Simple line accents
    tb_draw.line([margin + 210, tb_y, S - margin - 80, tb_y], fill=(60, 50, 90, 160), width=4)

    # 3. Accretion Disk & Black Hole (Gargantua / Aurum)
    cx, cy = S // 2, S // 2 + 35
    
    # Accretion glow layers
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Outer accretion disc (tilted ellipse)
    rx_out, ry_out = 380, 130
    for i in range(12, 0, -1):
        alpha = int(18 * (13 - i))
        glow_draw.ellipse(
            [cx - rx_out - i * 8, cy - ry_out - i * 5, cx + rx_out + i * 8, cy + ry_out + i * 5],
            outline=(255, 140, 20, alpha // 4),
            width=16
        )
    glow = glow.filter(ImageFilter.GaussianBlur(30))

    # Sharp accretion disk
    disk = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    disk_draw = ImageDraw.Draw(disk)
    
    # Golden / Amber accretion gradient
    for w in range(50, 0, -2):
        factor = w / 50.0
        # Doppler effect: left side is brighter / hotter (bluer/whiter)
        r_col = int(255 * (0.8 + 0.2 * factor))
        g_col = int(140 + 90 * factor)
        b_col = int(20 + 120 * factor)
        disk_draw.ellipse(
            [cx - rx_out + (50 - w) * 3, cy - ry_out + (50 - w), cx + rx_out - (50 - w) * 3, cy + ry_out - (50 - w)],
            outline=(r_col, g_col, b_col, 220),
            width=3
        )

    # Vertical Einstein gravitational lens arc (the upper & lower bent disk of Gargantua!)
    lens_arc = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    lens_draw = ImageDraw.Draw(lens_arc)
    # Upper arched halo
    lens_draw.arc([cx - 240, cy - 310, cx + 240, cy + 170], start=180, end=360, fill=(255, 185, 60, 240), width=24)
    lens_draw.arc([cx - 230, cy - 300, cx + 230, cy + 160], start=180, end=360, fill=(255, 235, 180, 255), width=8) # photon ring
    # Lower bent halo
    lens_draw.arc([cx - 220, cy - 140, cx + 220, cy + 300], start=0, end=180, fill=(240, 110, 20, 200), width=18)
    lens_draw.arc([cx - 210, cy - 130, cx + 210, cy + 290], start=0, end=180, fill=(255, 180, 60, 220), width=6)
    
    # 4. Central Black Void (Shadow of the Event Horizon)
    hole_r = 160
    hole = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hole_draw = ImageDraw.Draw(hole)
    hole_draw.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r], fill=(3, 2, 8, 255))
    # Sharp inner photon ring right on shadow boundary
    hole_draw.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r], outline=(255, 245, 220, 240), width=4)

    # 5. Crisp Foreground Prompt Symbol: Stylized ">_" Monogram
    # We draw a clean, glowing cyan/white terminal prompt ">" inside the void!
    prompt_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(prompt_img)
    
    # ">" prompt chevron
    # Points: top, tip, bottom
    tip_x = cx - 10
    top_y = cy - 65
    mid_y = cy
    bot_y = cy + 65
    left_x = cx - 75
    
    # Glowing shadow behind prompt
    p_glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pg_draw = ImageDraw.Draw(p_glow)
    pg_draw.line([(left_x, top_y), (tip_x, mid_y), (left_x, bot_y)], fill=(50, 220, 255, 220), width=28)
    pg_draw.line([(cx + 15, bot_y), (cx + 85, bot_y)], fill=(50, 220, 255, 220), width=28)
    p_glow = p_glow.filter(ImageFilter.GaussianBlur(16))

    # Core crisp prompt (pure white / electric cyan)
    p_draw.line([(left_x, top_y), (tip_x, mid_y), (left_x, bot_y)], fill=(240, 250, 255, 255), width=18)
    # Cursor underscore "_"
    p_draw.line([(cx + 15, bot_y), (cx + 85, bot_y)], fill=(255, 215, 80, 255), width=18)

    # Combine all layers in correct depth order:
    # 1. Background
    # 2. Title bar
    # 3. Ambient glow
    # 4. Upper/Lower Lens Arc (back)
    # 5. Accretion Disk
    # 6. Central Event Horizon (Shadow)
    # 7. Front Accretion Disk cross (front of hole)
    # 8. Terminal Prompt Glyph (>_)
    # 9. Border
    
    composite = Image.alpha_composite(bg, title_bar)
    composite = Image.alpha_composite(composite, glow)
    composite = Image.alpha_composite(composite, lens_arc)
    composite = Image.alpha_composite(composite, disk)
    composite = Image.alpha_composite(composite, hole)
    
    # Front half of accretion disk (draw over lower half of black hole shadow)
    front_disk = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fd_draw = ImageDraw.Draw(front_disk)
    # Draw arc across front
    fd_draw.arc([cx - rx_out, cy - ry_out, cx + rx_out, cy + ry_out], start=10, end=170, fill=(255, 170, 40, 230), width=18)
    fd_draw.arc([cx - rx_out + 10, cy - ry_out + 4, cx + rx_out - 10, cy + ry_out - 4], start=15, end=165, fill=(255, 230, 160, 255), width=6)
    composite = Image.alpha_composite(composite, front_disk)

    composite = Image.alpha_composite(composite, p_glow)
    composite = Image.alpha_composite(composite, prompt_img)
    composite = Image.alpha_composite(composite, border)

    # Target directory in repo
    from pathlib import Path
    assets_dir = str(Path(__file__).resolve().parent.parent / "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    png_path = os.path.join(assets_dir, "gravitui.png")
    ico_path = os.path.join(assets_dir, "gravitui.ico")

    # Downsample master PNG
    master_png = composite.resize((512, 512), Image.Resampling.LANCZOS)
    master_png.save(png_path, "PNG")
    print(f"✔ High-res PNG saved: {png_path}")

    # Generate multi-resolution ICO: 256, 128, 64, 48, 32, 16
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_images = [composite.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    
    icon_images[0].save(
        ico_path,
        format="ICO",
        sizes=sizes,
        append_images=icon_images[1:]
    )
    print(f"✔ Multi-resolution ICO saved: {ico_path} (Sizes: {[s[0] for s in sizes]})")
    return ico_path

if __name__ == "__main__":
    make_gravitui_icon()
