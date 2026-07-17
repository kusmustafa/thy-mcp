import subprocess
import json
import os
import sys

def run_mcp_remote():
    print("THY MCP sunucusuna 'npx mcp-remote' komutu ile bağlanılıyor...")
    
    # İletişim kurmak için JSON-RPC isteğini hazırlıyoruz
    rpc_request = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_active_flights",
            "arguments": {}
        }
    })

    try:
        # Alt işlem olarak (subprocess) npx mcp-remote komutunu başlatıyoruz
        # Sunucuyla etkileşim kurabilmek için stdin ve stdout'u kullanıyoruz
        process = subprocess.Popen(
            ["npx", "-y", "mcp-remote", "https://mcp.turkishtechlab.com/mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print("İstek gönderiliyor...")
        # JSON-RPC isteğini komutun standart girdisine gönderiyoruz
        stdout, stderr = process.communicate(input=rpc_request + '\n', timeout=30)
        
        if process.returncode != 0:
            raise Exception(f"mcp-remote komutu başarısız oldu. Hata: {stderr}")

        print("Yanıt alındı, veriler işleniyor...")
        
        # Çıktıdan sadece geçerli JSON kısmını ayıklamaya çalışıyoruz
        json_output = None
        for line in stdout.splitlines():
            try:
                parsed_line = json.loads(line)
                # Yanıt olduğunu (id: 1) doğrula
                if "id" in parsed_line and parsed_line["id"] == 1:
                    json_output = parsed_line
                    break
            except json.JSONDecodeError:
                continue

        if not json_output or "result" not in json_output or "content" not in json_output["result"]:
             raise Exception(f"Geçerli bir JSON-RPC yanıtı bulunamadı. Tam çıktı: {stdout}")

        mcp_content = json_output["result"]["content"][0]["text"]
        live_data = json.loads(mcp_content)

        formatted_data = {
            "status": "success",
            "totalFlights": len(live_data.get("flights", [])),
            "delayRate": live_data.get("delay_rate", 0.0),
            "averageOccupancy": live_data.get("average_occupancy", 0),
            "chartLabels": live_data.get("top_destinations", []),
            "chartData": live_data.get("destination_counts", []),
            "flights": []
        }

        for flight in live_data.get("flights", []):
            formatted_data["flights"].append({
                "flightNumber": flight.get("flight_number", "N/A"),
                "origin": flight.get("origin", "N/A"),
                "destination": flight.get("destination", "N/A"),
                "estimatedTime": flight.get("estimated_departure", "--:--"),
                "status": flight.get("status_text", "Zamanında")
            })

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=4)
        print("CANLI VERİLER BAŞARIYLA KAYDEDİLDİ.")

    except subprocess.TimeoutExpired:
         process.kill()
         print("[HATA] mcp-remote komutu zaman aşımına uğradı.")
         write_error("mcp-remote komutu zaman aşımına uğradı (Bağlantı veya Yetki hatası olabilir).")
    except Exception as e:
        print(f"\n[HATA] İşlem başarısız oldu: {e}")
        write_error(str(e))

def write_error(error_msg):
    error_data = {
        "status": "error",
        "error_message": f"THY MCP Bağlantı Hatası: {error_msg}",
        "totalFlights": 0, "delayRate": 0, "averageOccupancy": 0,
        "chartLabels": [], "chartData": [], "flights": []
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(error_data, f, ensure_ascii=False, indent=4)
    sys.exit(1)

if __name__ == "__main__":
    # Gerekli ortam değişkenlerini ayarlayalım (mcp-remote'un bu şifreleri nasıl aldığına bağlı olarak)
    # Eğer doğrudan standart girdi veya argüman beklemiyorsa, mcp-remote'un kimlik doğrulama yöntemi 
    # komut satırı arayüzünden farklılık gösterebilir.
    os.environ['MS_USER'] = os.environ.get('MILES_SMILES_USER', '')
    os.environ['MS_PASS'] = os.environ.get('MILES_SMILES_PASS', '')
    
    run_mcp_remote()
