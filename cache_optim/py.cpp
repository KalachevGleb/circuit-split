#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "cache.hpp"
#include "layer.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp, m) {
    py::class_<Cache>(m, "Cache")
        .def(py::init<const int&>())
        .def("push", &Cache::push)
        .def("contains", &Cache::contains)
        .def("antiscore", &Cache::antiscore)
        .def("weight", &Cache::weight)
        .def("history", &Cache::history);
          
    py::class_<Layer>(m, "Layer")
        .def(py::init<const int&>())
        .def("init_graph", &Layer::init_graph)
        .def("add_edge", &Layer::add_edge)
        .def("set_weights", &Layer::set_weights)
        .def("set_score", &Layer::set_score)
        .def("init_cache", &Layer::init_cache)
        .def("start", &Layer::start)
        .def("step", &Layer::step)
        .def("cache_history", &Layer::cache_history);
}
