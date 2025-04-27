#pragma once
#include "json.h"

#include <stdexcept>
#include <string>

class OptionError : public std::runtime_error {
public:
    using runtime_error::runtime_error;
};

struct Option {
    std::string name;
    std::string short_name;
    JSON::Type type;
    std::string description;
    JSON def;
    bool required=false;
};
using Options = std::vector<Option>;

JSON parseCmd(int& argc, char **argv, const Options& positional, const Options& options);
void printUsage(const std::string& prog, const Options& positionalArgs, const Options& options,
                const std::string& description="", bool verbose=true);
