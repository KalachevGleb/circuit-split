#pragma once

#include <vector>
#include <map>
#include <list>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

struct CacheEntry {
    int id;
    int weight;
};

class Cache {
    std::map<int, std::list<CacheEntry>::iterator> _map;
    std::list<CacheEntry> _ordered;
    int _capacity;
    int _allocated;
    
public:
    Cache(int capacity) : _capacity(capacity), _allocated(0) {};

    std::vector<CacheEntry> push(int id, int weight);
    bool contains(int id);
    int antiscore(std::vector<int> ids);
    int weight(int id);
};

PYBIND11_MODULE(cache, m) {
    py::class_<Cache>(m, "Cache")
        .def(py::init<const int &>())
        .def("push", &Cache::push)
        .def("contains", &Cache::contains)
        .def("antiscore", &Cache::antiscore)
        .def("weight", &Cache::weight);

    py::class_<CacheEntry>(m, "CacheEntry")
        .def("id", &CacheEntry::id)
        .def("weight", &CacheEntry::weight);
}