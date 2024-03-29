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
    explicit Cache(int capacity) : _capacity(capacity), _allocated(0) {};

    std::vector<CacheEntry> push(int id, int weight);
    bool contains(int id);
    int antiscore(const std::vector<int>& ids);
    int weight(int id);
};