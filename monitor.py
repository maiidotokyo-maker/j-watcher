import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    JKK_ID = os.environ.get("JKK_ID")
    JKK_PASSWORD = os.environ.get("JKK_PASSWORD")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 手順1: ログイン開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        time.sleep(5)
        
        # ログイン窓特定
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        
        # ID/PW入力と送信
        current_handles = set(driver.window_handles)
        driver.execute_script("""
            var f = document.getElementsByTagName('iframe')[0].contentDocument;
            f.getElementsByName('user_id')[0].value = '""" + JKK_ID + """';
            f.getElementsByName('password')[0].value = '""" + JKK_PASSWORD + """';
            f.defaultView.submitNext();
        """)
        
        log("⏳ マイページ移動中...")
        time.sleep(10)
        new_handle = (set(driver.window_handles) - current_handles).pop()
        driver.switch_to.window(new_handle)
        driver.refresh()
        time.sleep(5)

        # 第一ゴール：検索条件ボタンクリック
        log("🔍 第1ゴール：検索条件ボタンをクリック")
        driver.execute_script("""
            var f = document.getElementsByTagName('iframe')[0].contentDocument;
            var btn = f.querySelector("img[src*='btn_search_cond']").parentElement;
            btn.click();
        """)
        time.sleep(10)

        # --- 🚀 ここから第2ゴール：世田谷区を選択 ---
        log("📍 第2ゴール：世田谷区を選択して検索します")
        
        # 世田谷区(112)のチェックボックスを探してクリック
        # サイト構造に合わせてJavaScriptで確実に操作
        driver.execute_script("""
            var f = document.getElementsByTagName('iframe')[0].contentDocument;
            // 世田谷区のチェックボックス(値が112のもの)をチェック
            var setagaya = f.querySelector("input[type='checkbox'][value='112']");
            if(setagaya) {
                setagaya.checked = true;
                console.log("Setagaya Checked");
            }
            // 検索ボタン(btn_search_start)をクリック
            var searchBtn = f.querySelector("img[src*='btn_search_start']").parentElement;
            searchBtn.click();
        """)
        
        log("⏳ 検索結果の表示を待っています...")
        time.sleep(15)
        
        # 最終確認用のスクリーンショット
        driver.save_screenshot("search_result.png")
        log("✨ 検索完了！『search_result.png』を確認してください。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("error_debug.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    from selenium.webdriver.support.ui import WebDriverWait
    main()
