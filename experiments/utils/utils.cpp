#include "utils.h"

using namespace std;

string rootPath() {
    string res = UTILS_SRC_DIR;
    if (res.back() != '/') res.push_back('/');
    return res + "../";
}
