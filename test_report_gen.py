import requests
import json

data = {
    "sensorData": {
        "timestamps": ["10:00", "10:01", "10:02"],
        "smoke": [300, 310, 320],
        "methane": [100, 110, 120],
        "co": [50, 55, 60],
        "air": [60, 65, 70],
        "gpi": [40, 42, 45],
        "temperature": [25, 25.5, 26],
        "humidity": [50, 51, 52]
    }
}

try:
    print("Generating Report...")
    # Timeout increased because calling LLM might be slow
    r = requests.post('http://localhost:5000/generate-report', json=data, timeout=60)
    if r.status_code == 200:
        print("Report generated successfully (size: {} bytes)".format(len(r.content)))
        with open('test_report.pdf', 'wb') as f:
            f.write(r.content)
    else:
        print(f"Report generation FAILED: {r.status_code}")
        print(r.text)
except Exception as e:
    print(f"Report generation ERROR: {e}")
