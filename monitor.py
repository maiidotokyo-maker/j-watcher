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
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # あなたが手動で成功させた時のブラウザに近いUAを設定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: サイトのルート（/）から入ります")
        driver.get("https://jhomes.to-kousya.or.jp/")
        time.sleep(3)

        log("🔗 手順2: ページ内の『JKKねっと』関連リンクを探してクリック")
        # 直接 /jkknet/pc/ に行かず、リンクを踏んで移動（リファラを発生させる）
        links = driver.find_elements(By.PARTIAL_LINK_TEXT, "JKKねっと")
        if not links:
            # リンクテキストになければhrefで探す
            links = driver.find_elements(By.XPATH, "//a[contains(@href, 'jkknet')]")
        
        if links:
            links[0].click()
            time.sleep(5)
            log(f"🏠 現在のURL: {driver.current_url}")
            log(f"📄 タイトル: {driver.title}")
        else:
            log("⚠️ リンクが見つからないため、通常ページへ直接向かいます")
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/")
            time.sleep(5)

        log("🖱️ 手順3: ログインボタンを特定します")
        # 全ての 'a' タグを精査（NoneTypeエラー回避策）
        all_a = driver.find_elements(By.TAG_NAME, "a")
        target_btn = None
        
        for a in all_a:
            onclick = a.get_attribute("onclick")
            text = a.text
            # onclick属性が存在し、かつ文字列である場合のみチェック
            if onclick and "mypageLogin" in str(onclick):
                target_btn = a
                break
            if text and "ログイン" in text:
                target_btn = a
                break

        if target_btn:
            log("🎯 ボタン発見！クリックして別窓を開きます")
            driver.execute_script("arguments[0].click();", target_btn)
            
            # 窓の切り替えを待つ
            for _ in range(20):
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    log(f"✨ ログイン窓へ乗り換え成功 (URL: {driver.current_url})")
                    break
                time.sleep(0.5)
            
            # ログインフォーム入力
            time.sleep(3)
            u = driver.find_elements(By.NAME, "uid")
            if u:
                log("🔑 認証情報を入力します...")
                u[0].send_keys(os.environ.get("JKK_ID"))
                driver.find_element(By.NAME, "passwd").send_keys(os.environ.get("JKK_PASSWORD"))
                driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]").click()
                time.sleep(8)
                log(f"✅ 最終URL: {driver.current_url}")
            else:
                log(f"🚨 フォームなし。タイトル: {driver.title}")
        else:
            log("💀 ログインボタンが見つかりませんでした。")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
