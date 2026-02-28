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
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = None
    try:
        driver = setup_driver()
        
        log("🕰️ 玄関ページに潜入...")
        driver.get(START_URL)
        time.sleep(10) # 玄関でサーバーが落ち着くのを待つ
        
        log("💉 サイト自身のJavaScript（mypageLogin）に身を任せます...")
        # 自分でURLを開かず、サイトの関数を「踏み台」にする
        # 同時に window.open を横取り（フック）して、ヘッドレスでも確実に窓を捉える
        driver.execute_script("""
            window.target_url = null;
            var originalOpen = window.open;
            window.open = function(url, name, specs) {
                window.target_url = url;
                window.target_name = name;
                return originalOpen(url, name, specs);
            };
            // サイトのログイン関数をキック
            if(typeof mypageLogin === 'function') {
                mypageLogin();
            } else {
                // 関数がない場合はボタンを探して物理クリック
                var btn = document.querySelector('img[src*="btn_login"], a[onclick*="mypageLogin"]');
                if(btn) btn.click();
            }
        """)
        
        time.sleep(15) # ポップアップの生成とJSPの裏通信を待つ

        # 窓の切り替え
        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[-1])
            log(f"🪟 サイトが自ら開いた窓に移動完了: {driver.title}")
        else:
            log("🚨 窓が分かれませんでした。メイン画面のURLを確認します。")

        log(f"DEBUG: 現在のURL: {driver.current_url}")
        
        # --- ここからがレトロ迷宮（Frameset）探索 ---
        def deep_hunt(d):
            # name属性が 'uid' のものを探す（JSPの定番）
            u = d.find_elements(By.NAME, "uid")
            p = d.find_elements(By.NAME, "passwd") # password ではなく passwd の可能性
            if not p:
                p = d.find_elements(By.XPATH, "//input[@type='password']")

            if u and p:
                log("🎯 ついに『本物の入力欄』を捕捉！")
                u[0].send_keys(os.environ.get("JKK_ID"))
                p[0].send_keys(os.environ.get("JKK_PASSWORD"))
                
                # 送信。画像ボタン（<input type="image">）を優先
                btn = d.find_elements(By.XPATH, "//input[@type='image'] | //img[contains(@src, 'login')]")
                if btn:
                    log("🖱️ ログイン画像ボタンをクリック。")
                    btn[0].click()
                else:
                    p[0].submit()
                return True
            
            # フレーム構造（Frameset/Frame）を再帰的に掘る
            frames = d.find_elements(By.TAG_NAME, "frame") + d.find_elements(By.TAG_NAME, "iframe")
            for i in range(len(frames)):
                try:
                    d.switch_to.frame(i)
                    if deep_hunt(d): return True
                    d.switch_to.parent_frame()
                except: continue
            return False

        if deep_hunt(driver):
            log("🚀 ログイン情報を送信。運命の瞬間です。")
            time.sleep(15)
            log(f"最終URL: {driver.current_url}")
            log(f"最終Title: {driver.title}")
        else:
            log("🚨 依然としてフォームがありません。")
            log(f"最終ソース断片: {driver.page_source[-500:]}")

    except Exception as e:
        log(f"❌ 時代錯誤エラー: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
