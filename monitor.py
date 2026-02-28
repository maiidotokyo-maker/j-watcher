import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
START_URL = "https://jhomes.to-kousya.or.jp/search/jkknet/pc/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JKK_ID = os.environ.get("JKK_ID", "").strip()
JKK_PASS = os.environ.get("JKK_PASSWORD", "").strip()

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_check(driver):
    print(f"🏁 玄関ページへアクセス: {START_URL}")
    driver.get(START_URL)
    time.sleep(8) # セッションCookieをもらうために長めに待機

    # 1. ログイン画面への遷移（Noneエラー対策版）
    print("🖱️ ログイン画面へ進みます...")
    try:
        clicked = False
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        
        # ボタンを探してクリックする関数（安全設計）
        def try_click_login():
            elements = driver.find_elements(By.XPATH, "//a | //img | //input")
            for el in elements:
                text = el.text or ""
                src = el.get_attribute('src') or ""
                href = el.get_attribute('href') or ""
                if 'ログイン' in text or 'login' in src.lower() or 'login' in href.lower() or 'mypage' in href.lower():
                    el.click()
                    return True
            return False

        # メイン画面を探す
        if try_click_login():
            clicked = True
            print("✅ メイン画面でログインボタンをクリックしました！")
        else:
            # フレームの中を探す
            for i, frame in enumerate(frames):
                driver.switch_to.frame(frame)
                if try_click_login():
                    clicked = True
                    print(f"✅ フレーム[{i}]の中でログインボタンをクリックしました！")
                    driver.switch_to.default_content()
                    break
                driver.switch_to.default_content()

        if not clicked:
            print("⚠️ ボタンが見つからないため、セッションを保持したまま直接ログインURLへ移動します。")
            # 玄関を踏んでCookieを持っているので、直接移動しても弾かれないはず
            driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")
            
    except Exception as e:
        print(f"❌ ボタン検索中に予期せぬエラー: {e}")
        driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/mypageLogin")

    time.sleep(10)

    # 2. ログインフォームを探して入力（対フレームセット兵器）
    print("⌨️ ログインフォームを探しています...")
    logged_in = False
    
    # メインのHTML内をチェック
    try:
        uid_input = driver.find_element(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'user')]")
        pw_input = driver.find_element(By.XPATH, "//input[@type='password']")
        uid_input.send_keys(JKK_ID)
        pw_input.send_keys(JKK_PASS)
        pw_input.submit()
        print("✅ メイン画面でログイン情報を送信しました！")
        logged_in = True
    except:
        # メインになければ、フレームの中を一つずつ覗き込む
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(frames):
            try:
                driver.switch_to.frame(frame)
                uid_input = driver.find_element(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user') or contains(@id, 'user')]")
                pw_input = driver.find_element(By.XPATH, "//input[@type='password']")
                
                uid_input.send_keys(JKK_ID)
                pw_input.send_keys(JKK_PASS)
                pw_input.submit()
                print(f"✅ フレーム[{i}]の中でログイン情報を送信しました！")
                logged_in = True
                driver.switch_to.default_content()
                break
            except:
                driver.switch_to.default_content()

    if not logged_in:
        print("❌ どうしても入力フォームが見つかりませんでした。")
        driver.save_screenshot("login_form_missing.png")
        return False

    # 3. ログイン結果の確認
    print("⏳ ログイン処理中...")
    time.sleep(15)
    
    driver.save_screenshot("login_result.png")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    
    if "ログアウト" in body_text or "空室" in body_text or "退去" in body_text or "メニュー" in body_text:
        return True
    
    # 別フレームに結果が出ているかもしれないので確認
    frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
            text = driver.find_element(By.TAG_NAME, "body").text
            if "ログアウト" in text or "空室" in text or "退去" in text or "メニュー" in text:
                driver.switch_to.default_content()
                return True
            driver.switch_to.default_content()
        except:
            driver.switch_to.default_content()

    print("❌ ログイン成功を証明するテキストが見つかりません。")
    return False

def main():
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚨 ログイン突破成功！！！")
        else:
            print("👀 ログイン突破ならず...")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
