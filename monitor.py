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

# 標準出力をUTF-8に設定
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")  # 最新のヘッドレスモード
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 日本語環境と人間らしい挙動の偽装
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # ボット検知回避用スクリプト
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
        # 1. 公式サイトのトップから入る（リファラと正規Cookieを生成）
        log("🚪 手順1: JKK東京トップページへアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        time.sleep(5)
        
        # 2. 「JKKねっと」へのリンクを物理クリック
        log("🔎 手順2: サイト内の『JKKねっと』ボタンをクリック")
        jkk_xpath = "//a[contains(@href, 'jhomes.to-kousya.or.jp')]"
        jkk_btn = wait.until(EC.element_to_be_clickable((By.XPATH, jkk_xpath)))
        jkk_btn.click()
        
        # 別タブで開く場合があるため、最新のウィンドウに切り替え
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        # 3. 遷移後のページで「ログイン」ボタンを物理クリック
        log("🔗 手順3: ログイン画面へのボタンをクリック")
        login_btn_xpath = "//a[contains(@href, 'mypageMenu')]"
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))
        login_btn.click()
        
        # JSによるiframe生成を十分に待つ（真っ白画面対策）
        log("⏳ JSロード待機中（15秒）...")
        time.sleep(15)
        driver.save_screenshot("debug_after_transition.png")

        # 4. ログインフォーム探索（iframe全ループ）
        log("⌨️ 手順4: ログインフォームをiframe内から探索")
        found = False
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        log(f"検出されたiframe数: {len(frames)}")

        for i, frame in enumerate(frames):
            driver.switch_to.frame(frame)
            try:
                # 5秒だけ待ってuidがあるか確認
                u_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "uid"))
                )
                p_field = driver.find_element(By.NAME, "passwd")
                
                log(f"✅ iframe[{i}] 内にフォームを発見！入力します。")
                driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
                driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
                
                driver.save_screenshot("debug_input_ready.png")
                p_field.submit()
                found = True
                break
            except:
                driver.switch_to.default_content()

        if not found:
            # HTML直下も一応探す
            try:
                u_field = driver.find_element(By.NAME, "uid")
                u_field.send_keys(JKK_ID)
                driver.find_element(By.NAME, "passwd").send_keys(JKK_PASSWORD)
                u_field.submit()
                found = True
            except:
                raise Exception("ログインフォームがどの階層にも見つかりませんでした。")

        # 5. 成功判定
        log("🚀 認証結果を確認中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("Menu"),
            EC.title_contains("マイページ")
        ))
        
        log("🎉 ログイン成功！")
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログインに成功しました。監視を継続します。"})

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("fatal_error.png")
        # ページソースの一部を出力して解析のヒントにする
        print(f"--- DEBUG PAGE SOURCE (Partial) ---\n{driver.page_source[:500]}")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
