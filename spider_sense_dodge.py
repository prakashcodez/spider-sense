"""
SPIDER-SENSE DODGE
──────────────────────────────────────────────────────────
A Python Tkinter game for the "Python Programming for Design" course.
Spider-Man dodges Green Goblin's attacks using his spider-sense!
Uses ONLY: tkinter, random, math — no images or external files.
──────────────────────────────────────────────────────────
"""

import tkinter as tk
import random
import math

# ═══════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════
WIDTH = 700                 # Canvas width in pixels
HEIGHT = 450                # Canvas height in pixels
FPS = 30                    # Delay between frames in ms (~33 FPS)
PLAYER_SPEED = 5            # Pixels the player moves per tick
PLAYER_RADIUS = 14          # Radius of the player's body circle

INVINCIBLE_TICKS = 50       # ~1.5 s of invincibility after being hit
BOMB_RADIUS = 42            # Pumpkin bomb explosion radius
DEBRIS_WIDTH = 60           # Width of the debris rain column
GLIDER_HEIGHT = 42          # Height of the glider sweep band
ACTIVE_TICKS = 10           # How long a hazard stays in "active" state
BASE_WARNING = 18           # Starting warning duration (ticks)
MIN_WARNING = 7             # Shortest possible warning duration
BASE_SPAWN_INTERVAL = 90    # Starting spawn interval (ticks, ~2.7 s)
MIN_SPAWN_INTERVAL = 35     # Fastest spawn rate
POWERUP_LIFETIME = 200      # Power-up item on screen (~6 s)
SLOW_TIME_TICKS = 167       # Spider Time effect duration (~5 s)
MAX_HAZARDS_EARLY = 2       # Max simultaneous hazards before level 4
MAX_HAZARDS_LATE = 3        # Max simultaneous hazards from level 4+
SCORE_TICK_INTERVAL = 33    # Ticks between +1 survival score (~1 s)
CLOSE_CALL_DIST = 25        # Near-miss threshold in pixels

BG_COLOR = "#172554"        # Dark navy window background
CANVAS_BG = "#0F172A"       # Canvas background
CANVAS_BORDER = "#22D3EE"   # Cyan canvas border colour


