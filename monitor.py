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

# 標準出力をUTF-8に（ログの文字化け防止）
sys.stdout.reconfigure(encoding="utf-8")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    # ボット検知回避設定
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # webdriverプロパティを隠蔽
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # ① 公式「お部屋探し」トップへアクセス（セッション開始）
        log("🚪 手順1: 公式お部屋探しページへアクセス")
        driver.get("https://www.to-kousya.or.jp/chintai/index_search.html")
        time.sleep(3) # JS読み込みの物理待機
        
        # ② 「JKKねっと」へのリンクをURLパターンで特定してクリック
        log("🔎 手順2: JKKねっとへのリンクを探索中...")
        # FAQ(support...)を避け、jhomesまたはinter-jkkを含むリンクを狙い撃ち
        jkk_net_xpath = "//a[contains(@href, 'jhomes.to-kousya.or.jp') or contains(@href, 'inter-jkk.or.jp')]"
        jkk_link = wait.until(EC.element_to_be_clickable((By.XPATH, jkk_net_xpath)))
        log(f"🔗 ターゲット発見: {jkk_link.get_attribute('href')}")
        jkk_link.click()

        # ③ ログインページへのボタンをクリック（Logonを含むリンク）
        log("🔎 手順3: ログイン画面へのボタンを探索中...")
        login_btn_xpath = "//a[contains(@href, 'Logon') or contains(@href, 'login')]"
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))
        login_btn.click()

        # ④ ログインフォーム入力（iframe対応）
        log("⌨️ 手順4: ログインフォーム出現待機...")
        
        # もしフォームがiframe内にある場合を考慮したループ
        if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
            log("📦 iframeを検出。フレームを切り替えます。")
            driver.switch_to.frame(0) # 最初のフレームに切り替え

        # 要素名(uid)が出るまで待機
        u_field = wait.until(EC.presence_of_element_located((By.NAME, "uid")))
        p_field = driver.find_element(By.NAME, "passwd")

        log("✍️ ID/PWを入力中...")
        driver.execute_script("arguments[0].value = arguments[1];", u_field, JKK_ID)
        driver.execute_script("arguments[0].value = arguments[1];", p_field, JKK_PASSWORD)
        
        driver.save_screenshot("at_login_input.png")
        p_field.submit()

        # ⑤ 認証成功の判定
        log("🚀 認証完了を待機中...")
        wait.until(EC.any_of(
            EC.url_contains("mypage"),
            EC.url_contains("Menu"),
            EC.title_contains("マイページ")
        ))

        if "mypage" in driver.current_url.lower() or "menu" in driver.current_url.lower():
            log("🎉 ログイン成功！マイページに到達しました。")
            if DISCORD_WEBHOOK:
                requests.post(DISCORD_WEBHOOK, json={"content": "✅ JKKログイン成功！監視フェーズへ移行します。"})
        else:
            log(f"💀 ログイン判定失敗: {driver.current_url}")
            driver.save_screenshot("login_fail_final.png")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        driver.save_screenshot("fatal_error.png")
        # デバッグ用にHTMLの一部を出力
        print(f"--- DEBUG HTML ---\n{driver.page_source[:500]}")
    finally:
        driver.quit()
        log("🏁 プロセス終了")

if __name__ == "__main__":
    main()
