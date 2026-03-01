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

# ログの文字化け防止
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def save_debug_screenshot(driver, filename):
    """
    CI環境（GitHub Actions）では個人情報漏洩防止のためスクショを保存しない。
    ローカル環境での実行時のみ、デバッグ用に保存する。
    """
    if os.environ.get("GITHUB_ACTIONS") == "true":
        log(f"⚠️ CI環境のため、セキュリティ保護によりスクショ保存をスキップしました: {filename}")
    else:
        driver.save_screenshot(filename)
        log(f"📸 スクショを保存しました: {filename}")

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
        log("🚪 手順1: 公式サイトへアクセス")
        driver.get("https://www.to-kousya.or.jp/")

        # 手順2: 物理的な「ブリッジボタン」を生成してクリック（面積を持たせる）
        log("🌉 手順2: 物理ブリッジボタンを生成して遷移（おわび画面対策）")
        bridge_script = """
            let a = document.createElement('a');
            a.id = 'bridge_link';
            a.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/';
            a.innerText = 'CLICK_FOR_SECURE_ACCESS';
            a.style.cssText = 'position:fixed; top:0; left:0; width:300px; height:300px; z-index:9999; background:red; color:white; display:block;';
            document.body.appendChild(a);
        """
        driver.execute_script(bridge_script)
        
        # 物理的にクリック可能な状態になるのを待って叩く
        bridge_btn = wait.until(EC.element_to_be_clickable((By.ID, "bridge_link")))
        bridge_btn.click()
        log("✅ ブリッジ遷移を実行しました")

        # 手順3: ログイン画面(mypageLogin)呼び出し
        log("🔑 手順3: ログイン画面を呼び出し")
        time.sleep(5)
        driver.execute_script("if(typeof mypageLogin === 'function') { mypageLogin(); }")
        
        # 別窓が開くのを待機してスイッチ
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"📑 ログインウィンドウに切り替えました: {driver.title}")

        # 手順4: ID/PW入力（安全な send_keys 方式）
        log("⌨️ 手順4: ログイン情報を安全に入力中...")

        def try_fill_login(d):
            try:
                # 名前(NAME)で要素を特定。JSにID/PWを流さないので安全
                u_field = d.find_element(By.NAME, "uid")
                p_field = d.find_element(By.NAME, "passwd")
                
                u_field.clear()
                u_field.send_keys(os.environ.get("JKK_ID", ""))
                p_field.clear()
                p_field.send_keys(os.environ.get("JKK_PASSWORD", ""))
                
                p_field.submit()
                return True
            except:
                return False

        # メイン画面またはフレーム内を探索
        if not try_fill_login(driver):
            log("📦 メイン画面にフォームがないため、フレーム内を探索します")
            frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                driver.switch_to.frame(frame)
                if try_fill_login(driver):
                    log("🎯 フレーム内での入力・送信に成功しました")
                    break
                driver.switch_to.default_content()

        # 手順5: 最終URLでログイン成否を確認
        log("🚀 ログイン処理の完了を待機中...")
        time.sleep(10)
        log(f"📍 最終URL: {driver.current_url}")
        
        if "mypageMenu" in driver.current_url:
            log("🎉 完全成功！マイページに到達しました。")
            if os.environ.get("DISCORD_WEBHOOK_URL"):
                requests.post(os.environ["DISCORD_WEBHOOK_URL"], json={"content": "✅ **JKKログイン成功！**"})
        else:
            log(f"💀 失敗。タイトル: {driver.title}")
            # 安全なスクショ保存関数を呼び出し
            save_debug_screenshot(driver, "login_failed_redacted.png")

    except Exception as e:
        log(f"❌ エラー発生: {str(e)}")
        save_debug_screenshot(driver, "exception_occured.png")
    finally:
        driver.quit()
        log("🏁 プロセスを終了します")

if __name__ == "__main__":
    main()