# ═══════════════════════════════════════════════════════
#  GAME CLASS
# ═══════════════════════════════════════════════════════
class SpiderSenseGame:
    """Single class that manages the entire game: UI, logic, and drawing."""

    # ── Set up the window and start on the opening screen ──
    def __init__(self, root):
        self.root = root
        self.root.title("SPIDER-SENSE DODGE")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        self.high_score = 0       # Persists while the program is running
        self.loop_id = None       # Tracks the after() call ID

        self.setup_ui()
        self.bind_keys()
        self.init_game_vars()
        self.show_opening_screen()

    # ── Create all tkinter widgets (labels, canvas, buttons) ──
    def setup_ui(self):
        # Title label
        self.title_label = tk.Label(
            self.root, text="\u2666 SPIDER-SENSE DODGE \u2666",
            font=("Segoe UI", 18, "bold"), fg="#FF4444", bg=BG_COLOR
        )
        self.title_label.pack(pady=(8, 2))

        # Score + Lives info bar
        info_frame = tk.Frame(self.root, bg=BG_COLOR)
        info_frame.pack(pady=(0, 4))

        self.score_label = tk.Label(
            info_frame, text="SCORE: 0",
            font=("Consolas", 13, "bold"), fg="#FACC15", bg=BG_COLOR
        )
        self.score_label.pack(side=tk.LEFT, padx=20)

        self.lives_label = tk.Label(
            info_frame, text="\u2764 \u2764 \u2764",
            font=("Segoe UI", 14), fg="#FF4444", bg=BG_COLOR
        )
        self.lives_label.pack(side=tk.LEFT, padx=20)

        # Game canvas
        self.canvas = tk.Canvas(
            self.root, width=WIDTH, height=HEIGHT,
            bg=CANVAS_BG, highlightthickness=2,
            highlightbackground=CANVAS_BORDER
        )
        self.canvas.pack(padx=10, pady=4)

        # Bottom button bar
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=(6, 10))

        self.restart_btn = tk.Button(
            btn_frame, text="RESTART GAME",
            font=("Segoe UI", 11, "bold"), fg="white",
            bg="#16A34A", activebackground="#15803D",
            width=14, command=self.restart
        )
        self.restart_btn.pack(side=tk.LEFT, padx=10)

        self.exit_btn = tk.Button(
            btn_frame, text="EXIT",
            font=("Segoe UI", 11, "bold"), fg="white",
            bg="#DC2626", activebackground="#B91C1C",
            width=14, command=self.root.destroy
        )
        self.exit_btn.pack(side=tk.LEFT, padx=10)

    # ── Initialise / reset every game variable to its starting value ──
    def init_game_vars(self):
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT // 2
        self.keys_pressed = set()

        self.score = 0
        self.lives = 3
        self.tick = 0

        self.hazards = []           # List of hazard dictionaries
        self.powerups = []          # List of power-up dictionaries
        self.shield_active = False  # Web Shield absorbed next hit?
        self.slow_time_timer = 0    # Remaining ticks of Spider Time
        self.active_powerup = None  # Name shown on HUD ("shield"/"slowtime")

        self.invincible_timer = 0   # Remaining invincibility ticks
        self.spawn_timer = 0        # Ticks until next hazard spawn
        self.score_timer = 0        # Ticks until next +1 survival point

        self.close_call_timer = 0   # Remaining ticks to show "+5" text
        self.close_call_x = 0
        self.close_call_y = 0

        self.paused = False
        self.game_running = False
        self.game_over_flag = False
        self.opening = True

    # ── Bind keyboard events to the window ──
    def bind_keys(self):
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

    # ── Record a key being pressed; also handle special keys ──
    def key_press(self, event):
        key = event.keysym.lower()

        # Start game from the opening screen
        if self.opening:
            if key in ("up", "down", "left", "right", "w", "a", "s", "d"):
                self.start_game()
            return

        # Toggle pause
        if key == "p":
            self.toggle_pause()
            return

        # Quick restart
        if key == "r":
            self.restart()
            return

        self.keys_pressed.add(key)

    # ── Record a key being released ──
    def key_release(self, event):
        self.keys_pressed.discard(event.keysym.lower())

    # ── Display the opening "press a key to start" screen ──
    def show_opening_screen(self):
        self.canvas.delete("all")

        cx, cy = WIDTH // 2, HEIGHT // 2

        self.canvas.create_text(
            cx, cy - 80, text="\u2666 SPIDER-SENSE DODGE \u2666",
            font=("Segoe UI", 26, "bold"), fill="#FF4444"
        )
        self.canvas.create_text(
            cx, cy - 40, text="Dodge Green Goblin's attacks!",
            font=("Segoe UI", 13), fill="#94A3B8"
        )

        # Draw a small Spider-Man preview
        self.draw_player_at(cx, cy + 10)

        self.canvas.create_text(
            cx, cy + 60, text="Arrow Keys  /  W A S D  to move",
            font=("Consolas", 12), fill="#22D3EE"
        )
        self.canvas.create_text(
            cx, cy + 90, text="Press any arrow key to start",
            font=("Consolas", 11, "bold"), fill="#FACC15"
        )
        self.canvas.create_text(
            cx, cy + 130, text="P = Pause     R = Restart",
            font=("Consolas", 10), fill="#64748B"
        )

    # ── Transition from the opening screen into gameplay ──
    def start_game(self):
        self.opening = False
        self.game_running = True
        self.game_over_flag = False
        self.game_loop()

    # ── Pause or resume the game ──
    def toggle_pause(self):
        if self.game_over_flag or self.opening:
            return
        self.paused = not self.paused
        # If unpausing, restart the loop
        if not self.paused and self.game_running:
            self.game_loop()

    # ─────────────────────────────────────────────
    #  PLAYER
    # ─────────────────────────────────────────────

    # ── Move the player based on which keys are currently held ──
    def move_player(self):
        dx, dy = 0, 0
        if "left" in self.keys_pressed or "a" in self.keys_pressed:
            dx -= PLAYER_SPEED
        if "right" in self.keys_pressed or "d" in self.keys_pressed:
            dx += PLAYER_SPEED
        if "up" in self.keys_pressed or "w" in self.keys_pressed:
            dy -= PLAYER_SPEED
        if "down" in self.keys_pressed or "s" in self.keys_pressed:
            dy += PLAYER_SPEED

        # Clamp inside the canvas
        self.player_x = max(PLAYER_RADIUS,
                            min(WIDTH - PLAYER_RADIUS, self.player_x + dx))
        self.player_y = max(PLAYER_RADIUS,
                            min(HEIGHT - PLAYER_RADIUS, self.player_y + dy))

    # ── Draw Spider-Man at a given position (used for preview too) ──
    def draw_player_at(self, px, py):
        r = PLAYER_RADIUS

        # Red body
        self.canvas.create_oval(
            px - r, py - r, px + r, py + r,
            fill="#DC2626", outline="#991B1B", width=2
        )

        # Web pattern (cross lines on body)
        self.canvas.create_line(px - r, py, px + r, py,
                                fill="#7F1D1D", width=1)
        self.canvas.create_line(px, py - r, px, py + r,
                                fill="#7F1D1D", width=1)

        # Diagonal web lines
        self.canvas.create_line(px - r, py - r, px + r, py + r,
                                fill="#7F1D1D", width=1)
        self.canvas.create_line(px + r, py - r, px - r, py + r,
                                fill="#7F1D1D", width=1)

        # Two white eyes (angular Spider-Man style)
        self.canvas.create_polygon(
            px - 8, py - 3, px - 4, py - 7, px - 1, py - 2,
            fill="white", outline="white"
        )
        self.canvas.create_polygon(
            px + 8, py - 3, px + 4, py - 7, px + 1, py - 2,
            fill="white", outline="white"
        )

        # Blue legs (four short lines extending downward)
        for offset_x, angle in [(-7, -20), (-3, -5), (3, 5), (7, 20)]:
            end_x = px + offset_x + int(math.sin(math.radians(angle)) * 11)
            end_y = py + r + 9
            self.canvas.create_line(
                px + offset_x, py + r - 2, end_x, end_y,
                fill="#1E40AF", width=2
            )

        # Shield glow if Web Shield is active
        if self.shield_active:
            self.canvas.create_oval(
                px - r - 6, py - r - 6, px + r + 6, py + r + 6,
                outline="#60A5FA", width=2, dash=(4, 3)
            )

    # ── Draw the player (with invincibility blink effect) ──
    def draw_player(self):
        # Skip drawing every other short interval to create a blink
        if self.invincible_timer > 0 and self.tick % 4 < 2:
            return
        self.draw_player_at(self.player_x, self.player_y)

    # ─────────────────────────────────────────────
    #  LEVELS & DIFFICULTY
    # ─────────────────────────────────────────────

    # ── Calculate the current level from the score ──
    def get_level(self):
        return self.score // 100 + 1

    # ── Get warning time for the current level (decreases) ──
    def get_warning_time(self):
        return max(MIN_WARNING, BASE_WARNING - (self.get_level() - 1))

    # ── Get spawn interval for the current level (decreases) ──
    def get_spawn_interval(self):
        return max(MIN_SPAWN_INTERVAL,
                   BASE_SPAWN_INTERVAL - (self.get_level() - 1) * 5)

    # ── Get max simultaneous hazards for the current level ──
    def get_max_hazards(self):
        return MAX_HAZARDS_LATE if self.get_level() >= 4 else MAX_HAZARDS_EARLY

    # ─────────────────────────────────────────────
    #  HAZARDS
    # ─────────────────────────────────────────────

    # ── Create a new random hazard and add it to the list ──
    def spawn_hazard(self):
        if len(self.hazards) >= self.get_max_hazards():
            return

        htype = random.choice(["bomb", "debris", "glider"])
        wt = self.get_warning_time()

        if htype == "bomb":
            x = random.randint(BOMB_RADIUS + 10, WIDTH - BOMB_RADIUS - 10)
            y = random.randint(BOMB_RADIUS + 10, HEIGHT - BOMB_RADIUS - 10)
            hazard = {
                "type": "bomb", "x": x, "y": y,
                "radius": BOMB_RADIUS,
                "timer": 0, "warning_time": wt,
                "active_time": ACTIVE_TICKS,
                "state": "warning", "hit": False, "close_called": False
            }
        elif htype == "debris":
            x = random.randint(10, WIDTH - DEBRIS_WIDTH - 10)
            hazard = {
                "type": "debris", "x": x, "y": 0,
                "width": DEBRIS_WIDTH, "height": HEIGHT,
                "timer": 0, "warning_time": wt,
                "active_time": ACTIVE_TICKS,
                "state": "warning", "hit": False, "close_called": False
            }
        else:   # glider
            y = random.randint(10, HEIGHT - GLIDER_HEIGHT - 10)
            hazard = {
                "type": "glider", "x": 0, "y": y,
                "width": WIDTH, "height": GLIDER_HEIGHT,
                "timer": 0, "warning_time": wt,
                "active_time": ACTIVE_TICKS,
                "state": "warning", "hit": False, "close_called": False
            }

        self.hazards.append(hazard)

    # ── Advance hazard timers and transition warning → active → done ──
    def update_hazards(self):
        for h in self.hazards:
            # Spider Time slows hazard timers (advance every other tick)
            if self.slow_time_timer > 0 and self.tick % 2 != 0:
                continue

            h["timer"] += 1

            if h["state"] == "warning" and h["timer"] >= h["warning_time"]:
                h["state"] = "active"
                h["timer"] = 0
            elif h["state"] == "active" and h["timer"] >= h["active_time"]:
                h["state"] = "done"

        # Remove finished hazards; award +10 for each dodged
        remaining = []
        for h in self.hazards:
            if h["state"] == "done":
                if not h["hit"]:
                    self.score += 10
            else:
                remaining.append(h)
        self.hazards = remaining

    # ── Draw all hazards on the canvas (warnings and active zones) ──
    def draw_hazards(self):
        for h in self.hazards:
            if h["state"] == "warning":
                self.draw_warning(h)
            elif h["state"] == "active":
                self.draw_active(h)

    # ── Draw a pulsing warning zone for a hazard ──
    def draw_warning(self, h):
        # Pulse between two visual states every 3 ticks
        pulse = (h["timer"] // 3) % 2 == 0
        fill_color = "#FF4444" if pulse else "#CC3333"
        stipple = "gray25" if pulse else "gray12"

        if h["type"] == "bomb":
            r = h["radius"]
            self.canvas.create_oval(
                h["x"] - r, h["y"] - r, h["x"] + r, h["y"] + r,
                outline="#FF4444", fill=fill_color, stipple=stipple, width=2
            )
            self.canvas.create_text(
                h["x"], h["y"], text="!",
                font=("Segoe UI", 14, "bold"), fill="#FACC15"
            )
        elif h["type"] == "debris":
            self.canvas.create_rectangle(
                h["x"], 0, h["x"] + h["width"], HEIGHT,
                outline="#FF4444", fill=fill_color, stipple=stipple, width=2
            )
        elif h["type"] == "glider":
            self.canvas.create_rectangle(
                0, h["y"], WIDTH, h["y"] + h["height"],
                outline="#FF4444", fill=fill_color, stipple=stipple, width=2
            )

    # ── Draw an active hazard (the actual attack) ──
    def draw_active(self, h):
        if h["type"] == "bomb":
            r = h["radius"]
            # Orange explosion
            self.canvas.create_oval(
                h["x"] - r, h["y"] - r, h["x"] + r, h["y"] + r,
                fill="#F97316", outline="#EA580C", width=2
            )
            # Hot inner core
            ir = r // 2
            self.canvas.create_oval(
                h["x"] - ir, h["y"] - ir, h["x"] + ir, h["y"] + ir,
                fill="#FCD34D", outline=""
            )

        elif h["type"] == "debris":
            # Grey column
            self.canvas.create_rectangle(
                h["x"], 0, h["x"] + h["width"], HEIGHT,
                fill="#4B5563", outline="#6B7280", width=1
            )
            # Falling rocks (positions derived from column x for consistency)
            seed = h["x"]
            for i in range(10):
                rx = h["x"] + ((seed + i * 17) % max(1, h["width"] - 14))
                ry = ((i * 47 + h["timer"] * 20 + seed) % (HEIGHT + 10)) - 5
                self.canvas.create_oval(
                    rx, ry, rx + 14, ry + 11,
                    fill="#9CA3AF", outline="#6B7280"
                )

        elif h["type"] == "glider":
            # Green streak across the band
            self.canvas.create_rectangle(
                0, h["y"], WIDTH, h["y"] + h["height"],
                fill="#166534", outline="#15803D", width=1
            )
            # Moving glider triangle
            gx = (h["timer"] * 65) % (WIDTH + 40) - 20
            gy = h["y"] + h["height"] // 2
            self.canvas.create_polygon(
                gx, gy - 12, gx + 30, gy, gx, gy + 12,
                fill="#22C55E", outline="#4ADE80", width=2
            )
            # Thruster trail
            self.canvas.create_line(
                gx, gy, gx - 25, gy,
                fill="#86EFAC", width=3, dash=(5, 3)
            )

    # ─────────────────────────────────────────────
    #  COLLISION DETECTION
    # ─────────────────────────────────────────────

    # ── Check whether the player is hit by any active hazard ──
    def check_hit(self):
        if self.invincible_timer > 0:
            return

        px, py = self.player_x, self.player_y

        for h in self.hazards:
            if h["state"] != "active" or h["hit"]:
                continue

            inside = False

            if h["type"] == "bomb":
                dist = math.sqrt((px - h["x"]) ** 2 + (py - h["y"]) ** 2)
                inside = dist < h["radius"]
            elif h["type"] == "debris":
                inside = h["x"] < px < h["x"] + h["width"]
            elif h["type"] == "glider":
                inside = h["y"] < py < h["y"] + h["height"]

            if inside:
                h["hit"] = True
                # Web Shield absorbs one hit
                if self.shield_active:
                    self.shield_active = False
                    self.active_powerup = None
                else:
                    self.lives -= 1
                    self.invincible_timer = INVINCIBLE_TICKS
                    self.update_lives_label()
                    if self.lives <= 0:
                        self.do_game_over()
                return  # Only one hit processed per tick

    # ── Check if player narrowly escaped (close call +5 bonus) ──
    def check_close_call(self):
        px, py = self.player_x, self.player_y

        for h in self.hazards:
            if h["state"] != "active" or h["hit"] or h["close_called"]:
                continue

            near = False

            if h["type"] == "bomb":
                dist = math.sqrt((px - h["x"]) ** 2 + (py - h["y"]) ** 2)
                # Player is outside the blast but very close to its edge
                near = h["radius"] <= dist <= h["radius"] + CLOSE_CALL_DIST

            elif h["type"] == "debris":
                left_edge = abs(px - h["x"])
                right_edge = abs(px - (h["x"] + h["width"]))
                closest = min(left_edge, right_edge)
                # Near the edge but NOT inside the column
                near = (closest <= CLOSE_CALL_DIST and
                        not (h["x"] < px < h["x"] + h["width"]))

            elif h["type"] == "glider":
                top_edge = abs(py - h["y"])
                bot_edge = abs(py - (h["y"] + h["height"]))
                closest = min(top_edge, bot_edge)
                near = (closest <= CLOSE_CALL_DIST and
                        not (h["y"] < py < h["y"] + h["height"]))

            if near:
                h["close_called"] = True
                self.score += 5
                self.close_call_timer = 30
                self.close_call_x = px
                self.close_call_y = py - 35

    # ─────────────────────────────────────────────
    #  SPIDER-SENSE VISUALS
    # ─────────────────────────────────────────────

    # ── Draw radiating "sense lines" around Spider-Man's head ──
    def draw_spider_sense(self):
        # Only show when at least one warning is active
        has_warning = any(h["state"] == "warning" for h in self.hazards)
        if not has_warning:
            return

        px, py = self.player_x, self.player_y
        for i in range(8):
            angle = math.radians(i * 45 + self.tick * 6)
            x1 = px + math.cos(angle) * (PLAYER_RADIUS + 5)
            y1 = py - 4 + math.sin(angle) * (PLAYER_RADIUS + 5)
            x2 = px + math.cos(angle) * (PLAYER_RADIUS + 14)
            y2 = py - 4 + math.sin(angle) * (PLAYER_RADIUS + 14)
            self.canvas.create_line(x1, y1, x2, y2, fill="white", width=1)

    # ─────────────────────────────────────────────
    #  POWER-UPS
    # ─────────────────────────────────────────────

    # ── Randomly spawn a power-up (low probability each tick) ──
    def spawn_powerup(self):
        # Only one uncollected power-up at a time
        if len(self.powerups) > 0:
            return
        if random.random() > 0.008:
            return

        ptype = random.choice(["shield", "slowtime"])
        x = random.randint(30, WIDTH - 30)
        y = random.randint(30, HEIGHT - 30)
        self.powerups.append({
            "type": ptype, "x": x, "y": y,
            "timer": 0, "max_timer": POWERUP_LIFETIME
        })

    # ── Check if the player touches (collects) a power-up ──
    def check_powerup_collect(self):
        px, py = self.player_x, self.player_y
        remaining = []

        for p in self.powerups:
            dist = math.sqrt((px - p["x"]) ** 2 + (py - p["y"]) ** 2)
            if dist < 22:
                # Collected!
                if p["type"] == "shield":
                    self.shield_active = True
                    self.active_powerup = "shield"
                elif p["type"] == "slowtime":
                    self.slow_time_timer = SLOW_TIME_TICKS
                    self.active_powerup = "slowtime"
            else:
                p["timer"] += 1
                if p["timer"] < p["max_timer"]:
                    remaining.append(p)
        self.powerups = remaining

    # ── Draw power-up items on the canvas ──
    def draw_powerups(self):
        for p in self.powerups:
            x, y = p["x"], p["y"]

            # Blink when about to expire
            if p["timer"] > p["max_timer"] - 60 and self.tick % 4 < 2:
                continue

            if p["type"] == "shield":
                # Blue circle with "W" for Web Shield
                self.canvas.create_oval(
                    x - 13, y - 13, x + 13, y + 13,
                    fill="#3B82F6", outline="#93C5FD", width=2
                )
                self.canvas.create_text(
                    x, y, text="W",
                    font=("Consolas", 10, "bold"), fill="white"
                )

            elif p["type"] == "slowtime":
                # Yellow five-pointed star
                points = []
                for i in range(5):
                    outer = math.radians(i * 72 - 90)
                    points.extend([x + math.cos(outer) * 14,
                                   y + math.sin(outer) * 14])
                    inner = math.radians(i * 72 + 36 - 90)
                    points.extend([x + math.cos(inner) * 6,
                                   y + math.sin(inner) * 6])
                self.canvas.create_polygon(
                    points, fill="#FACC15", outline="#EAB308", width=1
                )

    # ─────────────────────────────────────────────
    #  SCORING
    # ─────────────────────────────────────────────

    # ── Award +1 point every ~1 second of survival ──
    def update_score(self):
        self.score_timer += 1
        if self.score_timer >= SCORE_TICK_INTERVAL:
            self.score += 1
            self.score_timer = 0

    # ── Refresh the lives label with heart symbols ──
    def update_lives_label(self):
        if self.lives > 0:
            self.lives_label.config(
                text=" ".join(["\u2764"] * self.lives), fg="#FF4444"
            )
        else:
            self.lives_label.config(text="\u2620", fg="#FF4444")

    # ─────────────────────────────────────────────
    #  DRAWING – MAIN FRAME
    # ─────────────────────────────────────────────

    # ── Redraw the entire canvas for one frame ──
    def draw_game(self):
        self.canvas.delete("all")

        # Layer 1: hazards (behind everything)
        self.draw_hazards()

        # Layer 2: power-ups
        self.draw_powerups()

        # Layer 3: player and sense lines
        self.draw_player()
        self.draw_spider_sense()

        # HUD – level in top-left
        self.canvas.create_text(
            12, 12, text=f"LEVEL {self.get_level()}",
            font=("Consolas", 12, "bold"), fill="#22D3EE", anchor="nw"
        )

        # HUD – active power-up in top-right
        if self.shield_active:
            self.canvas.create_text(
                WIDTH - 12, 12, text="WEB SHIELD",
                font=("Consolas", 10, "bold"), fill="#60A5FA", anchor="ne"
            )
        if self.slow_time_timer > 0:
            y_offset = 30 if self.shield_active else 12
            self.canvas.create_text(
                WIDTH - 12, y_offset, text="SPIDER TIME",
                font=("Consolas", 10, "bold"), fill="#FACC15", anchor="ne"
            )

        # Floating "CLOSE CALL! +5" text
        if self.close_call_timer > 0:
            self.canvas.create_text(
                self.close_call_x, self.close_call_y,
                text="CLOSE CALL! +5",
                font=("Consolas", 11, "bold"), fill="#22D3EE"
            )

        # Pause overlay
        if self.paused:
            self.canvas.create_rectangle(
                0, 0, WIDTH, HEIGHT, fill="black", stipple="gray50"
            )
            self.canvas.create_text(
                WIDTH // 2, HEIGHT // 2, text="PAUSED",
                font=("Segoe UI", 32, "bold"), fill="white"
            )
            self.canvas.create_text(
                WIDTH // 2, HEIGHT // 2 + 40,
                text="Press P to resume",
                font=("Consolas", 12), fill="#94A3B8"
            )

        # Update the score label widget
        self.score_label.config(text=f"SCORE: {self.score}")

    # ─────────────────────────────────────────────
    #  GAME OVER
    # ─────────────────────────────────────────────

    # ── End the game, show the game-over box on the canvas ──
    def do_game_over(self):
        self.game_running = False
        self.game_over_flag = True

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

        # Cancel pending loop
        if self.loop_id is not None:
            self.root.after_cancel(self.loop_id)
            self.loop_id = None

        self.canvas.delete("all")

        cx, cy = WIDTH // 2, HEIGHT // 2

        # Semi-dark background
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=CANVAS_BG)

        # Bordered box
        bx, by, bw, bh = cx - 170, cy - 100, 340, 200
        self.canvas.create_rectangle(
            bx, by, bx + bw, by + bh,
            fill="#1E293B", outline="#EF4444", width=3
        )

        self.canvas.create_text(
            cx, cy - 65, text="GAME OVER",
            font=("Segoe UI", 26, "bold"), fill="#EF4444"
        )
        self.canvas.create_text(
            cx, cy - 20, text=f"Final Score: {self.score}",
            font=("Consolas", 15), fill="#FACC15"
        )
        self.canvas.create_text(
            cx, cy + 15, text=f"High Score: {self.high_score}",
            font=("Consolas", 15), fill="#22D3EE"
        )
        self.canvas.create_text(
            cx, cy + 55, text=f"Level Reached: {self.get_level()}",
            font=("Consolas", 12), fill="#94A3B8"
        )
        self.canvas.create_text(
            cx, cy + 80, text="Press R or click RESTART",
            font=("Consolas", 11), fill="#64748B"
        )

    # ─────────────────────────────────────────────
    #  RESTART
    # ─────────────────────────────────────────────

    # ── Reset everything and show the opening screen again ──
    def restart(self):
        # Cancel any pending after() call to prevent double loops
        if self.loop_id is not None:
            self.root.after_cancel(self.loop_id)
            self.loop_id = None

        self.init_game_vars()
        self.update_lives_label()
        self.score_label.config(text="SCORE: 0")
        self.show_opening_screen()

    # ─────────────────────────────────────────────
    #  GAME LOOP
    # ─────────────────────────────────────────────

    # ── Main loop: called every FPS ms via root.after() ──
    def game_loop(self):
        # Safety: stop if game is over or not running
        if not self.game_running or self.game_over_flag:
            return

        # If paused, draw the paused overlay and stop scheduling
        if self.paused:
            self.draw_game()
            return

        self.tick += 1

        # --- Update phase ---
        self.move_player()

        # Tick down timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.slow_time_timer > 0:
            self.slow_time_timer -= 1
            if self.slow_time_timer <= 0 and self.active_powerup == "slowtime":
                self.active_powerup = None
        if self.close_call_timer > 0:
            self.close_call_timer -= 1

        # Spawn hazards on a timer
        self.spawn_timer += 1
        if self.spawn_timer >= self.get_spawn_interval():
            self.spawn_hazard()
            self.spawn_timer = 0

        self.update_hazards()

        # Collision checks
        self.check_hit()
        if self.game_over_flag:
            return

        self.check_close_call()

        # Score and power-ups
        self.update_score()
        self.spawn_powerup()
        self.check_powerup_collect()

        # --- Draw phase ---
        self.draw_game()

        # Schedule the next frame
        self.loop_id = self.root.after(FPS, self.game_loop)


# ═══════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════
root = tk.Tk()
game = SpiderSenseGame(root)
root.mainloop()
