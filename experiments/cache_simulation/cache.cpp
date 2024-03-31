#include <vector>
#include <iterator>
#include <iostream>

#include "cache.hpp"

using namespace std;

vector<CacheEntry> Cache::push(int id, int weight) {
    _history.push_back(id);

    vector<CacheEntry> ret;

    if (_map.contains(id)) {
        if(id == _ordered.front().id) {
            return ret;
        }

        auto ptr = _map[id];
        _ordered.splice(_ordered.end(), _ordered, ptr);

        auto pre_last = _ordered.end();
        advance(pre_last, -1);
        _map[id] = pre_last;

        return ret;
    }
    else {
        while((_capacity - _allocated) < weight) {
            ret.push_back(_ordered.front());
            int excess_vertex_id = ret.back().id;
            int excess_vertex_weight = ret.back().weight;
        
            _ordered.pop_front();
            _map.erase(excess_vertex_id);

            _allocated -= excess_vertex_weight;
        }
        
        CacheEntry new_vertex;
        new_vertex.id = id;
        new_vertex.weight = weight;
        _ordered.push_back(new_vertex);

        auto pre_last = _ordered.end();
        advance(pre_last, -1);
        _map.insert({id, pre_last});

        _allocated += weight;
    }

    return ret;
}

bool Cache::contains(int id) {
    return _map.contains(id);
}

int Cache::antiscore(const vector<int>& ids) {
    int ret = 0;

    for(auto& id: ids) {
        if(this -> contains(id)) {
            ret += _map[id] -> weight;
        }
    }

    return ret;
}

int Cache::weight(int id) {
    return _map[id] -> weight;
}