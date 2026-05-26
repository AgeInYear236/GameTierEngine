import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import api_client

if len(sys.argv) > 1:
    passed_token = sys.argv[1]
    if passed_token != "None":
        api_client.TOKEN = passed_token


# --- Constants & Configuration ---
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

# Global dictionary to temporarily hold calculation results before saving
current_calculation = {}


def show_help(title, message):
    """Displays a helpful info box for a given criterion."""
    messagebox.showinfo(f"About {title}", message)


def determine_tier(total_score, personal_score):
    """Determines the tier based on total score and personal score constraints."""
    if total_score >= 100:
        tier = "S"
    elif total_score >= 80:
        tier = "A"
    elif total_score >= 60:
        tier = "B"
    elif total_score >= 40:
        tier = "C"
    elif total_score >= 20:
        tier = "D"
    else:
        tier = "F"

    # Apply Personal Score Constraints
    if personal_score == 3 and tier in ["S", "A"]:
        tier = "B"
    elif personal_score in [1, 2] and tier in ["S", "A", "B"]:
        tier = "C"

    return tier


def calculate_tier():
    """Runs the math and shows a visual preview on screen."""
    global current_calculation
    game_name = entry_name.get().strip()

    if not game_name:
        messagebox.showerror("Error", "Please enter a game name first.")
        return

    # Gather scores from sliders
    criteria_scores = {}
    total_score = 0.0
    for criterion, multiplier in CRITERIA.items():
        slider_value = sliders[criterion].get()
        criteria_scores[criterion] = slider_value
        total_score += slider_value * multiplier

    personal_score = int(var_personal.get())
    tier = determine_tier(total_score, personal_score)

    # Display UI Result Preview
    result_text = f"Total Score: {total_score:.1f}/{MAX_SCORE}\nPersonal Score: {personal_score}/5\nAssigned Tier: {tier}"
    lbl_result.config(text=result_text, fg="#0056b3")

    # Stash the data into our temporary global variable
    current_calculation = {
        "game_name": game_name,
        "criteria_scores": criteria_scores,
        "personal_score": personal_score,
        "calculated_score": round(total_score, 1),
        "tier": tier,
    }

    # Enable the save button since data is fresh
    btn_save.config(state="normal", bg="#28a745")

# In your game_calculator.py
def save_to_db(game_name, scores, final_score, tier):
    print(f"DEBUG: Saving - Name: {game_name}, Score: {final_score}, Tier: {tier}")
    payload = {
        "game_name": game_name,
        "criteria_scores": scores,        # Must match data.get('criteria_scores')
        "calculated_score": final_score, # Must match data.get('calculated_score')
        "tier": tier                     # Must match data.get('tier')
    }
    
    # Call your api_client function here
    success, message = api_client.save_game_to_db(payload)

def save_to_json():
    """Saves the stashed calculation data to the JSON file."""
    global current_calculation

    if not current_calculation:
        messagebox.showerror("Error", "Please calculate the score first.")
        return

    try:
        # Load existing database
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                games_list = json.load(f)
        else:
            games_list = []

        # Append data
        games_list.append(current_calculation)

        # Write data back to file
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(games_list, f, indent=4, ensure_ascii=False)

        messagebox.showinfo(
            "Success",
            f"Successfully saved '{current_calculation['game_name']}' to {DATA_FILE}!",
        )

        # Reset Form and Save button state
        entry_name.delete(0, tk.END)
        lbl_result.config(
            text="Enter a game and click Calculate", fg="black"
        )
        btn_save.config(state="disabled", bg="#6c757d")

        game_name = current_calculation.get("game_name")
        scores = current_calculation.get("criteria_scores")
        final_score = current_calculation.get("calculated_score")
        tier = current_calculation.get("tier")

        # Invoke the database save function
        save_to_db(game_name, scores, final_score, tier)

        current_calculation = {}


        

    except Exception as e:
        messagebox.showerror("File Error", f"Could not save data: {e}")


