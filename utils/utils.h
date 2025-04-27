#pragma once
#include <string>
#include <vector>

#include <cstdint>

std::string rootPath();
std::string readFile(const std::string &filename);
std::vector<uint8_t> readFileBinary(const std::string &filename);
