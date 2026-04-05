import websocket
import json
import time
import sys
import os
import numpy as np
from stable_baselines3 import PPO

current_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(current_dir, "..", "build")
sys.path.append(os.path.abspath(build_dir))

import limit_order_book as lob

class LiveTradingNode:
    def __init__(self):
        print("Booting.. ")

        self.pool = lob.MemoryPool(1_000_000)
        self.book = lob.OrderBook(self.pool)

        try:
            self.agent = PPO.load("ppo_quant_market_maker")
            print("RL Agent Weights Loaded.")
        except Exception as e:
            print("Could not load model. Did you run train_agent.py first?")
            sys.exit(1)
        
        self.ws_url = "wss://stream.binance.com:9443/ws/btcusdt@depth"
        self.order_id_counter = 1
    
    def _next_id(self):
        idx = self.order_id_counter
        self.order_id_counter += 1
        return idx

    def on_message(self, ws, message):
        data = json.loads(message)
        
        # Process Asks (Sellers)
        for ask in data.get('a', []):
            price, qty = float(ask[0]), float(ask[1])
            if qty == 0:
                self.book.clear_price_level(price, lob.Side.SELL)
            else:
                self.book.add_order(self._next_id(), price, qty, lob.Side.SELL)

        # Process Bids (Buyers)
        for bid in data.get('b', []):
            price, qty = float(bid[0]), float(bid[1])
            if qty == 0:
                self.book.clear_price_level(price, lob.Side.BUY)
            else:
                self.book.add_order(self._next_id(), price, qty, lob.Side.BUY)

        bid = self.book.get_best_bid()
        ask = self.book.get_best_ask()
        spread = ask - bid if bid > 0 and ask > 0 else 0.0
        
        # Must match the 3-dimensional shape from your Gymnasium env
        state = np.array([bid, ask, spread], dtype=np.float32)
        
        if bid > 0 and ask > 0:
            # deterministic=True disables random exploration in live trading
            action, _ = self.agent.predict(state, deterministic=True)
            self.execute_trade(action, state)

    def execute_trade(self, action, state):
        # 0: Hold | 1: Mkt Buy | 2: Mkt Sell | 3: Lmt Buy | 4: Lmt Sell
        if action == 0:
            return # Do nothing
            
        action_map = {1: "MARKET BUY", 2: "MARKET SELL", 3: "LIMIT BUY", 4: "LIMIT SELL"}
        print(f"[\033[92mAI ACTION DECISION\033[0m] Firing {action_map[action]} | Spread: {state[2]}")
        
        # To make this trade real money, you would integrate the 'python-binance' library
        # and trigger a REST API call here using your API Keys.
    
    def run(self):
        print(f"Connecting to {self.ws_url}...")
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=lambda ws, error: print(f"Error: {error}"),
            on_close=lambda ws, status, msg: print("Stream Offline.")
        )
        ws.run_forever()
    
if __name__ == "__main__":
    node = LiveTradingNode()
    node.run()
    