import os
import math
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"c:\CODING FILES\PYTHON PROJECT"
BRAIN_DIR = r"C:\Users\COSMIC\.gemini\antigravity-ide\brain\44497b57-f615-4cc6-abe2-c82908024b51"
PREV_BRAIN_DIR = r"C:\Users\COSMIC\.gemini\antigravity-ide\brain\99dbda26-91ec-41e4-bc23-c1134d559774"

def get_brain_file(filename):
    p1 = os.path.join(BRAIN_DIR, filename)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(PREV_BRAIN_DIR, filename)
    if os.path.exists(p2):
        return p2
    return None

# Color Palette Constants
RED = (225, 29, 46, 255)         # #E11D2E
DARK_RED = (140, 15, 25, 255)
LIGHT_RED = (248, 113, 113, 255)
BLUE = (29, 78, 216, 255)        # #1D4ED8
LIGHT_BLUE = (56, 189, 248, 255) # Cyan / Electric glow
DARK_BLUE = (15, 23, 42, 255)
NAVY = (11, 16, 38, 255)         # #0B1026
BLACK = (5, 8, 18, 255)
WHITE = (255, 255, 255, 255)
YELLOW = (250, 204, 21, 255)
TRANSPARENT = (0, 0, 0, 0)

# Helper: Halftone pattern
def draw_halftone(draw, x0, y0, x1, y1, dot_color, spacing=4, radius=1):
    for y in range(y0, y1, spacing):
        for x in range(x0, x1, spacing):
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=dot_color)

# 1. bg_far.png (960x540)
def process_bg_far():
    src_path = get_brain_file("bg_far_1792942851817.jpg")
    out_path = os.path.join(OUTPUT_DIR, "bg_far.png")
    if src_path and os.path.exists(src_path):
        img = Image.open(src_path).convert("RGBA")
        img = img.resize((960, 540), Image.Resampling.LANCZOS)
        img.save(out_path, "PNG")
        print("Generated bg_far.png (960x540)")

# 2. bg_mid.png (960x540, transparent background)
def process_bg_mid():
    src_path = get_brain_file("bg_mid_1792942883757.jpg")
    out_path = os.path.join(OUTPUT_DIR, "bg_mid.png")
    if src_path and os.path.exists(src_path):
        img = Image.open(src_path).convert("RGBA")
        img = img.resize((960, 540), Image.Resampling.LANCZOS)
        
        # Make the dark night sky transparent while keeping the buildings & neon edges
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                # Sky in the image is deep dark navy/indigo (r < 20, g < 22, b < 40)
                if r < 20 and g < 22 and b < 40:
                    pixels[x, y] = (0, 0, 0, 0)
        img.save(out_path, "PNG")
        print("Generated bg_mid.png (960x540, transparent)")

# 3. title_art.png (960x540)
def process_title_art():
    src_path = get_brain_file("title_art_1792942923207.jpg")
    out_path = os.path.join(OUTPUT_DIR, "title_art.png")
    if src_path and os.path.exists(src_path):
        img = Image.open(src_path).convert("RGBA")
        img = img.resize((960, 540), Image.Resampling.LANCZOS)
        img.save(out_path, "PNG")
        print("Generated title_art.png (960x540)")

# 4. rooftop_tile.png (128x64, seamless horizontally)
def generate_rooftop_tile():
    out_path = os.path.join(OUTPUT_DIR, "rooftop_tile.png")
    w, h = 128, 64
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Dark concrete building wall base
    draw.rectangle([0, 14, w - 1, h - 1], fill=NAVY, outline=None)
    
    # Brick/panel mortar lines (seamless horizontally: line at 0, 32, 64, 96, 128)
    for x in [0, 32, 64, 96]:
        draw.line([(x, 14), (x, 38)], fill=BLACK, width=2)
    for x in [16, 48, 80, 112]:
        draw.line([(x, 38), (x, h - 1)], fill=BLACK, width=2)
    draw.line([(0, 38), (w, 38)], fill=BLACK, width=2)

    # Halftone texture on concrete
    for y in range(18, h - 2, 6):
        for x in range(2, w - 2, 6):
            draw.point((x, y), fill=(30, 41, 59, 255))

    # Rooftop cornice / edge trim
    draw.rectangle([0, 6, w - 1, 14], fill=(20, 30, 60, 255), outline=BLACK, width=2)
    
    # Electric blue neon illuminated ledge top
    draw.rectangle([0, 0, w - 1, 6], fill=BLUE, outline=BLACK, width=2)
    draw.line([(0, 2), (w, 2)], fill=LIGHT_BLUE, width=2)
    draw.line([(0, 1), (w, 1)], fill=WHITE, width=1)

    # Subtle red neon accent under ledge
    draw.line([(0, 14), (w, 14)], fill=RED, width=1)

    img.save(out_path, "PNG")
    print("Generated rooftop_tile.png (128x64)")

