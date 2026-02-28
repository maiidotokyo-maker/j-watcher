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
    # 最新のヘッドレスではなく、あえて挙動が少し鈍い（＝レトロに優しい）古いヘッドレス
    options.add_argument('--headless=old')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1024,768')
    # UAも少し古めの設定にして、サーバーを油断させます
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🕰️ 時代を遡ります。玄関ページへ...")
        driver.get(START_URL)
        time.sleep(10) # 玄関でしっかりとお辞儀（待機）
        
        log("💉 ログイン用『器』を物理的に構築中...")
        # 玄関ページで「ログイン」ボタンを押すのではなく、
        # その場で「JKK_WIN」という名前の自分自身のクローンを作り直すイメージです
        driver.execute_script("""
            window.name = "JKK_TOP";
            var f = document.createElement('form');
            f.action = 'https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin';
            f.method = 'GET';
            f.target = 'JKK_WIN'; // これが重要
            document.body.appendChild(f);
            window.open('', 'JKK_WIN', 'width=800,height=600');
            f.submit();
        """)
        
        time.sleep(15) # セッションが同期されるのをじっくり待つ
        
        # ログイン窓（別窓として開いているはず）へ切り替え
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        
        log(f"🔎 ログイン窓を捕捉。Title: {driver.title}")
        log(f"🔎 Window Name: {driver.execute_script('return window.name;')}")

        if "おわび" in driver.title:
            log("🚨 まだおわびが出ますか...。最終手段、リフレッシュ連打を試みます。")
            driver.refresh()
            time.sleep(10)

        # フォームの探索
        def find_and_fill(d):
            # レトロサイトはフレームに隠れがちなので default_content から全探索
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.XPATH, "//input[@type='password']")
            if u and p:
                log("🎯 ついに『生身』のフォームに到達しました！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # クリックもJSではなく、物理的な座標クリックをエミュレート
                btn = d.find_element(By.XPATH, "//input[@type='image']|//img[contains(@src,'login')]")
                btn.click()
                return True
            
            # フレームがあれば再帰的に
            frames = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    d.switch_to.frame(i)
                    if find_and_fill(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if find_and_fill(driver):
            log("🚀 ログイン情報を送信。成功を祈ります。")
            time.sleep(15)
            log(f"最終URL: {driver.current_url}")
        else:
            log("🚨 フォームが見つかりませんでした。レトロの壁、高し...")

    except Exception as e:
        log(f"❌ 時代錯誤なエラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
