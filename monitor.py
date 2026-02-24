import requests
from bs4 import BeautifulSoup

URL = "https://www.jkk-website.go.jp/example"  # ← 実際のURLに差し替えてね

def check_availability():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # ここで空き情報を抽出（例：特定のクラス名やタグを探す）
    status = soup.find("div", class_="availability").text.strip()
    print(f"現在の空き状況: {status}")

if __name__ == "__main__":
    check_availability()
