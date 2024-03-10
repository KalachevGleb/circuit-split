#pragma once

#include <vector>
#include <list>

struct LayerVertex {
    int id;
    int weight;
};

class Layer {
    std::vector< std::list<LayerVertex> > data;
    int curr_min;
public:
    Layer(int max_score);

    int pop();
    void push(int id, int score);
};