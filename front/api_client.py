import requests
import urllib

BASE_URL = "http://127.0.0.1:5000"
TOKEN = None

def register(username, password):
    try:
        response = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
        if response.status_code == 201:
            return True, "User registered successfully."
        return False, response.json().get("msg", "Registration failed.")
    except Exception as e:
        return False, str(e)

def login(username, password):
    global TOKEN
    try:
        response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            TOKEN = response.json().get("token")
            return True, "Login successful"
        return False, response.json().get("msg", "Login failed")
    except Exception as e:
        return False, str(e)

def save_game_to_db(game_data):
    global TOKEN
    if not TOKEN:
        return False, "No token found. Please log in."
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = requests.post(f"{BASE_URL}/save_game", json=game_data, headers=headers)
        if response.status_code == 201:
            return True, "Game saved to DB"
        return False, response.text
    except Exception as e:
        return False, str(e)

def fetch_games_from_db():
    global TOKEN
    if not TOKEN:
        return []
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = requests.get(f"{BASE_URL}/get_games", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def delete_game_from_db(game_name):
    global TOKEN
    headers = {"Authorization": f"Bearer {TOKEN}"}
    encoded_name = urllib.parse.quote(game_name)
    try:
        # Crucial: Ensure this uses .delete()
        response = requests.delete(f"{BASE_URL}/delete_game/{encoded_name}", headers=headers)
        if response.status_code == 200:
            return True, "Deleted"
        return False, f"Server returned {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)