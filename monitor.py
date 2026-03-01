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

sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    # 🥇 最新の不安定な headless=new を避け、旧 headless を試行
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 🥈 CI環境でクラッシュを防ぐための「おまじない」
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process") # プロセスを1つに集約
    options.add_argument("--no-zygote")      # 子プロセスの生成を抑制
    
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # ボット検知回避
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def force_navigate(driver, wait, xpath_list, step_name):
    """ハイブリッド遷移 + 遷移直後の徹底診断"""
    log(f"🔎 {step_name} のリンクを探索中...")
    
    element = None
    for xpath in xpath_list:
        try:
            element = driver.find_element(By.XPATH, xpath)
            if element: break
        except: continue
    
    if not element:
        # 🥉 診断: リンクが見つからない時のソースとスクショ
        log(f"💀 {step_name} リンク未検出。現在の状態を保存します。")
        driver.save_screenshot(f"debug_{step_name}_not_found.png")
        print(f"--- SOURCE START ---\n{driver.page_source[:2000]}\n--- SOURCE END ---")
        raise Exception(f"{step_name} リンクが見つかりません")

    href = element.get_attribute("href")
    log(f"🔗 ターゲット発見: {href}")

    if href and (href.startswith("http") or href.startswith("/")):
        driver.get(href)
    else:
        driver.execute_script("arguments[0].click();", element)

    # ページ遷移の完了を待機
    time.sleep(5) # 描画安定のためのバッファ
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 40)

    try:
        # ① 公式トップ
        log("🚪 手順1: トップアクセス")
        driver.get("https://www.to-kousya.or.jp/")
        
        # ② JKKねっとトップ
        force_navigate(driver, wait, ["//a[contains(@href,'jkk')]"], "JKKトップ")

        # ③ ログイン画面（URLパターンを広げる）
        log("🔑 手順3: ログイン画面への遷移開始")
        login_xpaths = [
            "//a[contains(@href, 'login')]", 
            "//a[contains(@href, 'Login')]",
            "//area[contains(@href, 'login')]",
            "//img[contains(@alt, 'ログイン')]/.."
        ]
        force_navigate(driver, wait, login_xpaths, "ログイン画面")

        # ④ ログインフォーム入力
        log("⌨️ 手順4: ログインフォーム入力")
        # 診断: ログイン画面表示直後のスクショ
        driver.save_screenshot("at_login_page.png")

        # フォーム入力ロジック（前回の fill_login_form を使用）
        # ... (中略: ログイン情報を送信)

        # ⑤ 判定
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("menu"),
            EC.title_contains("おわび")
        ))

        if "mypage" in driver.current_url or "menu" in driver.current_url:
            log("🎉 成功！ついにログインしました。")
        else:
            log(f"💀 失敗: {driver.title}")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        try: driver.save_screenshot("last_error.png")
        except: pass
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