# 5. icon_fluid.png (64x64, transparent)
def generate_icon_fluid():
    out_path = os.path.join(OUTPUT_DIR, "icon_fluid.png")
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Outer glow / shadow
    cx, cy = 32, 32
    # Canister cylinder
    left, top, right, bottom = 22, 16, 42, 54

    # Cartridge glass body (Electric blue)
    draw.rounded_rectangle([left, top, right, bottom], radius=4, fill=BLUE, outline=BLACK, width=2)

    # Liquid fluid fill inside (cyan glowing core)
    draw.rounded_rectangle([left + 3, top + 8, right - 3, bottom - 3], radius=2, fill=LIGHT_BLUE)
    
    # White fluid surface meniscus & bubbles
    draw.ellipse([left + 4, top + 6, right - 4, top + 10], fill=WHITE)
    draw.point((cx - 2, cy), fill=WHITE)
    draw.point((cx + 2, cy + 6), fill=WHITE)

    # White specular glass glare line
    draw.line([(left + 3, top + 4), (left + 3, bottom - 4)], fill=WHITE, width=2)

    # Halftone shadow dots on right side
    for dy in range(top + 8, bottom - 4, 4):
        draw.point((right - 4, dy), fill=BLACK)

    # Metal connector bands
    draw.rectangle([left, top + 14, right, top + 17], fill=DARK_BLUE, outline=BLACK, width=1)
    draw.rectangle([left, bottom - 10, right, bottom - 7], fill=DARK_BLUE, outline=BLACK, width=1)

    # Small red cap at top
    draw.rounded_rectangle([26, 8, 38, 16], radius=2, fill=RED, outline=BLACK, width=2)
    draw.rectangle([29, 6, 35, 8], fill=LIGHT_RED, outline=BLACK, width=1)
    # White highlight on cap
    draw.line([(28, 10), (28, 14)], fill=WHITE, width=1)

    img.save(out_path, "PNG")
    print("Generated icon_fluid.png (64x64)")

# 6. icon_chip.png (64x64, transparent)
def generate_icon_chip():
    out_path = os.path.join(OUTPUT_DIR, "icon_chip.png")
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Outer angled chip body in Spider Red #E11D2E
    # Notched corner data cartridge
    points = [
        (16, 12),
        (42, 12),
        (50, 20),
        (50, 52),
        (16, 52)
    ]
    draw.polygon(points, fill=RED, outline=BLACK)
    # Thick bold black comic outline
    draw.line([(16, 12), (42, 12), (50, 20), (50, 52), (16, 52), (16, 12)], fill=BLACK, width=3)

    # Darker red shadow on right side with halftone dots
    draw.polygon([(36, 24), (47, 24), (47, 49), (36, 49)], fill=DARK_RED)
    for y in range(26, 48, 4):
        for x in range(38, 46, 4):
            draw.point((x, y), fill=BLACK)

    # Inner core processor square (Electric Blue)
    draw.rectangle([24, 26, 36, 38], fill=BLUE, outline=BLACK, width=2)
    draw.rectangle([27, 29, 33, 35], fill=LIGHT_BLUE)

    # Glowing circuit lines
    circuit_color = LIGHT_BLUE
    # Top traces
    draw.line([(27, 26), (27, 18), (22, 18)], fill=circuit_color, width=2)
    draw.line([(33, 26), (33, 16)], fill=circuit_color, width=2)
    draw.ellipse([20, 16, 24, 20], fill=WHITE)
    draw.ellipse([31, 14, 35, 18], fill=WHITE)
    
    # Bottom traces
    draw.line([(27, 38), (27, 46), (22, 46)], fill=circuit_color, width=2)
    draw.line([(33, 38), (33, 46), (38, 46)], fill=circuit_color, width=2)
    draw.ellipse([20, 44, 24, 48], fill=WHITE)
    draw.ellipse([37, 44, 41, 48], fill=WHITE)

    # Gold connector pins along the left side
    for py in [18, 26, 34, 42]:
        draw.rectangle([11, py, 16, py + 4], fill=YELLOW, outline=BLACK, width=1)

    # White specular shine line along the top-left edge
    draw.line([(18, 14), (40, 14)], fill=WHITE, width=2)
    draw.line([(18, 14), (18, 48)], fill=WHITE, width=2)

    img.save(out_path, "PNG")
    print("Generated icon_chip.png (64x64)")

