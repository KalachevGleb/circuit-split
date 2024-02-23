#include "argparse.h"

#include <map>
#include <iostream>

using namespace std;

JSON parseCmd(int& argc, char **argv, const vector<Option>& positional, const vector<Option>& options) {
    // reads all options in the form --key [value], --no-key and -short_key [value], converting value to JSON
    // if value is not provided, it is assumed to be true or 1 (depending on the type of the option).
    // Parsed options are removed from argv and argc is updated accordingly.
    JSON res(JSON::Object);
    map<string, const Option*> optionMap;
    for (auto& opt: options) {
        optionMap[opt.name] = &opt;
        if (!opt.short_name.empty()) {
            optionMap[opt.short_name] = &opt;
        }
    }

    int remaining = 1;
    auto get_option = [argc, argv, optionMap, &res](int& pos, const string& key0, bool no, const Option *posopt) {
        if (!posopt && optionMap.count(key0) == 0) throw OptionError("Unknown option: " + key0);
        auto *opt = posopt ? posopt : optionMap.at(key0);
        auto type = opt->type;
        auto &key = opt->name;
        if (res.contains(key)) throw OptionError("Option " + key + " specified twice");
        if (type == JSON::Boolean && !posopt) {
            res[key] = !no;
            return 0;
        } else {
            if (no)
                throw OptionError("Option no option --no-" + key);
            if (pos == argc || argv[pos][0] == '-')
                throw OptionError("Expected value for option: " + key);
            if (type == JSON::String) {
                res[key] = argv[pos];
            } else {
                try {
                    res[key] = JSON::parse(argv[pos], true);
                } catch (const JSONError& e) {
                    throw OptionError("Error during parsing value for option `"s + key + "` = " + argv[pos] + ": " + e.what());
                }
                if (!res[key].toType(type)) {
                    throw OptionError(
                            "Invalid type for option `"s + key + "` = " + argv[pos] + ". Expected " +
                            JSON::type_name(type) + ", got " +
                            JSON::type_name(res[key].type()));
                }
            }
            pos++;
            return 1;
        }
    };
    for (int i = 1; i < argc;) {
        string arg = argv[i];
        if (arg.size() > 2 && arg[0] == '-' && arg[1] == '-') {
            string key = arg.substr(2);
            bool no  = false;
            if (key.size() > 3 && key.substr(0, 3) == "no-") {
                no = true;
                key = key.substr(3);
            }
            get_option(++i, key, no, nullptr);
        } else if (arg.size() > 1 && arg[0] == '-') {
            string keys = arg.substr(1);
            ++i;
            for (char key : keys) {
                string skey(1, key);
                if(get_option(i, skey, false, nullptr) && keys.size() > 1) {
                    throw OptionError("Non-boolean option -" + skey + " cannot be combined with other options");
                }
            }
        } else {
            argv[remaining++] = argv[i++];
        }
    }
    if (remaining != positional.size()+1) {
        throw OptionError("Expected " + to_string(positional.size()) + " positional arguments, got " + to_string(remaining-1));
    }
    for (int i = 1; i < remaining;) {
        get_option(i, positional[i-1].name, false, &positional[i-1]);
    }
    for (auto& opt: options) {
        if (opt.required && !res.contains(opt.name)) {
            throw OptionError("Option " + opt.name + " is required");
        }
        if (!res.contains(opt.name)){
            if(opt.def.type() != JSON::Null) {
                res[opt.name] = opt.def;
            } else if (opt.required) {
                throw OptionError("Option " + opt.name + " is required");
            } else {
                res[opt.name] = JSON(opt.type);
            }
        }
    }
    argc = remaining;
    return res;
}

void printUsage(const string& prog, const vector<Option>& positionalArgs, const vector<Option>& options,
                const string& description, bool verbose) {
    if (!description.empty()) {
        cout << description << endl << endl;
    }
    cout << "Usage: " << prog;
    for (auto& arg: positionalArgs) {
        cout << " <" << arg.name << ">";
    }
    for (auto& opt: options) {
        cout << " ";
        if(!opt.required) cout << "[";
        cout << "--" << opt.name;
        if (!opt.short_name.empty()) {
            cout << " | -" << opt.short_name;
        }
        if (opt.type != JSON::Boolean) {
            cout << " <value>";
        }
        if(!opt.required) cout << "]";
    }
    if (verbose) {
        cout << endl << endl;
        cout << "Positional arguments:" << endl;
        for (auto &arg: positionalArgs) {
            cout << "  " << arg.name << ": " << JSON::type_name(arg.type) << " \t " << arg.description;
            if (arg.def.type() != JSON::Null) {
                cout << " (default: " << arg.def << ")";
            }
            cout << endl;
        }

        cout << "Options:" << endl;
        for (auto &opt: options) {
            cout << "  --" << opt.name;
            if (!opt.short_name.empty()) {
                cout << ", -" << opt.short_name;
            }
            cout << ": " << JSON::type_name(opt.type) << " \t " << opt.description;
            if (opt.def.type() != JSON::Null) {
                cout << " (default: " << opt.def << ")";
            }
            cout << endl;
        }
    }
}

