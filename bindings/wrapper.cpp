#include <pybind11/pybind11.h>
#include "../include/OrderBook.h"
#include "../include/MemoryPool.h"

namespace py = pybind11;

PYBIND11_MODULE(limit_order_book, m) {
    m.doc() = "Ultra-Low Latency C++ Limit Order Book Engine";

    py::enum_<Side>(m, "Side")
        .value("BUY", Side::BUY)
        .value("SELL", Side::SELL)
        .export_values();

    py::class_<MemoryPool, std::shared_ptr<MemoryPool>>(m, "MemoryPool")
        .def(py::init<size_t>(), py::arg("capacity"));

    py::class_<OrderBook, std::shared_ptr<OrderBook>>(m, "OrderBook")
        .def(py::init<std::shared_ptr<MemoryPool>>(), py::arg("pool"))
        .def("add_order", &OrderBook::add_order, 
             py::arg("id"), py::arg("price"), py::arg("quantity"), py::arg("side"));
}