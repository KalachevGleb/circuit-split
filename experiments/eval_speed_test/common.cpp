#include <vector>
#include <string>

#include "common.hpp"
#include "defines.hpp"

using namespace std;

vector<int> split_string(string str) {
    vector<int> ret;

    for(int i = 0; i < str.size(); ++i) {
        while(i < str.size() && isspace(str[i])) ++i;
        if(i == str.size()) break;

        string s;
        while(i < str.size() && !isspace(str[i])) {
            s+= str[i];
            ++i;
        }
        ret.push_back(stoi(s));
    }

    return ret;
}