#include <string>
#include <vector>
#include <fstream>

#include "line.hpp"

using namespace std;

vector<Line> read_lines(const char* input_path) {
    ifstream fd;
    fd.open(input_path, ios_base::in);

    string read_buff;
    vector<Line> lines;
    if (fd.is_open()) {
        while (fd) {
            getline(fd, read_buff);

            if(split_string(read_buff).size() == 0) continue;       

            lines.push_back(Line(read_buff));
        }
    }

    fd.close();

    return lines;
}

vector<Line> schedule2lines(vector<int> schedule, vector<Line> clear_lines) {
    // TBD

    return vector<Line>();
}