# 7. icon_bomb.png (64x64, transparent)
def generate_icon_bomb():
    out_path = os.path.join(OUTPUT_DIR, "icon_bomb.png")
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Fuse at top
    # Curved rope fuse
    draw.arc([24, 6, 36, 22], start=180, end=340, fill=DARK_BLUE, width=3)
    
    # Lit spark flame burst (Yellow and White)
    fx, fy = 36, 8
    spark_pts = [
        (fx, fy - 6), (fx + 2, fy - 2), (fx + 7, fy), (fx + 2, fy + 2),
        (fx, fy + 7), (fx - 2, fy + 2), (fx - 7, fy), (fx - 2, fy - 2)
    ]
    draw.polygon(spark_pts, fill=YELLOW, outline=BLACK)
    draw.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=WHITE)

    # Pumpkin stem cap
    draw.rectangle([28, 16, 36, 22], fill=BLACK)

    # Pumpkin body (Orange-Red #E11D2E)
    bx, by, br = 32, 38, 20
    # Three overlapping lobes for pumpkin look
    draw.ellipse([bx - br, by - br + 2, bx - 2, by + br], fill=RED, outline=BLACK, width=2)
    draw.ellipse([bx + 2, by - br + 2, bx + br, by + br], fill=RED, outline=BLACK, width=2)
    draw.ellipse([bx - br + 4, by - br, bx + br - 4, by + br], fill=RED, outline=BLACK, width=3)

    # Halftone shadow dots on bottom-right
    for y in range(by + 4, by + br - 2, 3):
        for x in range(bx + 2, bx + br - 4, 3):
            if (x - bx)**2 + (y - by)**2 < (br - 2)**2:
                draw.point((x, y), fill=BLACK)

    # Menacing glowing eyes (Triangles)
    draw.polygon([(22, 32), (28, 30), (27, 36)], fill=YELLOW, outline=BLACK)
    draw.polygon([(42, 32), (36, 30), (37, 36)], fill=YELLOW, outline=BLACK)

    # Jagged Jack-O'-Lantern grin
    mouth = [
        (20, 44), (24, 41), (28, 45), (32, 41),
        (36, 45), (40, 41), (44, 44),
        (40, 49), (36, 46), (32, 50), (28, 46), (24, 49)
    ]
    draw.polygon(mouth, fill=YELLOW, outline=BLACK, width=1)
    # White glow centers in mouth and eyes
    draw.line([(24, 45), (40, 45)], fill=WHITE, width=1)

    # White specular highlight arc on top left
    draw.arc([bx - br + 6, by - br + 3, bx + 2, by], start=160, end=270, fill=WHITE, width=2)

    img.save(out_path, "PNG")
    print("Generated icon_bomb.png (64x64)")

