import json
import os
import sys
import re
import urllib.parse
from base64 import b64decode
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import requests
import api_client
from login_manager import AuthWindow
from PIL import Image, ImageTk, ImageDraw

# НАСТРОЙКИ
USER = "AgeInYear236"
REPO = "GameTierEngine"
CURRENT_VERSION = "v1.0.1"  # Текущая версия (меняйте при каждом новом билде)

# --- Инициализация токена (если передан) ---
if len(sys.argv) > 1:
    passed_token = sys.argv[1]
    if passed_token != "None":
        api_client.TOKEN = passed_token

# --- Константы для Калькулятора ---
CRITERIA = {
    "Gameplay": 4.0,
    "Graphics": 2.0,
    "Storyline": 3.0,
    "Music": 1.5,
    "Hardware": 1.5,
}

HELP_TEXTS = {
    "Gameplay": "How fun, responsive, and engaging the game mechanics are.\n\nWeight: 4.0x (Highest impact on final score).",
    "Graphics": "Visual quality, art style, animations, and aesthetic appeal.\n\nWeight: 2.0x.",
    "Storyline": "Plot, lore, character development, and writing quality.\n\nWeight: 3.0x.",
    "Music": "Soundtrack, sound effects, voice acting, and audio immersion.\n\nWeight: 1.5x.",
    "Hardware": "Optimization, performance, loading times, and bug-free state.\n\nWeight: 1.5x.",
    "Personal Score": "Your subjective enjoyment (1 to 5 scale).\n\n⚠️ Hard Restrictions:\n• 4 to 5: No restrictions (can be any tier).\n• 3: Capped at MAX 'B' Tier.\n• 1 to 2: Capped below B (MAX 'C' Tier).",
}

MAX_SCORE = 120
DATA_FILE = "games_tier_list.json"

# --- Константы для Просмотрщика ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CACHE_DIR = os.path.join(BASE_DIR, "image_cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

ZYTE_API_KEY = "4f8503c475894371ab356e15558c65d9"
TIER_COLORS = {
    "S": "#ff7f7f", "A": "#ffbf7f", "B": "#ffff7f",
    "C": "#bfff7f", "D": "#7fff7f", "F": "#7f7fff",
}
TIERS_ORDER = ["S", "A", "B", "C", "D", "F"]