# --- GUI Setup ---
root = tk.Tk()
root.title("Game Tier List Calculator")
root.geometry("480x1000")
root.resizable(True, True)

# Game Name Input
frame_name = tk.LabelFrame(root, text=" Game Details ", padx=10, pady=10)
frame_name.pack(fill="x", padx=15, pady=10)

tk.Label(frame_name, text="Game Name:", font=("Arial", 10, "bold")).pack(
    anchor="w"
)
entry_name = tk.Entry(frame_name, font=("Arial", 11))
entry_name.pack(fill="x", pady=5)

# Criteria Sliders
frame_criteria = tk.LabelFrame(
    root, text=" Criteria (0 - 10) ", padx=10, pady=10
)
frame_criteria.pack(fill="x", padx=15, pady=5)

sliders = {}
for criterion, multiplier in CRITERIA.items():
    header_frame = tk.Frame(frame_criteria)
    header_frame.pack(fill="x", pady=(5, 0))

    lbl_text = f"{criterion} (x{multiplier}):"
    tk.Label(header_frame, text=lbl_text, font=("Arial", 9, "bold")).pack(
        side="left"
    )

    btn_help = tk.Button(
        header_frame,
        text="?",
        font=("Arial", 8, "bold"),
        width=2,
        height=1,
        bd=1,
        relief="solid",
        bg="#e1e1e1",
        command=lambda c=criterion: show_help(c, HELP_TEXTS[c]),
    )
    btn_help.pack(side="right")

    slider = tk.Scale(
        frame_criteria, from_=0, to=10, orient="horizontal", resolution=0.5
    )
    slider.set(5)
    slider.pack(fill="x", pady=(0, 10))
    sliders[criterion] = slider

# Personal Score Dropdown Section
frame_personal = tk.LabelFrame(root, text=" Personal Preference ", padx=10, pady=5)
frame_personal.pack(fill="x", padx=15, pady=5)

personal_sub_frame = tk.Frame(frame_personal)
personal_sub_frame.pack(fill="x", pady=5)

tk.Label(
    personal_sub_frame, text="Personal Score (1 to 5):", font=("Arial", 9)
).pack(side="left", padx=5)

var_personal = tk.StringVar(value="5")
dropdown_personal = ttk.Combobox(
    personal_sub_frame,
    textvariable=var_personal,
    values=["1", "2", "3", "4", "5"],
    width=5,
    state="readonly",
)
dropdown_personal.pack(side="left", padx=5)

btn_help_p = tk.Button(
    personal_sub_frame,
    text="?",
    font=("Arial", 8, "bold"),
    width=2,
    bd=1,
    relief="solid",
    bg="#e1e1e1",
    command=lambda: show_help("Personal Score", HELP_TEXTS["Personal Score"]),
)
btn_help_p.pack(side="right", padx=5)

# Action Buttons Layout (Side-by-Side)
frame_buttons = tk.Frame(root)
frame_buttons.pack(fill="x", padx=15, pady=15)

# 1. Blue Calculate Button
btn_calculate = tk.Button(
    frame_buttons,
    text="⚙️ Calculate Tier",
    font=("Arial", 11, "bold"),
    bg="#007acc",
    fg="white",
    command=calculate_tier,
    pady=10,
)
btn_calculate.pack(side="left", fill="x", expand=True, padx=(0, 5))

# 2. Green Save Button (Disabled initially until calculation happens)
btn_save = tk.Button(
    frame_buttons,
    text="💾 Save Game",
    font=("Arial", 11, "bold"),
    bg="#6c757d",
    fg="white",
    command=save_to_json,
    state="disabled",
    pady=10,
)
btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))

# Result Display
frame_result = tk.LabelFrame(root, text=" Result Preview ", padx=10, pady=10)
frame_result.pack(fill="both", expand=True, padx=15, pady=10)

lbl_result = tk.Label(
    frame_result,
    text="Enter a game and click Calculate",
    font=("Arial", 11, "italic"),
    justify="left",
)
lbl_result.pack(anchor="w")

root.mainloop()