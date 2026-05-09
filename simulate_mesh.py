import requests
import time
import random

API_URL = "http://localhost:5000/api/emergency/receive"

MESSAGES = [
    "I am trapped under a collapsed wall, need help fast!",
    "Two people are injured here, heavy bleeding.",
    "We are low on food and water in Sector 4.",
    "Need urgent evacuation, water levels are rising.",
    "Fire spotted near the medical camp.",
    "Trapped in the basement, cannot breathe well.",
    "Old man with broken leg needs assistance.",
    "Sending distress signal from building rooftops.",
    "No clean water available for last 24 hours.",
    "Multiple victims trapped under debris near the bridge."
]

def send_message(text, x=None, y=None):
    if x is None or y is None:
        location = {
            "x": random.randint(10, 90),
            "y": random.randint(10, 90)
        }
    else:
        location = {"x": x, "y": y}
        
    payload = {
        "message": text,
        "location": location
    }
    try:
        print(f"Sending: {text} at ({location['x']}, {location['y']})")
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            res = response.json()
            print(f"Success: {res.get('category')} | {res.get('severity')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    print("Starting Enhanced Mesh Simulation (Hotspots)...")
    print("Ensure app.py and Ollama are running.")
    time.sleep(1)
    
    # Define 3 hot epicenters
    epicenters = [
        {"x": random.randint(20, 40), "y": random.randint(20, 40)},
        {"x": random.randint(60, 80), "y": random.randint(20, 40)},
        {"x": random.randint(40, 60), "y": random.randint(60, 80)}
    ]
    
    print(f"Simulating {len(epicenters)} disaster hotspots...")
    
    # Generate a cluster around each epicenter
    for i, epi in enumerate(epicenters):
        print(f"\n--- Simulating Hotspot {i+1} ---")
        num_reports = random.randint(4, 7)
        for _ in range(num_reports):
            # Normal distribution around epicenter
            x = int(max(0, min(100, random.gauss(epi['x'], 5))))
            y = int(max(0, min(100, random.gauss(epi['y'], 5))))
            
            msg = random.choice(MESSAGES)
            send_message(msg, x, y)
            time.sleep(0.5)
    
    # Send some random noise messages
    print("\n--- Sending general distress signals ---")
    for _ in range(5):
        msg = random.choice(MESSAGES)
        send_message(msg)
        time.sleep(0.5)
    
    print("\nSimulation complete. Dashboard hotspots and feed updated.")
