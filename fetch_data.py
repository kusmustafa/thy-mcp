import os
import json
import asyncio
import sys
from mcp import ClientSession
from mcp.client.sse import sse_client

# GitHub Secrets'tan gelen kullanıcı bilgileri
MS_USER = os.environ.get("MILES_SMILES_USER")
MS_PASS = os.environ.get("MILES_SMILES_PASS")

async def get_real_thy_mcp_data():
    print("THY MCP SSE sunucusuna resmi protokol üzerinden bağlanılıyor...")
    
    # THY MCP resmi SSE (Server-Sent Events) bağlantı adresi
    server_url = "https://mcp.turkishtechlab.com/sse"
    
    try:
        # 1. Adım: Resmi mcp kütüphanesi ile SSE kanalı açılıyor
        async with sse_client(server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                
                print("MCP Oturumu (Session) başlatılıyor...")
                await session.initialize()
                
                print("Oturum açıldı, THY Araç listesi sorgulanıyor...")
                tools = await session.list_tools()
                
                # THY'nin aktif uçuş sorgulama aracı (veya parametreleri) tetikleniyor
                print("get_active_flights aracı çağrılıyor...")
                tool_result = await session.call_tool(
                    "get_active_flights", 
                    arguments={}
                )
                
                # Gelen gerçek veriyi JSON formatına dönüştürün
                raw_text = tool_result.content[0].text
                live_data = json.loads(raw_text)
                
                # Dashboard'un okuyacağı standart formata dönüştürün
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
                
                # data.json dosyasını deponuza yazın
                with open("data.json", "w", encoding="utf-8") as f:
                    json.dump(formatted_data, f, ensure_ascii=False, indent=4)
                
                print("CANLI THY VERİLERİ BAŞARIYLA ALINDI VE KAYDEDİLDİ.")

    except Exception as e:
        print(f"\n[MCP BAĞLANTI HATASI] Canlı veri alınamadı: {e}")
        
        # Kullanıcı kuralı gereği fake veri üretilmez, hata durumu yazılır
        error_data = {
            "status": "error",
            "error_message": f"THY MCP Bağlantı Kesintisi: {str(e)}",
            "totalFlights": 0,
            "delayRate": 0,
            "averageOccupancy": 0,
            "chartLabels": [],
            "chartData": [],
            "flights": []
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
            
        sys.exit(1) # GitHub Actions'ın hata vererek durmasını sağla

if __name__ == "__main__":
    asyncio.run(get_real_thy_mcp_data())
