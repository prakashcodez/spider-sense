"""
═══════════════════════════════════════════════════════════════════════════════
                      WEBLINE: NIGHT PATROL
         A 2D Side-Scrolling Action Game in Python & Tkinter
       Project for 'Python Programming for Design' Course
═══════════════════════════════════════════════════════════════════════════════

Tech Constraints:
- Pure Python 3 standard library: tkinter, random, math, os, time.
- Optional PNG asset loading via tk.PhotoImage with full code-drawn fallbacks.
- Auto-scaling for title art and backgrounds of any dimension.
- 100% Canvas-drawn UI (no tk.Button or tk.Label widgets).
- Fixed-step ~50 FPS loop via root.after(20) with strict timer cleanup.
"""

import tkinter as tk
import random
import math
import os
import time

# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONSTANTS & DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 540
TICK_MS = 20                   # 50 updates per second
VIEW_CULL_MARGIN = 260         # Distance beyond camera view to update/draw objects

# Strict Comic-Book Palette
COLOR_NAVY = "#0B1026"         # Midnight Navy sky and shadows
COLOR_BLUE = "#1D4ED8"         # Electric Blue suit, ledges, UI accents
COLOR_LIGHT_BLUE = "#38BDF8"   # Cyan glow for fluid, lasers, sparks
COLOR_RED = "#E11D2E"          # Spider Red suit, alarms, comic boxes
COLOR_DARK_RED = "#991B1B"     # Deep crimson shading
COLOR_WHITE = "#FFFFFF"        # Web lines, eye lenses, text highlights
COLOR_BLACK = "#050812"        # Bold comic outlines and shadows
COLOR_YELLOW = "#FACC15"       # Spark flashes, star awards, warning tags
COLOR_DARK_GRAY = "#1E293B"    # Rooftop concrete walls
COLOR_GOLD = "#F59E0B"         # Data chip connectors, stars

# Player Physics & Capabilities
GRAVITY = 0.52
MAX_FALL_SPEED = 13.5
MOVE_ACCEL = 0.95
MOVE_DECEL = 0.78
MAX_RUN_SPEED = 6.6
JUMP_VELOCITY = -11.8
DOUBLE_JUMP_VELOCITY = -10.5
COYOTE_MAX_TICKS = 8
JUMP_BUFFER_TICKS = 6

# Dynamic Web-Swing Mechanics
SWING_ATTACH_RADIUS = 440
SWING_GRAVITY = 0.0036
SWING_DAMPING = 0.9988
SWING_LAUNCH_BOOST = 1.32

# Unlimited Web Fluid Resource
MAX_FLUID = 100.0
FLUID_PICKUP_BONUS = 50

# Health & Combat
MAX_HEARTS = 5
INVINCIBLE_TICKS = 75          # 1.5 seconds at 50 FPS
STUN_DURATION_TICKS = 125      # 2.5 seconds stunned

# Scoring Values
SCORE_STUN = 10
SCORE_STOMP = 25
SCORE_OBJECTIVE = 50
SCORE_CLOSE_CALL = 15


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SAFE LOADERS & GRAPHICAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
class AssetCache:
    """Manages optional tk.PhotoImage assets with auto-scaling and code fallback."""

    def __init__(self):
        self.images = {}

    def load(self, name, filename, max_w=None, max_h=None):
        """Safely load an asset and auto-downscale if larger than target dimensions."""
        possible_paths = [
            os.path.join("assets", filename),
            filename,
            os.path.join("c:\\CODING FILES\\PYTHON PROJECT\\assets", filename),
            os.path.join("c:\\CODING FILES\\PYTHON PROJECT", filename)
        ]
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    img = tk.PhotoImage(file=p)
                    # Automatically downscale if image exceeds max bounds
                    if max_w and max_h:
                        if img.width() > max_w or img.height() > max_h:
                            xf = max(1, round(img.width() / max_w))
                            yf = max(1, round(img.height() / max_h))
                            img = img.subsample(xf, yf)
                    self.images[name] = img
                    return img
                except Exception:
                    pass
        self.images[name] = None
        return None

    def get(self, name):
        """Get preloaded image or None."""
        return self.images.get(name)


def get_comic_font(size, weight="bold"):
    """Returns the best available comic font (Impact -> Arial Black -> Arial)."""
    return ("Impact", size, weight)


def draw_slanted_box(canvas, x1, y1, x2, y2, slant=14, fill=COLOR_NAVY, outline=COLOR_BLUE, width=2):
    """Draws a stylish comic-book slanted polygon box."""
    points = [
        x1 + slant, y1,
        x2, y1,
        x2 - slant, y2,
        x1, y2
    ]
    return canvas.create_polygon(points, fill=fill, outline=outline, width=width)


