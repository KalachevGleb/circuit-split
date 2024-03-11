#include "utils.h"
#include <fstream>
#include <stdexcept>

using namespace std;

string rootPath() {
    string res = UTILS_SRC_DIR;
    if (res.back() != '/') res.push_back('/');
    return res + "../";
}

string readFile(const string &filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        throw runtime_error("File not found: " + filename);
    }
    string res((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    return res;
}

vector<uint8_t> readFileBinary(const string &filename) {
    ifstream file(filename, ios::binary);
    if (!file.is_open()) {
        throw runtime_error("File not found: " + filename);
    }
    vector<uint8_t> res((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    return res;
}
