import os
import requests
from bs4 import BeautifulSoup

# ログインページとマイページのURL（必要に応じて調整）
LOGIN_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"
TARGET_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu"

def check_availability():
    session = requests.Session()

    # GitHub Secrets からIDとパスワードを取得
    payload = {
        "loginId": os.environ["JKK_ID"],
        "password": os.environ["JKK_PASSWORD"]
    }

    # ログイン処理（必要に応じてヘッダーやCSRFトークンの取得を追加）
    login_response = session.post(LOGIN_URL, data=payload)
    if login_response.status_code != 200:
        print("ログインに失敗しました")
        return

    # マイページにアクセス
    response = session.get(TARGET_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # 空き状況を抽出（仮の例：適切なクラス名に変更してね）
    availability_div = soup.find("div", class_="availability")
    if availability_div:
        status = availability_div.text.strip()
        print(f"現在の空き状況: {status}")
    else:
        print("空き状況の情報が見つかりませんでした")

if __name__ == "__main__":
    check_availability()
