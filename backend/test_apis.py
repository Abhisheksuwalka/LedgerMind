import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_result(name, res):
    print(f"--- Testing {name} ---")
    print(f"Status Code: {res.status_code}")
    try:
        print(f"Response: {res.json()}")
    except:
        print(f"Response (text): {res.text}")
    print()

def test_all():
    # 1. Settings
    res = requests.get(f"{BASE_URL}/settings")
    print_result("GET /settings", res)

    # 2. Snapshot
    res = requests.get(f"{BASE_URL}/snapshot")
    print_result("GET /snapshot", res)

    # 3. History
    res = requests.get(f"{BASE_URL}/history")
    print_result("GET /history", res)

    # 4. Alerts
    res = requests.get(f"{BASE_URL}/alerts")
    print_result("GET /alerts", res)

    # 5. Runs
    res = requests.get(f"{BASE_URL}/runs")
    print_result("GET /runs", res)

    # 6. Reports
    res = requests.get(f"{BASE_URL}/reports")
    print_result("GET /reports", res)

    # 7. Chat
    payload = {"message": "Hello, how are you?"}
    res = requests.post(f"{BASE_URL}/chat", json=payload)
    print_result("POST /chat", res)
    session_id = "test-session"
    if res.status_code == 200:
        data = res.json()
        if isinstance(data, dict) and "session_id" in data:
            session_id = data["session_id"]
        elif isinstance(data, dict) and "messages" in data:
             session_id = "default"

    # 8. Chat History
    res = requests.get(f"{BASE_URL}/chat/{session_id}/history")
    print_result(f"GET /chat/{session_id}/history", res)

    # 9. Delete Chat Session
    res = requests.delete(f"{BASE_URL}/chat/{session_id}")
    print_result(f"DELETE /chat/{session_id}", res)

    # 10. Data Reset
    res = requests.delete(f"{BASE_URL}/data/reset")
    print_result("DELETE /data/reset", res)

if __name__ == "__main__":
    test_all()
