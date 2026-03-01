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
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 手順1: トップページ（Refererの偽装元となるベースキャンプ）
        log("🚪 手順1: 公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: 直通ドアを生成して強行突破
        # UIに依存せず、ページ内に見えないリンクを作ってクリックさせる（これで正規遷移の証拠が残る）
        log("🌉 手順2: ページ内に直通リンクを自動生成して遷移します")
        bridge_script = """
            let a = document.createElement('a');
            a.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/';
            document.body.appendChild(a);
            a.click();
        """
        driver.execute_script(bridge_script)
        time.sleep(8)

        # 手順3: ログイン画面呼び出し
        log("🔑 手順3: ログイン画面を呼び出し")
        driver.execute_script("try { mypageLogin(); } catch(e) { console.log('error'); }")
        time.sleep(5)

        # 別窓対応
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # 手順4: ID/PW入力
        log("⌨️ 手順4: ログイン情報を投入")
        u = os.environ.get("JKK_ID", "")
        p = os.environ.get("JKK_PASSWORD", "")
        
        fill_script = f"""
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
                for(let f of frames) {{ if(fill(f.contentDocument)) break; }}
            }}
        """
        driver.execute_script(fill_script)

        # 最終確認
        time.sleep(10)
        log(f"📍 最終URL: {driver.current_url}")
        
        if "mypageMenu" in driver.current_url:
            log("🎉 成功！直通ドア戦略で突破しました。")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！** くじらを完全回避しました。"})
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            driver.save_screenshot("last_resort.png")

    except Exception as e:
        log(f"❌ エラー: {e}")
        driver.save_screenshot("exception.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
