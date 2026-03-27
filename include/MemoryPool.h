#pragma once
#include "Order.h"
#include <vector>
#include <stdexcept>
#include <iostream>

//Zero-allocation RAM manager
class MemoryPool{
    private:
        std::vector<Order> pool;
        Order* free_list_head;

    public:
        MemoryPool(const MemoryPool&) = delete;
        MemoryPool& operator=(const MemoryPool&) = delete;

        MemoryPool(size_t capacity){
            pool.resize(capacity);
            //pool = new Order[capacity]();

            for (size_t i=0; i<capacity-1; i++){
                pool[i].next = &pool[i+1];
            }

            pool[capacity-1].next = nullptr;
            free_list_head = &pool[0];
            std::cout << "[C++ ENGINE] Heap Locked. Capacity: " << pool.size() << " Orders." << std::endl;
        }

        Order* allocate(){
            if (!free_list_head){
                throw std::runtime_error("CRITICAL: Memory Pool Exhausted!");
            }

            Order* order = free_list_head;
            free_list_head = free_list_head->next;

            order->next = nullptr;
            order->prev = nullptr;

            return order;
        }
        
        void deallocate(Order *order){
            if (!order) return;
            order->next = free_list_head;
            free_list_head = order;
        }
};