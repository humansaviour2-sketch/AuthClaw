import requests
import json
import sys

def main():
    print("Testing live Gemini 2.5 Flash-Lite connectivity through AuthClaw Gateway...")
    
    url = "http://localhost:8080/v1/models/gemini-2.5-flash-lite:generateContent"
    headers = {
        "Authorization": "Bearer manual_verif_key_123",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Hello, is this Gemini 2.5 Flash-Lite? Please answer in exactly 5 words."}
                ]
            }
        ]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"Response Status Code: {r.status_code}")
        print("Response Body:")
        print(json.dumps(r.json(), indent=2))
        
        # Check if we got a valid response containing candidates
        resp_json = r.json()
        if "candidates" in resp_json:
            text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\nExtracted Response Text: {text.strip()}")
            print("\nRESULT: PASS - Live Gemini connectivity is fully verified and working!")
            sys.exit(0)
        else:
            print("\nRESULT: FAIL - Response did not contain candidates.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nRESULT: FAIL - Connection error or API failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