def draw_halftone_accent(canvas, x, y, w, h, step=7, dot_r=1.2, color=COLOR_DARK_RED):
    """Draws a subtle comic-book halftone dot pattern in a rectangular region."""
    for dy in range(int(y), int(y + h), step):
        for dx in range(int(x), int(x + w), step):
            canvas.create_oval(dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r, fill=color, outline="")


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """Calculates perpendicular distance from point (px, py) to line segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SPIDER-MAN HERO VECTOR RENDERER (NO SPRITE IMAGES)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_hero(canvas, cx, cy, pose, facing, tick, invincible, swing_angle=0.0):
    """
    Renders Spider-Man using pure canvas geometric primitives.
    Features:
    - Red head with black web pattern & white angular eye lenses with black borders
    - Red torso and biceps, electric-blue sides and legs, black chest emblem
    - White web-shooter wrist bands
    - Directional mirroring and full pose state articulation (run, jump, swing, punch, kick)
    """
    # Flash on alternate frames if invincible
    if invincible > 0 and (invincible // 3) % 2 == 1:
        return

    # Breathing displacement for idle
    breath = math.sin(tick * 0.12) * 1.5 if pose == "idle" else 0.0
    cy += breath

    # Coordinate transformation helper for mirroring
    def px(offset_x):
        return cx + (offset_x * facing)

    def py(offset_y):
        return cy + offset_y

    # --- SWING POSE (Tilted along web angle) ---
    if pose == "swing":
        tilt_sin = math.sin(swing_angle)
        tilt_cos = math.cos(swing_angle)
        
        def rxy(ox, oy):
            rx = ox * tilt_cos - oy * tilt_sin
            ry = ox * tilt_sin + oy * tilt_cos
            return cx + rx * facing, cy + ry

        # Trailing legs
        leg_pts = [rxy(-6, 8), rxy(-14, 26), rxy(-22, 38), rxy(-16, 40), rxy(-8, 26), rxy(2, 10)]
        canvas.create_polygon(leg_pts, fill=COLOR_BLUE, outline=COLOR_BLACK, width=2)
        # Red boot
        canvas.create_polygon([rxy(-22, 38), rxy(-26, 44), rxy(-16, 46), rxy(-16, 40)],
                              fill=COLOR_RED, outline=COLOR_BLACK, width=2)

        # Torso (red center, blue sides)
        canvas.create_polygon([rxy(-8, -10), rxy(8, -10), rxy(7, 10), rxy(-7, 10)],
                              fill=COLOR_RED, outline=COLOR_BLACK, width=2)
        canvas.create_line(rxy(-7, -4), rxy(-6, 9), fill=COLOR_BLUE, width=3)
        canvas.create_line(rxy(7, -4), rxy(6, 9), fill=COLOR_BLUE, width=3)

        # Arms holding web overhead
        canvas.create_line(rxy(-4, -8), rxy(-10, -26), fill=COLOR_RED, width=4)
        canvas.create_line(rxy(4, -8), rxy(2, -28), fill=COLOR_RED, width=4)
        # White web-shooter wrists
        canvas.create_oval(rxy(-11, -27)[0]-2, rxy(-11, -27)[1]-2, rxy(-11, -27)[0]+2, rxy(-11, -27)[1]+2, fill=COLOR_WHITE)

        # Spider Head
        hx, hy = rxy(2, -18)
        canvas.create_oval(hx - 8, hy - 9, hx + 8, hy + 9, fill=COLOR_RED, outline=COLOR_BLACK, width=2)
        canvas.create_line(hx - 6, hy, hx + 6, hy, fill=COLOR_BLACK, width=1)
        canvas.create_line(hx, hy - 7, hx, hy + 7, fill=COLOR_BLACK, width=1)
        ex1, ey1 = rxy(3, -19)
        canvas.create_polygon([ex1, ey1 - 4, ex1 + 5 * facing, ey1 - 1, ex1, ey1 + 3],
                              fill=COLOR_WHITE, outline=COLOR_BLACK, width=1.5)
        return

    # --- GROUND, AIR & COMBAT POSES (run, jump, fall, idle, shot, punch, kick, crouch) ---
    
    # 1. Legs Animation
    if pose == "run":
        leg_swing = math.sin(tick * 0.35) * 12
        # Back leg
        canvas.create_line(px(-3), py(8), px(-8 - leg_swing), py(22), px(-10 - leg_swing), py(32),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(-10 - leg_swing), py(30), px(-6 - leg_swing), py(34),
                           fill=COLOR_RED, width=5, capstyle=tk.ROUND)
        # Front leg
        canvas.create_line(px(3), py(8), px(6 + leg_swing), py(22), px(8 + leg_swing), py(32),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(8 + leg_swing), py(30), px(12 + leg_swing), py(34),
                           fill=COLOR_RED, width=5, capstyle=tk.ROUND)
    elif pose in ("jump", "fall"):
        # Tucked / jumping legs
        canvas.create_line(px(-4), py(8), px(-10), py(18), px(-4), py(26),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(-4), py(26), px(-1), py(28), fill=COLOR_RED, width=5)
        canvas.create_line(px(4), py(8), px(11), py(19), px(5), py(27),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(5), py(27), px(8), py(29), fill=COLOR_RED, width=5)
    elif pose == "punch":
        # Lunging combat stance legs
        canvas.create_line(px(-6), py(8), px(-14), py(22), px(-18), py(33),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(-18), py(31), px(-14), py(34), fill=COLOR_RED, width=5)
        canvas.create_line(px(4), py(8), px(12), py(20), px(16), py(33),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(16), py(31), px(20), py(34), fill=COLOR_RED, width=5)
    elif pose == "kick":
        # Flying martial arts kick legs
        canvas.create_line(px(-4), py(8), px(-10), py(18), px(-8), py(30),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(-8), py(28), px(-5), py(32), fill=COLOR_RED, width=5)
        canvas.create_line(px(4), py(6), px(18), py(0), px(30), py(-4),
                           fill=COLOR_BLUE, width=6, capstyle=tk.ROUND)
        canvas.create_polygon([px(28), py(-8), px(38), py(-4), px(30), py(1)],
                              fill=COLOR_RED, outline=COLOR_BLACK, width=1.5)
    elif pose == "crouch":
        canvas.create_line(px(-4), py(6), px(-12), py(16), px(-4), py(24), fill=COLOR_BLUE, width=5)
        canvas.create_line(px(4), py(6), px(10), py(17), px(6), py(24), fill=COLOR_BLUE, width=5)
    else:
        # Idle standing
        canvas.create_line(px(-4), py(8), px(-5), py(22), px(-5), py(33),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(-5), py(31), px(-2), py(34), fill=COLOR_RED, width=5)
        canvas.create_line(px(4), py(8), px(5), py(22), px(6), py(33),
                           fill=COLOR_BLUE, width=5, capstyle=tk.ROUND)
        canvas.create_line(px(6), py(31), px(9), py(34), fill=COLOR_RED, width=5)

    # 2. Torso & Costume
    torso_y = py(-4)
    canvas.create_polygon([
        px(-8), torso_y - 8,
        px(8), torso_y - 8,
        px(6), torso_y + 12,
        px(-6), torso_y + 12
    ], fill=COLOR_RED, outline=COLOR_BLACK, width=2)
    
    # Blue side flanks
    canvas.create_line(px(-7), torso_y - 4, px(-5), torso_y + 11, fill=COLOR_BLUE, width=3)
    canvas.create_line(px(7), torso_y - 4, px(5), torso_y + 11, fill=COLOR_BLUE, width=3)

    # Black Spider Chest Insignia
    canvas.create_oval(px(0) - 2.5, torso_y - 2, px(0) + 2.5, torso_y + 4, fill=COLOR_BLACK, outline="")
    canvas.create_line(px(-5), torso_y - 4, px(0), torso_y, px(5), torso_y - 4, fill=COLOR_BLACK, width=1.5)
    canvas.create_line(px(-5), torso_y + 5, px(0), torso_y + 2, px(5), torso_y + 5, fill=COLOR_BLACK, width=1.5)

    # 3. Arms
    if pose == "web_shot":
        canvas.create_line(px(2), torso_y - 5, px(16), torso_y - 4, px(26), torso_y - 3,
                           fill=COLOR_RED, width=4, capstyle=tk.ROUND)
        canvas.create_rectangle(px(22) - 2, torso_y - 6, px(22) + 2, torso_y, fill=COLOR_WHITE, outline=COLOR_BLACK)
        canvas.create_oval(px(27) - 3, torso_y - 6, px(27) + 3, torso_y, fill=COLOR_LIGHT_BLUE, outline="")
    elif pose == "punch":
        # Rear arm braced for balance
        canvas.create_line(px(-5), torso_y - 4, px(-15), torso_y + 2, px(-13), torso_y + 10,
                           fill=COLOR_RED, width=4, capstyle=tk.ROUND)
        # Power punch forward arm with clenched fist
        canvas.create_line(px(2), torso_y - 4, px(16), torso_y - 4, px(27), torso_y - 4,
                           fill=COLOR_RED, width=5, capstyle=tk.ROUND)
        canvas.create_oval(px(25), torso_y - 7, px(33), torso_y + 1, fill=COLOR_RED, outline=COLOR_BLACK, width=1.5)
        # Comic punch action lines
        canvas.create_line(px(32), torso_y - 8, px(38), torso_y - 12, fill=COLOR_YELLOW, width=1.5)
        canvas.create_line(px(35), torso_y - 4, px(42), torso_y - 4, fill=COLOR_YELLOW, width=2)
        canvas.create_line(px(32), torso_y, px(38), torso_y + 4, fill=COLOR_YELLOW, width=1.5)
    elif pose == "kick":
        # Aerial kick braced arms
        canvas.create_line(px(-4), torso_y - 6, px(-14), torso_y - 14, fill=COLOR_RED, width=4)
        canvas.create_line(px(4), torso_y - 4, px(14), torso_y + 8, fill=COLOR_RED, width=4)
    elif pose == "run":
        arm_swing = math.sin(tick * 0.35) * 10
        canvas.create_line(px(-4), torso_y - 6, px(-8 + arm_swing), torso_y + 4, px(-12 + arm_swing), torso_y + 10,
                           fill=COLOR_RED, width=4, capstyle=tk.ROUND)
        canvas.create_line(px(4), torso_y - 6, px(8 - arm_swing), torso_y + 4, px(12 - arm_swing), torso_y + 10,
                           fill=COLOR_RED, width=4, capstyle=tk.ROUND)
    elif pose in ("jump", "fall"):
        canvas.create_line(px(-4), torso_y - 6, px(-12), torso_y - 14, fill=COLOR_RED, width=4)
        canvas.create_line(px(4), torso_y - 6, px(12), torso_y - 12, fill=COLOR_RED, width=4)
    else:
        # Idle / Crouch arms
        canvas.create_line(px(-5), torso_y - 5, px(-9), torso_y + 3, px(-7), torso_y + 9, fill=COLOR_RED, width=4)
        canvas.create_line(px(5), torso_y - 5, px(9), torso_y + 3, px(7), torso_y + 9, fill=COLOR_RED, width=4)

    # 4. Spider Head
    head_y = torso_y - 17
    canvas.create_oval(px(-8), head_y - 9, px(8), head_y + 9, fill=COLOR_RED, outline=COLOR_BLACK, width=2)
    canvas.create_line(px(-7), head_y, px(7), head_y, fill=COLOR_BLACK, width=1)
    canvas.create_line(px(0), head_y - 8, px(0), head_y + 8, fill=COLOR_BLACK, width=1)
    canvas.create_arc(px(-6), head_y - 6, px(6), head_y + 6, start=20, extent=140, style=tk.ARC, outline=COLOR_BLACK)

    # Angular White Eye Lenses
    canvas.create_polygon([
        px(1), head_y - 5,
        px(7), head_y - 1,
        px(2), head_y + 4,
        px(0), head_y - 1
    ], fill=COLOR_WHITE, outline=COLOR_BLACK, width=2)
    canvas.create_polygon([
        px(-5), head_y - 4,
        px(-2), head_y - 1,
        px(-5), head_y + 3
    ], fill=COLOR_WHITE, outline=COLOR_BLACK, width=1.5)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PARTICLES & COMIC POPUPS
# ═══════════════════════════════════════════════════════════════════════════════
class ParticleManager:
    """Manages dust, web sparks, and hit effects capped at 80 particles for high FPS."""

    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=5, color=COLOR_LIGHT_BLUE, speed=2.5, size=3.0, life=20):
        for _ in range(count):
            if len(self.particles) >= 80:
                self.particles.pop(0)
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(0.5, speed)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd - 0.5,
                "color": color,
                "size": size,
                "life": life,
                "max_life": life
            })

    def update_and_draw(self, canvas, cam_x):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
                sx = p["x"] - cam_x
                if -20 <= sx <= CANVAS_WIDTH + 20:
                    r = p["size"] * (p["life"] / p["max_life"])
                    canvas.create_oval(sx - r, p["y"] - r, sx + r, p["y"] + r, fill=p["color"], outline="")
        self.particles = alive


class ComicPopupManager:
    """Manages floating, rising comic-book exclamations (POW!, THWIP!, WHAM!)."""

    def __init__(self):
        self.popups = []

    def add(self, x, y, text, color=COLOR_YELLOW):
        self.popups.append({
            "x": x,
            "y": y,
            "text": text,
            "color": color,
            "life": 34,
            "vy": -1.8
        })

    def update_and_draw(self, canvas, cam_x):
        alive = []
        for pop in self.popups:
            pop["y"] += pop["vy"]
            pop["life"] -= 1
            if pop["life"] > 0:
                alive.append(pop)
                sx = pop["x"] - cam_x
                if -50 <= sx <= CANVAS_WIDTH + 50:
                    font = get_comic_font(16 if len(pop["text"]) <= 7 else 13, "bold")
                    # Comic drop shadow
                    canvas.create_text(sx + 2, pop["y"] + 2, text=pop["text"], font=font, fill=COLOR_BLACK)
                    canvas.create_text(sx, pop["y"], text=pop["text"], font=font, fill=pop["color"])
        self.popups = alive


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ROOFTOPS, ANCHORS & PICKUPS
# ═══════════════════════════════════════════════════════════════════════════════
class Rooftop:
    """Represents a building rooftop platform."""

    def __init__(self, x, y, w, h=600):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, canvas, cam_x, tile_img=None):
        sx1 = self.x - cam_x
        sx2 = sx1 + self.w
        if sx2 < -VIEW_CULL_MARGIN or sx1 > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        # Main building concrete wall
        canvas.create_rectangle(sx1, self.y + 6, sx2, self.y + self.h,
                                fill=COLOR_NAVY, outline=COLOR_BLACK, width=2)

        # Architectural mortar panels / brick lines
        panel_w = 64
        for px in range(int(sx1), int(sx2), panel_w):
            canvas.create_line(px, self.y + 6, px, self.y + 44, fill="#121832", width=1.5)
            canvas.create_line(px + 32, self.y + 44, px + 32, self.y + 120, fill="#121832", width=1.5)
        canvas.create_line(sx1, self.y + 44, sx2, self.y + 44, fill="#121832", width=1.5)

        # Ledge top: if tile_img exists, tile it; otherwise draw electric-blue comic cornice
        if tile_img is not None:
            tile_w = 128
            start_x = int(sx1)
            while start_x < sx2:
                canvas.create_image(start_x, self.y, image=tile_img, anchor=tk.NW)
                start_x += tile_w
        else:
            canvas.create_rectangle(sx1, self.y - 4, sx2, self.y + 6,
                                    fill=COLOR_BLUE, outline=COLOR_BLACK, width=2)
            canvas.create_line(sx1, self.y - 2, sx2, self.y - 2, fill=COLOR_LIGHT_BLUE, width=2)
            canvas.create_line(sx1, self.y - 4, sx2, self.y - 4, fill=COLOR_WHITE, width=1)
            canvas.create_line(sx1, self.y + 6, sx2, self.y + 6, fill=COLOR_RED, width=1.5)


class AnchorPoint:
    """A web-slinging anchor mounted on physical rooftop poles, cranes, towers and spires."""

    def __init__(self, x, y, kind="crane", base_y=None):
        self.x = x
        self.y = y
        self.kind = kind
        self.base_y = base_y if base_y is not None else y + 140

    def draw(self, canvas, cam_x, is_target=False):
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        by = self.base_y

        if self.kind == "lamp":
            # Rooftop concrete mounting plate
            canvas.create_rectangle(sx - 6, by - 4, sx + 6, by, fill=COLOR_DARK_GRAY, outline=COLOR_BLACK, width=1.5)
            # Main black steel streetlight pole grounded directly onto rooftop
            canvas.create_line(sx, by, sx, self.y + 12, fill=COLOR_BLACK, width=4)
            canvas.create_line(sx - 1, by, sx - 1, self.y + 12, fill=COLOR_BLUE, width=1.5)
            # Curved lamp arm & lantern fixture
            canvas.create_line(sx, self.y + 12, sx - 14, self.y + 6, sx - 18, self.y + 16, fill=COLOR_BLACK, width=3)
            canvas.create_oval(sx - 22, self.y + 12, sx - 14, self.y + 20, fill=COLOR_YELLOW, outline=COLOR_BLACK, width=1.5)
            # Glow cone
            canvas.create_polygon([sx - 20, self.y + 20, sx - 32, self.y + 55, sx - 8, self.y + 55],
                                  fill="", outline=COLOR_YELLOW, dash=(2, 4))

        elif self.kind == "crane":
            # Construction derrick lattice tower rooted on rooftop
            canvas.create_line(sx - 12, by, sx - 12, self.y + 16, fill=COLOR_RED, width=3)
            canvas.create_line(sx + 12, by, sx + 12, self.y + 16, fill=COLOR_RED, width=3)
            # Lattice struts
            step_stride = 24
            for sy in range(int(self.y + 20), int(by), step_stride):
                canvas.create_line(sx - 12, sy, sx + 12, sy, fill=COLOR_BLACK, width=1.5)
                canvas.create_line(sx - 12, sy, sx + 12, sy - step_stride, fill=COLOR_YELLOW, width=1.5)
            # Horizontal boom arm
            canvas.create_line(sx - 24, self.y + 10, sx + 34, self.y + 10, fill=COLOR_RED, width=4)
            canvas.create_line(sx, self.y - 10, sx - 24, self.y + 10, fill=COLOR_BLACK, width=1.5)
            canvas.create_line(sx, self.y - 10, sx + 34, self.y + 10, fill=COLOR_BLACK, width=1.5)
            # Pulley hoist cable to anchor ring
            canvas.create_line(sx + 20, self.y + 10, sx + 20, self.y, fill=COLOR_WHITE, width=2)
            # Beacon light
            canvas.create_oval(sx - 3, self.y - 12, sx + 3, self.y - 6, fill=COLOR_YELLOW, outline="")

        elif self.kind == "antenna":
            # Radio mast lattice grounded on rooftop
            canvas.create_rectangle(sx - 8, by - 4, sx + 8, by, fill=COLOR_DARK_GRAY, outline=COLOR_BLACK)
            canvas.create_line(sx, by, sx, self.y, fill=COLOR_BLACK, width=3)
            canvas.create_line(sx - 18, by, sx, self.y + 40, fill=COLOR_BLUE, width=1.5)
            canvas.create_line(sx + 18, by, sx, self.y + 40, fill=COLOR_BLUE, width=1.5)
            # Cross dipole bars
            for dy in [20, 48, 76]:
                canvas.create_line(sx - 14, self.y + dy, sx + 14, self.y + dy, fill=COLOR_LIGHT_BLUE, width=2)
            # Red warning aviation beacon
            canvas.create_oval(sx - 4, self.y - 7, sx + 4, self.y + 1, fill=COLOR_RED, outline="")

        elif self.kind == "water_tower":
            # NYC rooftop timber tank on steel stilts
            canvas.create_line(sx - 20, by, sx - 14, self.y + 48, fill="#334155", width=3)
            canvas.create_line(sx + 20, by, sx + 14, self.y + 48, fill="#334155", width=3)
            canvas.create_line(sx - 14, by, sx + 14, by, fill=COLOR_BLACK, width=2)
            # Tank body
            canvas.create_rectangle(sx - 22, self.y + 14, sx + 22, self.y + 48,
                                    fill="#0F172A", outline=COLOR_RED, width=2)
            canvas.create_line(sx - 22, self.y + 26, sx + 22, self.y + 26, fill=COLOR_BLACK, width=2)
            canvas.create_line(sx - 22, self.y + 38, sx + 22, self.y + 38, fill=COLOR_BLACK, width=2)
            # Conical roof & lightning rod
            canvas.create_polygon([sx - 24, self.y + 14, sx, self.y + 2, sx + 24, self.y + 14],
                                  fill="#1E293B", outline=COLOR_BLACK, width=2)
            canvas.create_line(sx, self.y + 2, sx, self.y, fill=COLOR_WHITE, width=2)

        elif self.kind == "spire":
            # Neoclassical Art Deco spire pinnacle
            canvas.create_rectangle(sx - 18, by - 8, sx + 18, by, fill=COLOR_DARK_GRAY, outline=COLOR_BLACK, width=2)
            canvas.create_polygon([sx - 10, by - 8, sx, self.y, sx + 10, by - 8],
                                  fill=COLOR_BLUE, outline=COLOR_BLACK, width=2)
            canvas.create_line(sx, by - 8, sx, self.y, fill=COLOR_WHITE, width=1.5)

        elif self.kind == "billboard":
            canvas.create_line(sx - 16, by, sx - 16, self.y + 6, fill=COLOR_BLACK, width=3)
            canvas.create_line(sx + 16, by, sx + 16, self.y + 6, fill=COLOR_BLACK, width=3)
            canvas.create_rectangle(sx - 22, self.y - 12, sx + 22, self.y + 6,
                                    fill=COLOR_BLUE, outline=COLOR_BLACK, width=2)

        # Glowing Anchor ring on top
        ring_color = COLOR_YELLOW if is_target else COLOR_LIGHT_BLUE
        r = 9 if is_target else 6
        canvas.create_oval(sx - r, self.y - r, sx + r, self.y + r,
                           fill=COLOR_NAVY, outline=ring_color, width=3)
        canvas.create_oval(sx - 2, self.y - 2, sx + 2, self.y + 2, fill=COLOR_WHITE, outline="")
        if is_target:
            # Active target beacon pulse
            canvas.create_oval(sx - 14, self.y - 14, sx + 14, self.y + 14, outline=COLOR_YELLOW, width=1.5)


class FluidCartridge:
    """Collectable web-fluid cartridge awarding +50 score bonus and web sparkle effects."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.anim_t = random.uniform(0, math.pi * 2)

    def draw(self, canvas, cam_x, icon_img=None):
        if self.collected:
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        self.anim_t += 0.08
        bob = math.sin(self.anim_t) * 4
        sy = self.y + bob

        if icon_img is not None:
            canvas.create_image(sx, sy, image=icon_img, anchor=tk.CENTER)
        else:
            canvas.create_rectangle(sx - 8, sy - 14, sx + 8, sy + 14,
                                    fill=COLOR_BLUE, outline=COLOR_BLACK, width=2)
            canvas.create_rectangle(sx - 6, sy - 10, sx + 6, sy + 10,
                                    fill=COLOR_LIGHT_BLUE, outline="")
            canvas.create_rectangle(sx - 4, sy - 18, sx + 4, sy - 14,
                                    fill=COLOR_RED, outline=COLOR_BLACK, width=1.5)
            canvas.create_line(sx - 5, sy - 12, sx - 5, sy + 8, fill=COLOR_WHITE, width=2)


