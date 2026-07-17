import os
import json
import requests
import sys

# Şifrelerimizi alıyoruz
MS_USER = os.environ.get("MILES_SMILES_USER")
MS_PASS = os.environ.get("MILES_SMILES_PASS")

def get_real_thy_data():
    print("THY MCP Canlı Bağlantısı Başlatılıyor...")
    
    token_url = "https://mcp.turkishtechlab.com/oauth/token"
    mcp_url = "https://mcp.turkishtechlab.com/mcp"
    
    login_payload = {
        "grant_type": "password",
        "username": MS_USER,
        "password": MS_PASS,
        "scope": "openid flight.read miles.read"
    }
    
    try:
        print("Miles&Smiles ile canlı kimlik doğrulaması deneniyor...")
        token_response = requests.post(token_url, data=login_payload, timeout=15)
        
        # Giriş başarısızsa doğrudan hata fırlat ve durdur (Fake veri yazma!)
        if token_response.status_code != 200:
            raise Exception(f"Giriş Başarısız (Sunucu Yanıtı: {token_response.status_code} - {token_response.text})")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise Exception("Access token alınamadı.")
            
        print("Giriş başarılı! Canlı uçuş verileri MCP sunucusundan isteniyor...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        tool_call = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_active_flights",
                "arguments": {}
            }
        }

        mcp_response = requests.post(mcp_url, json=tool_call, headers=headers, timeout=15)
        
        if mcp_response.status_code != 200:
            raise Exception(f"MCP Sunucu Hatası (Durum Kodu: {mcp_response.status_code})")
            
        raw_data = mcp_response.json()

        # MCP'den gelen gerçek verileri kontrol ediyoruz
        if "result" in raw_data and "content" in raw_data["result"]:
            mcp_content = raw_data["result"]["content"][0]["text"]
            live_data = json.loads(mcp_content)
            
            # Sadece ve sadece canlı gelen verilerle JSON dosyası oluşturuluyor
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
            
            # Dosyayı başarılı canlı verilerle kaydet
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=4)
            print("CANLI VERİLER BAŞARIYLA KAYDEDİLDİ.")
            
        else:
            raise Exception("MCP sunucusundan beklenen uçuş verisi yapısı gelmedi.")
            
    except Exception as e:
        print(f"\n[HATA] Canlı veri akışı kesildi: {e}")
        print("Kullanıcı talebi gereği hiçbir simüle/fake veri oluşturulmadı.")
        
        # Dashboard'a hata durumunu bildiren boş şablonu yaz
        error_data = {
            "status": "error",
            "error_message": str(e),
            "totalFlights": 0,
            "delayRate": 0,
            "averageOccupancy": 0,
            "chartLabels": [],
            "chartData": [],
            "flights": []
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
            
        # GitHub Actions'ın hata vererek (Kırmızı) durmasını sağla (Böylece loglardan hata incelenebilir)
        sys.exit(1)

if __name__ == "__main__":
    get_real_thy_data()
