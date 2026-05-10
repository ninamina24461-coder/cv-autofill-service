import requests
import time
import schedule

def ping_service():
    try:
        response = requests.get("https://cv-autofill-service.onrender.com/health", timeout=10)
        print(f"Ping successful: {response.status_code}")
    except Exception as e:
        print(f"Ping failed: {e}")

if __name__ == "__main__":
    schedule.every(10).minutes.do(ping_service)
    print("Keep-alive service started. Pinging every 10 minutes...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)
