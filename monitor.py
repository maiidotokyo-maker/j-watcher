import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定 ---
# 直リンク禁止！必ず「玄関」から入る
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
    # レトロサイトに怪しまれないための標準的なユーザーエージェント
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_and_check(driver):
    print(f"🏁 玄関ページ（トップページ）へアクセス: {START_URL}")
    driver.get(START_URL)
    time.sleep(8) # レトロサイトは読み込みに時間がかかるので待つ

    # 1. ログイン画面を開く（リンクを探してクリック）
    print("🖱️ ログインボタンを探してクリックします...")
    try:
        # aタグや画像からログインらしきものを探す
        elements = driver.find_elements(By.XPATH, "//a | //img")
        login_btn = next((el for el in elements if 'ログイン' in el.text or 'login' in el.get_attribute('src').lower() or 'login' in el.get_attribute('href').lower()), None)
        
        if login_btn:
            login_btn.click()
            print("✅ ログインボタンをクリックしました！")
        else:
            print("⚠️ ログインボタンが見つかりません。")
            return False
    except Exception as e:
        print(f"❌ ボタンクリックでエラー: {e}")
        return False

    time.sleep(10) # 画面遷移またはポップアップを待つ

    # --- 🪟 ポップアップ対応 ---
    # もし新しいウィンドウが開いていたら、そっちに乗り換える
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        print("🪟 新しいウィンドウ（ポップアップ）に移動しました。")

    # 2. フレームを切り替えながらID/PASSを探す（対フレームセット兵器）
    print("⌨️ ログインフォームを探しています...")
    logged_in = False
    
    # メインのHTML内に直接あるかチェック
    try:
        uid_input = driver.find_element(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user')]")
        pw_input = driver.find_element(By.XPATH, "//input[@type='password']")
        uid_input.send_keys(JKK_ID)
        pw_input.send_keys(JKK_PASS)
        pw_input.submit() # Enterキーを押すのと同じ効果
        print("✅ メイン画面でログイン情報を送信しました！")
        logged_in = True
    except:
        # メインになければ、フレームの中を一つずつ覗き込む
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for i, frame in enumerate(frames):
            try:
                driver.switch_to.frame(frame)
                uid_input = driver.find_element(By.XPATH, "//input[contains(@name, 'uid') or contains(@id, 'uid') or contains(@name, 'user')]")
                pw_input = driver.find_element(By.XPATH, "//input[@type='password']")
                
                uid_input.send_keys(JKK_ID)
                pw_input.send_keys(JKK_PASS)
                pw_input.submit()
                print(f"✅ フレーム[{i}]の中でログイン情報を送信しました！")
                logged_in = True
                driver.switch_to.default_content() # フレームから脱出
                break
            except:
                driver.switch_to.default_content() # なければ脱出して次へ

    if not logged_in:
        print("❌ どうしても入力フォームが見つかりませんでした。")
        driver.save_screenshot("retro_login_failed.png")
        return False

    # --- ログイン後の待機 ---
    print("⏳ ログイン処理中...")
    time.sleep(15)

    # 以降、空室検索の処理（今回はまずログイン突破を最優先にするため、簡易的な生存確認のみ）
    driver.save_screenshot("login_success_check.png")
    print("📸 ログイン後の画面を保存しました。Artifactsで確認してください。")
    
    # マイページっぽい文字があるか確認
    body_text = driver.find_element(By.TAG_NAME, "body").text
    if "ログアウト" in body_text or "空室" in body_text or "退去" in body_text:
        return True
    
    return False

def main():
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚨 ログイン突破成功！（仮）")
            # 検索ロジックはログインが安定してから追加します
        else:
            print("👀 ログイン突破ならず...")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
