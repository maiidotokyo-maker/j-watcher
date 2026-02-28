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

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    # サーバーを騙すのではなく、標準的なブラウザとして振る舞う
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: トップページ（セッションの種をまく）
        log("🚪 手順1: 公式サイトへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        
        # 手順2: リンクを隠すバナーを「削除」ではなく「透明化・無効化」
        log("🧹 画面上の遮蔽物をクリアします")
        driver.execute_script("""
            const selectors = ['.cc-window', '.cookie-banner', '#cookie-consent', '[class*="cookie"]'];
            selectors.forEach(s => {
                document.querySelectorAll(s).forEach(el => el.remove());
            });
        """)

        # 手順3: 物理リンクの探索と「正規クリック」
        log("🔍 手順2: 『JKKねっと』リンクを特定中...")
        # 直接URLを叩くフォールバックを廃止
        target_link = driver.find_element(By.XPATH, "//a[contains(@href, 'jkknet')]")
        
        log(f"🎯 発見。正規ルートで遷移を開始します。")
        driver.execute_script("arguments[0].click();", target_link)

        # 手順4: ログインボタンの実行
        # ここで「おわび」が出るなら、手順3のクリックが正規とみなされていない
        time.sleep(5) 
        log("🔍 手順3: ログイン画面を呼び出し")
        driver.execute_script("mypageLogin();")

        # 手順5: 入力フォームへのアクセス
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        log("⌨️ 手順4: ID/PW入力")
        # フォーム入力もJSで行うことで、要素の認識エラーを回避
        u = os.environ.get("JKK_ID")
        p = os.environ.get("JKK_PASSWORD")
        
        # フレーム内も自動で探して入力
        script = f"""
            function fill(doc) {{
                let uid = doc.querySelector('input[name="uid"]');
                let pwd = doc.querySelector('input[name="passwd"]');
                if(uid && pwd) {{
                    uid.value = '{u}';
                    pwd.value = '{p}';
                    pwd.form.submit();
                    return true;
                }}
                return false;
            }}
            if(!fill(document)) {{
                let frames = document.querySelectorAll('frame, iframe');
                for(let f of frames) {{
                    if(fill(f.contentDocument)) break;
                }}
            }}
        """
        driver.execute_script(script)

        log("🚀 ログイン実行。結果を確認します。")
        time.sleep(10) # 遷移に必要な最小限の固定待ち
        
        if "mypageMenu" in driver.current_url:
            log("🎉 成功！正規手順で突破しました。")
        else:
            log(f"💀 失敗。現在のURL: {driver.current_url}")
            driver.save_screenshot("fail_analysis.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("crash.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
