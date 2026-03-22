#pragma once
#include "Order.h"
#include <vector>
#include <stdexcept>

class MemoryPool{
    private:
        std::vector<Order> pool;
        Order* free_list_head;

    public:
        MemoryPool(size_t capacity){
            pool.resize(capacity);

            for (int i=0; i<capacity-1; i++){
                pool[i].next = &pool[i+1];
            }

            pool[capacity-1].next = nullptr;
            free_list_head = &pool[0];
        }

        Order* allocate(){
            if (!free_list_head){
                // In a true HFT system, we would dynamically expand or drop orders.
            // For this RL environment, running out of memory is a fatal error.
                throw std::runtime_error("CRITICAL: Memory Pool Exhausted!");
            }

            Order* order = free_list_head;
            free_list_head = free_list_head->next;

            // Scrub the intrusive pointers before handing it to the matching engine
            order->next = nullptr;
            order->prev = nullptr;

            return order;
        }
        
        // O(1) Deallocation: Recycle the memory instantly.
        void deallocate(Order *order){
            if (!order) return;


            // Push the used order back onto the top of the free list
            order->next = free_list_head;
            free_list_head = order;
        }
};