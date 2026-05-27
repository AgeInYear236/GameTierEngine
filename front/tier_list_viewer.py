import json
import os
import sys
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext
from base64 import b64decode
import urllib.parse
import requests
import api_client
from PIL import Image, ImageTk, ImageDraw

if len(sys.argv) > 1:
    passed_token = sys.argv[1]
    if passed_token != "None":
        api_client.TOKEN = passed_token

# --- Configuration & Path Routing ---
DATA_FILE = "games_tier_list.json"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CACHE_DIR = os.path.join(BASE_DIR, "image_cache")
DATA_PATH = os.path.join(BASE_DIR, DATA_FILE)

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

ZYTE_API_KEY = "4f8503c475894371ab356e15558c65d9"

TIER_COLORS = {
    "S": "#ff7f7f",
    "A": "#ffbf7f",
    "B": "#ffff7f",
    "C": "#bfff7f",
    "D": "#7fff7f",
    "F": "#7f7fff",
}
TIERS_ORDER = ["S", "A", "B", "C", "D", "F"]


class TierListViewer:
    # --- ACCEPT AN OPTIONAL PROFILE PARAMETER ON INIT ---
    def __init__(self, root, selected_profile=None):
        self.root = root
        self.selected_profile = selected_profile
        
        if self.selected_profile:
            self.root.title(f"🏆 {self.selected_profile}'s Tier List Board")
        else:
            self.root.title("🏆 Visual Wrapped Tier List Board")
            
        self.root.geometry("1100x800")
        self.root.configure(bg="#1a1a1a")

        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2a2a2a", fg="white", activebackground="#007acc")
        self.selected_game_to_delete = None
        self.image_references = {}

        # --- Top Control Bar ---
        self.control_frame = tk.Frame(self.root, bg="#2a2a2a", pady=10, padx=15)
        self.control_frame.pack(fill="x")

        tk.Label(
            self.control_frame, text="Filter Game:", font=("Arial", 11, "bold"), bg="#2a2a2a", fg="white"
        ).pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.draw_tier_list())
        self.search_entry = tk.Entry(
            self.control_frame, textvariable=self.search_var, font=("Arial", 11),
            bg="#3a3a3a", fg="white", insertbackground="white", bd=1, relief="solid", width=22
        )
        self.search_entry.pack(side="left", padx=5)

        #self.btn_refresh = tk.Button(
        #    self.control_frame, text="🔄 Clear Layout & Re-Fetch", font=("Arial", 10, "bold"),
        #    bg="#007acc", fg="white", relief="flat", command=self.load_and_draw, padx=12
        #)
        #self.btn_refresh.pack(side="right")

        # --- Main Layout Frames ---
        self.canvas_frame = tk.Frame(self.root, bg="#121212")
        self.canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient="vertical")
        self.v_scroll.pack(side="right", fill="y")

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", bd=0, highlightthickness=0, yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill="both", expand=True)
        self.v_scroll.config(command=self.canvas.yview)

        # Lower Component: Live Debug Terminal Console
        self.debug_frame = tk.LabelFrame(self.root, text=" 🖥️ Live Zyte & DuckDuckGo API Debug Terminal Logs ", bg="#1a1a1a", fg="#00ffcc", font=("Arial", 9, "bold"), padx=10, pady=5)
        self.debug_frame.pack(fill="x", side="bottom", padx=15, pady=(0, 15))

        self.log_console = scrolledtext.ScrolledText(
            self.debug_frame, height=8, bg="#0a0a0a", fg="#dcdcdc", font=("Courier New", 10),
            insertbackground="white", relief="solid", bd=1
        )
        self.log_console.pack(fill="both", expand=True)
        
        self.log_debug("SYSTEM: Initialization Complete. Standing by to draw cached assets...")

        self.games_data = []
        # Pass profile details over to engine trigger
        self.load_and_draw(target_username=self.selected_profile)

    def log_debug(self, message):
        self.log_console.insert(tk.END, f"{message}\n")
        self.log_console.see(tk.END)
        self.root.update_idletasks()

    def load_and_draw(self, target_username=None):
        """Fetches data from the remote PostgreSQL database via API."""
        if target_username:
            self.log_debug(f"🌐 [NETWORK] Fetching public profile data for user: {target_username}")
            try:
                encoded_user = urllib.parse.quote(target_username)
                response = requests.get(f"{api_client.BASE_URL}/get_user_games/{encoded_user}", timeout=5)
                if response.status_code == 200:
                    self.games_data = response.json()
                else:
                    self.games_data = []
            except Exception as e:
                self.log_debug(f"❌ Error downloading profile data: {e}")
                self.games_data = []
        else:
            self.log_debug("🌐 [NETWORK] Fetching game data for logged-in session user...")
            self.games_data = api_client.fetch_games_from_db()
        
        if not self.games_data:
            self.canvas.delete("all")
            display_msg = f"No profile dataset entries found for user '{target_username}'." if target_username else "No games found in database.\nAdd new entries via the Calculator."
            self.canvas.create_text(
                500, 200, text=display_msg,
                fill="#888888", font=("Arial", 13, "italic"), justify="center"
            )
            return

        self.log_debug(f"✅ [SUCCESS] Loaded {len(self.games_data)} game entries.")
        
        # Process and download images via premium API
        self.download_missing_images_via_zyte()
        self.draw_tier_list()

    def download_missing_images_via_zyte(self):
        for game in self.games_data:
            game_name = game.get("game_name", "").strip()
            if not game_name:
                continue

            safe_name = re.sub(r'[\\/*?:"<>|]', "", game_name)
            final_path = os.path.join(CACHE_DIR, f"{safe_name}.png")

            if os.path.exists(final_path):
                continue

            self.log_debug(f"🔍 [API LOGO FETCH] Requesting high-res asset for: '{game_name}'")
            image_saved = False

            try:
                encoded_query = urllib.parse.quote(game_name)
                target_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1"
                
                api_response = requests.post(
                    "https://api.zyte.com/v1/extract",
                    auth=(ZYTE_API_KEY, ""),
                    json={"url": target_url, "httpResponseBody": True},
                    timeout=12
                )
                
                if api_response.status_code == 200:
                    raw_payload = api_response.json().get("httpResponseBody", "")
                    json_data = json.loads(b64decode(raw_payload).decode('utf-8', errors='ignore'))
                    direct_img_url = json_data.get("Image", "")
                    
                    if direct_img_url:
                        if direct_img_url.startswith("/"):
                            direct_img_url = "https://duckduckgo.com" + direct_img_url
                            
                        img_response = requests.post(
                            "https://api.zyte.com/v1/extract",
                            auth=(ZYTE_API_KEY, ""),
                            json={"url": direct_img_url, "httpResponseBody": True},
                            timeout=10
                        )

                        if img_response.status_code == 200:
                            img_bytes = b64decode(img_response.json()["httpResponseBody"])
                            with open(final_path, "wb") as f:
                                f.write(img_bytes)
                            image_saved = True

            except Exception as e:
                self.log_debug(f"   💥 [EXCEPTION ENCOUNTERED]: {e}")

            if not image_saved:
                try:
                    fallback_img = Image.new('RGB', (100, 100), color='#2c3e50')
                    draw = ImageDraw.Draw(fallback_img)
                    draw.text((50, 50), safe_name[0].upper() if safe_name else "?", fill="#00ffcc", anchor="mm", font_size=40)
                    fallback_img.save(final_path, "PNG")
                except Exception:
                    pass

    def get_game_image(self, game_name):
        safe_name = re.sub(r'[\\/*?:"<>|]', "", game_name).strip()
        img_path = os.path.join(CACHE_DIR, f"{safe_name}.png")
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img = img.resize((50, 50), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                pass
        return None

    def show_context_menu(self, event, game_name):
        # --- PREVENT OTHER USERS FROM DELETING SOMEONE ELSE'S DATA ---
        if self.selected_profile:
            return 
            
        self.selected_game_to_delete = game_name
        self.context_menu.delete(0, tk.END)
        self.context_menu.add_command(label=f"❌ Delete '{game_name}'", command=self.confirm_and_delete_game)
        self.context_menu.post(event.x_root, event.y_root)

    def confirm_and_delete_game(self):
        if not self.selected_game_to_delete:
            return
            
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
            # Check dictionary keys based on standard API schema format mapping
            name = game.get("game_name", "Unknown Game")
            tier = game.get("tier", "F")
            if filter_keyword and filter_keyword not in name.lower():
                continue
            if tier in tier_groups:
                tier_groups[tier].append(game)

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
                self.canvas.create_text(
                    x_offset + 60, current_y + 18, text=short_name, fill="#ffffff", font=("Arial", 9, "bold"), anchor="nw", tags=tag_id
                )
                self.canvas.create_text(
                    x_offset + 60, current_y + 36, text=f"Score: {calc_score}", fill="#aaaaaa", font=("Arial", 8), anchor="nw", tags=tag_id
                )

                # Right click binds (Only active if viewing your own tier list)
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


if __name__ == "__main__":
    root = tk.Tk()
    app = TierListViewer(root)
    root.mainloop()