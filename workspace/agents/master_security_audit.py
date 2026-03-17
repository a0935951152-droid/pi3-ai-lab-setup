import os
import sys
import socket
import requests
import subprocess
from pathlib import Path

# 定義顏色
G = '\033[92m' # Green
R = '\033[91m' # Red
Y = '\033[93m' # Yellow
C = '\033[96m' # Cyan
NC = '\033[0m' # No Color

ENV_PATH = Path.home() / "ai-lab" / ".env"
TARGET_HOST = "127.0.0.1" # 檢查本機

def print_header(title):
    print(f"\n{C}=================================================={NC}")
    print(f"{C}   {title}{NC}")
    print(f"{C}=================================================={NC}")

def check_env():
    print_header("1. 環境變數檢查 (.env)")
    if not ENV_PATH.exists():
        print(f"{R}❌ 找不到 .env 檔案！{NC}")
        return {}
    
    config = {}
    with open(ENV_PATH, "r") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                config[k] = v

    # 檢查關鍵變數
    keys = ["NGROK_DOMAIN", "NGROK_AUTHTOKEN", "WEBUI_SECRET_KEY", "IP_NGINX"]
    for k in keys:
        val = config.get(k, None)
        if val:
            if "KEY" in k or "TOKEN" in k:
                print(f"✅ {k:20}: {val[:5]}...****** (已遮蔽)")
            else:
                print(f"✅ {k:20}: {val}")
        else:
            print(f"{R}❌ {k:20}: 未設定！{NC}")
    return config

def check_ports():
    print_header("2. 端口防火牆檢查 (Port Security)")
    # 規則：(端口, 描述, 預期狀態)
    rules = [
        (80, "Nginx (入口)", True),
        (22, "SSH (遠端)", True),
        (8080, "WebUI (後台)", False),
        (11434, "Ollama (模型)", False)
    ]
    
    for port, desc, expect_open in rules:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((TARGET_HOST, port))
        sock.close()
        
        is_open = (result == 0)
        status_icon = f"{G}🟢 開放{NC}" if is_open else f"{R}🔴 關閉{NC}"
        
        if is_open == expect_open:
            print(f"✅ {desc:15} Port {port:<5}: {status_icon} (符合預期)")
        else:
            print(f"{R}❌ {desc:15} Port {port:<5}: {status_icon} (安全漏洞!){NC}")

def check_docker_network(config):
    print_header("3. Docker 內部網路檢查")
    try:
        # 獲取所有容器的 IP
        cmd = "docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -q)"
        output = subprocess.check_output(cmd, shell=True).decode()
        
        expected_ips = {
            "nginx-proxy": config.get("IP_NGINX", ""),
            "open-webui": config.get("IP_WEBUI", ""),
            "ollama": config.get("IP_OLLAMA", "")
        }

        for line in output.strip().split('\n'):
            if not line: continue
            name = line.split(" - ")[0].replace("/", "")
            ip = line.split(" - ")[1]
            
            # 檢查是否符合 .env 設定
            is_match = False
            for key, val in expected_ips.items():
                if key in name and val == ip:
                    is_match = True
            
            if "ngrok" in name:
                print(f"✅ {name:15}: {ip} (Ngrok 容器運行中)")
            elif is_match:
                print(f"✅ {name:15}: {ip} (固定 IP 正確)")
            else:
                print(f"{Y}⚠️  {name:15}: {ip} (IP 與 .env 設定不符或未定義){NC}")

    except Exception as e:
        print(f"{R}❌ Docker 檢查失敗: {e}{NC}")

def check_ngrok_connectivity(domain):
    print_header("4. Ngrok 外網穿透實測")
    
    if not domain:
        print(f"{R}❌ 無法測試：未設定 NGROK_DOMAIN{NC}")
        return

    url = f"https://{domain}"
    print(f"📡 正在連線到: {url} ...")
    
    try:
        # 設定 5 秒超時
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"{G}✅ 連線成功！狀態碼: 200 OK{NC}")
            print(f"   網站標題: Open WebUI (或登入頁面)")
            print(f"   🎉 恭喜！你的 Pi 5 已成功暴露在網際網路上。")
        else:
            print(f"{Y}⚠️  連線通了，但狀態碼是: {response.status_code}{NC}")
            
    except requests.exceptions.ConnectionError:
        print(f"{R}❌ 連線失敗：無法找到伺服器 (DNS 或 Ngrok 未啟動){NC}")
        print("   建議檢查：docker compose logs ngrok")
    except Exception as e:
        print(f"{R}❌ 發生錯誤: {e}{NC}")

if __name__ == "__main__":
    print(f"🕵️  開始進行 Raspberry Pi 5 AI Lab 安全性總體檢...")
    
    # 1. 檢查 .env
    conf = check_env()
    
    # 2. 檢查端口
    check_ports()
    
    # 3. 檢查 Docker
    check_docker_network(conf)
    
    # 4. 檢查 Ngrok (這是你最擔心的部分)
    ngrok_domain = conf.get("NGROK_DOMAIN", "").replace("https://", "").strip()
    check_ngrok_connectivity(ngrok_domain)
    
    print(f"\n{C}🏁 檢查結束{NC}")
