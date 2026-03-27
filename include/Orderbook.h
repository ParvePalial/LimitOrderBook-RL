#pragma once
#include "Order.h"
#include "MemoryPool.h"
#include <map>
#include <iostream>
#include <memory>

struct OrderQueue{
    Order* head=nullptr;
    Order* tail=nullptr;

    void append(Order* order){
        if (!head) head = tail = order;
        else{
            tail->next = order;
            order->prev = tail;
            tail = order;
        }
    }

    void remove(Order* order){
        if (order->prev) order->prev->next = order->next;
        if (order->next) order->next->prev = order->prev;
        if (order==head) head = order->next;
        if (order==tail) tail = order->prev;

        order->next = nullptr;
        order->prev = nullptr;
    }
};


class OrderBook{
private:
    std::shared_ptr<MemoryPool> memory_pool;
    std::map<uint64_t, OrderQueue, std::greater<uint64_t>> bids;
    std::map<uint64_t, OrderQueue> asks;
    
public:
    OrderBook(std::shared_ptr<MemoryPool> pool) : memory_pool(pool){}



    // The core execution engine. Called every time a new order hits the network.
    void add_order(uint64_t id, uint64_t price, uint32_t quantity, Side side){
        Order* incoming = memory_pool->allocate();
        incoming->id = id;
        incoming->price = price;
        incoming->quantity=quantity;
        incoming->side = side;

        // Matching model for buysers
        if (side == Side::BUY){
            // While we still need shares AND there are sellers in the book
            while(incoming->quantity > 0 && !asks.empty()){
                auto best_ask_iter = asks.begin();
                uint64_t best_ask_price  = best_ask_iter->first;

                // If the cheapest seller wants more than we are willing to pay, STOP matching.
                if (best_ask_price > incoming->price) break;

                OrderQueue& queue = best_ask_iter->second;
                Order* resting_order = queue.head;

                while (resting_order && incoming->quantity >0){
                    uint32_t  fill_qty = std::min(incoming->quantity, resting_order->quantity);
                    incoming->quantity -= fill_qty;
                    resting_order->quantity -= fill_qty;

                    if (resting_order->quantity == 0){
                        Order* to_delete = resting_order;
                        resting_order = resting_order->next;

                        queue.remove(to_delete);
                        memory_pool->deallocate(to_delete);
                    }
                }

                if (!queue.head) asks.erase(best_ask_iter);
            }
            if (incoming->quantity > 0) {
                bids[incoming->price].append(incoming);
            } else {
                memory_pool->deallocate(incoming);
            }
        }

        else{
            while(incoming->quantity > 0 && !bids.empty()){
                auto best_bid_iter = bids.begin();
                uint64_t best_bid_price = best_bid_iter->first;

                // Buyers are too cheap. Stop.
                if (best_bid_price < incoming->price) break;

                OrderQueue& queue = best_bid_iter->second;
                Order* resting_order = queue.head;

                while(resting_order && incoming->quantity>0){
                    uint32_t fill_qty = std::min(incoming->quantity, resting_order->quantity);
                    incoming->quantity -= fill_qty;
                    resting_order->quantity -= fill_qty;

                    if (resting_order->quantity == 0){
                        Order* to_delete = resting_order;
                        resting_order = resting_order->next;
                        queue.remove(to_delete);
                        memory_pool->deallocate(to_delete);
                    }
                }
                if (!queue.head) bids.erase(best_bid_iter);
            }

            // 3. RESTING LOGIC
            // If we ate through the sellers and STILL have quantity left, rest in the book
            if (incoming->quantity > 0) asks[incoming->price].append(incoming);
            else memory_pool->deallocate(incoming);
        }
    }



    void cancel_order(Order* order){
        if (order->side == Side::BUY){
            bids[order->price].remove(order);
            if (!bids[order->price].head) bids.erase(order->price);
        }
        else{
            asks[order->price].remove(order);
            if (!asks[order->price].head) asks.erase(order->price);
        }
        memory_pool->deallocate(order);
    }
};