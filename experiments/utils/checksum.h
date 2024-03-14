#pragma once

#include <cstdint>
#include <vector>
#include <string>

std::vector<uint8_t> md5(const std::vector<uint8_t> &data);
std::string md5AsHexString(const std::vector<uint8_t> &hash);
std::string md5(const std::string &data);
std::string md5ForFile(const std::string &filename);
