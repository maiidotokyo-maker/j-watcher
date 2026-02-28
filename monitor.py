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

START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
LOGIN_JSP = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin"

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🚪 玄関ページでCookieを定着させます...")
        driver.get(START_URL)
        time.sleep(5)
        
        # --- レトロ攻略の極意：自己フレーム化 ---
        log("🏗️ 画面を強引にFrameset構造へ改造します...")
        # window.nameを固定しつつ、ドキュメント全体を書き換えて「おわび」判定を封じる
        driver.execute_script(f"""
            window.name = "JKK_TOP";
            document.open();
            document.write('<html><head><title>JKK_SYSTEM</title></head>');
            document.write('<frameset rows="*">');
            document.write('<frame name="JKK_WIN" id="JKK_WIN" src="{LOGIN_JSP}">');
            document.write('</frameset></html>');
            document.close();
        """)
        
        # 内部フレームが読み込まれるまでじっくり待機
        log("⏳ 内部フレームの生成を待機中...")
        time.sleep(20)
        
        # 生成したフレーム 'JKK_WIN' に潜り込む
        try:
            driver.switch_to.frame("JKK_WIN")
            log(f"🔎 フレーム内部に潜入。Title: {driver.title}")
            
            # 再帰的に全要素からID/PASS入力欄を探す
            def find_and_fill(d):
                u = d.find_elements(By.NAME, "uid")
                p = d.find_elements(By.XPATH, "//input[@type='password']")
                if u and p:
                    log("🎯 ついにログインフォームの『生身』を捕捉！")
                    u[0].send_keys(os.environ.get("JKK_ID"))
                    p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                    
                    # 送信。レトロサイトは .submit() よりクリックを好む
                    btn = d.find_elements(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
                    if btn:
                        log("🖱️ ログインボタンをクリック。")
                        btn[0].click()
                    else:
                        p[0].submit()
                    return True
                
                # 孫フレームがあればさらに掘る
                sub_fms = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
                for i in range(len(sub_fms)):
                    try:
                        d.switch_to.frame(i)
                        if find_and_fill(d): return True
                        d.switch_to.parent_frame()
                    except: continue
                return False

            if find_and_fill(driver):
                log("🚀 送信完了。マイページへの遷移を待ちます。")
                time.sleep(10)
                driver.switch_to.default_content() # 一旦外に出て状況確認
                log(f"最終URL: {driver.current_url}")
            else:
                log(f"🚨 フォームが見つかりません。タイトル: {driver.title}")
                # おわび回避のデバッグ用にソース末尾を
                log(f"ソース断片: {driver.page_source[-300:]}")

        except Exception as fe:
            log(f"❌ フレーム遷移に失敗: {fe}")

    except Exception as e:
        log(f"❌ 致命的エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
