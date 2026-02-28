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

def setup_driver():
    options = Options()
    # あえて 'new' ではない旧来の headless を使う（レトロサイトとの相性が良い場合があるため）
    options.add_argument('--headless=old')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1024,768') # 当時の標準解像度
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko') # IE11に偽装
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🕰️ タイムスリップ開始。玄関ページへ...")
        driver.get(START_URL)
        time.sleep(7) # サーバーが落ち着くのを待つ
        
        log("💉 レトロなお作法（ウィンドウ名とReferer）を注入中...")
        # サイト側のmypageLogin()を解析した挙動をJSで再現
        driver.execute_script("""
            window.name = 'JKK_TOP';
            var loginWin = window.open('about:blank', 'JKK_WIN', 'width=800,height=600');
            loginWin.location.href = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin';
        """)
        
        time.sleep(10)
        
        # ログイン窓に移動
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        log(f"🔎 ログイン窓を捕捉。Title: {driver.title}")

        # ここでまだ「おわび」なら、Cookieの伝播が遅い
        if "おわび" in driver.title:
            log("🚨 まだ『おわび』です。サーバーに『私は人間です』と再アピールします...")
            driver.refresh()
            time.sleep(10)

        def deep_scan():
            # ページ内の全フレームを虱潰しに探す
            for frame_type in ["frame", "iframe"]:
                fms = driver.find_elements(By.TAG_NAME, frame_type)
                for i in range(len(fms)):
                    try:
                        driver.switch_to.frame(i)
                        log(f"--- Frame[{i}] スキャン中 ---")
                        u = driver.find_elements(By.NAME, "uid")
                        if u:
                            log("🎯 ビンゴ！ログインフォームを発見！")
                            u[0].send_keys(os.environ.get("JKK_ID"))
                            driver.find_element(By.XPATH, "//input[@type='password']").send_keys(os.environ.get("JKK_PASSWORD"))
                            # 送信は 'submit' ではなく、物理クリックを模倣
                            btn = driver.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
                            driver.execute_script("arguments[0].click();", btn)
                            return True
                        driver.switch_to.parent_frame()
                    except:
                        driver.switch_to.default_content()
                        continue
            return False

        if deep_scan():
            log("🚀 ログイン情報を送信しました。")
            time.sleep(15)
            log(f"最終地点: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりません。当時のサイト特有の『隠しフレーム』に阻まれています。")

    except Exception as e:
        log(f"❌ 時代遅れのエラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
