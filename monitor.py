def select_area_and_scan(driver):
    print("📍 エリア選択画面へ移動します...")
    # 直接エリア選択のURLを叩く（ログインセッションが維持されていれば可能）
    driver.get("https://jhomes.to-kousya.or.jp/search/jkknet/pc/vacancy/area")
    time.sleep(8)

    # 1. 世田谷区のチェックボックス(113)を選択して検索実行
    print("🎯 世田谷区を選択中...")
    selected = driver.execute_script("""
        function selectRecursive(w) {
            try {
                let cb = w.document.querySelector("input[value='113']");
                if (cb) {
                    cb.click();
                    // 検索実行ボタン（画像またはJS関数）
                    let btn = w.document.querySelector('img[src*="search"], a[onclick*="doSearch"]');
                    if (btn) btn.click(); else if (w.doSearch) w.doSearch();
                    return true;
                }
                for (let i = 0; i < w.frames.length; i++) {
                    if (selectRecursive(w.frames[i])) return true;
                }
            } catch(e) {}
            return false;
        }
        return selectRecursive(window);
    """)

    if not selected:
        print("❌ 世田谷区の選択に失敗しました。")
        driver.save_screenshot("area_select_failed.png")
        return False

    print("🔎 空室状況をスキャン中...")
    time.sleep(10)

    # 2. 別窓が開いた場合のハンドリング
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    # 3. 「空室」を意味するキーワードがあるか全フレームから探す
    # (JKKは空室がある場合、間取り[DK, LDK]や「詳細」ボタンが出現する)
    found = driver.execute_script("""
        function scanRecursive(w) {
            try {
                const keywords = ['DK', 'LDK', '1DK', '2DK', '詳細'];
                let text = w.document.body.innerText.toUpperCase();
                if (keywords.some(k => text.includes(k))) return true;
                for (let i = 0; i < w.frames.length; i++) {
                    if (scanRecursive(w.frames[i])) return true;
                }
            } catch(e) {}
            return false;
        }
        return scanRecursive(window);
    """)
    return found

# --- main関数の修正案 ---
def main():
    driver = setup_driver()
    try:
        if login_and_check(driver):
            print("🚀 ログイン成功。エリアスキャンを開始します...")
            if select_area_and_scan(driver):
                print("🚨 【空室あり】世田谷区に空室が見つかりました！")
                if DISCORD_WEBHOOK_URL:
                    requests.post(DISCORD_WEBHOOK_URL, json={
                        "content": "🏠 **JKK世田谷区：空室あり！**\n今すぐ確認してください！\nhttps://jhomes.to-kousya.or.jp/search/jkknet/pc/"
                    })
            else:
                print("👀 現在、世田谷区に空室はありません。")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        driver.quit()
