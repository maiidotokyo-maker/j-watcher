import os
import requests
from bs4 import BeautifulSoup

LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
TARGET_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu"

def check_availability():
    session = requests.Session()

    # SecretsからIDとパスワードを取得
    payload = {
        "loginId": os.environ["JKK_ID"],
        "password": os.environ["JKK_PASSWORD"]
    }

    # ログイン処理
    session.post(LOGIN_URL, data=payload)

    # マイページにアクセス
    response = session.get(TARGET_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # 空き状況を抽出（仮の例）
    status = soup.find("div", class_="availability").text.strip()
    print(f"現在の空き状況: {status}")

if __name__ == "__main__":
    check_availability()
