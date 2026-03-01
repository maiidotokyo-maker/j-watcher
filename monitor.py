import os
import sys
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

# 出力エンコーディング設定
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # 1. 公式トップから開始（セッション確立）
        log("🚪 手順1: JKK東京トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)
        
        # 2. 「JKKねっと」リンクを多角的に探索して強制クリック
        log("🔎 手順2: 『JKKねっと』ボタンを探索・クリック")
        # href属性に'jhomes'を含むAタグを最優先で探す
        jkk_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'jhomes.to-kousya.or.jp')]")
        
        if not jkk_links:
            # 代替案：バナー画像などのALT属性から探す
            jkk_links = driver.find_elements(By.XPATH, "//*[contains(@alt, 'JKKねっと')]/ancestor::a")

        if jkk_links:
            # 要素が隠れていてもクリックできるJavaScript実行方式を採用
            driver.execute_script("arguments[0].click();", jkk_links[0])
            log("🔗 JSによる強制クリックを実行しました")
        else:
            raise Exception("JKKねっとへの遷移ボタンが見つかりません。")

        # 3. ウィンドウ切り替え（別タブ対策）
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log(f"🔄 新しいタブに切り替えました: {driver.current_url}")

        # 4. ログイン画面への遷移
        log("🔗 手順3: ログインメニューをクリック")
        # mypageMenuを含むリンクを探してJSクリック
        login_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'mypageMenu')]")))
        driver.execute_script("arguments[0].click();", login_btn)

        # 5. JSロード待ち（ここが重要：真っ白画面対策）
        log("⏳ JSロードを待機中（15秒）...")
        time.sleep(15)
        driver.save_screenshot("debug_login_ready.png")

        # 6. iframe全探索とログイン実行
        log("⌨️ 手順4: iframe内のログインフォームを探索")
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        found = False

        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # 5秒待機して uid 入力欄があるか確認
                u_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "uid")))
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内にフォームを発見。入力を開始します。")
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                driver.save_screenshot("debug_before_submit.png")
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            raise Exception("ログインフォームが見つかりませんでした（iframe内未検出）")

        # 7. ログイン成功判定
        log("🚀 ログイン結果を確認中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.title_contains("マイページ")
        ))
        
        log("🎉 ログイン成功！")
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログインに成功しました。監視プロセスを開始します。"})

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("final_fatal_error.png")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
