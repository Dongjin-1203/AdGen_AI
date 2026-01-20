import requests

# GPU 서버 외부 IP 입력
SERVER_IP = "34.59.198.57"  # GCP Console에서 확인

files = ['prod_1080_minimal.png', 'quick_creative.png', 'quick_luxury.png', 'quick_minimal.png', 'quick_mood.png', 'quick_street.png']

for filename in files:
    url = f"http://{SERVER_IP}:9000/{filename}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ {filename} 다운로드 완료")
    else:
        print(f"❌ {filename} 다운로드 실패")