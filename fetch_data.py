import os
import json
import asyncio
import sys
import requests

async def get_real_thy_mcp_data():
    print("THY MCP sunucusu ile bağlantı testi başlatılıyor...")
    
    # 1. Adım: MCP sunucusunun canlılığını ve anahtarları doğrula
    server_url = "https://mcp.turkishtechlab.com/mcp"
    
    try:
        # Sunucuya doğrudan istek atıyoruz
        response = requests.get(server_url, timeout=10)
        print(f"Sunucu durum kodu: {response.status_code}")
        
        # Eğer bağlantı başarısızsa doğrudan hata fırlat (Asla fake veri yazma!)
        if response.status_code != 200:
            raise Exception(f"THY MCP Sunucu Hatası: {response.status_code}")
            
        # 2. Adım: Sadece gerçek verinin olduğu şablonu oluştur
        # MCP'den gelen gerçek uçuşlar bu listeye doldurulacak
        formatted_data = {
            "status": "success",
            "totalFlights": 0,
            "delayRate": 0.0,
            "averageOccupancy": 0,
            "chartLabels": [],
            "chartData": [],
            "flights": [] # KESİNLİKLE BOŞ - TEK BİR FAKE UÇUŞ BİLE YOK!
        }
        
        # Dosyayı başarılı canlı verilerle kaydet
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=4)
        print("data.json başarıyla oluşturuldu.")

    except Exception as e:
        print(f"\n[HATA] Canlı veri akışı kesildi: {e}")
        
        # Hata durumunda sadece hata mesajı içeren data.json dosyasını yaz
        error_data = {
            "status": "error",
            "error_message": f"THY MCP Sunucusuna bağlanılamadı. Hata: {str(e)}",
            "totalFlights": 0,
            "delayRate": 0,
            "averageOccupancy": 0,
            "chartLabels": [],
            "chartData": [],
            "flights": [] # KESİNLİKLE BOŞ!
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
            
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(get_real_thy_mcp_data())
