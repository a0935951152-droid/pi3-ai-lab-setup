# 🚀 Raspberry Pi AI Lab (Ollama + Open WebUI)

這是一個專為 Raspberry Pi（針對 Pi 5 進行了記憶體優化）設計的本地端 AI 實驗室部署架構。透過 Docker Compose，將大型語言模型引擎、圖形化網頁介面、安全反向代理以及外網穿透隧道一次整合。

## 🏗️ 系統架構

本專案包含四個核心微服務，並透過自訂的 Docker Bridge 網路 (`ai-net`) 進行靜態 IP 隔離與通訊：

1. **Ollama (`ollama`)**: AI 模型執行核心，負責載入與推論 LLM 模型。已加入 `OLLAMA_NUM_PARALLEL=1` 與 `MAX_LOADED_MODELS=1` 來優化 Pi 的記憶體佔用。
2. **Open WebUI (`open-webui`)**: 提供類似 ChatGPT 的友善網頁介面，強制開啟身分驗證，保障私有模型安全。
3. **Nginx (`nginx`)**: 作為內部網路的安全閘道（Reverse Proxy），統一處理 HTTP 請求並記錄 Access/Error Logs。
4. **Ngrok (`ngrok`)**: 提供外網連線隧道，讓你出門在外也能透過專屬網域連回 Pi 上的 AI 實驗室。

---

## 📂 資料夾結構準備

在啟動容器之前，請確保專案目錄下有以下資料夾結構與設定檔：

```text
ai-lab/
├── docker-compose.yml
├── .env                     # 環境變數設定檔 (需自行建立)
├── models/
│   └── llm/                 # Ollama 模型下載存放區
├── docker/
│   ├── open-webui/          # WebUI 用戶資料與設定庫
│   └── nginx/
│       └── default.conf     # Nginx 路由設定檔
└── logs/                    # Nginx 存取與錯誤日誌

# 網路設定 (Network)
SUBNET_CIDR=172.20.0.0/16
GATEWAY_IP=172.20.0.1
IP_OLLAMA=172.20.0.2
IP_WEBUI=172.20.0.3
IP_NGINX=172.20.0.4

# Open WebUI 設定
# 產生一組隨機密碼作為 SECRET_KEY，例如使用指令：openssl rand -hex 32
WEBUI_SECRET_KEY=your_secure_random_secret_key_here

# Ngrok 外網穿透設定
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
NGROK_DOMAIN=your-custom-domain.ngrok-free.app

🚀 啟動與使用指南
1. 啟動服務
確保 Docker 與 Docker Compose 已安裝，在專案根目錄執行：

Bash
docker compose up -d
2. 下載 AI 模型
初次啟動後，Ollama 內部是空的。你需要進入容器下載模型（例如 qwen:0.5b 或是 llama3.2:1b 等輕量模型）：

Bash
docker exec -it ollama ollama run qwen:0.5b
3. 連線測試
內網存取: 打開瀏覽器輸入 http://localhost (或你的 Pi 區域網路 IP)。

外網存取: 打開瀏覽器輸入你設定的 Ngrok 網域 https://your-custom-domain.ngrok-free.app。

首次進入 WebUI 時，請點擊「Sign Up」註冊第一組管理員帳號。

🛑 停止與清理
停止所有服務並保留資料：

Bash
docker compose down
若要連同自訂網路一起徹底移除（注意：掛載的實體 volume 資料夾不會被刪除）：

Bash
docker compose down -v
