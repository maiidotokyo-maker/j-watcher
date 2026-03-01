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
        log("🚪 ログイン開始")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/service/mypageMenu")
        
        # 1. ログイン窓が出るまで待機
        time.sleep(10)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            log("🪟 ログイン窓に切り替え")

        # 2. 【核心】全iframeを走査してID/PWを叩き込むJavaScript
        log("⌨️ 全iframeへID/PWを強制注入...")
        inject_script = """
        var inputs_found = false;
        function fill(doc) {
            var u = doc.getElementsByName('user_id')[0];
            var p = doc.getElementsByName('password')[0];
            if (u && p) {
                u.value = arguments[0];
                p.value = arguments[1];
                doc.defaultView.submitNext();
                inputs_found = true;
            }
        }
        fill(document);
        var frames = document.getElementsByTagName('iframe');
        for (var i = 0; i < frames.length; i++) {
            try { fill(frames[i].contentDocument); } catch(e) {}
        }
        return inputs_found;
        """
        
        success = driver.execute_script(inject_script, JKK_ID, JKK_PASSWORD)
        
        if success:
            log("🚀 注入成功！遷移を待ちます...")
            time.sleep(15)
            driver.switch_to.default_content()
            driver.save_screenshot("final_hope.png")
            log("📸 『final_hope.png』を確認してください。クジラが消えていれば勝ちです。")
        else:
            log("⚠️ 入力欄が見つかりませんでした。")
            driver.save_screenshot("not_found.png")

    except Exception as e:
        log(f"⚠️ エラー: {e}")
        driver.save_screenshot("last_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
