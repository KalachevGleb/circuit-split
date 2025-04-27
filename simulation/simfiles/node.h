#pragma once
#include <cstdint>

template<int W>
struct Node {
    uint32_t data[W];
    Node() {
        for (int i = 0; i < W; i++) {
            data[i] = i;  // some non-zero initial values
        }
    }
    template<int start>
    void _calc() {}
    template<int start, int W1, int ... Ws>
    void _calc(const Node<W1>& n1, const Node<Ws>& ... args) {
        for (int i = 0; i < W1; i++) {
            data[(i+start)%W] += n1.data[i];
        }
        _calc<(start+W1)%W>(args...);
    }

    template<int ... Ws>
    void calc(const Node<Ws>& ... args) {
        _calc<0>(args...);
    }
    template<int S, int start>
    void _calc_P() {}
    template<int S, int start, int W1, int ... Ws>
    void _calc_P(const Node<W1>& n1, const Node<Ws>& ... args) {
        for (int i = 0; i < W1; i++) {
            data[(i+start)%W] += n1.data[i]*S;
        }
        _calc_P<(S>>2)*7 | 1, (start+W1)%W>(args...);
    }
    template<int S, int ... Ws>
    void calc_P(const Node<Ws>& ... args) {
        _calc_P<S*2 + 1, 0>(args...);
    }
};
