import requests
import json
import time

# --- 1. 設定區 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"  # 確保與 docker pull 的名稱一致

# --- 2. 模擬感測器輸入 (假裝這是從 MLX9064 或 LD2450 讀到的) ---
fake_sensor_data = {
    "timestamp": "23:15:00",
    "location": "Front_Door",
    "status": "Moving_Object_Detected",
    "temperature_avg": 36.5
}

def ask_llm_for_command(sensor_data):
    print(f"📡 正在傳送數據給 {MODEL_NAME} (極速模式)...")
    
    # --- 3. 建構極簡 Prompt ---
    # 去除所有客套話，直接定義規則，減少 Prefill 運算時間
    prompt = f"""Role: IoT Security Controller.
Input Data: {json.dumps(sensor_data)}
Rules:
1. If location is "Front_Door" AND time > "22:00", risk is HIGH.
2. Output strictly JSON.
Output Schema: {{"risk": "low|high", "cmd": "ALARM_ON|IGNORE", "reason": "brief explanation"}}
"""

    # --- 4. 準備 Payload (Pi 5 專屬優化參數) ---
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,       # 關閉打字機效果，一次拿回結果
        "format": "json",      # 強制 JSON 模式 (Qwen 強項)
        "keep_alive": -1,      # 🔥 關鍵：永遠保持熱機，不要卸載模型！
        "options": {
            "num_ctx": 1024,      # 🔥 關鍵：上下文鎖死在 512 (省記憶體)
            "num_predict": 128,  # 🔥 限制：回答不准超過 128 tokens (強迫簡短)
            "num_thread": 4,     # 榨乾 Pi 5 的 4 顆核心
            "temperature": 0.0   # 絕對理性模式，不隨機，速度最快
        }
    }

    try:
        # 開始計時
        start_time = time.time()
        
        # 發送請求 (Timeout 設為 10 秒，因為熱機後應該要很快)
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        
        # 結束計時
        end_time = time.time()
        duration = end_time - start_time
        
        # 解析回應
        result = response.json()
        llm_output = result['response']
        command_data = json.loads(llm_output)

        # --- 5. 顯示結果 ---
        print(f"✅ 成功! (耗時: {duration:.2f}秒)")
        print("-" * 30)
        print("⚙️  指令解析:")
        print(f"   風險: {command_data.get('risk')}")
        print(f"   動作: {command_data.get('cmd')}")
        print(f"   理由: {command_data.get('reason')}")
        print("-" * 30)
        
        return command_data

    except requests.exceptions.Timeout:
        print("❌ 錯誤: 回應超時 (超過10秒)。可能模型正在冷啟動。")
    except requests.exceptions.ConnectionError:
        print("❌ 錯誤: 連線失敗。請檢查 Docker 是否執行中? Port 是否為 11434?")
    except json.JSONDecodeError:
        print("❌ 錯誤: JSON 解析失敗。模型回傳了非 JSON 格式。")
        print("原始回傳:", result.get('response', 'Empty'))
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")

if __name__ == "__main__":
    # 執行主程式
    ask_llm_for_command(fake_sensor_data)