# =========================================================================
# 1. СТРУКТУРА КАЛЬКУЛЯТОРА
# =========================================================================
class GameCalculatorWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Game Tier List Calculator")
        self.window.geometry("480x850")
        self.window.resizable(True, True)
        
        self.current_calculation = {}

        # Game Name Input
        frame_name = tk.LabelFrame(self.window, text=" Game Details ", padx=10, pady=10)
        frame_name.pack(fill="x", padx=15, pady=10)

        tk.Label(frame_name, text="Game Name:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_name = tk.Entry(frame_name, font=("Arial", 11))
        self.entry_name.pack(fill="x", pady=5)

        # Criteria Sliders
        frame_criteria = tk.LabelFrame(self.window, text=" Criteria (0 - 10) ", padx=10, pady=10)
        frame_criteria.pack(fill="x", padx=15, pady=5)

        self.sliders = {}
        for criterion, multiplier in CRITERIA.items():
            header_frame = tk.Frame(frame_criteria)
            header_frame.pack(fill="x", pady=(5, 0))

            lbl_text = f"{criterion} (x{multiplier}):"
            tk.Label(header_frame, text=lbl_text, font=("Arial", 9, "bold")).pack(side="left")

            btn_help = tk.Button(
                header_frame, text="?", font=("Arial", 8, "bold"), width=2, height=1, bd=1, relief="solid", bg="#e1e1e1",
                command=lambda c=criterion: self.show_help(c, HELP_TEXTS[c]),
            )
            btn_help.pack(side="right")

            slider = tk.Scale(frame_criteria, from_=0, to=10, orient="horizontal", resolution=0.5)
            slider.set(5)
            slider.pack(fill="x", pady=(0, 10))
            self.sliders[criterion] = slider

        # Personal Score Dropdown Section
        frame_personal = tk.LabelFrame(self.window, text=" Personal Preference ", padx=10, pady=5)
        frame_personal.pack(fill="x", padx=15, pady=5)

        personal_sub_frame = tk.Frame(frame_personal)
        personal_sub_frame.pack(fill="x", pady=5)

        tk.Label(personal_sub_frame, text="Personal Score (1 to 5):", font=("Arial", 9)).pack(side="left", padx=5)

        self.var_personal = tk.StringVar(value="5")
        self.dropdown_personal = ttk.Combobox(
            personal_sub_frame, textvariable=self.var_personal, values=["1", "2", "3", "4", "5"], width=5, state="readonly"
        )
        self.dropdown_personal.pack(side="left", padx=5)

        btn_help_p = tk.Button(
            personal_sub_frame, text="?", font=("Arial", 8, "bold"), width=2, bd=1, relief="solid", bg="#e1e1e1",
            command=lambda: self.show_help("Personal Score", HELP_TEXTS["Personal Score"]),
        )
        btn_help_p.pack(side="right", padx=5)

        # Action Buttons Layout (Side-by-Side)
        frame_buttons = tk.Frame(self.window)
        frame_buttons.pack(fill="x", padx=15, pady=15)

        self.btn_calculate = tk.Button(
            frame_buttons, text="⚙️ Calculate Tier", font=("Arial", 11, "bold"), bg="#007acc", fg="white",
            command=self.calculate_tier, pady=10
        )
        self.btn_calculate.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_save = tk.Button(
            frame_buttons, text="💾 Save Game", font=("Arial", 11, "bold"), bg="#6c757d", fg="white",
            command=self.save_to_json, state="disabled", pady=10
        )
        self.btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Result Display
        frame_result = tk.LabelFrame(self.window, text=" Result Preview ", padx=10, pady=10)
        frame_result.pack(fill="both", expand=True, padx=15, pady=10)

        self.lbl_result = tk.Label(frame_result, text="Enter a game and click Calculate", font=("Arial", 11, "italic"), justify="left")
        self.lbl_result.pack(anchor="w")

    def show_help(self, title, message):
        messagebox.showinfo(f"About {title}", message)

    def determine_tier(self, total_score, personal_score):
        if total_score >= 100: tier = "S"
        elif total_score >= 80: tier = "A"
        elif total_score >= 60: tier = "B"
        elif total_score >= 40: tier = "C"
        elif total_score >= 20: tier = "D"
        else: tier = "F"

        if personal_score == 3 and tier in ["S", "A"]: tier = "B"
        elif personal_score in [1, 2] and tier in ["S", "A", "B"]: tier = "C"
        return tier

    def calculate_tier(self):
        game_name = self.entry_name.get().strip()
        if not game_name:
            messagebox.showerror("Error", "Please enter a game name first.")
            return

        criteria_scores = {}
        total_score = 0.0
        for criterion, multiplier in CRITERIA.items():
            slider_value = self.sliders[criterion].get()
            criteria_scores[criterion] = slider_value
            total_score += slider_value * multiplier

        personal_score = int(self.var_personal.get())
        tier = self.determine_tier(total_score, personal_score)

        result_text = f"Total Score: {total_score:.1f}/{MAX_SCORE}\nPersonal Score: {personal_score}/5\nAssigned Tier: {tier}"
        self.lbl_result.config(text=result_text, fg="#0056b3")

        self.current_calculation = {
            "game_name": game_name,
            "criteria_scores": criteria_scores,
            "personal_score": personal_score,
            "calculated_score": round(total_score, 1),
            "tier": tier,
        }
        self.btn_save.config(state="normal", bg="#28a745")

    def save_to_db(self, game_name, scores, final_score, tier):
        payload = {
            "game_name": game_name,
            "criteria_scores": scores,
            "calculated_score": final_score,
            "tier": tier
        }
        api_client.save_game_to_db(payload)

    def save_to_json(self):
        if not self.current_calculation:
            messagebox.showerror("Error", "Please calculate the score first.")
            return

        try:
            if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    games_list = json.load(f)
            else:
                games_list = []

            games_list.append(self.current_calculation)

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(games_list, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Success", f"Successfully saved '{self.current_calculation['game_name']}' to {DATA_FILE}!")

            game_name = self.current_calculation.get("game_name")
            scores = self.current_calculation.get("criteria_scores")
            final_score = self.current_calculation.get("calculated_score")
            tier = self.current_calculation.get("tier")

            self.save_to_db(game_name, scores, final_score, tier)

            self.entry_name.delete(0, tk.END)
            self.lbl_result.config(text="Enter a game and click Calculate", fg="black")
            self.btn_save.config(state="disabled", bg="#6c757d")
            self.current_calculation = {}

        except Exception as e:
            messagebox.showerror("File Error", f"Could not save data: {e}")


# =========================================================================
# 2. СТРУКТУРА ПРОСМОТРЩИКА ТИР-ЛИСТОВ
# =========================================================================
class TierListViewerWindow:
    def __init__(self, parent, selected_profile=None):
        self.window = tk.Toplevel(parent)
        self.selected_profile = selected_profile
        
        if self.selected_profile:
            self.window.title(f"🏆 {self.selected_profile}'s Tier List Board")
        else:
            self.window.title("🏆 Visual Wrapped Tier List Board")
            
        self.window.geometry("1100x800")
        self.window.configure(bg="#1a1a1a")

        self.context_menu = tk.Menu(self.window, tearoff=0, bg="#2a2a2a", fg="white", activebackground="#007acc")
        self.selected_game_to_delete = None
        self.image_references = {}

        # Top Control Bar
        self.control_frame = tk.Frame(self.window, bg="#2a2a2a", pady=10, padx=15)
        self.control_frame.pack(fill="x")

        tk.Label(self.control_frame, text="Filter Game:", font=("Arial", 11, "bold"), bg="#2a2a2a", fg="white").pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.draw_tier_list())
        self.search_entry = tk.Entry(
            self.control_frame, textvariable=self.search_var, font=("Arial", 11),
            bg="#3a3a3a", fg="white", insertbackground="white", bd=1, relief="solid", width=22
        )
        self.search_entry.pack(side="left", padx=5)

        # Main Layout Frames
        self.canvas_frame = tk.Frame(self.window, bg="#121212")
        self.canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.v_scroll.pack(side="right", fill="y")

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", bd=0, highlightthickness=0, yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill="both", expand=True)
        self.v_scroll.config(command=self.canvas.yview)

        # Lower Component: Live Debug Terminal Console
        self.debug_frame = tk.LabelFrame(self.window, text=" 🖥️ Live Zyte & DuckDuckGo API Debug Terminal Logs ", bg="#1a1a1a", fg="#00ffcc", font=("Arial", 9, "bold"), padx=10, pady=5)
        self.debug_frame.pack(fill="x", side="bottom", padx=15, pady=(0, 15))

        self.log_console = scrolledtext.ScrolledText(self.debug_frame, height=8, bg="#0a0a0a", fg="#dcdcdc", font=("Courier New", 10), insertbackground="white", relief="solid", bd=1)
        self.log_console.pack(fill="both", expand=True)
        
        self.log_debug("SYSTEM: Initialization Complete. Standing by to draw cached assets...")

        self.games_data = []
        self.load_and_draw(target_username=self.selected_profile)

    def log_debug(self, message):
        self.log_console.insert(tk.END, f"{message}\n")
        self.log_console.see(tk.END)
        self.window.update_idletasks()

    def load_and_draw(self, target_username=None):
        if target_username:
            self.log_debug(f"🌐 [NETWORK] Fetching public profile data for user: {target_username}")
            try:
                encoded_user = urllib.parse.quote(target_username)
                response = requests.get(f"{api_client.BASE_URL}/get_user_games/{encoded_user}", timeout=5)
                if response.status_code == 200: self.games_data = response.json()
                else: self.games_data = []
            except Exception as e:
                self.log_debug(f"❌ Error downloading profile data: {e}")
                self.games_data = []
        else:
            self.log_debug("🌐 [NETWORK] Fetching game data for logged-in session user...")
            self.games_data = api_client.fetch_games_from_db()
        
        if not self.games_data:
            self.canvas.delete("all")
            display_msg = f"No profile dataset entries found for user '{target_username}'." if target_username else "No games found in database.\nAdd new entries via the Calculator."
            self.canvas.create_text(500, 200, text=display_msg, fill="#888888", font=("Arial", 13, "italic"), justify="center")
            return

        self.log_debug(f"✅ [SUCCESS] Loaded {len(self.games_data)} game entries.")
        self.download_missing_images_via_zyte()
        self.draw_tier_list()

    def download_missing_images_via_zyte(self):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        for game in self.games_data:
            raw_game_name = game.get("game_name", "").strip()
            if not raw_game_name: continue

            game_name = raw_game_name
            if game_name.upper() == "GTA V" or game_name.upper() == "GTA 5":
                game_name = "Grand Theft Auto V"
            elif "GTA" in game_name.upper():
                game_name = game_name.upper().replace("GTA", "Grand Theft Auto")

            safe_name = re.sub(r'[\\/*?:"<>|]', "", raw_game_name)
            final_path = os.path.join(CACHE_DIR, f"{safe_name}.png")

            if os.path.exists(final_path): continue 

            self.log_debug(f"🔍 [API LOGO FETCH] Requesting high-res asset for: '{raw_game_name}'") 
            image_saved = False

            try:
                encoded_query = urllib.parse.quote(game_name) 
                steam_search_url = f"https://store.steampowered.com/api/storesearch/?term={encoded_query}&l=english&cc=US"
                response = requests.get(steam_search_url, timeout=8)
                
                if response.status_code == 200:
                    search_data = response.json()
                    items = search_data.get("items", [])
                    
                    if items:
                        best_match = items[0]
                        app_id = best_match.get("id")
                        matched_title = best_match.get("name")
                        self.log_debug(f"   🎯 Match Found: {matched_title} (AppID: {app_id})")
                        
                        direct_img_url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
                        img_response = requests.get(direct_img_url, timeout=10)

                        if img_response.status_code == 200 and img_response.content:
                            with open(final_path, "wb") as f: 
                                f.write(img_response.content) 
                            image_saved = True
                            self.log_debug(f"   ✅ Image downloaded successfully!")
                    else:
                        self.log_debug(f"   ⚠️ No matches found on Steam for '{game_name}'")

            except Exception as e:
                self.log_debug(f"   💥 [EXCEPTION ENCOUNTERED]: {e}")

            if not image_saved:
                try:
                    self.log_debug(f"   🎨 Generating fallback placeholder for '{raw_game_name}'")
                    fallback_img = Image.new('RGB', (460, 215), color='#2c3e50')
                    draw = ImageDraw.Draw(fallback_img) 
                    letter = safe_name[0].upper() if safe_name else "?" 
                    draw.text((230, 107), letter, fill="#00ffcc", anchor="mm", font_size=60)
                    fallback_img.save(final_path, "PNG") 
                except Exception: pass 

    def get_game_image(self, game_name):
        safe_name = re.sub(r'[\\/*?:"<>|]', "", game_name).strip()
        img_path = os.path.join(CACHE_DIR, f"{safe_name}.png")
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img = img.resize((50, 50), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception: pass
        return None

    def show_context_menu(self, event, game_name):
        if self.selected_profile: return 
        self.selected_game_to_delete = game_name
        self.context_menu.delete(0, tk.END)
        self.context_menu.add_command(label=f"❌ Delete '{game_name}'", command=self.confirm_and_delete_game)
        self.context_menu.post(event.x_root, event.y_root)

    def confirm_and_delete_game(self):
        if not self.selected_game_to_delete: return
        confirm = messagebox.askyesno("Confirm Deletion", f"Permanently remove '{self.selected_game_to_delete}' from DB?")
        if confirm:
            success, message = api_client.delete_game_from_db(self.selected_game_to_delete)
            if success:
                self.log_debug(f"🗑️ [DB TRANSACTION] Purged: '{self.selected_game_to_delete}'")
                self.load_and_draw(target_username=self.selected_profile) 
            else:
                messagebox.showerror("Delete Error", message)
        self.selected_game_to_delete = None

    def draw_tier_list(self):
        self.canvas.delete("all")
        self.image_references.clear()
        filter_keyword = self.search_var.get().strip().lower()

        tier_groups = {tier: [] for tier in TIERS_ORDER}
        for game in self.games_data:
            name = game.get("game_name", "Unknown Game")
            tier = game.get("tier", "F")
            if filter_keyword and filter_keyword not in name.lower(): continue
            if tier in tier_groups: tier_groups[tier].append(game)

        current_y = 10
        row_min_height = 70
        max_width = 1040
        card_width = 165

        for tier in TIERS_ORDER:
            games_in_tier = tier_groups[tier]
            x_offset = 85
            tier_start_y = current_y
            
            for game in games_in_tier:
                if x_offset + card_width > max_width - 10:
                    x_offset = 85
                    current_y += row_min_height
                
                display_name = game["game_name"]
                calc_score = game.get("calculated_score", 0.0)
                
                tk_img = self.get_game_image(display_name)
                tag_id = f"game_{display_name.replace(' ', '_')}"
                
                self.canvas.create_rectangle(
                    x_offset, current_y + 5, x_offset + card_width, current_y + row_min_height - 5,
                    fill="#262626", outline="#444444", width=1, tags=tag_id
                )

                if tk_img:
                    img_key = f"img_{tier}_{display_name}_{x_offset}_{current_y}"
                    self.image_references[img_key] = tk_img
                    self.canvas.create_image(x_offset + 5, current_y + 7, anchor="nw", image=tk_img, tags=tag_id)

                short_name = display_name if len(display_name) <= 14 else display_name[:11] + "..."
                self.canvas.create_text(x_offset + 60, current_y + 18, text=short_name, fill="#ffffff", font=("Arial", 9, "bold"), anchor="nw", tags=tag_id)
                self.canvas.create_text(x_offset + 60, current_y + 36, text=f"Score: {calc_score}", fill="#aaaaaa", font=("Arial", 8), anchor="nw", tags=tag_id)

                if not self.selected_profile:
                    self.canvas.tag_bind(tag_id, "<Button-3>", lambda e, name=display_name: self.show_context_menu(e, name))
                    self.canvas.tag_bind(tag_id, "<Button-2>", lambda e, name=display_name: self.show_context_menu(e, name))

                x_offset += card_width + 10

            tier_end_y = current_y + row_min_height - 5
            self.canvas.create_rectangle(0, tier_start_y, 70, tier_end_y, fill=TIER_COLORS[tier], outline="#333333")
            self.canvas.create_text(35, (tier_start_y + tier_end_y) // 2, text=tier, font=("Arial", 22, "bold"), fill="#111111")
            self.canvas.create_rectangle(70, tier_start_y, max_width, tier_end_y, fill="", outline="#252525")
            self.canvas.tag_lower(self.canvas.create_rectangle(70, tier_start_y, max_width, tier_end_y, fill="#151515", outline=""))
            current_y = tier_end_y + 10

        self.canvas.config(scrollregion=(0, 0, max_width, current_y + 20))


# =========================================================================
# 3. ОСНОВНОЙ ЛАУНЧЕР (Панель Управления)
# =========================================================================
class GameHubLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Game Evaluation & Tier List Hub")
        self.root.geometry("500x620") # Слегка увеличили высоту под блок обновлений
        self.root.configure(bg="#141414")
        self.root.resizable(True, True)
        if os.path.exists("/app_icon.ico"):
            self.root.iconbitmap("/app_icon.ico")

        # Header
        self.header_frame = tk.Frame(self.root, bg="#1e1e1e", pady=20)
        self.header_frame.pack(fill="x")
        tk.Label(self.header_frame, text="GAME RANKING ENGINE", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00ffcc").pack()
        tk.Label(self.header_frame, text="Central Management Suite", font=("Arial", 10, "italic"), bg="#1e1e1e", fg="#888888").pack(pady=(2, 0))

        self.lbl_user_status = tk.Label(self.root, text="Not logged in", font=("Arial", 10, "bold"), bg="#1a1a1a", fg="#888888")
        self.lbl_user_status.pack(anchor="nw", padx=10, pady=5)

        # Buttons Container
        self.button_container = tk.Frame(self.root, bg="#141414", pady=15)
        self.button_container.pack(fill="both", expand=True, padx=40)

        self.btn_calc = tk.Button(
            self.button_container, text="➕ Rank & Log New Game Entry", font=("Arial", 12, "bold"),
            bg="#2b2b2b", fg="white", activebackground="#007acc", activeforeground="white",
            bd=1, relief="solid", pady=10, command=self.launch_calculator
        )
        self.btn_calc.pack(fill="x", pady=5)

        self.btn_viewer = tk.Button(
            self.button_container, text="🏆 Open Tier List Board", font=("Arial", 12, "bold"),
            bg="#2b2b2b", fg="white", activebackground="#27ae60", activeforeground="white",
            bd=1, relief="solid", pady=10, command=self.launch_viewer
        )
        self.btn_viewer.pack(fill="x", pady=5)

        self.btn_auth = tk.Button(self.button_container, text="👤 Login / Register Account", font=("Arial", 10), bg="#00bd10", fg="white", command=self.open_auth)
        self.btn_auth.pack(fill="x", pady=5)

        self.btn_users = tk.Button(self.button_container, text="👥 View All Users", font=("Arial", 12, "bold"), bg="#2b2b2b", fg="white", command=self.open_user_directory)
        self.btn_users.pack(fill="x", pady=5)

        self.btn_explore = tk.Button(self.button_container, text="🔍 Explore Games", font=("Arial", 12), bg="#4a4a4a", fg="white", command=self.open_explorer)
        self.btn_explore.pack(fill="x", pady=5)

        # --- UPDATE SECTION ---
        # Теперь все элементы аккуратно упакованы внутрь button_container лаунчера
        self.version_label = tk.Label(
            self.button_container, text=f"Application Version: {CURRENT_VERSION}", font=("Arial", 10), bg="#141414", fg="#aaaaaa"
        )
        self.version_label.pack(pady=(15, 0))

        self.update_button = tk.Button(
            self.button_container,
            text="Check for Updates",
            command=lambda: GameUpdater.check_updates(self.root, self.status_label),
            font=("Arial", 10, "bold"),
            bg="#238636",
            fg="white",
            padx=10,
            pady=5,
            bd=0
        )
        self.update_button.pack(pady=5)

        self.status_label = tk.Label(self.button_container, text="", font=("Arial", 9), fg="gray", bg="#141414")
        self.status_label.pack(pady=5)

        # Status Bar
        self.status_bar = tk.Frame(self.root, bg="#1e1e1e", pady=8, padx=10)
        self.status_bar.pack(fill="x", side="bottom")
        self.lbl_status = tk.Label(self.status_bar, text="Ready to launch subsystems.", font=("Arial", 9), bg="#1e1e1e", fg="#aaaaaa")
        self.lbl_status.pack(side="left")

        self.check_login_status()

    def check_login_status(self):
        user = api_client.get_current_user()
        if user:
            self.lbl_user_status.config(text=f"Logged in as: {user}", fg="#00ffcc")
        self.root.after(1000, self.check_login_status)

    def open_user_directory(self):
        from user_directory import UserDirectory
        UserDirectory(self.root)

    def open_explorer(self):
        from game_explorer import GameExplorer
        GameExplorer(self.root)

    def open_auth(self):
        AuthWindow(self.root, lambda: self.lbl_status.config(text="✅ Authenticated.", fg="#00ffcc"))

    def launch_calculator(self):
        if api_client.TOKEN is None:
            AuthWindow(self.root, lambda: GameCalculatorWindow(self.root))
        else:
            GameCalculatorWindow(self.root)
        self.lbl_status.config(text="✅ Game Calculator opened.", fg="#aaaaaa")

    def launch_viewer(self):
        if api_client.TOKEN is None:
            AuthWindow(self.root, lambda: TierListViewerWindow(self.root))
        else:
            TierListViewerWindow(self.root)
        self.lbl_status.config(text="✅ Tier List Board opened.", fg="#aaaaaa")


# =========================================================================
# 4. СТРУКТУРА ОБНОВЛЕНИЙ (ИСПРАВЛЕНА СВЯЗЬ GUI И ОШИБКА PYINSTALLER DLL)
# =========================================================================
class GameUpdater:
    @staticmethod
    def check_updates(root_win, status_lbl):
        url = f"https://api.github.com/repos/{USER}/{REPO}/releases/latest"
        status_lbl.config(text="Checking for updates...", fg="yellow")
        root_win.update()

        try:
            response = requests.get(url)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"]

                if latest_version != CURRENT_VERSION:
                    status_lbl.config(text="Update available!", fg="#00ffcc")
                    answer = messagebox.askyesno(
                        "Update Available",
                        f"A new version ({latest_version}) is available.\n"
                        f"Current version: {CURRENT_VERSION}\n\n"
                        f"Do you want to download and install it now?",
                    )

                    if answer:
                        download_url = None
                        for asset in release_data["assets"]:
                            if asset["name"].endswith(".exe"):
                                download_url = asset["browser_download_url"]
                                break

                        if download_url:
                            GameUpdater.download_and_install(download_url, root_win, status_lbl)
                        else:
                            status_lbl.config(text="No exe asset found", fg="red")
                            messagebox.showerror(
                                "Error", "No .exe asset found in the latest GitHub release."
                            )
                    else:
                        status_lbl.config(text="Update canceled", fg="gray")
                else:
                    status_lbl.config(text="App is up to date", fg="green")
                    messagebox.showinfo(
                        "Up to Date", "You are already using the latest version."
                    )
            else:
                status_lbl.config(text="Check failed", fg="red")
                messagebox.showerror(
                    "Error", "Failed to fetch release data from GitHub."
                )

        except Exception as e:
            status_lbl.config(text="Error occurred", fg="red")
            messagebox.showerror("Error", f"An error occurred: {e}")

    @staticmethod
    def download_and_install(url, root_win, status_lbl):
        try:
            current_exe = os.path.abspath(sys.executable)
            exe_dir = os.path.dirname(current_exe)
            temp_exe = os.path.join(exe_dir, "update_temp.exe")

            status_lbl.config(text="Downloading update...", fg="yellow")
            root_win.update()

            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(temp_exe, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            status_lbl.config(text="Installing update...", fg="yellow")
            root_win.update()

            exe_name = os.path.basename(current_exe)

            # НОВАЯ КОМАНДА:
            # 1. timeout /t 1 -> Ждем 1 секунду, чтобы команда запустилась в фоне
            # 2. taskkill -> Жестко убиваем старый процесс по имени (это предотвратит вызов деструкторов PyInstaller и уберет ошибку DLL)
            # 3. timeout /t 2 -> Ждем 2 секунды, чтобы ОС полностью освободила файл
            # 4. del и move -> Безопасно меняем файлы
            # 5. start -> Запускаем новую версию
            cmd_command = (
                f'timeout /t 1 && '
                f'taskkill /f /im "{exe_name}" && '
                f'timeout /t 2 && '
                f'del /f /q "{current_exe}" && '
                f'move "{temp_exe}" "{current_exe}" && '
                f'start "" "{current_exe}"'
            )

            subprocess.Popen(
                cmd_command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            root_win.withdraw()

        except Exception as e:
            status_lbl.config(text="Update failed", fg="red")
            messagebox.showerror("Error", f"Failed to install update: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameHubLauncher(root)
    root.mainloop()