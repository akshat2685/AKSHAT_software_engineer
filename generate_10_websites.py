import time
import requests

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImkuamFpbi5ha3NoYXRAZ21haWwuY29tIiwiZXhwIjoxNzgxMDcwNTk3LjY2OTE0Njh9.wMrcpank-9gaY3GR1z85Ue7rTo2i5DaTtPeWFhbKuyo"
BASE_URL = "http://127.0.0.1:3000"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

NICHES = [
    "modern coffee shop and bakery",
    "luxury real estate agency",
    "personal photography portfolio",
    "cryptocurrency analytics dashboard",
    "local fitness gym and tracker",
    "professional law firm",
    "boutique pet grooming service",
    "tech news blog",
    "exotic travel agency",
    "vintage clothing store"
]

def wait_for_completion():
    print("Waiting for AKSHAT to finish current task...")
    while True:
        try:
            res = requests.get(f"{BASE_URL}/api/status", headers=HEADERS)
            data = res.json()
            status = data.get("status", "idle")
            if status in ["success", "error", "idle"]:
                print(f"Task completed with status: {status}")
                return
            time.sleep(5)
        except Exception as e:
            print(f"Error checking status: {e}")
            time.sleep(5)

def run_tests():
    print("Starting 10 website generation test...")
    for i, niche in enumerate(NICHES):
        prompt = f"Build a complete, beautifully styled website for a {niche}. Make sure it is responsive and has a modern dark mode design."
        print(f"\n[{i+1}/10] Submitting task: {niche}")
        
        try:
            res = requests.post(
                f"{BASE_URL}/api/task",
                headers=HEADERS,
                json={"prompt": prompt}
            )
            if res.status_code == 200:
                print(f"Successfully submitted task {i+1}")
                wait_for_completion()
                # Wait a bit before the next one to let the system rest
                time.sleep(3)
            else:
                print(f"Failed to submit task: {res.status_code} {res.text}")
                break
        except Exception as e:
            print(f"Request failed: {e}")
            break

    print("\nAll tasks submitted and processed.")
    
    print("\nVerifying database state...")
    try:
        res = requests.get(f"{BASE_URL}/api/projects", headers=HEADERS)
        projects = res.json()
        print(f"Found {len(projects)} projects in the database for this user:")
        for p in projects[:10]:
            print(f" - {p.get('name', '')} (Status: {p.get('status', '')})")
    except Exception as e:
        print(f"Failed to fetch projects: {e}")

if __name__ == "__main__":
    run_tests()
