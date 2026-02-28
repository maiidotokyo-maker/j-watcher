import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    # 日本語環境であることをサーバーに伝える（これだけで通るレトロサイトは多い）
    options.add_argument('--lang=ja-JP')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 玄関ページにアクセス")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
        
        # レトロサイトは読み込みが遅い。物理的に10秒待つ。
        time.sleep(10)

        # フレーム構造を無視して、ページ全体の「文字」でボタンを探す力技
        log("🔍 ページ内の『ログイン』という文字を全探索...")
        
        # すべてのフレームをチェック
        all_frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        
        target_frame = None
        if not all_frames:
            log("📄 フレームなし。直接探します。")
        else:
            for i in range(len(all_frames)):
                driver.switch_to.frame(i)
                if "ログイン" in driver.page_source:
                    log(f"🎯 第{i}フレームにログインの気配あり")
                    target_frame = i
                    break
                driver.switch_to.default_content()

        # ボタン（またはリンク）を特定してクリック
        try:
            # 「mypageLogin」という文字が含まれる要素を強引に叩く
            btn = driver.find_element(By.XPATH, "//*[@onclick*='mypageLogin']|//*[contains(@src, 'login')]")
            log("🖱️ ボタンを叩きます")
            driver.execute_script("arguments[0].click();", btn)
        except:
            log("🚨 物理ボタン不能。直接URLへジャンプを試みます。")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")

        time.sleep(10)
        
        # 最終確認
        log(f"📄 現在のTitle: {driver.title}")
        if "おわび" in driver.title:
            log("💀 サーバーに拒絶されました（IP制限等の可能性あり）")
        else:
            log(f"✅ 突破の可能性あり: {driver.current_url}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
