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
        # 手順1: トップページ
        log("🚪 手順1: 公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)

        # 手順2: メニューをこじ開ける
        log("🖱️ 手順2: 『住宅をお探しの方』メニューを展開します")
        # メニュー自体をクリックしてJSでサブメニューを表示させる
        menu_script = """
            let menu = document.evaluate("//span[contains(text(), '住宅をお探しの方')]/..", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if(menu) menu.click();
        """
        driver.execute_script(menu_script)
        time.sleep(2)

        # 手順3: 展開された中からJKKねっとへのリンクを叩く
        log("🔍 手順3: 展開されたメニューから『JKKねっと』を特定")
        # 待ち時間に頼らず、JSで要素を直接叩き起こす
        jkk_click_script = """
            let links = Array.from(document.querySelectorAll('a'));
            let target = links.find(a => a.href.includes('jkknet') || a.innerText.includes('JKKねっと'));
            if(target) {
                target.click();
                return true;
            }
            return false;
        """
        found = driver.execute_script(jkk_click_script)
        
        if not found:
            log("🚨 メニュー展開後のリンク特定に失敗。スクショを撮ります。")
            driver.save_screenshot("menu_fail.png")
            return

        # 手順4: ログインボタンの実行（正規ルート経由なのでおわびは出ないはず）
        time.sleep(5)
        log("🔑 手順4: ログイン画面を呼び出し")
        driver.execute_script("mypageLogin();")
        time.sleep(5)

        # 別窓対応
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # 手順5: ID/PW入力（JSで瞬時に実行）
        log("⌨️ 手順5: ログイン情報を投入")
        u = os.environ.get("JKK_ID")
        p = os.environ.get("JKK_PASSWORD")
        
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
            log("🎉 成功！正規の階段を登りきりました。")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！**"})
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
