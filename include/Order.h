#pragma once
#include <cstdint>

enum class Side {BUY, SELL};

// Aligning to 64 bytes perfectly matches standard L1/L2 CPU cache lines.
struct alignas(64) Order{
    uint64_t id;
    uint64_t price;
    uint32_t quantity;
    Side side;

    Order *next;
    Order *prev;
};