class MedkitPickup:
    """Medical first-aid crate on rooftops restoring +2 hearts on touch."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.anim_t = random.uniform(0, math.pi * 2)

    def draw(self, canvas, cam_x, icon_img=None):
        if self.collected:
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        self.anim_t += 0.08
        bob = math.sin(self.anim_t) * 3
        sy = self.y + bob

        if icon_img is not None:
            canvas.create_image(sx, sy, image=icon_img, anchor=tk.CENTER)
        else:
            # Glowing green medical pulse aura
            canvas.create_oval(sx - 18, sy - 18, sx + 18, sy + 18, fill="", outline="#4ADE80", width=1.5)
            # White emergency first-aid crate
            canvas.create_rectangle(sx - 12, sy - 9, sx + 12, sy + 9, fill=COLOR_WHITE, outline=COLOR_BLACK, width=2)
            canvas.create_line(sx - 4, sy - 11, sx + 4, sy - 11, fill=COLOR_BLACK, width=2)
            # Bold Red Cross
            canvas.create_rectangle(sx - 7, sy - 2.5, sx + 7, sy + 2.5, fill=COLOR_RED, outline="")
            canvas.create_rectangle(sx - 2.5, sy - 7, sx + 2.5, sy + 7, fill=COLOR_RED, outline="")


class MissionItem:
    """Interactive mission object: trapped civilian, data chip, bomb or extraction gate."""

    def __init__(self, x, y, kind="civilian"):
        self.x = x
        self.y = y
        self.kind = kind
        self.completed = False
        self.hold_progress = 0.0
        self.hold_required = 1.0 if kind == "civilian" else 2.0  # seconds

    def draw(self, canvas, cam_x, tick, icon_img=None):
        if self.completed and self.kind != "gate":
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        if self.kind == "civilian":
            if icon_img is not None:
                canvas.create_image(sx, self.y, image=icon_img, anchor=tk.CENTER)
            else:
                canvas.create_oval(sx - 14, self.y - 20, sx + 14, self.y + 20,
                                   fill=COLOR_NAVY, outline=COLOR_BLACK, width=2)
                canvas.create_oval(sx - 8, self.y - 14, sx + 8, self.y + 2,
                                   fill="#FED7AA", outline=COLOR_BLACK, width=1.5)
                canvas.create_oval(sx - 5, self.y - 9, sx - 2, self.y - 5, fill=COLOR_BLACK)
                canvas.create_oval(sx + 2, self.y - 9, sx + 5, self.y - 5, fill=COLOR_BLACK)
                for dy in [-16, -6, 4, 14]:
                    canvas.create_line(sx - 13, self.y + dy, sx + 13, self.y + dy, fill=COLOR_WHITE, width=2)
                    canvas.create_line(sx - 13, self.y + dy + 4, sx + 13, self.y + dy - 4, fill=COLOR_WHITE, width=1.5)

        elif self.kind == "chip":
            if icon_img is not None:
                canvas.create_image(sx, self.y, image=icon_img, anchor=tk.CENTER)
            else:
                canvas.create_polygon([
                    sx - 12, self.y - 14,
                    sx + 4, self.y - 14,
                    sx + 12, self.y - 6,
                    sx + 12, self.y + 14,
                    sx - 12, self.y + 14
                ], fill=COLOR_RED, outline=COLOR_BLACK, width=2)
                canvas.create_rectangle(sx - 5, self.y - 5, sx + 5, self.y + 5, fill=COLOR_BLUE)
                canvas.create_line(sx - 3, self.y, sx + 3, self.y, fill=COLOR_LIGHT_BLUE, width=2)

        elif self.kind == "bomb":
            if icon_img is not None:
                canvas.create_image(sx, self.y, image=icon_img, anchor=tk.CENTER)
            else:
                canvas.create_oval(sx - 15, self.y - 14, sx + 15, self.y + 16,
                                   fill=COLOR_RED, outline=COLOR_BLACK, width=2)
                canvas.create_polygon([sx - 8, self.y - 3, sx - 3, self.y - 5, sx - 4, self.y + 1], fill=COLOR_YELLOW)
                canvas.create_polygon([sx + 8, self.y - 3, sx + 3, self.y - 5, sx + 4, self.y + 1], fill=COLOR_YELLOW)
                canvas.create_line(sx - 7, self.y + 8, sx + 7, self.y + 8, fill=COLOR_YELLOW, width=3)
                fuse_color = COLOR_YELLOW if (tick // 3) % 2 == 0 else COLOR_WHITE
                canvas.create_line(sx, self.y - 14, sx + 6, self.y - 22, fill=COLOR_BLACK, width=2)
                canvas.create_oval(sx + 4, self.y - 25, sx + 9, self.y - 20, fill=fuse_color, outline="")

        elif self.kind == "gate":
            # Giant Extraction Portal / Safe Landing Zone
            canvas.create_rectangle(sx - 32, self.y - 110, sx + 32, self.y,
                                    fill=COLOR_NAVY, outline=COLOR_BLUE, width=4)
            # Beams
            pulse = (tick * 4) % 110
            canvas.create_line(sx - 28, self.y - pulse, sx + 28, self.y - pulse, fill=COLOR_LIGHT_BLUE, width=3)
            canvas.create_text(sx, self.y - 130, text="▼ EXTRACTION ZONE ▼",
                               font=get_comic_font(13, "bold"), fill=COLOR_YELLOW)

        # Hold-E radial progress ring
        if self.hold_progress > 0.0 and not self.completed:
            arc_extent = int(self.hold_progress * 360)
            canvas.create_oval(sx - 26, self.y - 26, sx + 26, self.y + 26, outline=COLOR_BLACK, width=4)
            canvas.create_arc(sx - 26, self.y - 26, sx + 26, self.y + 26,
                              start=90, extent=-arc_extent, style=tk.ARC, outline=COLOR_YELLOW, width=4)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ENEMY CLASS HIERARCHY
# ═══════════════════════════════════════════════════════════════════════════════
class Enemy:
    """Base class for comic-book enemies."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.hp = 1
        self.stun_timer = 0
        self.active = True
        self.facing = -1

    def is_stunned(self):
        return self.stun_timer > 0

    def stun(self):
        self.stun_timer = STUN_DURATION_TICKS

    def update(self, player, rooftops):
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

    def draw_cocoon(self, canvas, sx, sy, r=18):
        """Draws a white web cocoon when stunned by web-shot."""
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill="", outline=COLOR_WHITE, width=3)
        canvas.create_line(sx - r + 3, sy - r + 3, sx + r - 3, sy + r - 3, fill=COLOR_WHITE, width=2)
        canvas.create_line(sx - r + 3, sy + r - 3, sx + r - 3, sy - r + 3, fill=COLOR_WHITE, width=2)
        canvas.create_line(sx - r, sy, sx + r, sy, fill=COLOR_WHITE, width=2)
        canvas.create_line(sx, sy - r, sx, sy + r, fill=COLOR_WHITE, width=2)


class StreetThug(Enemy):
    """Patrols rooftops, lunges at Spider-Man, stompable from above."""

    def __init__(self, x, y, min_x, max_x):
        super().__init__(x, y)
        self.min_x = min_x
        self.max_x = max_x
        self.speed = 2.0
        self.vx = self.speed
        self.w = 26
        self.h = 42
        self.telegraph_attack = 0

    def update(self, player, rooftops):
        super().update(player, rooftops)
        if self.is_stunned() or not self.active:
            return

        dist_x = player.x - self.x
        dist_y = abs(player.y - self.y)
        if abs(dist_x) < 220 and dist_y < 45:
            self.facing = 1 if dist_x > 0 else -1
            self.vx = self.facing * (self.speed + 0.6)
            if abs(dist_x) < 55:
                self.telegraph_attack = 18
        else:
            self.telegraph_attack = max(0, self.telegraph_attack - 1)
            if self.x <= self.min_x:
                self.vx = self.speed
                self.facing = 1
            elif self.x >= self.max_x:
                self.vx = -self.speed
                self.facing = -1

        self.x += self.vx

    def draw(self, canvas, cam_x, tick):
        if not self.active:
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        leg_offset = math.sin(tick * 0.3) * 6 if not self.is_stunned() else 0
        canvas.create_line(sx - 4, self.y + 10, sx - 6 - leg_offset, self.y + 24, fill=COLOR_BLACK, width=4)
        canvas.create_line(sx + 4, self.y + 10, sx + 6 + leg_offset, self.y + 24, fill=COLOR_BLACK, width=4)
        canvas.create_rectangle(sx - 10, self.y - 12, sx + 10, self.y + 10,
                                fill="#7E22CE", outline=COLOR_BLACK, width=2)
        canvas.create_oval(sx - 7, self.y - 25, sx + 7, self.y - 12, fill="#374151", outline=COLOR_BLACK, width=2)
        canvas.create_line(sx - 3, self.y - 19, sx + 3, self.y - 19, fill=COLOR_WHITE, width=2)
        cx = sx + (12 * self.facing)
        canvas.create_line(sx, self.y - 2, cx, self.y - 14, fill=COLOR_YELLOW, width=3)

        if self.is_stunned():
            self.draw_cocoon(canvas, sx, self.y)


