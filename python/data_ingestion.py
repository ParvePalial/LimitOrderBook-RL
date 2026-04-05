import websocket
import json
import csv
import time
import os

os.makedirs("../data/raw", exist_ok=True)
csv_file = "../data/raw/btcusdt_l2_book.csv"

# We stream the top 20 levels of the BTC/USDT order book every 100ms
WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms"

with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    #Header: timestamp, best_bid_price, best_bid_qty, best_ask_price, best_ask_qty
    writer.writerow(["timestamp", "best_bid_prc", "best_bid_qty", "best_ask_prc", "best_ask_qty"])

message_count =0 

def on_message(ws, message):
    global message_count 
    data = json.loads(message)

    try:
        # Extract the absolute top of the book (Level 0)
        best_bid_prc = float(data['bids'][0][0])
        best_bid_qty = float(data['bids'][0][1])
        
        best_ask_prc = float(data['asks'][0][0])
        best_ask_qty = float(data['asks'][0][1])

        timestamp = time.time()
        
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, best_bid_prc, best_bid_qty, best_ask_prc, best_ask_qty])
        
        message_count +=1
        if message_count % 100 == 0:
            print(f"[{message_count} Ticks Harvested] BID: {best_bid_prc} | ASK: {best_ask_prc}")

    except Exception as e:
        print(f"Error parsing tick: {e}")
    
def on_error(ws, error):
    print(f"WebSocket Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Harvester Disconnected.")

if __name__ == "__main__":
    print("Initiating Binance L2 Harvester. Press Ctrl+C to stop.")
    ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close = on_close)
    ws.run_forever()