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
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        log("🚪 ログイン開始（再帰探索モード）")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 1. ログイン窓へ移動
        time.sleep(10)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("🪟 ログイン窓を捕捉")

        # 2. 【核心】再帰的にすべてのiframeの奥底まで探索するJavaScript
        log("⛏️ 全iframeの奥底までID/PWを注入します...")
        deep_inject_script = """
        var found = false;
        function findAndFill(win) {
            if (!win || found) return;
            try {
                var doc = win.document;
                var u = doc.getElementsByName('user_id')[0];
                var p = doc.getElementsByName('password')[0];
                if (u && p) {
                    u.value = arguments[0];
                    p.value = arguments[1];
                    // フォーム送信
                    if (win.submitNext) { win.submitNext(); } 
                    else if (doc.defaultView.submitNext) { doc.defaultView.submitNext(); }
                    found = true;
                    return;
                }
                // 子iframeを再帰探索
                var fs = win.frames;
                for (var i = 0; i < fs.length; i++) {
                    findAndFill(fs[i]);
                }
            } catch (e) {}
        }
        findAndFill(window);
        return found;
        """
        
        # 3. 実行
        for attempt in range(5): # 最大5回、時間を置いてリトライ
            success = driver.execute_script(deep_inject_script, JKK_ID, JKK_PASSWORD)
            if success:
                log("🚀 ついにヒット！注入と送信を実行しました。")
                break
            log(f"⏳ 探索中... (試行 {attempt+1}/5)")
            time.sleep(3)

        # 4. 遷移後の結果
        time.sleep(15)
        driver.switch_to.default_content()
        driver.save_screenshot("final_recursive_result.png")
        log("📸 結果を『final_recursive_result.png』に保存しました。")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("recursive_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