class SentryDrone(Enemy):
    """Oscorp security drone that locks on with a red laser telegraph then fires."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.base_y = y
        self.hover_t = random.uniform(0, math.pi * 2)
        self.lock_timer = 0
        self.cooldown = 0
        self.laser_firing = False
        self.target_px = 0
        self.target_py = 0

    def update(self, player, rooftops):
        super().update(player, rooftops)
        if self.is_stunned() or not self.active:
            self.lock_timer = 0
            self.laser_firing = False
            return

        self.hover_t += 0.08
        self.y = self.base_y + math.sin(self.hover_t) * 14

        dist = math.hypot(player.x - self.x, player.y - self.y)
        if self.cooldown > 0:
            self.cooldown -= 1
            self.laser_firing = False
            return

        if dist < 440:
            self.lock_timer += 1
            # Track player until tick 36; then freeze aim position so player can dodge!
            if self.lock_timer < 36:
                self.target_px = player.x
                self.target_py = player.y

            # Fire laser beam from tick 50 to 54
            if self.lock_timer >= 50:
                self.laser_firing = True
                if self.lock_timer >= 54:
                    self.cooldown = 60
                    self.lock_timer = 0
                    self.laser_firing = False
        else:
            self.lock_timer = max(0, self.lock_timer - 1)
            self.laser_firing = False

    def draw(self, canvas, cam_x, tick):
        if not self.active:
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        # Telegraph laser beam
        if self.lock_timer > 0 and not self.is_stunned() and not self.laser_firing:
            t_sx = self.target_px - cam_x
            if self.lock_timer >= 36:
                # Target aim is locked: solid warning line with blinking reticle
                beam_color = COLOR_RED if (tick // 2) % 2 == 0 else COLOR_YELLOW
                canvas.create_line(sx, self.y, t_sx, self.target_py, fill=beam_color, width=2)
                canvas.create_oval(t_sx - 8, self.target_py - 8, t_sx + 8, self.target_py + 8,
                                   outline=COLOR_RED, width=2)
            else:
                # Tracking player: dotted line
                beam_color = COLOR_YELLOW if (tick // 2) % 2 == 0 else COLOR_LIGHT_BLUE
                canvas.create_line(sx, self.y, t_sx, self.target_py,
                                   fill=beam_color, width=1.5, dash=(4, 4))

        if self.laser_firing:
            t_sx = self.target_px - cam_x
            canvas.create_line(sx, self.y, t_sx, self.target_py, fill=COLOR_RED, width=5)
            canvas.create_line(sx, self.y, t_sx, self.target_py, fill=COLOR_WHITE, width=2)
            canvas.create_oval(t_sx - 10, self.target_py - 10, t_sx + 10, self.target_py + 10,
                               fill=COLOR_YELLOW, outline=COLOR_RED, width=2)

        canvas.create_polygon([
            sx - 18, self.y - 6,
            sx, self.y - 14,
            sx + 18, self.y - 6,
            sx + 12, self.y + 12,
            sx - 12, self.y + 12
        ], fill="#334155", outline=COLOR_BLACK, width=2)
        canvas.create_oval(sx - 5, self.y - 3, sx + 5, self.y + 7, fill=COLOR_RED, outline=COLOR_BLACK)
        canvas.create_line(sx - 16, self.y + 8, sx - 22, self.y + 14, fill=COLOR_LIGHT_BLUE, width=3)
        canvas.create_line(sx + 16, self.y + 8, sx + 22, self.y + 14, fill=COLOR_LIGHT_BLUE, width=3)

        if self.is_stunned():
            self.draw_cocoon(canvas, sx, self.y)


class GoblinBomber(Enemy):
    """Flies overhead on a glider and drops pumpkin bombs with ground telegraphs."""

    def __init__(self, start_x, y=110):
        super().__init__(start_x, y)
        self.flight_t = 0.0
        self.drop_cooldown = 80
        self.bombs = []

    def update(self, player, rooftops):
        super().update(player, rooftops)
        self.flight_t += 0.04
        target_x = player.x + math.sin(self.flight_t) * 160
        self.x += (target_x - self.x) * 0.04
        self.y = 110 + math.sin(self.flight_t * 1.5) * 16

        if not self.is_stunned():
            self.drop_cooldown -= 1
            if self.drop_cooldown <= 0 and abs(player.x - self.x) < 260:
                target_ground_y = 440
                for r in rooftops:
                    if r.x <= player.x <= r.x + r.w:
                        target_ground_y = r.y
                        break
                self.bombs.append({
                    "x": self.x,
                    "y": self.y + 10,
                    "target_x": player.x + random.uniform(-40, 40),
                    "target_y": target_ground_y,
                    "vy": 1.5,
                    "ticks_to_hit": 50,
                    "exploded": False
                })
                self.drop_cooldown = 110

        alive_bombs = []
        for b in self.bombs:
            b["ticks_to_hit"] -= 1
            b["y"] += (b["target_y"] - b["y"]) / max(1, b["ticks_to_hit"])
            b["x"] += (b["target_x"] - b["x"]) / max(1, b["ticks_to_hit"])
            if b["ticks_to_hit"] <= 0:
                b["exploded"] = True
            else:
                alive_bombs.append(b)
        self.bombs = alive_bombs

    def draw(self, canvas, cam_x, tick):
        if not self.active:
            return
        sx = self.x - cam_x
        if sx < -VIEW_CULL_MARGIN or sx > CANVAS_WIDTH + VIEW_CULL_MARGIN:
            return

        canvas.create_polygon([
            sx - 35, self.y + 8,
            sx - 15, self.y,
            sx, self.y + 12,
            sx + 15, self.y,
            sx + 35, self.y + 8,
            sx + 20, self.y + 16,
            sx - 20, self.y + 16
        ], fill="#15803D", outline=COLOR_BLACK, width=2)
        canvas.create_oval(sx - 7, self.y - 16, sx + 7, self.y - 2, fill="#16A34A", outline=COLOR_BLACK, width=2)
        canvas.create_polygon([sx - 12, self.y - 24, sx, self.y - 12, sx - 4, self.y - 8], fill="#7E22CE")
        canvas.create_line(sx - 10, self.y + 14, sx - 16, self.y + 22, fill="#A855F7", width=3)
        canvas.create_line(sx + 10, self.y + 14, sx + 16, self.y + 22, fill="#A855F7", width=3)

        for b in self.bombs:
            bx = b["x"] - cam_x
            tx = b["target_x"] - cam_x
            pulse_r = 22 + (b["ticks_to_hit"] % 4) * 2
            canvas.create_oval(tx - pulse_r, b["target_y"] - 8, tx + pulse_r, b["target_y"] + 8,
                               outline=COLOR_RED, width=3)
            canvas.create_text(tx, b["target_y"] - 14, text="DANGER!", font=get_comic_font(9, "bold"), fill=COLOR_RED)
            canvas.create_oval(bx - 9, b["y"] - 9, bx + 9, b["y"] + 9, fill=COLOR_RED, outline=COLOR_BLACK, width=2)
            canvas.create_oval(bx - 3, b["y"] - 3, bx + 3, b["y"] + 3, fill=COLOR_YELLOW)

        if self.is_stunned():
            self.draw_cocoon(canvas, sx, self.y, r=26)


class HunterDrone(Enemy):
    """Mission 5 Chase Drone that advances relentlessly from the left."""

    def __init__(self, start_x):
        super().__init__(start_x, 260)
        self.speed = 3.6
        self.w = 90
        self.h = 160

    def update(self, player, rooftops):
        self.x += self.speed
        self.y = player.y

    def draw(self, canvas, cam_x, tick):
        sx = self.x - cam_x
        canvas.create_polygon([
            sx - 60, self.y - 90,
            sx + 30, self.y - 50,
            sx + 50, self.y,
            sx + 30, self.y + 50,
            sx - 60, self.y + 90
        ], fill="#1E293B", outline=COLOR_RED, width=4)
        eye_color = COLOR_YELLOW if (tick // 4) % 2 == 0 else COLOR_RED
        canvas.create_oval(sx + 10, self.y - 18, sx + 42, self.y + 18, fill=eye_color, outline=COLOR_BLACK, width=3)
        ang = tick * 0.4
        for da in [0, math.pi / 2, math.pi, math.pi * 1.5]:
            bx = sx + 48 + math.cos(ang + da) * 24
            by = self.y + math.sin(ang + da) * 24
            canvas.create_line(sx + 48, self.y, bx, by, fill=COLOR_LIGHT_BLUE, width=3)
        canvas.create_text(sx - 10, self.y - 65, text="HUNTER V-9", font=get_comic_font(12, "bold"), fill=COLOR_RED)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PLAYER CLASS (SUPERHERO FLUIDITY & UNLIMITED SWINGING)
# ═══════════════════════════════════════════════════════════════════════════════
class Player:
    """The Spider-Man player entity handling physics, swinging and abilities."""

    def __init__(self, x=150, y=360):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.pose = "idle"

        # Platforming Physics State
        self.on_ground = False
        self.coyote_timer = 0
        self.jump_buffered = 0
        self.can_double_jump = True
        self.last_safe_x = x
        self.last_safe_y = y

        # Web Swing State
        self.is_swinging = False
        self.swing_anchor = None
        self.swing_len = 0.0
        self.swing_angle = 0.0
        self.swing_dtheta = 0.0

        # Health & Fluid
        self.hearts = MAX_HEARTS
        self.web_fluid = MAX_FLUID     # Unlimited fluid
        self.invincible = 0
        self.crouch_hold = False
        self.interact_item = None

        # Combat Attack State
        self.attack_timer = 0
        self.attack_type = "punch"

    def take_damage(self, amount=1):
        """Reduces hearts ONLY when hit by enemies."""
        if self.invincible <= 0:
            self.hearts = max(0, self.hearts - amount)
            self.invincible = INVINCIBLE_TICKS
            return True
        return False

    def respawn_at_safe(self):
        """Catapults player safely back onto the rooftop with a safety web (NO damage)."""
        self.x = self.last_safe_x
        self.y = self.last_safe_y - 30
        self.vx = 4.0 * self.facing
        self.vy = -11.0  # Heroic upward flip onto roof
        self.is_swinging = False
        self.on_ground = False
        self.can_double_jump = True

    def attach_swing(self, anchors):
        """
        Attaches web to the nearest physical rooftop pole or crane ahead.
        Falls back to overhead skyline if no physical pole is in range.
        """
        if self.is_swinging:
            return False

        best = None
        best_dist = 999999
        for a in anchors:
            dx = a.x - self.x
            dy = a.y - self.y
            dist = math.hypot(dx, dy)
            # Find poles ahead or directly overhead
            if dist <= SWING_ATTACH_RADIUS and dy < 25 and (dx * self.facing >= -75):
                if dist < best_dist:
                    best_dist = dist
                    best = a

        # If no physical pole is in range, shoot web up to the overhead skyscraper skyline!
        if not best:
            sky_x = self.x + (160 * self.facing)
            sky_y = max(30.0, self.y - 280.0)
            best = AnchorPoint(sky_x, sky_y, kind="sky", base_y=self.y)

        self.is_swinging = True
        self.swing_anchor = best
        dx = self.x - best.x
        dy = self.y - best.y
        self.swing_len = max(120.0, min(400.0, math.hypot(dx, dy)))
        self.swing_angle = math.atan2(dx, dy)
        # Give initial forward swing momentum
        init_spd = max(5.2, abs(self.vx) + 3.0) * self.facing
        self.swing_dtheta = (init_spd * math.cos(self.swing_angle)) / self.swing_len
        self.can_double_jump = True
        return True

    def release_swing(self):
        """Releases the web line and launches upward and forward with exhilarating momentum!"""
        if not self.is_swinging:
            return
        self.is_swinging = False
        if self.swing_anchor:
            tangent_spd = self.swing_len * self.swing_dtheta * SWING_LAUNCH_BOOST
            # Launch higher and farther with authentic pendulum kinetic energy
            self.vx = tangent_spd * math.cos(self.swing_angle) * 1.35
            self.vy = - abs(tangent_spd * math.sin(self.swing_angle)) * 1.35 - 4.8
            # Clamp limits to generous hero values
            self.vx = max(-18.0, min(18.0, self.vx))
            self.vy = max(-17.0, min(6.0, self.vy))
            self.swing_anchor = None
            self.can_double_jump = True

    def update(self, keys, mouse_swing_held, rooftops, anchors):
        """Fixed-step physics update."""
        if self.invincible > 0:
            self.invincible -= 1

        # ── 1. DYNAMIC AUTHENTIC PENDULUM WEB SWINGING ──
        if self.is_swinging:
            if not mouse_swing_held:
                self.release_swing()
            else:
                self.web_fluid = MAX_FLUID  # Always full
                # Authentic pendulum angular gravity acceleration: swoops down fast, climbs to crest
                accel = - (1.65 / self.swing_len) * math.sin(self.swing_angle)
                self.swing_dtheta += accel
                self.swing_dtheta *= 0.9992

                # Swing height pumping: hold W or Up or Space to reel in and gain height
                if keys.get("w") or keys.get("Up") or keys.get("space"):
                    self.swing_len = max(85.0, self.swing_len - 4.5)
                    self.swing_dtheta += 0.0030 * (1 if self.swing_dtheta >= 0 else -1)

                # Horizontal pumping: accelerate swing
                if keys.get("d") or keys.get("Right"):
                    self.swing_dtheta += 0.0035
                    self.facing = 1
                elif keys.get("a") or keys.get("Left"):
                    self.swing_dtheta -= 0.0035
                    self.facing = -1

                self.swing_angle += self.swing_dtheta
                self.x = self.swing_anchor.x + self.swing_len * math.sin(self.swing_angle)
                self.y = self.swing_anchor.y + self.swing_len * math.cos(self.swing_angle)
                self.pose = "swing"
                self.on_ground = False
                return

        # ── 2. ON-FOOT RUNNING & JUMPING ──
        move_dir = 0
        if keys.get("d") or keys.get("Right"):
            move_dir += 1
        if keys.get("a") or keys.get("Left"):
            move_dir -= 1

        if move_dir != 0:
            self.facing = move_dir
            self.vx += move_dir * MOVE_ACCEL
            self.vx = max(-MAX_RUN_SPEED, min(MAX_RUN_SPEED, self.vx))
            if self.on_ground:
                self.pose = "run"
        else:
            self.vx *= MOVE_DECEL
            if abs(self.vx) < 0.2:
                self.vx = 0.0
            if self.on_ground:
                self.pose = "idle"

        # Combat Attack Pose Override
        if self.attack_timer > 0:
            self.attack_timer -= 1
            self.pose = self.attack_type

        # Gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Coyote time & jump buffer
        if self.on_ground:
            self.coyote_timer = COYOTE_MAX_TICKS
            self.can_double_jump = True
        else:
            self.coyote_timer = max(0, self.coyote_timer - 1)

        # Jump execution
        jump_requested = keys.get("w") or keys.get("Up") or keys.get("space")
        if jump_requested:
            if self.jump_buffered == 0:
                self.jump_buffered = JUMP_BUFFER_TICKS

        if self.jump_buffered > 0:
            self.jump_buffered -= 1
            if self.coyote_timer > 0:
                self.vy = JUMP_VELOCITY
                self.coyote_timer = 0
                self.jump_buffered = 0
                self.on_ground = False
            elif self.can_double_jump:
                self.vy = DOUBLE_JUMP_VELOCITY
                self.can_double_jump = False
                self.jump_buffered = 0

        # Apply velocity
        self.x += self.vx
        self.y += self.vy

        # ── 3. ROOFTOP COLLISION DETECTION ──
        self.on_ground = False
        foot_y = self.y + 34
        for r in rooftops:
            if r.x - 14 <= self.x <= r.x + r.w + 14:
                if r.y - 8 <= foot_y <= r.y + 16 and self.vy >= 0:
                    self.y = r.y - 34
                    self.vy = 0.0
                    self.on_ground = True
                    self.last_safe_x = self.x
                    self.last_safe_y = self.y
                    break

        if not self.on_ground and self.attack_timer <= 0:
            self.pose = "jump" if self.vy < 0 else "fall"

        if self.crouch_hold and self.attack_timer <= 0:
            self.pose = "crouch"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. MISSION SYSTEM (DATA-DRIVEN)
# ═══════════════════════════════════════════════════════════════════════════════
MISSIONS = [
    {
        "id": 1,
        "title": "Rooftop Rescue",
        "length": 5200,
        "desc": "Hostile street thugs have ambushed civilians along the skyline. Locate and free 3 trapped civilians by holding [E] near them. Watch your footing, swing between streetlights, and punch or stomp thugs!",
        "target_type": "civilian",
        "target_count": 3,
        "thugs": 7, "drones": 0, "bombers": 0, "hunter": False,
        "cartridge_count": 14,
        "medkit_count": 3,
        "par_time": 75,
    },
    {
        "id": 2,
        "title": "Data Heist",
        "length": 5600,
        "desc": "Oscorp security drones guard encrypted data chips along high-rise towers. Infiltrate and retrieve all 5 chips! Evade telegraphed laser beams or use Right-Click combat & Medkits.",
        "target_type": "chip",
        "target_count": 5,
        "thugs": 4, "drones": 4, "bombers": 0, "hunter": False,
        "cartridge_count": 14,
        "medkit_count": 4,
        "par_time": 85,
    },
    {
        "id": 3,
        "title": "Defuse the Bombs",
        "length": 5800,
        "desc": "The Green Goblin has rigged 3 pumpkin bombs across the downtown sector! Reach each bomb and hold [E] for 2 seconds to disarm it before the 90s countdown runs out. Look out for glider air strikes!",
        "target_type": "bomb",
        "target_count": 3,
        "time_limit": 90,
        "thugs": 5, "drones": 3, "bombers": 1, "hunter": False,
        "cartridge_count": 15,
        "medkit_count": 3,
        "par_time": 70,
    },
    {
        "id": 4,
        "title": "Skyline Sprint",
        "length": 6200,
        "desc": "Sprint and web-swing across dizzying skyscraper chasms. Use your unlimited web-fluid and authentic pendulum swing physics to soar to the extraction portal in record time!",
        "target_type": "gate",
        "target_count": 1,
        "thugs": 5, "drones": 4, "bombers": 0, "hunter": False,
        "cartridge_count": 14,
        "medkit_count": 4,
        "par_time": 95,
    },
    {
        "id": 5,
        "title": "Escape the Hunter",
        "length": 6800,
        "desc": "CRITICAL EMERGENCY: An experimental Hunter Drone has locked onto your signature! Web-swing across the city to the extraction gate before the Hunter catches you. All forces active!",
        "target_type": "gate",
        "target_count": 1,
        "thugs": 6, "drones": 5, "bombers": 1, "hunter": True,
        "cartridge_count": 16,
        "medkit_count": 4,
        "par_time": 90,
    }
]


def generate_level(mission_data, seed_val=100):
    """
    Procedurally generates level geometry based on mission specs.
    Guarantees:
    - Dense physical rooftop poles, cranes, antennas, and water towers rooted directly to roofs.
    - Health medkit pickups distributed along rooftops for heart recovery.
    - Wide, connected rooftops with natural gaps.
    - Massive, safe final Extraction Rooftop with skyscraper barrier.
    """
    rng = random.Random(seed_val)
    length = mission_data["length"]

    rooftops = []
    anchors = []
    cartridges = []
    medkits = []
    items = []
    enemies = []

    # 1. Safe starting rooftop (width 800)
    cur_x = 0
    cur_y = 390
    rooftops.append(Rooftop(cur_x, cur_y, 800))
    anchors.append(AnchorPoint(cur_x + 200, cur_y - 130, "lamp", base_y=cur_y))
    anchors.append(AnchorPoint(cur_x + 440, cur_y - 170, "antenna", base_y=cur_y))
    anchors.append(AnchorPoint(cur_x + 680, cur_y - 180, "crane", base_y=cur_y))
    cur_x += 800

    # 2. Build rooftop chain with dense physical poles every 120-180 px
    while cur_x < length:
        gap = rng.randint(90, 210)
        roof_w = rng.randint(450, 700)
        dy = rng.randint(-50, 50)
        cur_y = max(280, min(420, cur_y + dy))

        # Anchor suspended over the gap
        anchor_x = cur_x + gap * 0.5
        anchor_y = min(cur_y - 140, 200)
        gap_kind = rng.choice(["crane", "lamp", "billboard"])
        anchors.append(AnchorPoint(anchor_x, anchor_y, gap_kind, base_y=cur_y))

        cur_x += gap
        rooftop = Rooftop(cur_x, cur_y, roof_w)
        rooftops.append(rooftop)

        # 3 physical poles on every rooftop: Left, Center landmark, Right
        anchors.append(AnchorPoint(cur_x + 80, cur_y - 135, rng.choice(["lamp", "antenna"]), base_y=cur_y))

        center_kind = rng.choice(["crane", "water_tower", "spire"])
        center_h = 175 if center_kind == "crane" else (150 if center_kind == "water_tower" else 165)
        anchors.append(AnchorPoint(cur_x + roof_w * 0.5, cur_y - center_h, center_kind, base_y=cur_y))

        anchors.append(AnchorPoint(cur_x + roof_w - 80, cur_y - 135, rng.choice(["lamp", "antenna"]), base_y=cur_y))

        cur_x += roof_w

    # Final giant Extraction Rooftop with safety barrier
    final_w = 1200
    final_roof = Rooftop(cur_x, cur_y, final_w)
    rooftops.append(final_roof)
    rooftops.append(Rooftop(cur_x + final_w - 40, cur_y - 320, 200, 500))
    anchors.append(AnchorPoint(cur_x + 220, cur_y - 135, "lamp", base_y=cur_y))
    anchors.append(AnchorPoint(cur_x + 520, cur_y - 175, "crane", base_y=cur_y))
    anchors.append(AnchorPoint(cur_x + 860, cur_y - 160, "spire", base_y=cur_y))
    cur_x += final_w

    # 3. Distribute Fluid Cartridges along roofs
    cartridge_budget = mission_data.get("cartridge_count", 14)
    step = len(rooftops) // max(1, cartridge_budget)
    for i in range(1, len(rooftops) - 1, max(1, step)):
        r = rooftops[i]
        cartridges.append(FluidCartridge(r.x + r.w * 0.45, r.y - 20))

    # 4. Distribute Medkit Health Pickups (+2 hearts recovery)
    medkit_budget = mission_data.get("medkit_count", 3)
    if len(rooftops) > 3:
        med_step = max(2, len(rooftops) // max(1, medkit_budget))
        for i in range(2, len(rooftops) - 1, med_step):
            r = rooftops[i]
            medkits.append(MedkitPickup(r.x + r.w * 0.78, r.y - 16))

    # 5. Place Mission Objective Items
    target_type = mission_data["target_type"]
    target_count = mission_data["target_count"]

    if target_type == "gate":
        items.append(MissionItem(final_roof.x + 500, final_roof.y, "gate"))
    else:
        # Spread evenly across middle rooftops
        available_roofs = rooftops[2:-2]
        spacing = len(available_roofs) // max(1, target_count)
        for i in range(target_count):
            idx = min(len(available_roofs) - 1, i * spacing + rng.randint(0, max(0, spacing - 1)))
            r = available_roofs[idx]
            items.append(MissionItem(r.x + r.w * 0.5, r.y - 15, target_type))

    # 6. Populate Enemies
    thug_count = mission_data["thugs"]
    thug_step = len(rooftops) // max(1, thug_count)
    for i in range(1, len(rooftops) - 2, max(1, thug_step)):
        r = rooftops[i]
        enemies.append(StreetThug(r.x + 80, r.y - 20, r.x + 30, r.x + r.w - 30))

    drone_count = mission_data["drones"]
    for i in range(drone_count):
        dx = 700 + (length - 900) * (i / max(1, drone_count)) + rng.randint(-80, 80)
        enemies.append(SentryDrone(dx, rng.randint(200, 310)))

    if mission_data.get("bombers", 0) > 0:
        enemies.append(GoblinBomber(800))

    if mission_data.get("hunter", False):
        enemies.append(HunterDrone(0))

    return rooftops, anchors, cartridges, medkits, items, enemies


# ═══════════════════════════════════════════════════════════════════════════════
# 9. MAIN GAME CLASS (STATE MACHINE, CANVAS UI & EVENT LOOP)
# ═══════════════════════════════════════════════════════════════════════════════
class Game:
    """Master controller managing game loop, UI screens, canvas graphics, and state transitions."""

    def __init__(self, root):
        self.root = root
        self.root.title("WEBLINE: Night Patrol")
        self.root.resizable(False, False)

        # Master Canvas (960x540)
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                                bg=COLOR_NAVY, highlightthickness=0)
        self.canvas.pack()

        # Asset Cache
        self.assets = AssetCache()
        self.preload_assets()

        # State Machine: "TITLE", "HELP", "BRIEFING", "PLAYING", "PAUSED", "COMPLETE", "FAILED", "GAME_OVER"
        self.state = "TITLE"
        self.loop_id = None
        self.tick_count = 0

        # Input Tracking
        self.keys = {}
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_down = False
        self.buttons = []

        # Gameplay Entities
        self.current_mission_idx = 0
        self.player = Player()
        self.rooftops = []
        self.anchors = []
        self.cartridges = []
        self.medkits = []
        self.items = []
        self.enemies = []

        # FX & Camera
        self.cam_x = 0.0
        self.screen_shake = 0
        self.particles = ParticleManager()
        self.popups = ComicPopupManager()

        # Score & Mission Tracking
        self.score = 0
        self.combo = 1
        self.mission_start_time = 0.0
        self.time_remaining = 0
        self.total_stars = 0
        self.selected_button_idx = 0

        # Bind All Events
        self.bind_events()
        self.show_screen("TITLE")

    def preload_assets(self):
        """Loads optional PNG assets into cache with auto-downscaling."""
        self.assets.load("bg_far", "bg_far.png")
        self.assets.load("bg_mid", "bg_mid.png")
        # Auto-scale title_art to canvas dimensions if 4K or high-res
        self.assets.load("title_art", "title_art.png", max_w=CANVAS_WIDTH, max_h=CANVAS_HEIGHT)
        self.assets.load("rooftop_tile", "rooftop_tile.png")
        self.assets.load("icon_fluid", "icon_fluid.png")
        self.assets.load("icon_medkit", "icon_medkit.png")
        self.assets.load("icon_chip", "icon_chip.png")
        self.assets.load("icon_bomb", "icon_bomb.png")
        self.assets.load("icon_civilian", "icon_civilian.png")
        self.assets.load("logo_webline", "logo_webline.png")

    def bind_events(self):
        """Binds keyboard and mouse handlers to the canvas."""
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)

    def cancel_loop(self):
        """Cancels scheduled timer strictly to prevent double game loops."""
        if self.loop_id is not None:
            self.root.after_cancel(self.loop_id)
            self.loop_id = None

    def schedule_next_tick(self):
        """Schedules fixed-step game update."""
        self.cancel_loop()
        self.loop_id = self.root.after(TICK_MS, self.game_loop)

    def show_screen(self, new_state):
        """Transitions state machine cleanly, resetting timers and active buttons."""
        self.cancel_loop()
        self.state = new_state
        self.buttons = []
        self.selected_button_idx = 0

        if self.state == "TITLE":
            self.draw_title_screen()
        elif self.state == "HELP":
            self.draw_help_screen()
        elif self.state == "BRIEFING":
            self.draw_briefing_screen()
        elif self.state == "PLAYING":
            self.schedule_next_tick()
        elif self.state == "PAUSED":
            self.draw_pause_screen()
        elif self.state == "COMPLETE":
            self.draw_mission_complete_screen()
        elif self.state == "FAILED":
            self.draw_mission_failed_screen()
        elif self.state == "GAME_OVER":
            self.draw_game_over_screen()

    # ═══════════════════════════════════════════════════════════════════════════
    # CANVAS-ONLY BUTTONS & INPUT HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    def register_button(self, x, y, w, h, text, callback, hotkey=None):
        """Registers a clickable canvas button with hover and keyboard activation."""
        self.buttons.append({
            "rect": (x, y, x + w, y + h),
            "text": text,
            "callback": callback,
            "hotkey": hotkey
        })

    def draw_all_buttons(self):
        """Renders all registered buttons on canvas with comic hover styling."""
        for i, b in enumerate(self.buttons):
            x1, y1, x2, y2 = b["rect"]
            is_hovered = (x1 <= self.mouse_x <= x2 and y1 <= self.mouse_y <= y2) or (i == self.selected_button_idx)
            
            box_fill = COLOR_RED if is_hovered else COLOR_NAVY
            border_col = COLOR_YELLOW if is_hovered else COLOR_BLUE
            text_col = COLOR_WHITE

            draw_slanted_box(self.canvas, x1, y1, x2, y2, slant=10, fill=box_fill, outline=border_col, width=3)
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                    text=b["text"], font=get_comic_font(15, "bold"), fill=text_col)

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.state in ("TITLE", "HELP", "BRIEFING", "PAUSED", "COMPLETE", "FAILED", "GAME_OVER"):
            self.canvas.delete("all")
            if self.state == "TITLE": self.draw_title_screen()
            elif self.state == "HELP": self.draw_help_screen()
            elif self.state == "BRIEFING": self.draw_briefing_screen()
            elif self.state == "PAUSED": self.draw_pause_screen()
            elif self.state == "COMPLETE": self.draw_mission_complete_screen()
            elif self.state == "FAILED": self.draw_mission_failed_screen()
            elif self.state == "GAME_OVER": self.draw_game_over_screen()

    def on_mouse_press(self, event):
        self.mouse_down = True
        if self.state == "PLAYING":
            # Left Click attaches and initiates web-swinging anywhere
            self.player.attach_swing(self.anchors)
        else:
            for b in self.buttons:
                x1, y1, x2, y2 = b["rect"]
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    b["callback"]()
                    break

    def on_mouse_release(self, event):
        self.mouse_down = False
        if self.state == "PLAYING":
            self.player.release_swing()

    def on_right_click(self, event):
        """Right Click triggers direct combat attack / web-strike."""
        if self.state == "PLAYING":
            self.perform_attack()

    def on_key_press(self, event):
        k = event.keysym.lower()
        self.keys[k] = True

        if k == "escape":
            if self.state == "PLAYING":
                self.show_screen("PAUSED")
            elif self.state in ("PAUSED", "HELP", "BRIEFING"):
                self.show_screen("TITLE")
        elif k == "p":
            if self.state == "PLAYING":
                self.show_screen("PAUSED")
            elif self.state == "PAUSED":
                self.show_screen("PLAYING")
        elif k == "r":
            if self.state in ("PLAYING", "FAILED", "PAUSED"):
                self.start_mission(self.current_mission_idx)
        elif k == "shift_l" or k == "shift_r":
            if self.state == "PLAYING":
                self.player.attach_swing(self.anchors)
        elif k == "f":
            if self.state == "PLAYING":
                self.perform_web_shot()
        elif k in ("c", "v", "q"):
            if self.state == "PLAYING":
                self.perform_attack()
        elif k == "e":
            if self.state == "PLAYING":
                self.player.crouch_hold = True
        elif k in ("return", "space"):
            if self.buttons and self.state != "PLAYING":
                self.buttons[self.selected_button_idx]["callback"]()

    def on_key_release(self, event):
        k = event.keysym.lower()
        self.keys[k] = False
        if k == "shift_l" or k == "shift_r":
            if self.state == "PLAYING":
                self.player.release_swing()
        elif k == "e":
            if self.state == "PLAYING":
                self.player.crouch_hold = False

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE COMBAT & WEB ABILITIES
    # ═══════════════════════════════════════════════════════════════════════════
    def perform_web_shot(self):
        """Fires a high-speed web shot that stuns the nearest enemy in front."""
        self.player.web_fluid = MAX_FLUID
        self.player.pose = "web_shot"
        self.popups.add(self.player.x, self.player.y - 30, "THWIP!", COLOR_LIGHT_BLUE)
        self.particles.emit(self.player.x + (25 * self.player.facing), self.player.y - 5,
                            count=8, color=COLOR_WHITE, speed=4.0)

        hit_enemy = None
        min_dist = 360
        for e in self.enemies:
            if not e.active:
                continue
            dx = (e.x - self.player.x) * self.player.facing
            dy = abs(e.y - self.player.y)
            if 0 < dx < min_dist and dy < 90:
                hit_enemy = e
                min_dist = dx

        if hit_enemy:
            hit_enemy.stun()
            self.popups.add(hit_enemy.x, hit_enemy.y - 20, "STUNNED!", COLOR_YELLOW)
            self.score += SCORE_STUN * self.combo
            self.combo = min(8, self.combo + 1)
            self.particles.emit(hit_enemy.x, hit_enemy.y, count=12, color=COLOR_WHITE, speed=3.0)

    def perform_attack(self):
        """
        Executes Spider-Man's combat attack:
        - Within 95px: Acrobatic punch / kick melee combo that stuns thugs and smashes drones.
        - Between 95px and 280px: Web-Strike Zip Attack that pulls Spider-Man to the enemy with a flying strike!
        - Air / whiff: Acrobatic strike swoosh.
        """
        self.player.web_fluid = MAX_FLUID

        # Find closest active enemy in front or near player
        best_target = None
        best_dist = 999999
        is_melee = False

        for e in self.enemies:
            if not e.active:
                continue
            dx = (e.x - self.player.x) * self.player.facing
            dy = abs(e.y - self.player.y)
            dist = math.hypot(e.x - self.player.x, e.y - self.player.y)

            # Melee check: close in 360 radius or in front
            if dist <= 95 or (0 <= dx <= 90 and dy <= 50):
                if dist < best_dist:
                    best_dist = dist
                    best_target = e
                    is_melee = True
            elif 0 < dx <= 280 and dy <= 120 and not is_melee:
                if dist < best_dist:
                    best_dist = dist
                    best_target = e

        if best_target:
            if is_melee:
                # ── MELEE COMBO STRIKE ──
                attack_type = random.choice(["punch", "kick"])
                self.player.pose = attack_type
                self.player.attack_type = attack_type
                self.player.attack_timer = 10
                self.player.vx = 4.0 * self.player.facing

                # Comic sound effects
                words = ["POW!", "WHAM!", "KAPOW!", "SMACK!"]
                word = random.choice(words)

                if isinstance(best_target, StreetThug):
                    best_target.stun_timer = STUN_DURATION_TICKS + 40
                    best_target.x += 35 * self.player.facing
                    self.popups.add(best_target.x, best_target.y - 25, word, COLOR_YELLOW)
                elif isinstance(best_target, SentryDrone):
                    best_target.stun()
                    best_target.lock_timer = 0
                    best_target.laser_firing = False
                    best_target.cooldown = 70
                    self.popups.add(best_target.x, best_target.y - 25, "CRUNCH!", COLOR_RED)
                elif isinstance(best_target, GoblinBomber):
                    best_target.stun()
                    self.popups.add(best_target.x, best_target.y - 25, "BAM!", COLOR_YELLOW)
                elif isinstance(best_target, HunterDrone):
                    best_target.x -= 45
                    self.popups.add(best_target.x, best_target.y - 25, "DEFLECT!", COLOR_LIGHT_BLUE)

                self.score += SCORE_STOMP * self.combo
                self.combo = min(8, self.combo + 1)
                self.screen_shake = 6
                self.particles.emit(best_target.x, best_target.y, count=16, color=COLOR_YELLOW, speed=4.5)
                self.particles.emit(best_target.x, best_target.y, count=8, color=COLOR_RED, speed=3.0)

            else:
                # ── WEB-STRIKE ZIP ATTACK ──
                self.player.pose = "kick"
                self.player.attack_type = "kick"
                self.player.attack_timer = 12
                # Zip web particle line from player to enemy
                steps = 10
                for s in range(steps):
                    frac = s / float(steps)
                    zx = self.player.x + (best_target.x - self.player.x) * frac
                    zy = self.player.y + (best_target.y - self.player.y) * frac
                    self.particles.emit(zx, zy, count=2, color=COLOR_WHITE, speed=1.5)

                # Zip player directly to target with flying kick
                self.player.x = best_target.x - (28 * self.player.facing)
                self.player.y = best_target.y
                self.player.vx = 5.0 * self.player.facing
                self.player.vy = -3.0

                # Stun / knock back target
                if isinstance(best_target, StreetThug):
                    best_target.stun_timer = STUN_DURATION_TICKS + 50
                    best_target.x += 40 * self.player.facing
                    self.popups.add(best_target.x, best_target.y - 25, "ZIP-STRIKE!", COLOR_YELLOW)
                elif isinstance(best_target, SentryDrone):
                    best_target.stun()
                    best_target.lock_timer = 0
                    best_target.laser_firing = False
                    best_target.cooldown = 70
                    self.popups.add(best_target.x, best_target.y - 25, "ZIP-KICK!", COLOR_YELLOW)
                elif isinstance(best_target, GoblinBomber):
                    best_target.stun()
                    self.popups.add(best_target.x, best_target.y - 25, "WHACK!", COLOR_YELLOW)
                elif isinstance(best_target, HunterDrone):
                    best_target.x -= 50
                    self.popups.add(best_target.x, best_target.y - 25, "INTERCEPT!", COLOR_YELLOW)

                self.score += (SCORE_STOMP + SCORE_STUN) * self.combo
                self.combo = min(8, self.combo + 1)
                self.screen_shake = 7
                self.particles.emit(best_target.x, best_target.y, count=20, color=COLOR_YELLOW, speed=5.0)

        else:
            # Whiff / Air jab
            attack_type = random.choice(["punch", "kick"])
            self.player.pose = attack_type
            self.player.attack_type = attack_type
            self.player.attack_timer = 8
            self.popups.add(self.player.x + 25 * self.player.facing, self.player.y - 15, "SWOOSH!", COLOR_LIGHT_BLUE)
            self.particles.emit(self.player.x + 20 * self.player.facing, self.player.y, count=6, color=COLOR_LIGHT_BLUE, speed=2.5)

    # ═══════════════════════════════════════════════════════════════════════════
    # GAME LOOP (FIXED-STEP @ 50 FPS)
    # ═══════════════════════════════════════════════════════════════════════════
    def game_loop(self):
        """Main gameplay frame update."""
        if self.state != "PLAYING":
            return

        self.tick_count += 1

        # 1. Update Player
        mouse_held = self.mouse_down or self.keys.get("shift_l") or self.keys.get("shift_r")
        self.player.update(self.keys, mouse_held, self.rooftops, self.anchors)

        # Fall into gap safety: web rescue automatically bounces him back up (NO heart loss!)
        if self.player.y > 510:
            self.player.respawn_at_safe()
            self.popups.add(self.player.x, self.player.y - 40, "WEB RESCUE! THWIP!", COLOR_YELLOW)
            self.particles.emit(self.player.x, self.player.y, count=16, color=COLOR_WHITE, speed=5.0)
            self.screen_shake = 5

        # 2. Camera Horizontal Tracking with Smooth Follow
        target_cam_x = self.player.x - CANVAS_WIDTH * 0.35
        self.cam_x += (target_cam_x - self.cam_x) * 0.12
        self.cam_x = max(0.0, self.cam_x)

        # 3. Pickups & Cartridge Collection (Awards +50 bonus score & particles)
        for c in self.cartridges:
            if not c.collected and math.hypot(self.player.x - c.x, self.player.y - c.y) < 32:
                c.collected = True
                self.score += FLUID_PICKUP_BONUS * self.combo
                self.popups.add(c.x, c.y - 20, "+50 BONUS!", COLOR_LIGHT_BLUE)
                self.particles.emit(c.x, c.y, count=12, color=COLOR_LIGHT_BLUE, speed=3.0)

        # Medkit Health Pickups (+2 hearts recovery)
        for m in self.medkits:
            if not m.collected and math.hypot(self.player.x - m.x, self.player.y - m.y) < 32:
                m.collected = True
                healed = min(2, MAX_HEARTS - self.player.hearts)
                self.player.hearts = min(MAX_HEARTS, self.player.hearts + 2)
                self.score += 25 * self.combo
                heal_text = f"+{healed} HEARTS!" if healed > 0 else "+25 BONUS!"
                self.popups.add(m.x, m.y - 20, heal_text, "#4ADE80")
                self.particles.emit(m.x, m.y, count=16, color="#4ADE80", speed=3.5)

        # 4. Interactive Mission Objectives (Hold E)
        for item in self.items:
            if item.completed:
                continue
            dist = math.hypot(self.player.x - item.x, self.player.y - item.y)
            if dist < 65:
                if item.kind == "gate":
                    # Extraction gate finishes mission upon reaching
                    self.finish_mission(success=True)
                    return
                elif self.player.crouch_hold:
                    item.hold_progress += (1.0 / (item.hold_required * 50.0))
                    if item.hold_progress >= 1.0:
                        item.completed = True
                        item.hold_progress = 0.0
                        self.score += SCORE_OBJECTIVE * self.combo
                        self.combo = min(8, self.combo + 1)
                        if item.kind == "civilian":
                            self.popups.add(item.x, item.y - 20, "RESCUED!", COLOR_YELLOW)
                        elif item.kind == "bomb":
                            self.popups.add(item.x, item.y - 20, "DEFUSED!", COLOR_YELLOW)
                else:
                    item.hold_progress = max(0.0, item.hold_progress - 0.02)
            else:
                item.hold_progress = max(0.0, item.hold_progress - 0.02)

            # Data chip auto-collects on touch
            if item.kind == "chip" and dist < 36 and not item.completed:
                item.completed = True
                self.score += SCORE_OBJECTIVE * self.combo
                self.popups.add(item.x, item.y - 20, "CHIP SECURED!", COLOR_YELLOW)
                self.particles.emit(item.x, item.y, count=12, color=COLOR_YELLOW)

        # Check mission completion if non-gate objectives all cleared
        m_data = MISSIONS[self.current_mission_idx]
        if m_data["target_type"] != "gate":
            completed_count = sum(1 for it in self.items if it.completed)
            if completed_count >= m_data["target_count"]:
                self.finish_mission(success=True)
                return

        # 5. Timer for Mission 3
        if "time_limit" in m_data:
            elapsed = time.time() - self.mission_start_time
            self.time_remaining = max(0, int(m_data["time_limit"] - elapsed))
            if self.time_remaining <= 0:
                self.show_screen("FAILED")
                return

        # 6. Update Enemies & Combat Checks
        spider_sense_alert = False
        danger_coords = []

        for e in self.enemies:
            e.update(self.player, self.rooftops)
            if not e.active:
                continue

            # Stomp Street Thug from above
            if isinstance(e, StreetThug):
                dist_x = abs(self.player.x - e.x)
                dist_y = (e.y - self.player.y)
                if dist_x < 24 and 15 < dist_y < 45 and self.player.vy > 1.2:
                    e.active = False
                    self.player.vy = -10.0
                    self.score += SCORE_STOMP * self.combo
                    self.combo = min(8, self.combo + 1)
                    self.popups.add(e.x, e.y - 20, "POW!", COLOR_YELLOW)
                    self.particles.emit(e.x, e.y, count=15, color=COLOR_RED, speed=3.5)
                    self.screen_shake = 6
                elif dist_x < 28 and abs(self.player.y - e.y) < 28 and not e.is_stunned():
                    if self.player.take_damage(1):
                        self.popups.add(self.player.x, self.player.y - 20, "WHAM!", COLOR_RED)
                        self.screen_shake = 8
                        self.combo = 1
                elif e.telegraph_attack > 0 and dist_x < 70:
                    spider_sense_alert = True
                    danger_coords.append((e.x, e.y))

            # Sentry Drone firing checks
            elif isinstance(e, SentryDrone):
                if e.lock_timer > 12 and not e.is_stunned():
                    spider_sense_alert = True
                    danger_coords.append((e.target_px, e.target_py))
                if e.laser_firing:
                    # Directional laser beam collision using perpendicular distance to line segment
                    dist_to_beam = point_to_segment_dist(self.player.x, self.player.y,
                                                         e.x, e.y, e.target_px, e.target_py)
                    if dist_to_beam < 18.0:
                        if self.player.take_damage(1):
                            self.popups.add(self.player.x, self.player.y - 20, "ZAP!", COLOR_RED)
                            self.screen_shake = 8
                            self.combo = 1

            # Goblin Bomber pumpkin bombs
            elif isinstance(e, GoblinBomber):
                for b in e.bombs:
                    if b["ticks_to_hit"] < 25:
                        spider_sense_alert = True
                        danger_coords.append((b["target_x"], b["target_y"]))
                    if b.get("exploded", False):
                        b["exploded"] = False
                        self.particles.emit(b["target_x"], b["target_y"], count=25, color=COLOR_RED, speed=5.0)
                        self.screen_shake = 10
                        if math.hypot(self.player.x - b["target_x"], self.player.y - b["target_y"]) < 55:
                            if self.player.take_damage(1):
                                self.popups.add(self.player.x, self.player.y - 20, "BOOM!", COLOR_RED)
                                self.combo = 1

            # Hunter Drone chase
            elif isinstance(e, HunterDrone):
                if self.player.x < e.x + 40:
                    if self.player.take_damage(1):
                        self.popups.add(self.player.x, self.player.y - 20, "SHREDDED!", COLOR_RED)
                        self.screen_shake = 12
                        self.player.x = e.x + 80
                elif self.player.x < e.x + 220:
                    spider_sense_alert = True
                    danger_coords.append((e.x, self.player.y))

        # Check death (only from enemy damage)
        if self.player.hearts <= 0:
            self.show_screen("FAILED")
            return

        # 7. Render Whole Game World
        self.render_gameplay(spider_sense_alert, danger_coords)
        self.schedule_next_tick()

    def finish_mission(self, success=True):
        """Concludes mission and displays results screen."""
        if success:
            m = MISSIONS[self.current_mission_idx]
            elapsed = time.time() - self.mission_start_time
            if elapsed < m['par_time']:
                bonus = int((m['par_time'] - elapsed) * 10)
                self.score += bonus
            self.show_screen("COMPLETE")
        else:
            self.show_screen("FAILED")

    # ═══════════════════════════════════════════════════════════════════════════
    # PARALLAX BACKGROUND & GAMEPLAY RENDERING (SEAMLESS TILING FIX)
    # ═══════════════════════════════════════════════════════════════════════════
    def render_gameplay(self, spider_sense_alert, danger_coords):
        """Draws all world layers, entities, spider-sense warnings and comic HUD."""
        self.canvas.delete("all")

        ox = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        oy = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        self.screen_shake = max(0, self.screen_shake - 1)

        # ── LAYER 1: PARALLAX FAR BACKGROUND (SEAMLESS TILING) ──
        bg_far = self.assets.get("bg_far")
        if bg_far:
            bg_far_w = bg_far.width()
            start_far = - (int(self.cam_x * 0.15) % bg_far_w)
            for x in range(start_far, CANVAS_WIDTH + bg_far_w, bg_far_w):
                self.canvas.create_image(x + ox, oy, image=bg_far, anchor=tk.NW)
        else:
            self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
            self.canvas.create_oval(780, 50, 840, 110, fill="#FEF08A", outline="")
            for i in range(12):
                bx = (i * 90 - (self.cam_x * 0.15)) % (CANVAS_WIDTH + 100)
                bh = 140 + (i * 37) % 180
                self.canvas.create_rectangle(bx, CANVAS_HEIGHT - bh, bx + 70, CANVAS_HEIGHT, fill="#0F172A")

        # ── LAYER 2: PARALLAX MID-DISTANCE SKYLINE (SEAMLESS TILING) ──
        bg_mid = self.assets.get("bg_mid")
        if bg_mid:
            bg_mid_w = bg_mid.width()
            start_mid = - (int(self.cam_x * 0.42) % bg_mid_w)
            for x in range(start_mid, CANVAS_WIDTH + bg_mid_w, bg_mid_w):
                self.canvas.create_image(x + ox, oy, image=bg_mid, anchor=tk.NW)
        else:
            for i in range(8):
                bx = (i * 140 - (self.cam_x * 0.42)) % (CANVAS_WIDTH + 150)
                bh = 220 + (i * 51) % 150
                self.canvas.create_rectangle(bx, CANVAS_HEIGHT - bh, bx + 110, CANVAS_HEIGHT,
                                             fill="#131C38", outline=COLOR_RED, width=1.5)
                if i % 3 == 0:
                    self.canvas.create_rectangle(bx + 20, CANVAS_HEIGHT - bh - 30, bx + 50, CANVAS_HEIGHT - bh,
                                                 fill="#1E293B", outline=COLOR_BLACK)

        # ── LAYER 3: FOREGROUND ROOFTOPS, ANCHORS & PICKUPS ──
        tile_img = self.assets.get("rooftop_tile")
        for r in self.rooftops:
            r.draw(self.canvas, self.cam_x - ox, tile_img)

        # Draw Web Anchors
        for a in self.anchors:
            is_target = (self.player.is_swinging and self.player.swing_anchor == a)
            a.draw(self.canvas, self.cam_x - ox, is_target)

        # Draw Fluid Cartridges
        icon_fluid = self.assets.get("icon_fluid")
        for c in self.cartridges:
            c.draw(self.canvas, self.cam_x - ox, icon_fluid)

        # Draw Medkits (+2 hearts recovery)
        icon_medkit = self.assets.get("icon_medkit")
        for m in self.medkits:
            m.draw(self.canvas, self.cam_x - ox, icon_medkit)

        # Draw Mission Items
        icon_civilian = self.assets.get("icon_civilian")
        icon_chip = self.assets.get("icon_chip")
        icon_bomb = self.assets.get("icon_bomb")
        for item in self.items:
            img = icon_civilian if item.kind == "civilian" else (icon_chip if item.kind == "chip" else icon_bomb)
            item.draw(self.canvas, self.cam_x - ox, self.tick_count, img)

        # Draw Enemies
        for e in self.enemies:
            e.draw(self.canvas, self.cam_x - ox, self.tick_count)

        # ── DRAW WEB LINE (WHEN SWINGING) ──
        if self.player.is_swinging and self.player.swing_anchor:
            ax = self.player.swing_anchor.x - self.cam_x + ox
            ay = self.player.swing_anchor.y + oy
            px = self.player.x - self.cam_x + ox
            py = self.player.y - 12 + oy
            mid_x = (ax + px) * 0.5
            mid_y = (ay + py) * 0.5 + 8
            # White web line with tension curve
            self.canvas.create_line(ax, ay, mid_x, mid_y, px, py,
                                    smooth=True, fill=COLOR_WHITE, width=2.5)
            # Glowing attachment point spark at top
            self.canvas.create_oval(ax - 4, ay - 4, ax + 4, ay + 4, fill=COLOR_YELLOW, outline="")

        # ── DRAW HERO (SPIDER-MAN) ──
        draw_hero(self.canvas, self.player.x - self.cam_x + ox, self.player.y + oy,
                  self.player.pose, self.player.facing, self.tick_count,
                  self.player.invincible, self.player.swing_angle)

        # ── PARTICLES & FLOATING COMIC POPUPS ──
        self.particles.update_and_draw(self.canvas, self.cam_x)
        self.popups.update_and_draw(self.canvas, self.cam_x)

        # ── SPIDER-SENSE TELEGRAPH SYSTEM ──
        if spider_sense_alert:
            hx = self.player.x - self.cam_x
            hy = self.player.y
            pulse = (self.tick_count * 5) % 30
            for r in [28 + pulse, 38 + pulse]:
                self.canvas.create_oval(hx - r, hy - r, hx + r, hy + r, outline=COLOR_RED, width=2)
            for ang_deg in [30, 75, 120, 165, 210, 255, 300, 345]:
                rad = math.radians(ang_deg)
                lx1 = hx + math.cos(rad) * 26
                ly1 = hy + math.sin(rad) * 26
                lx2 = hx + math.cos(rad) * 42
                ly2 = hy + math.sin(rad) * 42
                self.canvas.create_line(lx1, ly1, lx2, ly2, fill=COLOR_RED, width=2)

            for dx, dy in danger_coords:
                scr_dx = dx - self.cam_x
                if scr_dx < 30:
                    self.canvas.create_polygon([10, CANVAS_HEIGHT // 2, 28, CANVAS_HEIGHT // 2 - 12, 28, CANVAS_HEIGHT // 2 + 12],
                                               fill=COLOR_RED, outline=COLOR_YELLOW, width=2)
                elif scr_dx > CANVAS_WIDTH - 30:
                    self.canvas.create_polygon([CANVAS_WIDTH - 10, CANVAS_HEIGHT // 2, CANVAS_WIDTH - 28, CANVAS_HEIGHT // 2 - 12, CANVAS_WIDTH - 28, CANVAS_HEIGHT // 2 + 12],
                                               fill=COLOR_RED, outline=COLOR_YELLOW, width=2)

        # ── COMIC-BOOK HUD OVERLAY ──
        self.render_hud()

    # ═══════════════════════════════════════════════════════════════════════════
    # SLANTED COMIC-BOOK HUD
    # ═══════════════════════════════════════════════════════════════════════════
    def render_hud(self):
        """Draws slanted comic boxes for Hearts, Unlimited Web-Fluid Meter, Tracker and Combo."""
        # 1. Top-Left: Health Hearts Panel
        draw_slanted_box(self.canvas, 16, 12, 220, 52, slant=12, fill=COLOR_NAVY, outline=COLOR_BLUE, width=2)
        for h in range(MAX_HEARTS):
            hx = 40 + h * 34
            hy = 32
            heart_color = COLOR_RED if h < self.player.hearts else "#1E293B"
            self.canvas.create_polygon([
                hx, hy + 8,
                hx - 10, hy - 2,
                hx - 10, hy - 8,
                hx - 4, hy - 12,
                hx, hy - 7,
                hx + 4, hy - 12,
                hx + 10, hy - 8,
                hx + 10, hy - 2
            ], fill=heart_color, outline=COLOR_BLACK, width=1.5)
            if h < self.player.hearts:
                self.canvas.create_line(hx - 6, hy - 4, hx + 6, hy - 4, fill=COLOR_WHITE, width=1)
                self.canvas.create_line(hx, hy - 9, hx, hy + 5, fill=COLOR_WHITE, width=1)

        # 2. Unlimited Web-Fluid Cartridge Gauge
        draw_slanted_box(self.canvas, 16, 58, 250, 94, slant=12, fill=COLOR_NAVY, outline=COLOR_BLUE, width=2)
        self.canvas.create_text(50, 76, text="FLUID", font=get_comic_font(11, "bold"), fill=COLOR_WHITE)
        bar_x1, bar_y1, bar_x2, bar_y2 = 82, 66, 236, 86
        self.canvas.create_rectangle(bar_x1, bar_y1, bar_x2, bar_y2, fill="#0F172A", outline=COLOR_BLACK, width=2)
        # Always glowing full
        self.canvas.create_rectangle(bar_x1 + 1, bar_y1 + 1, bar_x2 - 1, bar_y2 - 1, fill=COLOR_LIGHT_BLUE, outline="")
        self.canvas.create_line(bar_x1 + 2, bar_y1 + 4, bar_x2 - 2, bar_y1 + 4, fill=COLOR_WHITE, width=1.5)
        self.canvas.create_text((bar_x1 + bar_x2) // 2, 76, text="∞ UNLIMITED",
                                font=get_comic_font(11, "bold"), fill=COLOR_BLACK)

        # 3. Top-Right: Slanted Mission Objective Tracker
        m_data = MISSIONS[self.current_mission_idx]
        draw_slanted_box(self.canvas, CANVAS_WIDTH - 280, 12, CANVAS_WIDTH - 16, 68, slant=12,
                         fill=COLOR_NAVY, outline=COLOR_RED, width=2)
        self.canvas.create_text(CANVAS_WIDTH - 148, 26, text=f"M{m_data['id']}: {m_data['title'].upper()}",
                                font=get_comic_font(12, "bold"), fill=COLOR_YELLOW)

        if m_data["target_type"] == "gate":
            obj_text = "REACH EXTRACTION GATE"
        else:
            done = sum(1 for it in self.items if it.completed)
            obj_text = f"{m_data['target_type'].upper()}S: {done} / {m_data['target_count']}"
        self.canvas.create_text(CANVAS_WIDTH - 148, 48, text=obj_text,
                                font=get_comic_font(14, "bold"), fill=COLOR_WHITE)

        if "time_limit" in m_data:
            t_color = COLOR_RED if self.time_remaining < 20 else COLOR_YELLOW
            self.canvas.create_text(CANVAS_WIDTH - 148, 86, text=f"TIMER: {self.time_remaining}s",
                                    font=get_comic_font(16, "bold"), fill=t_color)

        # 4. Bottom-Right: Score & Combo Badge
        draw_slanted_box(self.canvas, CANVAS_WIDTH - 220, CANVAS_HEIGHT - 65, CANVAS_WIDTH - 16, CANVAS_HEIGHT - 16,
                         slant=12, fill=COLOR_NAVY, outline=COLOR_BLUE, width=2)
        self.canvas.create_text(CANVAS_WIDTH - 118, CANVAS_HEIGHT - 48,
                                text=f"SCORE: {self.score}", font=get_comic_font(14, "bold"), fill=COLOR_WHITE)
        if self.combo > 1:
            self.canvas.create_text(CANVAS_WIDTH - 118, CANVAS_HEIGHT - 30,
                                    text=f"COMBO x{self.combo}!", font=get_comic_font(13, "bold"), fill=COLOR_YELLOW)

        # 5. Bottom-Left: Contextual Prompt
        near_item = None
        for it in self.items:
            if not it.completed and math.hypot(self.player.x - it.x, self.player.y - it.y) < 65:
                near_item = it
                break
        if near_item and near_item.kind != "gate":
            action_verb = "RESCUE CIVILIAN" if near_item.kind == "civilian" else "DEFUSE BOMB"
            draw_slanted_box(self.canvas, 16, CANVAS_HEIGHT - 60, 240, CANVAS_HEIGHT - 16, slant=12,
                             fill=COLOR_RED, outline=COLOR_YELLOW, width=2)
            self.canvas.create_text(128, CANVAS_HEIGHT - 38, text=f"HOLD [E]: {action_verb}",
                                    font=get_comic_font(13, "bold"), fill=COLOR_WHITE)
        else:
            draw_slanted_box(self.canvas, 16, CANVAS_HEIGHT - 48, 230, CANVAS_HEIGHT - 16, slant=10,
                             fill=COLOR_NAVY, outline=COLOR_BLUE, width=1.5)
            self.canvas.create_text(123, CANVAS_HEIGHT - 32, text="[R-CLICK / C]: ATTACK / ZIP",
                                    font=get_comic_font(10, "bold"), fill=COLOR_YELLOW)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCREENS & MENUS (100% CANVAS DRAWN & CENTERED AUTO-SCALED TITLE ART)
    # ═══════════════════════════════════════════════════════════════════════════
    def draw_title_screen(self):
        """Draws opening comic cover title screen with auto-scaled artwork."""
        self.canvas.delete("all")
        self.buttons = []

        title_img = self.assets.get("title_art")
        if title_img:
            # Centered on canvas, perfectly fitting any resolution
            self.canvas.create_image(CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2, image=title_img, anchor=tk.CENTER)
        else:
            self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
            draw_halftone_accent(self.canvas, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, step=12)

        # Translucent dark wash for text legibility
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY, stipple="gray50")

        # Logo banner (or logo_webline.png)
        logo_img = self.assets.get("logo_webline")
        if logo_img:
            self.canvas.create_image(CANVAS_WIDTH // 2, 125, image=logo_img, anchor=tk.CENTER)
        else:
            draw_slanted_box(self.canvas, CANVAS_WIDTH // 2 - 250, 70, CANVAS_WIDTH // 2 + 250, 170, slant=20,
                             fill=COLOR_RED, outline=COLOR_BLUE, width=4)
            self.canvas.create_text(CANVAS_WIDTH // 2, 120, text="WEBLINE",
                                    font=get_comic_font(68, "bold"), fill=COLOR_WHITE)

        self.canvas.create_text(CANVAS_WIDTH // 2, 200, text="♦ NIGHT PATROL ♦",
                                font=get_comic_font(24, "bold"), fill=COLOR_YELLOW)
        self.canvas.create_text(CANVAS_WIDTH // 2, 230, text="College Design Project • Spider-Man Side-Scrolling Action",
                                font=get_comic_font(13, "bold"), fill=COLOR_LIGHT_BLUE)

        # Canvas Buttons
        btn_y = 285
        self.register_button(CANVAS_WIDTH // 2 - 130, btn_y, 260, 48, "START PATROL",
                             lambda: self.start_mission(0))
        self.register_button(CANVAS_WIDTH // 2 - 130, btn_y + 60, 260, 48, "HOW TO PLAY",
                             lambda: self.show_screen("HELP"))
        self.register_button(CANVAS_WIDTH // 2 - 130, btn_y + 120, 260, 48, "EXIT GAME",
                             self.root.destroy)

        self.draw_all_buttons()

    def draw_help_screen(self):
        """Displays comic manual with controls and game mechanics."""
        self.canvas.delete("all")
        self.buttons = []

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
        draw_slanted_box(self.canvas, 60, 20, CANVAS_WIDTH - 60, 80, slant=16,
                         fill=COLOR_RED, outline=COLOR_BLUE, width=3)
        self.canvas.create_text(CANVAS_WIDTH // 2, 50, text="♦ HOW TO PLAY & CONTROLS ♦",
                                font=get_comic_font(26, "bold"), fill=COLOR_WHITE)

        # Left Panel: Controls
        draw_slanted_box(self.canvas, 70, 100, CANVAS_WIDTH // 2 - 15, CANVAS_HEIGHT - 90, slant=14,
                         fill="#0F172A", outline=COLOR_BLUE, width=2)
        self.canvas.create_text(CANVAS_WIDTH // 4 + 20, 130, text="HERO CONTROLS",
                                font=get_comic_font(18, "bold"), fill=COLOR_YELLOW)
        ctrls = [
            ("A / D or Left / Right", "Run & pump swing speed"),
            ("W / Up / Space", "Jump / Double Jump / Reel-in"),
            ("Hold Left Mouse / Shift", "Authentic Pendulum Web-Swing"),
            ("Right Mouse / C", "Attack! Melee Combo & Web-Strike"),
            ("F", "Web-Shot (Stun enemies for 2.5s)"),
            ("Hold E", "Interact (Rescue / Defuse / Crouch)"),
            ("P / Space", "Pause patrol"),
            ("R", "Restart current mission"),
            ("Esc", "Return to main menu")
        ]
        for idx, (k, d) in enumerate(ctrls):
            cy = 165 + idx * 28
            self.canvas.create_text(95, cy, text=f"[{k}]", anchor=tk.W, font=get_comic_font(12, "bold"), fill=COLOR_LIGHT_BLUE)
            self.canvas.create_text(260, cy, text=d, anchor=tk.W, font=get_comic_font(12, "normal"), fill=COLOR_WHITE)

        # Right Panel: Mechanics
        draw_slanted_box(self.canvas, CANVAS_WIDTH // 2 + 15, 100, CANVAS_WIDTH - 70, CANVAS_HEIGHT - 90, slant=14,
                         fill="#0F172A", outline=COLOR_BLUE, width=2)
        self.canvas.create_text(CANVAS_WIDTH * 0.75 - 20, 130, text="CORE MECHANICS",
                                font=get_comic_font(18, "bold"), fill=COLOR_YELLOW)
        mechanics = [
            "• COMBAT & ZIP-STRIKE: Right Click punches/kicks nearby",
            "  foes or zips to distant enemies with flying strikes!",
            "• MEDKITS: Collect green first-aid crates (+2 hearts).",
            "• REAL SWING POLES: Swing from real rooftop streetlights,",
            "  derrick cranes, radio antennas, and water towers!",
            "• PENDULUM SWING: Swoop down fast, climb to high crests,",
            "  and hold W/Space to reel in and gain altitude!",
            "• WEB RESCUE: Falling never hurts! A safety web bounces",
            "  Spider-Man straight back onto the rooftop.",
            "• SPIDER-SENSE: Red warning alerts show incoming attacks."
        ]
        for idx, line in enumerate(mechanics):
            cy = 170 + idx * 26
            self.canvas.create_text(CANVAS_WIDTH // 2 + 35, cy, text=line, anchor=tk.W,
                                    font=get_comic_font(12, "bold" if "•" in line else "normal"),
                                    fill=COLOR_YELLOW if "•" in line else COLOR_WHITE)

        self.register_button(CANVAS_WIDTH // 2 - 100, CANVAS_HEIGHT - 70, 200, 44, "BACK TO MENU",
                             lambda: self.show_screen("TITLE"))
        self.draw_all_buttons()

    def draw_briefing_screen(self):
        """Displays comic briefing dossier before mission launch."""
        self.canvas.delete("all")
        self.buttons = []
        m = MISSIONS[self.current_mission_idx]

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
        draw_slanted_box(self.canvas, 100, 50, CANVAS_WIDTH - 100, CANVAS_HEIGHT - 80, slant=18,
                         fill="#0F172A", outline=COLOR_RED, width=3)

        self.canvas.create_text(CANVAS_WIDTH // 2, 95, text=f"♦ MISSION {m['id']} BRIEFING ♦",
                                font=get_comic_font(22, "bold"), fill=COLOR_YELLOW)
        self.canvas.create_text(CANVAS_WIDTH // 2, 135, text=m['title'].upper(),
                                font=get_comic_font(28, "bold"), fill=COLOR_WHITE)

        self.canvas.create_text(CANVAS_WIDTH // 2, 200, text=m['desc'],
                                width=640, justify=tk.CENTER, font=get_comic_font(15, "normal"), fill=COLOR_WHITE)

        stat_y = 280
        stats = [
            f"Sector Distance: {m['length']} px",
            f"Primary Target: {m['target_count']}x {m['target_type'].title()}",
            f"Active Hostiles: {m['thugs']} Thugs, {m['drones']} Drones" + (", Goblin Glider" if m['bombers'] else ""),
            f"Target Par Time: {m['par_time']} seconds"
        ]
        for idx, s in enumerate(stats):
            self.canvas.create_text(CANVAS_WIDTH // 2, stat_y + idx * 26, text=f"• {s}",
                                    font=get_comic_font(13, "bold"), fill=COLOR_LIGHT_BLUE)

        self.register_button(CANVAS_WIDTH // 2 - 120, CANVAS_HEIGHT - 135, 240, 46, "LAUNCH PATROL",
                             lambda: self.show_screen("PLAYING"))
        self.draw_all_buttons()

    def draw_pause_screen(self):
        """Displays semi-transparent pause menu."""
        self.buttons = []
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY, stipple="gray50")

        draw_slanted_box(self.canvas, CANVAS_WIDTH // 2 - 180, 100, CANVAS_WIDTH // 2 + 180, 420, slant=16,
                         fill="#0F172A", outline=COLOR_BLUE, width=3)
        self.canvas.create_text(CANVAS_WIDTH // 2, 145, text="PATROL PAUSED",
                                font=get_comic_font(26, "bold"), fill=COLOR_YELLOW)

        self.register_button(CANVAS_WIDTH // 2 - 120, 195, 240, 46, "RESUME",
                             lambda: self.show_screen("PLAYING"))
        self.register_button(CANVAS_WIDTH // 2 - 120, 255, 240, 46, "RESTART MISSION",
                             lambda: self.start_mission(self.current_mission_idx))
        self.register_button(CANVAS_WIDTH // 2 - 120, 315, 240, 46, "MAIN MENU",
                             lambda: self.show_screen("TITLE"))
        self.draw_all_buttons()

    def draw_mission_complete_screen(self):
        """Displays victory dossier and star rating."""
        self.canvas.delete("all")
        self.buttons = []
        m = MISSIONS[self.current_mission_idx]

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
        draw_slanted_box(self.canvas, 120, 40, CANVAS_WIDTH - 120, CANVAS_HEIGHT - 50, slant=18,
                         fill="#0F172A", outline=COLOR_BLUE, width=3)

        self.canvas.create_text(CANVAS_WIDTH // 2, 85, text="♦ MISSION COMPLETE! ♦",
                                font=get_comic_font(28, "bold"), fill=COLOR_YELLOW)
        self.canvas.create_text(CANVAS_WIDTH // 2, 125, text=m['title'].upper(),
                                font=get_comic_font(20, "bold"), fill=COLOR_WHITE)

        elapsed = int(time.time() - self.mission_start_time)
        stars = 1
        if self.player.hearts >= 4:
            stars += 1
        if elapsed <= m['par_time']:
            stars += 1
        self.total_stars += stars

        star_str = "★ " * stars + "☆ " * (3 - stars)
        self.canvas.create_text(CANVAS_WIDTH // 2, 180, text=star_str,
                                font=get_comic_font(34, "bold"), fill=COLOR_YELLOW)

        self.canvas.create_text(CANVAS_WIDTH // 2, 230, text=f"Time Taken: {elapsed}s (Par: {m['par_time']}s)",
                                font=get_comic_font(15, "bold"), fill=COLOR_WHITE)
        self.canvas.create_text(CANVAS_WIDTH // 2, 260, text=f"Hearts Remaining: {self.player.hearts} / {MAX_HEARTS}",
                                font=get_comic_font(15, "bold"), fill=COLOR_WHITE)
        self.canvas.create_text(CANVAS_WIDTH // 2, 290, text=f"Total Score: {self.score}",
                                font=get_comic_font(18, "bold"), fill=COLOR_LIGHT_BLUE)

        if self.current_mission_idx < len(MISSIONS) - 1:
            self.register_button(CANVAS_WIDTH // 2 - 120, 345, 240, 48, "NEXT MISSION",
                                 lambda: self.start_mission(self.current_mission_idx + 1))
        else:
            self.register_button(CANVAS_WIDTH // 2 - 120, 345, 240, 48, "CITY SAVED!",
                                 lambda: self.show_screen("GAME_OVER"))
        self.draw_all_buttons()

    def draw_mission_failed_screen(self):
        """Displays comic defeat screen with retry option."""
        self.canvas.delete("all")
        self.buttons = []

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
        draw_slanted_box(self.canvas, 140, 60, CANVAS_WIDTH - 140, CANVAS_HEIGHT - 70, slant=18,
                         fill="#0F172A", outline=COLOR_RED, width=3)

        self.canvas.create_text(CANVAS_WIDTH // 2, 120, text="♦ MISSION FAILED ♦",
                                font=get_comic_font(32, "bold"), fill=COLOR_RED)
        self.canvas.create_text(CANVAS_WIDTH // 2, 175, text="Spider-Man took too much damage from enemies!",
                                font=get_comic_font(18, "bold"), fill=COLOR_WHITE)

        tips = [
            "PATROL TIPS:",
            "• Hold Left Mouse to shoot webs and swing anywhere into the sky!",
            "• Press W while swinging to pump upward and climb higher.",
            "• Watch for pulsing red Spider-Sense rings to dodge incoming lasers & bombs.",
            "• Stomp thugs from above to knock them out safely."
        ]
        for idx, t in enumerate(tips):
            self.canvas.create_text(CANVAS_WIDTH // 2, 225 + idx * 24, text=t,
                                    font=get_comic_font(13, "bold" if idx == 0 else "normal"),
                                    fill=COLOR_YELLOW if idx == 0 else COLOR_WHITE)

        self.register_button(CANVAS_WIDTH // 2 - 120, 345, 240, 46, "RETRY MISSION",
                             lambda: self.start_mission(self.current_mission_idx))
        self.register_button(CANVAS_WIDTH // 2 - 120, 405, 240, 46, "MAIN MENU",
                             lambda: self.show_screen("TITLE"))
        self.draw_all_buttons()

    def draw_game_over_screen(self):
        """Displays grand finale screen after Mission 5 completion."""
        self.canvas.delete("all")
        self.buttons = []

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, fill=COLOR_NAVY)
        draw_slanted_box(self.canvas, 100, 40, CANVAS_WIDTH - 100, CANVAS_HEIGHT - 50, slant=20,
                         fill=COLOR_RED, outline=COLOR_YELLOW, width=4)

        self.canvas.create_text(CANVAS_WIDTH // 2, 95, text="★ CITY SAVED! ★",
                                font=get_comic_font(38, "bold"), fill=COLOR_WHITE)
        self.canvas.create_text(CANVAS_WIDTH // 2, 145, text="ALL MISSIONS COMPLETED • NIGHT PATROL CONQUERED",
                                font=get_comic_font(16, "bold"), fill=COLOR_YELLOW)

        self.canvas.create_text(CANVAS_WIDTH // 2, 205, text="You successfully freed civilians, secured encrypted chips,",
                                font=get_comic_font(15, "normal"), fill=COLOR_WHITE)
        self.canvas.create_text(CANVAS_WIDTH // 2, 230, text="defused goblin explosives, soared across the city skyline,",
                                font=get_comic_font(15, "normal"), fill=COLOR_WHITE)
        self.canvas.create_text(CANVAS_WIDTH // 2, 255, text="and outmaneuvered the experimental Hunter Drone!",
                                font=get_comic_font(15, "normal"), fill=COLOR_WHITE)

        self.canvas.create_text(CANVAS_WIDTH // 2, 310, text=f"FINAL SCORE: {self.score}  |  TOTAL STARS: {self.total_stars} ★",
                                font=get_comic_font(20, "bold"), fill=COLOR_YELLOW)

        self.register_button(CANVAS_WIDTH // 2 - 120, 375, 240, 48, "PLAY AGAIN",
                             lambda: self.start_mission(0))
        self.draw_all_buttons()

    def start_mission(self, mission_idx):
        """Initializes a new mission and opens its briefing card."""
        self.current_mission_idx = mission_idx
        m = MISSIONS[mission_idx]
        self.player = Player(x=150, y=340)
        self.cam_x = 0.0
        self.combo = 1
        self.mission_start_time = time.time()
        self.time_remaining = m.get("time_limit", 0)

        self.rooftops, self.anchors, self.cartridges, self.medkits, self.items, self.enemies = generate_level(m, seed_val=100 + mission_idx * 17)
        self.show_screen("BRIEFING")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    game = Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
