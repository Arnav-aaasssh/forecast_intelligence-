import requests
import json
import time

def test_health():
    print("Testing /health endpoint...")
    response = requests.get("http://127.0.0.1:8000/health")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("="*40)

def test_review():
    print("Testing /review endpoint...")
    url = "http://127.0.0.1:8000/review"
    file_path = "sample_data/FinalForecast_Imputed.xlsx"
    
    with open(file_path, "rb") as f:
        files = {
            "file": (
                "FinalForecast_Imputed.xlsx", 
                f, 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        }
        
        start_time = time.time()
        response = requests.post(url, files=files)
        end_time = time.time()
        
    print(f"Status Code: {response.status_code}")
    print(f"Total Client Time: {end_time - start_time:.2f}s")
    if response.status_code == 200:
        print("Success! JSON schema snippet:")
        data = response.json()
        print(json.dumps({
            "metadata": data.get("metadata"),
            "pipeline": data.get("pipeline"),
            "validation": data.get("validation"),
            "artifacts": data.get("artifacts")
        }, indent=2))
    else:
        print(response.text)

if __name__ == "__main__":
    test_health()
    test_review()