# 8. icon_civilian.png (64x64, transparent)
def generate_icon_civilian():
    out_path = os.path.join(OUTPUT_DIR, "icon_civilian.png")
    w, h = 64, 64
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Cocooned body shape (Tightly webbed mummy style)
    # Background shadow
    draw.ellipse([18, 14, 46, 56], fill=NAVY, outline=BLACK, width=2)

    # Civilian face peeking out through webs
    # Skin / face circle
    draw.ellipse([22, 16, 42, 36], fill=(254, 215, 170, 255), outline=BLACK, width=2)
    
    # Worried wide comic eyes
    draw.ellipse([25, 21, 31, 29], fill=WHITE, outline=BLACK, width=1)
    draw.ellipse([33, 21, 39, 29], fill=WHITE, outline=BLACK, width=1)
    # Pupils looking up/worried
    draw.ellipse([28, 23, 30, 26], fill=BLACK)
    draw.ellipse([34, 23, 36, 26], fill=BLACK)

    # Worried wavy mouth
    draw.line([(27, 33), (29, 31), (32, 33), (35, 31), (37, 33)], fill=BLACK, width=2)

    # Sweat drop (Cyan #38BDF8)
    draw.polygon([(40, 18), (42, 23), (39, 23)], fill=LIGHT_BLUE, outline=BLACK)
    draw.ellipse([39, 21, 42, 24], fill=LIGHT_BLUE)

    # Dense criss-crossing WHITE web strands wrapping the civilian
    web_lines = [
        # Around head/forehead
        [(19, 17), (45, 17)],
        [(18, 20), (25, 15)],
        [(39, 15), (46, 20)],
        # Under chin
        [(18, 35), (46, 35)],
        [(18, 38), (46, 42)],
        [(46, 38), (18, 42)],
        # Body cocoon criss-cross
        [(20, 44), (44, 44)],
        [(19, 47), (45, 51)],
        [(45, 47), (19, 51)],
        [(22, 53), (42, 53)],
        [(24, 56), (40, 56)]
    ]
    for p1, p2 in web_lines:
        # Outline behind strand
        draw.line([p1, p2], fill=BLACK, width=4)
        # Main white strand
        draw.line([p1, p2], fill=WHITE, width=2)

    # Vertical web anchor hanging down
    draw.line([(32, 2), (32, 14)], fill=BLACK, width=3)
    draw.line([(32, 2), (32, 14)], fill=WHITE, width=2)

    img.save(out_path, "PNG")
    print("Generated icon_civilian.png (64x64)")

# 9. logo_webline.png (480x140, transparent)
def generate_logo_webline():
    out_path = os.path.join(OUTPUT_DIR, "logo_webline.png")
    w, h = 480, 140
    img = Image.new("RGBA", (w, h), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Font handling: try Segoe UI, Impact, Arial, or default
    font = None
    for font_name in ["impact.ttf", "segoeuib.ttf", "arialbd.ttf", "arial.ttf"]:
        try:
            font = ImageFont.truetype(font_name, 72)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    text = "WEBLINE"
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = (h - th) // 2 - 4

    # 1. Electric blue 3D drop extrude block / shadow
    for offset in range(10, 0, -1):
        draw.text((tx + offset, ty + offset), text, font=font, fill=BLUE)

    # 2. Bold black outline around text (stroke)
    for ox in range(-5, 6):
        for oy in range(-5, 6):
            if ox*ox + oy*oy <= 25:
                draw.text((tx + ox, ty + oy), text, font=font, fill=BLACK)

    # 3. Fill text with Spider Red #E11D2E
    draw.text((tx, ty), text, font=font, fill=RED)

    # 4. Halftone dots on lower half of letters
    # Create mask of text
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((tx, ty), text, font=font, fill=255)

    # Dot pattern layer
    dots_img = Image.new("RGBA", (w, h), TRANSPARENT)
    dots_draw = ImageDraw.Draw(dots_img)
    for y in range(ty + th // 2, ty + th + 6, 4):
        for x in range(tx, tx + tw, 4):
            dots_draw.point((x, y), fill=DARK_RED)
    
    # Composite dots over red text where mask is white
    img.paste(dots_img, (0, 0), mask)

    # 5. White web crack fractures across letters
    cracks_layer = Image.new("RGBA", (w, h), TRANSPARENT)
    cdraw = ImageDraw.Draw(cracks_layer)
    
    # Intricate spider web crack pattern
    center_web = (tx + tw // 2, ty + th // 2)
    wx, wy = center_web
    for angle_deg in [20, 65, 115, 160, 205, 250, 295, 340]:
        rad = math.radians(angle_deg)
        ex = wx + math.cos(rad) * 160
        ey = wy + math.sin(rad) * 60
        cdraw.line([(wx, wy), (ex, ey)], fill=WHITE, width=2)
    
    # Web concentric rings
    for r in [20, 40, 65, 95]:
        cdraw.arc([wx - r*2, wy - r, wx + r*2, wy + r], start=0, end=360, fill=WHITE, width=1)
    
    # Composite cracks only inside the text
    img.paste(cracks_layer, (0, 0), mask)

    # 6. Sharp white highlights along the top edges
    draw.line([(tx, ty + 2), (tx + tw, ty + 2)], fill=WHITE, width=2)

    img.save(out_path, "PNG")
    print("Generated logo_webline.png (480x140)")

if __name__ == "__main__":
    process_bg_far()
    process_bg_mid()
    process_title_art()
    generate_rooftop_tile()
    generate_icon_fluid()
    generate_icon_chip()
    generate_icon_bomb()
    generate_icon_civilian()
    generate_logo_webline()
