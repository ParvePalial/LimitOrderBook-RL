import sys
import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(current_dir, "..", "build")
sys.path.append(os.path.abspath(build_dir))

import limit_order_book as lob

class LimitOrderBookEnv(gym.Env):
    def __init__(self):
        super(LimitOrderBookEnv, self).__init__()

        csv_path = os.path.join(current_dir, "..", "data", "raw", "btcusdt_l2_book.csv")
        try:
            print(f"Loading Historical Data from {csv_path}...")
            self.df = pd.read_csv(csv_path)
            self.max_steps = len(self.df)-1
            print(f"Successfully loaded {self.max_steps} market ticks.")
        except FileNotFoundError:
            print("ERROR: CSV not found. Did you run data_ingestion.py?")
            sys.exit(1)


        self.current_step = 0
        self.order_id_counter = 1

        #CPP Memory Pool & Engine
        self.pool = lob.MemoryPool(1_000_000)
        self.engine = lob.OrderBook(self.pool)

        #Observation Space: [Best Bid, Best Ask, Spread]
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(3,), dtype=np.float32)

        #Action Space: 5 discrete actions
        # 0: Do nothing
        # 1: Market Buy 10 shares (Hits the Ask)
        # 2: Market Sell 10 shares (Hits the Bid)
        # 3: Limit Buy 10 shares at current Best Bid
        # 4: Limit Sell 10 shares at current Best Ask

        self.action_space = spaces.Discrete(5)


    def _get_state(self):
        bid = self.engine.get_best_bid()
        ask = self.engine.get_best_ask()

        spread = ask - bid if (bid > 0 and ask > 0) else 0.0
        return np.array([bid, ask, spread], dtype=np.float32)
    
    def _next_id(self):
        idx = self.order_id_counter
        self.order_id_counter +=1
        return idx
    
    def _apply_market_data(self, row_idx):
        """Injects the historical CSV data into the C++ Engine"""
        row = self.df.iloc[row_idx]
        
        #claer the old top of the book
        old_bid = self.engine.get_best_bid()
        old_ask = self.engine.get_best_ask()
        if old_bid > 0: self.engine.clear_price_level(old_bid, lob.Side.BUY)
        if old_ask > 0: self.engine.clear_price_level(old_ask, lob.Side.SELL)

        #add new hisotrical data on top of the book
        self.engine.add_order(self._next_id(), float(row['best_bid_prc']), float(row['best_bid_qty']), lob.Side.BUY)
        self.engine.add_order(self._next_id(), float(row['best_ask_prc']), float(row['best_ask_qty']), lob.Side.SELL)



    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.order_id_counter = 1
        
        self.engine.reset()
        self._apply_market_data(self.current_step)

        return self._get_state(), {}


    def step(self, action):
        self.current_step += 1
        self._apply_market_data(self.current_step)

        if action == 1:
            # Market Buy: Price is set artificially high to cross the spread
            self.engine.add_order(self._next_id(), 999999, 10, lob.Side.BUY)
        elif action == 2:
            # Market Sell: Price is set artificially low to cross the spread
            self.engine.add_order(self._next_id(), 1, 10, lob.Side.SELL)
        elif action == 3:
            # Limit Buy at the current Best Bid
            bid = self.engine.get_best_bid()
            if bid > 0: self.engine.add_order(self._next_id(), bid, 10, lob.Side.BUY)
        elif action == 4:
            # Limit Sell at the current Best Ask
            ask = self.engine.get_best_ask()
            if ask > 0: self.engine.add_order(self._next_id(), ask, 10, lob.Side.SELL)
        
        state = self._get_state()
        spread = state[2]

        #Calculate Reward (Simple logic: smaller spread = good, big spread = bad)
        reward = -spread if spread >0 else -10.0
        reward = float(reward)

        #check for episode to over
        terminated = False
        truncated = self.current_step >= self.max_steps

        return state, reward, terminated, truncated, {}

    def render(self):
        state = self._get_state()
        print(f"[{self.current_step}] BID: {state[0]} | ASK: {state[1]} | SPREAD: {state[2]}")



if __name__ == "__main__":
    print("Gym Env Linked to Custom C++ Engine")
    env = LimitOrderBookEnv()

    state, _ = env.reset()
    print(f"Initial Market State=> {state}")
    print("\nsimulating 5 random AI actions.."
    for i in range(5):
        action = env.action_space.sample()
        state, reward, done, _, _ = env.step(action)
        print(f"Action: {action} | Reward: {reward}")
        env.render()