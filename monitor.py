import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# 玄関と、直接叩くべき「中身」のJSP
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
DIRECT_LOGIN_JSP = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    driver = None
    try:
        driver = setup_driver()
        
        # 1. まず玄関へ行き、Cookie（JSESSIONID）を強制的に発行させる
        log("🚪 玄関ページにアクセス（Cookie取得用）...")
        driver.get(START_URL)
        time.sleep(10)
        
        # 2. 「おわび」が出ていても無視して、本丸のURLへ「上書き」アクセスする
        # これにより、玄関で得たCookieを維持したまま、フレームを破壊して進む
        log(f"破壊的遷移: {DIRECT_LOGIN_JSP} へ直行...")
        driver.get(DIRECT_LOGIN_JSP)
        time.sleep(15) 

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        log(f"DEBUG: ページタイトル: '{driver.title}'")

        # 3. フォームがあるか全フレームから徹底捜索
        def find_and_fill(d):
            # ID/PASS入力欄の典型的なname属性などを狙う
            u_tags = d.find_elements(By.NAME, "uid") + d.find_elements(By.ID, "uid")
            p_tags = d.find_elements(By.XPATH, "//input[@type='password']")
            
            if u_tags and p_tags:
                log("🎯 ログインフォームを発見！")
                u_tags[0].send_keys(os.environ.get("JKK_ID"))
                p_tags[0].send_keys(os.environ.get("JKK_PASSWORD"))
                # 送信ボタンも探してクリック
                btns = d.find_elements(By.XPATH, "//img[contains(@src, 'login')] | //input[@type='submit']")
                if btns: btns[0].click()
                else: p_tags[0].submit()
                return True
            
            # 再帰的にフレームへ
            fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(fms)):
                try:
                    d.switch_to.frame(i)
                    if find_and_fill(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if find_and_fill(driver):
            log("✅ ログイン情報を送信しました！")
            time.sleep(10)
            log(f"送信後のURL: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりません。")
            # 最後の手段：ページ全体に何が書かれているか出力（デバッグ）
            body_text = driver.find_element(By.TAG_NAME, "body").text
            log(f"ページ内容の一部: {body_text[:200]}")

    except Exception as e:
        log(f"❌ エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
