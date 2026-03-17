import requests
import time
import json
import subprocess

# 取得樹莓派溫度的輔助函式 (僅限 Raspberry Pi OS 環境)
def get_pi_temp():
    try:
        res = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True)
        return res.stdout.strip().replace("temp=", "")
    except Exception:
        return "無法取得溫度"

def run_benchmark(model_name, user_command):
    url = "http://localhost:11434/api/generate"
    
    # 升級版系統提示詞：加入 Few-Shot 範例，明確定義數值對應關係
    system_prompt = """
    你是一個智慧風扇的控制核心。請將指令轉換為JSON格式。
    JSON必須嚴格包含以下三個欄位：
    - action: "set_fan"
    - speed: 0到100的整數 (最大/全速=100, 中等=50, 最小/微風=10, 關閉/停止=0)
    - direction: "left", "right", "center", 或 "follow" (追蹤人體)
    
    範例1：
    輸入：幫我把風扇關掉。
    輸出：{"action": "set_fan", "speed": 0, "direction": "center"}
    
    範例2：
    輸入：太熱了，風速開到最大，往左邊吹。
    輸出：{"action": "set_fan", "speed": 100, "direction": "left"}
    """
    
    payload = {
        "model": model_name,
        "prompt": user_command,
        "system": system_prompt,
        "stream": True,
        "format": "json",  # 強制 Ollama 只輸出乾淨的 JSON 結構，不帶 Markdown 標籤
        "options": {
            "num_ctx": 512,  # 限制上下文長度以節省記憶體
            "num_thread": 3  # Pi 5 有 4 核，保留 1 核給 Linux 系統和背景程式
        }
    }

    print(f"🚀 開始測試模型: {model_name}")
    print(f"🌡️ 測試前系統溫度: {get_pi_temp()}")
    print("-" * 40)
    
    start_time = time.time()
    first_token_time = None
    token_count = 0
    full_response = "" # 用來收集完整的 JSON 字串
    
    try:
        response = requests.post(url, json=payload, stream=True)
        print("💡 模型串流輸出: ", end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                body = json.loads(line)
                token_count += 1
                
                # 記錄第一個 Token 出現的時間
                if first_token_time is None:
                    first_token_time = time.time()
                    
                word = body.get("response", "")
                full_response += word
                print(word, end="", flush=True)
                
                if body.get("done"):
                    break
                    
    except requests.exceptions.ConnectionError:
        print("\n錯誤：無法連線到 Ollama API，請確認服務已啟動。")
        return
    except Exception as e:
        print(f"\n發生未預期的錯誤: {e}")
        return

    end_time = time.time()
    print("\n")
    
    # 驗證 Python 字典解析與變數提取
    print("-" * 40)
    try:
        parsed_json = json.loads(full_response)
        print("✅ JSON 解析成功！即將發送給硬體的參數為:")
        print(f"   ➔ 目標風速 (Speed): {parsed_json.get('speed')} %")
        print(f"   ➔ 目標方向 (Direction): {parsed_json.get('direction')}")
    except json.JSONDecodeError:
        print("❌ JSON 解析失敗，模型輸出了非標準格式。")

    # 計算效能指標
    ttft = first_token_time - start_time
    total_time = end_time - start_time
    generate_time = end_time - first_token_time
    tps = (token_count - 1) / generate_time if generate_time > 0 else 0
    
    print("-" * 40)
    print("📊 效能測試報告")
    print(f"🔸 模型名稱: {model_name}")
    print(f"🔸 輸入指令: {user_command}")
    print(f"⏱️ 首字延遲 (TTFT): {ttft:.2f} 秒")
    print(f"⚡ 推論速度 (TPS):  {tps:.2f} tokens/秒")
    print(f"⏳ 總耗時:          {total_time:.2f} 秒")
    print(f"📝 總生成 Tokens:   {token_count}")
    print(f"🌡️ 測試後系統溫度: {get_pi_temp()}")
    print("-" * 40)

if __name__ == "__main__":
    # 鎖定效能最佳的 0.5B 模型
    TARGET_MODEL = "qwen2.5:0.5b" 
    
    # 測試極端詞彙：觀察 speed 是否能正確達到 100
    TEST_COMMAND = "現在有點太熱了，幫我把風扇往左邊吹並且風速開到最大。"
    run_benchmark(TARGET_MODEL, TEST_COMMAND)
    
    print("\n" + "="*40 + "\n")
    
    # 執行第二次測試 (觀察 KV Cache 效果)
    print("🔄 執行第二次測試 (觀察 KV Cache 效果)...")
    TEST_COMMAND_2 = "改往右邊吹，風速調小一點。"
    run_benchmark(TARGET_MODEL, TEST_COMMAND_2)
