import requests

def test_chat(key: str , msg: str):
    # API endpoint
    url = "http://localhost:8000/chat"
    
    # Test message with key
    payload = {
        "message": msg,
        "key": key
    }
    
    try:
        # Send request
        response = requests.post(url, json=payload)
        
        # Print status code
        print(f"\nTesting with key: {key}")
        print("Status Code:", response.status_code)
        
        # Get response data
        response_data = response.json()
        
        # Print the message
        print("Response Message:", response_data.get("message", "No message in response"))
        
        # If there was an error, print the full response
        if response.status_code != 200:
            print("Full Response:", response_data)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test with Macdora key
    # test_chat("macdora_secret_key_2024")
    
    # Test with Bulipe Tech key
    test_chat("bulipe_secret_key_2024" , "where are you working") 