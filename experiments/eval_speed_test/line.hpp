#ifndef LINE_HPP
#define LINE_HPP

#include <vector>
#include <string>
#include <algorithm>

#include "common.hpp"

struct Line {
    int thread;
    int index;
    int weight;
    mutable std::vector<uint32_t> data;
    std::vector<int> forward_deps, sync_deps;            //Родители из текущего потока и родители из другого потока соответственно

    // Конструктор из строки cut.txt
    Line(std::string args) {
        auto contents = split_string(args);

        thread = contents[0];
        index = contents[1];
        weight = contents[2];

        if(contents.size() > 3) {
            for(auto dep: std::vector<int>(contents.begin() + 3, contents.end())) {
                if(dep < 0) sync_deps.push_back(-dep - 1);
                else forward_deps.push_back(dep);
            }
        }

        data.resize(std::max(1, weight));
    }

private:
    Line() = delete;
};

std::vector<Line> read_lines(const char* input_path);
std::vector<Line> schedule2lines(std::vector<int> schedule, std::vector<Line> clear_lines);

#endif