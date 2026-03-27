import sys
import os
import time


current_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(current_dir, "..", "build")

sys.path.append(os.path.abspath(build_dir))

try:
    import limit_order_book as lob
    print("Success")
except ImportError as e:
    print(f"Failed {e}")
    sys.exit(1)

def main():
    print("Allocating 1,000,000 order structs in C++ memory pool")
    pool = lob.MemoryPool(1000000)

    engine = lob.OrderBook(pool)

    print("\n--- HIGHSPEED TRADE TEST ---")

    start_time = time.perf_counter()

    engine.add_order(1,10000,50,lob.Side.BUY)
    engine.add_order(2,10005,50,lob.Side.SELL)

    engine.add_order(3,10005,20,lob.Side.BUY)

    end_time = time.perf_counter()

    execution_time_us = (end_time - start_time) * 1_000_000
    print(f"3 Orders Processed and Matched in {execution_time_us:.2f} microseconds.")
    print("--- TEST COMPLETE ---")

if __name__ == "__main__":
    main()




