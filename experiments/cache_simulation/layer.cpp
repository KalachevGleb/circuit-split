#include "layer.hpp"

Graph::Graph(int size) : _mem(size) {}

void Graph::add_edge(int start, int end) {
    _mem[start].children.push_back(&_mem[end]);
    _mem[end].parents.push_back(&_mem[start]);
}