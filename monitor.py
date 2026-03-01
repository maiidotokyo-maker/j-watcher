import sys
import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ログ出力の文字化け防止
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # 手順1: 公式サイト(www)へアクセス（Refererの起点）
        log("🚪 手順1: 公社公式サイト(www)へアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # 手順2: 直通リンクを動的に生成して「物理クリック」
        # これにより、文字化けやメニューの開閉状態に依存せず正規Refererを送信できる
        log("🌉 手順2: 直通ブリッジリンクを生成して遷移（おわび画面対策）")
        bridge_script = """
            let a = document.createElement('a');
            a.id = 'bridge_link';
            a.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/';
            document.body.appendChild(a);
        """
        driver.execute_script(bridge_script)
        # Selenium側で要素を掴んでクリック（JSでの.click()より物理クリックに近い挙動）
        driver.find_element(By.ID, "bridge_link").click()

        # 手順3: ログイン画面呼び出し
        log("🔑 手順3: ログイン画面(mypageLogin)を呼び出し")
        wait.until(lambda d: d.execute_script("return typeof mypageLogin === 'function'"))
        driver.execute_script("mypageLogin();")
        
        # 別窓が開くのを待機
        time.sleep(3)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 ログインウィンドウに切り替えました: {driver.title}")

        # 手順4: 安全なID/PW入力（send_keys 方式）
        log("⌨️ 手順4: ログイン情報を安全に入力中...")

        def try_fill_login(d):
            try:
                # By.NAME で確実に特定。JS文字列展開は行わない
                uid_field = d.find_element(By.NAME, "uid")
                pwd_field = d.find_element(By.NAME, "passwd")
                
                uid_field.clear()
                uid_field.send_keys(os.environ.get("JKK_ID"))
                pwd_field.clear()
                pwd_field.send_keys(os.environ.get("JKK_PASSWORD"))
                
                pwd_field.submit()
                return True
            except:
                return False

        # 1. まずメインコンテンツで試行
        if not try_fill_login(driver):
            log("📦 メイン画面にフォームが見つからないため、フレーム内を走査します")
            # 2. フレーム/アイフレームを全てチェック
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            success = False
            for index, frame in enumerate(frames):
                driver.switch_to.frame(frame)
                if try_fill_login(driver):
                    log(f"🎯 第{index}フレーム内で入力に成功しました")
                    success = True
                    break
                driver.switch_to.default_content()
            
            if not success:
                raise Exception("ログインフォームがどのフレーム内にも見つかりませんでした。")

        # 手順5: ログイン結果の検証
        log("🚀 ログイン実行。最終判定へ向かいます...")
        time.sleep(10)
        
        log(f"📍 最終到達URL: {driver.current_url}")
        if "mypageMenu" in driver.current_url:
            log("🎉 完全成功！セキュリティと安定性を両立してマイページを突破しました。")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={
                    "content": "✅ **JKKログイン成功！**\n安全な`send_keys`方式とブリッジ遷移により、くじらを回避してマイページに到達しました。"
                })
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            driver.save_screenshot("final_fail.png")

    except Exception as e:
        log(f"❌ エラー発生: {str(e)}")
        driver.save_screenshot("crash_report.png")
    finally:
        driver.quit()
        log("🏁 プロセスを終了します")

if __name__ == "__main__":
    main()
