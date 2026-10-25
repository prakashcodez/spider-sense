import tkinter as tk
import random
import math


# -------------------- GAME CONSTANTS --------------------

WIDTH = 700
HEIGHT = 450
FPS_DELAY = 30

PLAYER_SPEED = 4
PLAYER_RADIUS = 13
PLAYER_MARGIN = 22

INITIAL_LIVES = 3
INITIAL_WARNING_TICKS = 18
MIN_WARNING_TICKS = 7

HAZARD_ACTIVE_TICKS = 10
INVINCIBILITY_TICKS = 50

TICKS_PER_SECOND = round(1000 / FPS_DELAY)


class SpiderSenseGame:

    # Create the game window, initialize variables and start the game loop.
    def __init__(self, root):
        self.root = root
        self.root.title("SPIDER-SENSE DODGE")
        self.root.resizable(False, False)
        self.root.configure(bg="#172554")

        # The high score remains available when restarting the game.
        self.high_score = 0

        # Stores the ID of the scheduled game loop.
        self.after_id = None

        # Create labels, canvas and buttons.
        self.build_interface()

        # Listen for keyboard presses and releases.
        self.bind_keys()

        # Initialize the game and display the opening screen.
        self.restart()

    # Create the title, score label, lives label, canvas and buttons.
    def build_interface(self):

        self.title_label = tk.Label(
            self.root,
            text="SPIDER-SENSE DODGE",
            font=("Arial", 20, "bold"),
            bg="#172554",
            fg="#67E8F9"
        )
        self.title_label.pack(pady=(12, 5))

        # Create a frame for the score and lives labels.
        hud_frame = tk.Frame(self.root, bg="#172554")
        hud_frame.pack(fill="x", padx=18)

        self.score_label = tk.Label(
            hud_frame,
            text="Score: 0",
            font=("Arial", 12, "bold"),
            bg="#172554",
            fg="#FDE047"
        )
        self.score_label.pack(side="left")

        self.lives_label = tk.Label(
            hud_frame,
            text="Lives: ♥ ♥ ♥",
            font=("Arial", 12, "bold"),
            bg="#172554",
            fg="#F87171"
        )
        self.lives_label.pack(side="right")

        # Create the playing area with a cyan border.
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg="#0F172A",
            highlightthickness=2,
            highlightbackground="#22D3EE"
        )
        self.canvas.pack(padx=12, pady=8)

        # Create the button frame below the canvas.
        button_frame = tk.Frame(self.root, bg="#172554")
        button_frame.pack(pady=(2, 12))

        self.restart_button = tk.Button(
            button_frame,
            text="RESTART GAME",
            command=self.restart,
            font=("Arial", 11, "bold"),
            bg="#22C55E",
            fg="#052E16",
            activebackground="#4ADE80",
            width=16,
            relief="raised",
            cursor="hand2"
        )
        self.restart_button.pack(side="left", padx=8)

        self.exit_button = tk.Button(
            button_frame,
            text="EXIT",
            command=self.root.destroy,
            font=("Arial", 11, "bold"),
            bg="#EF4444",
            fg="#FFFFFF",
            activebackground="#F87171",
            width=10,
            relief="raised",
            cursor="hand2"
        )
        self.exit_button.pack(side="left", padx=8)

    # Bind keyboard events so held keys can move the player smoothly.
    def bind_keys(self):
        self.root.bind_all("<KeyPress>", self.on_key_press)
        self.root.bind_all("<KeyRelease>", self.on_key_release)

    # Handle movement keys, starting the game, pausing and restarting.
    def on_key_press(self, event):
        key = event.keysym.lower()

        # R restarts the game at any time.
        if key == "r":
            self.restart()
            return

        # P pauses or resumes a running game.
        if key == "p":
            if self.started and not self.game_over_state:
                self.paused = not self.paused

                # Prevent movement from continuing after pausing.
                if self.paused:
                    self.keys_pressed.clear()

            return

        movement_keys = {
            "left", "right", "up", "down",
            "w", "a", "s", "d"
        }

        # Store movement keys in a set until they are released.
        if key in movement_keys and not self.game_over_state:
            self.keys_pressed.add(key)

            # Start the game when a movement key is pressed.
            if not self.started:
                self.started = True

    # Remove released movement keys from the set.
    def on_key_release(self, event):
        key = event.keysym.lower()
        self.keys_pressed.discard(key)

    # Run the game repeatedly using root.after().
    def game_loop(self):
        # This callback is no longer waiting to run.
        self.after_id = None

        # Stop completely after game over.
        if self.game_over_state:
            self.draw_game()
            return

        self.tick_count += 1

        # Update game logic only after starting and while not paused.
        if self.started and not self.paused:
            self.update_game()

        # Redraw the screen after updating the game.
        self.draw_game()

        # Schedule exactly one next update.
        if not self.game_over_state:
            self.after_id = self.root.after(
                FPS_DELAY,
                self.game_loop
            )

    # Update movement, hazards, power-ups, messages and score.
    def update_game(self):

        # Count down temporary effects.
        if self.invincible_ticks > 0:
            self.invincible_ticks -= 1

        if self.spider_time_ticks > 0:
            self.spider_time_ticks -= 1

        if self.message_ticks > 0:
            self.message_ticks -= 1

        # Update the player first.
        self.move_player()

        # Update existing hazards and handle collisions.
        self.update_hazards()

        if self.game_over_state:
            return

        # Update power-ups and check whether one was collected.
        self.update_powerups()

        # Give one point for approximately every second survived.
        self.survival_ticks += 1

        if self.survival_ticks >= TICKS_PER_SECOND:
            self.score += 1
            self.survival_ticks = 0

        # Count down to the next hazard.
        if self.spawn_timer > 0:
            self.spawn_timer -= 1

        # Spawn only when there is room for another hazard.
        if (
            self.spawn_timer <= 0
            and len(self.hazards) < self.get_max_hazards()
        ):
            self.spawn_hazard()
            self.spawn_timer = self.get_spawn_interval()

    # Move Spider-Man according to all currently held movement keys.
    def move_player(self):
        dx = 0
        dy = 0

        if "left" in self.keys_pressed or "a" in self.keys_pressed:
            dx -= 1

        if "right" in self.keys_pressed or "d" in self.keys_pressed:
            dx += 1

        if "up" in self.keys_pressed or "w" in self.keys_pressed:
            dy -= 1

        if "down" in self.keys_pressed or "s" in self.keys_pressed:
            dy += 1

        # Normalize diagonal movement so it is not faster.
        if dx != 0 and dy != 0:
            diagonal_length = math.sqrt(dx * dx + dy * dy)
            dx /= diagonal_length
            dy /= diagonal_length

        self.player_x += dx * PLAYER_SPEED
        self.player_y += dy * PLAYER_SPEED

        # Keep the player inside the canvas.
        self.player_x = max(
            PLAYER_MARGIN,
            min(WIDTH - PLAYER_MARGIN, self.player_x)
        )

        self.player_y = max(
            PLAYER_MARGIN,
            min(HEIGHT - PLAYER_MARGIN, self.player_y)
        )

    # Create a randomly positioned pumpkin, debris column or glider band.
    def spawn_hazard(self):

        hazard_type = random.choice([
            "pumpkin",
            "debris",
            "glider"
        ])

        x = random.randint(70, WIDTH - 70)
        y = random.randint(70, HEIGHT - 70)

        # The size means radius for a pumpkin and width or height otherwise.
        if hazard_type == "pumpkin":
            size = random.randint(45, 60)
            position = (x, y)

        elif hazard_type == "debris":
            size = random.randint(75, 100)
            position = (x, HEIGHT / 2)

        else:
            size = random.randint(48, 62)
            position = (WIDTH / 2, y)

        # Each hazard stores its type, position, size, timer and state.
        hazard = {
            "type": hazard_type,
            "position": position,
            "size": size,
            "timer": self.get_warning_ticks(),
            "state": "warning",

            # Additional flags prevent repeated hits and rewards.
            "hit": False,
            "contact": False,
            "close_call_awarded": False
        }

        self.hazards.append(hazard)

    # Advance hazard timers, activate attacks and award successful dodges.
    def update_hazards(self):

        # Spider Time makes hazard timers advance only every other tick.
        if self.spider_time_ticks > 0:
            advance_timers = self.tick_count % 2 == 0
        else:
            advance_timers = True

        for hazard in self.hazards:

            # Warning hazards cannot hurt the player.
            if hazard["state"] == "warning":

                if advance_timers:
                    hazard["timer"] -= 1

                # Activate the attack when its warning finishes.
                if hazard["timer"] <= 0:
                    hazard["state"] = "active"
                    hazard["timer"] = HAZARD_ACTIVE_TICKS

                    # Check immediately when the attack becomes active.
                    self.check_hit(hazard)

                    if self.game_over_state:
                        return

            # Active hazards can hit the player.
            elif hazard["state"] == "active":

                self.check_hit(hazard)

                if self.game_over_state:
                    return

                # Check whether the player narrowly avoided the attack.
                self.check_close_call(hazard)

                # Keep the hazard active for its allotted time.
                if advance_timers:
                    hazard["timer"] -= 1

                    if hazard["timer"] <= 0:

                        # Reward the player if the hazard made no contact.
                        if not hazard["contact"]:
                            self.score += 10
                            self.show_message("DODGED! +10", 30)

                        hazard["state"] = "done"

        # Remove completed hazards from the list.
        self.hazards = [
            hazard
            for hazard in self.hazards
            if hazard["state"] != "done"
        ]

    # Check whether an active hazard hits the player and apply the damage.
    def check_hit(self, hazard):

        if hazard["state"] != "active" or hazard["hit"]:
            return

        # A warning is harmless; only active hazards can cause contact.
        if not self.is_player_in_hazard(hazard):
            return

        hazard["contact"] = True

        # Existing invincibility prevents another life from being lost.
        if self.invincible_ticks > 0:
            return

        # Register this hazard's hit only once.
        hazard["hit"] = True

        # A Web Shield absorbs the hit instead of losing a life.
        if self.shield_active:
            self.shield_active = False
            self.invincible_ticks = INVINCIBILITY_TICKS
            self.show_message("WEB SHIELD BLOCKED THE HIT!", 40)
            return

        # Apply damage and start approximately 1.5 seconds of invincibility.
        self.lives -= 1
        self.invincible_ticks = INVINCIBILITY_TICKS

        self.show_message("SPIDER-SENSE HIT! -1 LIFE", 40)

        # Finish the game when all lives are lost.
        if self.lives <= 0:
            self.game_over()

    # Use distance and range checks to determine whether the player is in a hazard.
    def is_player_in_hazard(self, hazard):

        x, y = hazard["position"]
        size = hazard["size"]

        # Pumpkin Bomb: the player's centre must be inside the circle.
        if hazard["type"] == "pumpkin":
            dx = self.player_x - x
            dy = self.player_y - y
            distance = math.sqrt(dx * dx + dy * dy)

            return distance <= size

        # Debris Rain: the player's centre must be inside the column.
        if hazard["type"] == "debris":
            left = x - size / 2
            right = x + size / 2

            return left <= self.player_x <= right

        # Goblin Glider Sweep: check whether the centre is inside the band.
        if hazard["type"] == "glider":
            top = y - size / 2
            bottom = y + size / 2

            return top <= self.player_y <= bottom

        return False

    # Award five points once when the player passes within 25 pixels of an edge.
    def check_close_call(self, hazard):

        if hazard["close_call_awarded"]:
            return

        # An attack that reaches the player's centre is not a close-call dodge.
        if self.is_player_in_hazard(hazard):
            return

        x, y = hazard["position"]
        size = hazard["size"]

        # Measure the distance from the player to the nearest hazard edge.
        if hazard["type"] == "pumpkin":
            dx = self.player_x - x
            dy = self.player_y - y
            distance = math.sqrt(dx * dx + dy * dy)
            edge_distance = abs(distance - size)

        elif hazard["type"] == "debris":
            left = x - size / 2
            right = x + size / 2

            if self.player_x < left:
                edge_distance = left - self.player_x
            else:
                edge_distance = self.player_x - right

        else:
            top = y - size / 2
            bottom = y + size / 2

            if self.player_y < top:
                edge_distance = top - self.player_y
            else:
                edge_distance = self.player_y - bottom

        # Award the bonus only once for this hazard.
        if 0 < edge_distance <= 25:
            hazard["close_call_awarded"] = True
            self.score += 5
            self.show_message("CLOSE CALL! +5", 40)

    # Spawn random power-ups, remove expired ones and detect collection.
    def update_powerups(self):

        # Randomly create a power-up when none is currently on the canvas.
        if self.powerup is None:

            # Approximately one spawn attempt every 6.6 seconds on average.
            if random.randint(1, 220) == 1:

                powerup_type = random.choice([
                    "shield",
                    "spider_time"
                ])

                position = (
                    random.randint(35, WIDTH - 35),
                    random.randint(35, HEIGHT - 35)
                )

                self.powerup = {
                    "type": powerup_type,
                    "position": position,
                    "timer": 6 * TICKS_PER_SECOND
                }

            return

        # Make an uncollected power-up disappear after about six seconds.
        self.powerup["timer"] -= 1

        x, y = self.powerup["position"]

        dx = self.player_x - x
        dy = self.player_y - y
        distance = math.sqrt(dx * dx + dy * dy)

        # Collect the power-up when the player reaches its position.
        if distance <= PLAYER_RADIUS + 12:

            collected_type = self.powerup["type"]
            self.collect_powerup(collected_type)
            self.powerup = None

        elif self.powerup["timer"] <= 0:
            self.powerup = None

    # Activate a Web Shield or Spider Time after the player collects it.
    def collect_powerup(self, powerup_type):

        if powerup_type == "shield":
            self.shield_active = True
            self.show_message("WEB SHIELD READY!", 40)

        elif powerup_type == "spider_time":
            self.spider_time_ticks = 5 * TICKS_PER_SECOND
            self.show_message("SPIDER TIME ACTIVATED!", 40)

    # Display a temporary message such as a close call or a successful dodge.
    def show_message(self, text, duration):
        self.message_text = text
        self.message_ticks = duration

    # Draw the opening screen, hazards, player, level and active power-ups.
    def draw_game(self):

        self.canvas.delete("all")

        # Update the score label outside the canvas.
        self.score_label.configure(text=f"Score: {self.score}")

        # Show filled hearts for remaining lives and empty hearts for lost lives.
        hearts = (
            ["♥"] * self.lives
            + ["♡"] * (INITIAL_LIVES - self.lives)
        )

        self.lives_label.configure(
            text=f"Lives: {' '.join(hearts)}"
        )

        # Display the opening screen before the game starts.
        if not self.started and not self.game_over_state:

            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 - 65,
                text="SPIDER-SENSE DODGE",
                fill="#67E8F9",
                font=("Arial", 25, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 - 15,
                text="Spider-Man vs. Green Goblin",
                fill="#F8FAFC",
                font=("Arial", 16, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 + 30,
                text="Dodge the attacks. Survive as long as possible!",
                fill="#CBD5E1",
                font=("Arial", 12)
            )

            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 + 75,
                text="PRESS ANY ARROW KEY TO START",
                fill="#FDE047",
                font=("Arial", 15, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 + 115,
                text="Move: Arrow Keys / WASD    Pause: P    Restart: R",
                fill="#94A3B8",
                font=("Arial", 10)
            )

            return

        # Draw all hazards that are not yet completed.
        for hazard in self.hazards:
            if hazard["state"] != "done":
                self.draw_hazard(hazard)

        # Draw any power-up waiting to be collected.
        if self.powerup is not None:
            self.draw_powerup()

        # Draw white spider-sense lines whenever a warning is active.
        warning_active = any(
            hazard["state"] == "warning"
            for hazard in self.hazards
        )

        if warning_active:
            self.draw_sense_lines()

        # Blink the player during invincibility.
        player_visible = (
            self.invincible_ticks <= 0
            or self.tick_count % 6 < 3
        )

        if player_visible:
            self.draw_player()

        # Display the current difficulty level in the top-left corner.
        level = self.get_level()

        self.canvas.create_text(
            12,
            12,
            text=f"LEVEL {level}",
            fill="#F8FAFC",
            anchor="nw",
            font=("Arial", 13, "bold")
        )

        # Display the currently active power-ups.
        active_effects = []

        if self.shield_active:
            active_effects.append("WEB SHIELD READY")

        if self.spider_time_ticks > 0:
            remaining_seconds = math.ceil(
                self.spider_time_ticks / TICKS_PER_SECOND
            )
            active_effects.append(
                f"SPIDER TIME: {remaining_seconds}s"
            )

        if active_effects:
            self.canvas.create_text(
                WIDTH / 2,
                14,
                text=" | ".join(active_effects),
                fill="#93C5FD",
                anchor="n",
                font=("Arial", 10, "bold")
            )

        # Display temporary messages near the bottom of the canvas.
        if self.message_ticks > 0:
            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT - 30,
                text=self.message_text,
                fill="#FDE047",
                font=("Arial", 17, "bold")
            )

        # Draw the pause or game-over screen when necessary.
        self.draw_overlays()

    # Draw the warning or active appearance of a particular hazard.
    def draw_hazard(self, hazard):

        hazard_type = hazard["type"]
        x, y = hazard["position"]
        size = hazard["size"]

        # Alternate warning colours to create a pulsing spider-sense effect.
        pulse = (self.tick_count // 5) % 2 == 0

        warning_fill = "#7F1D1D" if pulse else "#B91C1C"
        warning_outline = "#FCA5A5" if pulse else "#F87171"

        # Draw a Pumpkin Bomb warning circle or its orange explosion.
        if hazard_type == "pumpkin":

            if hazard["state"] == "warning":

                self.canvas.create_oval(
                    x - size,
                    y - size,
                    x + size,
                    y + size,
                    fill=warning_fill,
                    outline=warning_outline,
                    width=3,
                    stipple="gray50"
                )

                self.canvas.create_text(
                    x,
                    y,
                    text="WARNING",
                    fill="#FFFFFF",
                    font=("Arial", 10, "bold")
                )

            else:

                self.canvas.create_oval(
                    x - size,
                    y - size,
                    x + size,
                    y + size,
                    fill="#F97316",
                    outline="#FDE047",
                    width=3
                )

                self.canvas.create_oval(
                    x - size * 0.65,
                    y - size * 0.65,
                    x + size * 0.65,
                    y + size * 0.65,
                    outline="#FDBA74",
                    width=3
                )

                self.canvas.create_text(
                    x,
                    y,
                    text="BOOM!",
                    fill="#7C2D12",
                    font=("Arial", 12, "bold")
                )

        # Draw a vertical warning column or falling grey debris.
        elif hazard_type == "debris":

            left = x - size / 2
            right = x + size / 2

            if hazard["state"] == "warning":

                self.canvas.create_rectangle(
                    left,
                    0,
                    right,
                    HEIGHT,
                    fill=warning_fill,
                    outline=warning_outline,
                    width=3,
                    stipple="gray50"
                )

                self.canvas.create_text(
                    x,
                    35,
                    text="DEBRIS WARNING",
                    fill="#FFFFFF",
                    font=("Arial", 10, "bold")
                )

            else:

                # Fill the dangerous column with grey rocks.
                self.canvas.create_rectangle(
                    left,
                    0,
                    right,
                    HEIGHT,
                    fill="#475569",
                    outline="#CBD5E1",
                    width=2
                )

                # Place rocks at fixed positions to keep them from flickering.
                for i in range(7):

                    rock_y = 35 + i * 58

                    if i % 2 == 0:
                        rock_x = x - size * 0.18
                    else:
                        rock_x = x + size * 0.18

                    half_width = size * 0.22
                    half_height = 15

                    points = [
                        rock_x - half_width,
                        rock_y - half_height,
                        rock_x - half_width * 0.7,
                        rock_y - half_height * 1.2,
                        rock_x + half_width * 0.6,
                        rock_y - half_height,
                        rock_x + half_width,
                        rock_y + half_height * 0.3,
                        rock_x,
                        rock_y + half_height,
                        rock_x - half_width,
                        rock_y + half_height * 0.3
                    ]

                    self.canvas.create_polygon(
                        *points,
                        fill="#94A3B8" if i % 2 == 0 else "#64748B",
                        outline="#CBD5E1",
                        width=2
                    )

        # Draw the horizontal warning band or the moving Green Goblin glider.
        elif hazard_type == "glider":

            top = y - size / 2
            bottom = y + size / 2

            if hazard["state"] == "warning":

                self.canvas.create_rectangle(
                    0,
                    top,
                    WIDTH,
                    bottom,
                    fill=warning_fill,
                    outline=warning_outline,
                    width=3,
                    stipple="gray50"
                )

                self.canvas.create_text(
                    WIDTH / 2,
                    y,
                    text="GLIDER SWEEP WARNING",
                    fill="#FFFFFF",
                    font=("Arial", 11, "bold")
                )

            else:

                # Mark the full danger band.
                self.canvas.create_rectangle(
                    0,
                    top,
                    WIDTH,
                    bottom,
                    fill="#052E16",
                    outline="#16A34A",
                    width=2
                )

                # Move the bright green glider streak across the canvas.
                glider_x = (
                    self.tick_count * 18
                ) % (WIDTH + 100) - 50

                self.canvas.create_line(
                    max(0, glider_x - 50),
                    y,
                    min(WIDTH, glider_x + 50),
                    y,
                    fill="#4ADE80",
                    width=8
                )

                # Draw a small diamond-shaped glider.
                self.canvas.create_polygon(
                    glider_x - 20, y,
                    glider_x, y - 10,
                    glider_x + 20, y,
                    glider_x, y + 10,
                    fill="#22C55E",
                    outline="#BBF7D0",
                    width=2
                )

    # Draw Spider-Man using simple Canvas shapes and lines.
    def draw_player(self):

        x = self.player_x
        y = self.player_y

        # A blue ring indicates that the Web Shield is ready.
        if self.shield_active:

            self.canvas.create_oval(
                x - 23,
                y - 23,
                x + 23,
                y + 23,
                outline="#38BDF8",
                width=3
            )

        # Draw blue arms and legs behind the red body.
        self.canvas.create_line(
            x - 7, y + 1,
            x - 17, y + 8,
            fill="#2563EB",
            width=5
        )

        self.canvas.create_line(
            x + 7, y + 1,
            x + 17, y + 8,
            fill="#2563EB",
            width=5
        )

        self.canvas.create_line(
            x - 5, y + 8,
            x - 11, y + 20,
            fill="#2563EB",
            width=5
        )

        self.canvas.create_line(
            x + 5, y + 8,
            x + 11, y + 20,
            fill="#2563EB",
            width=5
        )

        # Draw the red circular body and head.
        self.canvas.create_oval(
            x - PLAYER_RADIUS,
            y - PLAYER_RADIUS,
            x + PLAYER_RADIUS,
            y + PLAYER_RADIUS,
            fill="#DC2626",
            outline="#FCA5A5",
            width=2
        )

        # Draw the two white eyes.
        self.canvas.create_oval(
            x - 8, y - 5,
            x - 2, y + 2,
            fill="#FFFFFF",
            outline="#FFFFFF"
        )

        self.canvas.create_oval(
            x + 2, y - 5,
            x + 8, y + 2,
            fill="#FFFFFF",
            outline="#FFFFFF"
        )

    # Draw short white lines around the player whenever a warning is active.
    def draw_sense_lines(self):

        x = self.player_x
        y = self.player_y - 2

        # Draw eight short lines at different angles around the head.
        for angle_degrees in range(0, 360, 45):

            angle = math.radians(angle_degrees)

            inner_radius = PLAYER_RADIUS + 5
            outer_radius = PLAYER_RADIUS + 13

            x1 = x + math.cos(angle) * inner_radius
            y1 = y + math.sin(angle) * inner_radius

            x2 = x + math.cos(angle) * outer_radius
            y2 = y + math.sin(angle) * outer_radius

            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#FFFFFF",
                width=2
            )

    # Draw a blue Web Shield circle or a yellow Spider Time star.
    def draw_powerup(self):

        powerup_type = self.powerup["type"]
        x, y = self.powerup["position"]

        if powerup_type == "shield":

            self.canvas.create_oval(
                x - 12,
                y - 12,
                x + 12,
                y + 12,
                fill="#0284C7",
                outline="#7DD3FC",
                width=3
            )

            self.canvas.create_text(
                x,
                y + 23,
                text="WEB SHIELD",
                fill="#7DD3FC",
                font=("Arial", 8, "bold")
            )

        else:

            # Calculate alternating outer and inner points for a five-point star.
            points = []

            for i in range(10):

                angle = -math.pi / 2 + i * math.pi / 5

                if i % 2 == 0:
                    radius = 15
                else:
                    radius = 7

                point_x = x + math.cos(angle) * radius
                point_y = y + math.sin(angle) * radius

                points.extend([point_x, point_y])

            self.canvas.create_polygon(
                *points,
                fill="#FACC15",
                outline="#FEF08A",
                width=2
            )

            self.canvas.create_text(
                x,
                y + 25,
                text="SPIDER TIME",
                fill="#FDE047",
                font=("Arial", 8, "bold")
            )

    # Draw the pause screen or the game-over box over the playing area.
    def draw_overlays(self):

        if self.paused and not self.game_over_state:

            self.canvas.create_rectangle(
                190, 160,
                510, 290,
                fill="#020617",
                outline="#67E8F9",
                width=3
            )

            self.canvas.create_text(
                WIDTH / 2,
                200,
                text="PAUSED",
                fill="#FDE047",
                font=("Arial", 25, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                245,
                text="Press P to resume",
                fill="#F8FAFC",
                font=("Arial", 13)
            )

        # Show the final score and high score after losing all lives.
        if self.game_over_state:

            self.canvas.create_rectangle(
                140, 115,
                560, 335,
                fill="#020617",
                outline="#F43F5E",
                width=4
            )

            self.canvas.create_text(
                WIDTH / 2,
                155,
                text="GAME OVER",
                fill="#F87171",
                font=("Arial", 27, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                205,
                text=f"Final Score: {self.score}",
                fill="#FDE047",
                font=("Arial", 16, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                240,
                text=f"High Score: {self.high_score}",
                fill="#67E8F9",
                font=("Arial", 15, "bold")
            )

            self.canvas.create_text(
                WIDTH / 2,
                290,
                text="Press R or click RESTART GAME",
                fill="#F8FAFC",
                font=("Arial", 11)
            )

    # Calculate the current level from the score.
    def get_level(self):
        return self.score // 100 + 1

    # Calculate warning duration, shortening it as the level increases.
    def get_warning_ticks(self):
        return max(
            MIN_WARNING_TICKS,
            INITIAL_WARNING_TICKS - (self.get_level() - 1)
        )

    # Calculate the spawn interval, with a minimum interval at higher levels.
    def get_spawn_interval(self):
        return max(
            35,
            95 - (self.get_level() - 1) * 8
        )

    # Allow more simultaneous hazards at higher difficulty levels.
    def get_max_hazards(self):

        level = self.get_level()

        if level >= 4:
            return 3

        if level >= 2:
            return 2

        return 1

    # Stop gameplay, preserve the high score and prepare the game-over screen.
    def game_over(self):

        if self.game_over_state:
            return

        self.game_over_state = True
        self.paused = False
        self.keys_pressed.clear()

        # Keep the best score achieved during this program session.
        self.high_score = max(self.high_score, self.score)

    # Cancel any pending callback and reset all game variables for a new game.
    def restart(self):

        # Cancel the previous timer before scheduling another one.
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        # Reset score, lives and player position.
        self.score = 0
        self.lives = INITIAL_LIVES

        self.player_x = WIDTH / 2
        self.player_y = HEIGHT / 2

        # Clear all hazards and pressed keys.
        self.hazards = []
        self.keys_pressed = set()

        # Reset the game state.
        self.started = False
        self.paused = False
        self.game_over_state = False

        # Reset timers and counters.
        self.tick_count = 0
        self.survival_ticks = 0
        self.spawn_timer = self.get_spawn_interval()
        self.invincible_ticks = 0

        # Reset power-ups without changing the high score.
        self.shield_active = False
        self.spider_time_ticks = 0
        self.powerup = None

        # Remove temporary messages.
        self.message_text = ""
        self.message_ticks = 0

        # Clear old graphics and show the opening screen.
        self.canvas.delete("all")
        self.draw_game()

        # Allow keyboard input immediately.
        self.canvas.focus_set()

        # Start exactly one new game loop.
        self.after_id = self.root.after(
            FPS_DELAY,
            self.game_loop
        )


# -------------------- START THE GAME --------------------

root = tk.Tk()
game = SpiderSenseGame(root)
root.mainloop()