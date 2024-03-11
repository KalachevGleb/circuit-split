#pragma once

#include <vector>
#include <list>

#include "cache.hpp"

class Graph {
public:
    struct Vertex {
        int id;
        int weight;

        std::vector<Vertex*> parents;
        std::vector<Vertex*> children;
    };

    Graph(int size);
    Graph(const Graph&);
    Graph& operator=(const Graph&);
    const Graph& operator=(const Graph&) const;
    ~Graph();

    void add_edge(int start, int end);

private:
    Vertex* _mem;
};

class Layer {
public:
    struct LayerNode {
        LayerNode* prev;
        LayerNode* next;

        Graph::Vertex* vertex;
    };

    Layer(int max_score, Cache* cache);

    int pop();
    void step(int id, int score);

private:
    std::vector<LayerNode*> _mem;
    std::vector<LayerNode*> _nodes;
    std::map<int, LayerNode*> _id2node;

    Cache* _cache;

    int _curr_min;
};