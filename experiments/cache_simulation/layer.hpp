#pragma once

#include <vector>
#include <list>
#include <string>
#include <iostream>
#include <set>
#include <algorithm>

#include "cache.hpp"

template <class T>
std::string container2string(T container) {
    std::vector<int> data;
    for(auto entry: container) {
        data.push_back(entry);
    }

    std::sort(data.begin(), data.end());

    std::string ret;
    for(auto entry: data) {
        ret += " ";
        ret += std::to_string(entry);
    }
    ret.erase(0, 1);

    return ret;
}

class Error {
public:
    Error(std::string msg = "Unknown error") {
        std::cerr << msg << std::endl;
    }
};

class Graph {
public:
    struct Vertex {
        int id;
        int weight;
        int score;
        int codegree;

        std::vector<Vertex*> parents;
        std::vector<Vertex*> children;

        std::string parents2string() {
            std::vector<int> data;

            for(auto vertex: parents) {     
                data.push_back(vertex -> id);
            }

            return container2string(data);
        }
        
        std::string children2string() {
            std::vector<int> data;

            for(auto vertex: children) {     
                data.push_back(vertex -> id);
            }

            return container2string(data);
        }
    };

    Graph(int size);
    Graph(const Graph&) = delete;
    Graph& operator=(const Graph&) = delete;
    const Graph& operator=(const Graph&) const = delete;
    ~Graph();

    void add_edge(int start, int end);
    void set_weights(std::vector<int> weights);
    void set_score(int id, int score);
    std::vector<int> in_vertices() const;
    int size() const {
        return _size;
    }

private:
    Vertex* _mem;
    size_t _size;

public:
    Vertex& operator()(int pos) {return _mem[pos];}
    const Vertex& operator()(int pos) const {return _mem[pos];}

    Vertex& at(int pos) {return _mem[pos];}
    const Vertex& at(int pos) const {return _mem[pos];}
};

class Layer {
public:
    struct LayerNode {
        LayerNode* prev;
        LayerNode* next;

        Graph::Vertex* vertex;
    };

    Layer(int max_score);
    ~Layer() {throw Error("Сделай деструктор!");}

    void init_graph(int size) {
        if(size <= 0) {
            throw Error("Плохой size");
        }

        _graph = new Graph(size);
    }
    void add_edge(int start, int end) {
        if (_graph == nullptr) {
            throw Error("Граф не инициализирован");
        }

        _graph -> add_edge(start, end);
    }
    void set_weights(std::vector<int> weights) {
        if (_graph == nullptr) {
            throw Error("Граф не инициализирован");
        }

        _graph -> set_weights(weights);
    }
    void set_score(int id, int score) {
        if (_graph == nullptr) {
            throw Error("Граф не инициализирован");
        }

        _graph -> set_score(id, score);
    }

    void init_cache(int capacity) {
        if(capacity <= 0) {
            throw Error("capacity <= 0 в конструкторе Cache");
        }

        _cache = new Cache(capacity);
    }

    void start();

    int step();

private:
    std::set<LayerNode*> _mem;
    std::vector<LayerNode*> _lists;
    std::map<int, LayerNode*> _id2node;

    Graph* _graph;
    Cache* _cache;

    int _max_score;

    int _curr_min;
};