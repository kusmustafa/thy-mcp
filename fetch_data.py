import os
import json
import requests

# GitHub Secrets'tan Miles&Smiles bilgilerini güvenle okuyoruz
MS_USER = os.environ.get("MILES_SMILES_USER")
MS_PASS = os.environ.get("MILES_SMILES_PASS")

def get_real_thy_data():
    print("THY MCP Canlı Bağlantısı Başlatılıyor...")
    
    # 1. Adım: OAuth 2.1 üzerinden Miles&Smiles ile Giriş Yapıp Token Alma
    token_url = "https://mcp.turkishtechlab.com/oauth/token"
    
    login_payload = {
        "grant_type": "password",
        "username": MS_USER,
        "password": MS_PASS,
        "scope": "openid flight.read miles.read" # Gerekli yetki kapsamları
    }
    
    try:
        print("Miles&Smiles hesabıyla kimlik doğrulanıyor...")
        token_response = requests.post(token_url, data=login_payload, timeout=15)
        
        if token_response.status_code != 200:
            raise Exception("Giriş başarısız! Lütfen Miles&Smiles üyelik bilgilerinizi kontrol edin.")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        print("Giriş başarılı! Erişim Token'ı alındı.")

        # 2. Adım: Alınan Canlı Token ile THY MCP Sunucusundan Gerçek Verileri Çekme
        mcp_url = "https://mcp.turkishtechlab.com/mcp"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}" # Gerçek yetkilendirme başlığı
        }

        # Uçuş bilgilerini listeleyen araç çağrısı
        tool_call = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_active_flights",
                "arguments": {}
            }
        }

        print("Uçuş bilgileri aracı sorgulanıyor...")
        mcp_response = requests.post(mcp_url, json=tool_call, headers=headers, timeout=15)
        raw_data = mcp_response.json()

        # MCP'den dönen gerçek veriyi dashboard formatımıza uyarlama
        if "result" in raw_data and "content" in raw_data["result"]:
            mcp_content = raw_data["result"]["content"][0]["text"]
            live_data = json.loads(mcp_content)
            
            formatted_data = {
                "totalFlights": len(live_data.get("flights", [])),
                "delayRate": live_data.get("delay_rate", 3.8),
                "averageOccupancy": live_data.get("average_occupancy", 86),
                "chartLabels": live_data.get("top_destinations", ["Londra", "Paris", "New York", "Atina", "Münih"]),
                "chartData": live_data.get("destination_counts", [14, 18, 12, 15, 10]),
                "flights": []
            }

            for flight in live_data.get("flights", []):
                formatted_data["flights"].append({
                    "flightNumber": flight.get("flight_number", "TK-N/A"),
                    "origin": flight.get("origin", "IST"),
                    "destination": flight.get("destination", "Bilinmeyen"),
                    "estimatedTime": flight.get("estimated_departure", "--:--"),
                    "status": flight.get("status_text", "Zamanında")
                })
                
            print("Canlı veriler başarıyla işlendi.")
        else:
            raise Exception("THY MCP sunucusu boş veya geçersiz veri döndü.")

    except Exception as e:
        print(f"Hata oluştu: {e}")
        print("Geçici/simüle veriler yedek plan olarak yükleniyor...")
        # Herhangi bir bağlantı kesilmesinde sistemin durmaması için fallback
        formatted_data = {
            "totalFlights": 24,
            "delayRate": 6.4,
            "averageOccupancy": 83,
            "chartLabels": ["Londra", "Atina", "New York", "Paris", "Münih"],
            "chartData": [10, 16, 9, 14, 11],
            "flights": [
                { "flightNumber": "TK1903", "origin": "IST", "destination": "LHR (Londra)", "estimatedTime": "14:20", "status": "Zamanında" },
                { "flightNumber": "TK1881", "origin": "IST", "destination": "ATH (Atina)", "estimatedTime": "14:45", "status": "Zamanında" },
                { "flightNumber": "TK2026", "origin": "IST", "destination": "JFK (New York)", "estimatedTime": "15:10", "status": "Rötarlı (+25dk)" },
                { "flightNumber": "TK1920", "origin": "IST", "destination": "CDG (Paris)", "estimatedTime": "15:40", "status": "Biniş Başladı" },
                { "flightNumber": "TK1552", "origin": "IST", "destination": "MUC (Münih)", "estimatedTime": "16:05", "status": "Zamanında" }
            ]
        }

    # data.json dosyasını yazdır
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    print("data.json güncellendi!")

if __name__ == "__main__":
    get_real_thy_data()
