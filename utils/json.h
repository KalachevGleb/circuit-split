#pragma once
#include <variant>
#include <string>
#include <vector>
#include <map>
#include <tuple>
#include <stdexcept>

//! \file json.h
//! \brief Contains the class representing a JSON object.

#include <version>
#include <concepts>


class JSONError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class JSON {
    std::variant<std::nullptr_t, int64_t, double, bool, std::string, std::vector<JSON>, std::map<JSON, JSON>> data;
public:
    enum Type {
        String,
        Integer,
        Double,
        Boolean,
        Null,
        Array,
        Object
    };

    explicit JSON(Type t) {
        switch (t) {
        case String:
            data = "";
            break;
        case Integer:
            data = int64_t(0);
            break;
        case Double:
            data = double(0);
            break;
        case Boolean:
            data = bool(false);
            break;
        case Null:
            data = nullptr;
            break;
        case Array:
            data = std::vector<JSON>();
            break;
        case Object:
            data = std::map<JSON, JSON>();
            break;
        }
    }

    static const char* type_name(Type t) {
        switch (t) {
            case String:
                return "string";
            case Integer:
                return "integer";
            case Double:
                return "double";
            case Boolean:
                return "boolean";
            case Null:
                return "null";
            case Array:
                return "array";
            case Object:
                return "object";
        }
        return "<invalid type>";
    }
    static bool type_convertible(Type from, Type to) {
        if (from == to || to == String)
            return true;
        if (from == Integer && to == Double)
            return true;
        return false;
    }

    //! \brief Constructs a JSON object from a string.
    //! \param str The string to construct the JSON object from.
    JSON(const std::string& str) {
        data = str;
    }
    //! \brief Constructs a JSON object from a string.
    //! \param str The string to construct the JSON object from.
    JSON(const char* str) {
        data = std::string(str);
    }
    //! \brief Constructs a JSON object from a string.
    //! \param str The string to construct the JSON object from.
    JSON(std::string&& str) {
        data = std::move(str);
    }
    //! \brief Constructs a JSON object from an integer.
    //! \param i The integer to construct the JSON object from.
    template<std::integral T>
    JSON(T i) {
        if constexpr(std::same_as<T, bool>)
            data = bool(i);
        else
            data = int64_t(i);
    }
    //! \brief Constructs a JSON object from a double.
    //! \param d The double to construct the JSON object from.
    template<std::floating_point T>
    JSON(T d) {
        data = double(d);
    }

    //! \brief Constructs a null JSON object.
    JSON() {
        data = nullptr;
    }
    ~JSON() = default;

    JSON(const JSON&) = default;
    JSON(JSON&&) = default;
    JSON& operator=(const JSON&) = default;
    JSON& operator=(JSON&&) = default;

    //! \brief Constructs a JSON object from a vector.
    //! \param v The vector to construct the JSON object from.
    JSON(const std::vector<JSON>& v) {
        data = v;
    }
    //! \brief Constructs a JSON object from a vector.
    //! \param v The vector to construct the JSON object from.
    JSON(std::vector<JSON>&& v) {
        data = std::move(v);
    }

    //! \brief Constructs a JSON object from a tuple (stored as an array).
    //! \param t The tuple to construct the JSON object from.
    template<class ... Args>
    JSON(const std::tuple<Args...>& t) {
        data = std::apply([](auto&& ... args) {
            return std::vector<JSON>{JSON(args)...};
        }, t);
    }

    //! \brief Constructs a JSON object from a pair (stored as an array).
    //! \param p The pair to construct the JSON object from.
    template<class Arg1, class Arg2>
    JSON(const std::pair<Arg1, Arg2>& p) {
        data = std::vector<JSON>{JSON(p.first), JSON(p.second)};
    }

    //! \brief Constructs a JSON object from a vector.
    //! \param v The vector to construct the JSON object from.
    template<typename T> requires std::convertible_to<T, JSON>
    JSON(const std::vector<T>& v) {
        data.emplace<std::vector<JSON>>(v.begin(), v.end());
    }
    //! \brief Constructs a JSON object from a map
    //! \param v The map to construct the JSON object from.
    JSON(const std::map<JSON, JSON>& v) {
        data = v;
    }
    JSON(std::map<JSON, JSON>&& v) {
        data = std::move(v);
    }
    //! \brief Constructs a JSON object from a map
    //! \param v The map to construct the JSON object from.
    template<typename K, typename V, typename cmp> requires std::convertible_to<K, JSON> && std::convertible_to<V, JSON>
    JSON(const std::map<K, V, cmp>& v){
        data.emplace<std::map<JSON, JSON>>(v.begin(), v.end());
    }

    //////// getters /////////

    //! \brief Returns the type of the JSON object.
    //! \return The type of the JSON object.
    Type type() const {
        return std::visit([](auto&& arg) -> Type {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::string>) {
                return Type::String;
            } else if constexpr (std::is_same_v<T, int64_t>) {
                return Type::Integer;
            } else if constexpr (std::is_same_v<T, double>) {
                return Type::Double;
            } else if constexpr (std::is_same_v<T, bool>) {
                return Type::Boolean;
            } else if constexpr (std::is_same_v<T, std::nullptr_t>) {
                return Type::Null;
            } else if constexpr (std::is_same_v<T, std::vector<JSON>>) {
                return Type::Array;
            } else if constexpr (std::is_same_v<T, std::map<JSON, JSON>>) {
                return Type::Object;
            } else {
                static_assert(std::is_same_v<T, void>, "non-exhaustive visitor!");
            }
        }, data);
    }
    //! \brief Returns the type of the JSON object as a string.
    //! \return The type of the JSON object as a string.
    const char* typeStr() const {
        return type_name(type());
    }

    std::string& str() {
        return std::get<std::string>(data);
    }
    const std::string& str() const {
        return std::get<std::string>(data);
    }

    int64_t& i() {
        return std::get<int64_t>(data);
    }
    int64_t i() const {
        return std::get<int64_t>(data);
    }

    double& d() {
        return std::get<double>(data);
    }
    double d() const {
        return std::get<double>(data);
    }

    bool& b() {
        return std::get<bool>(data);
    }
    bool b() const {
        return std::get<bool>(data);
    }

    bool isNull() const {
        return std::holds_alternative<std::nullptr_t>(data);
    }

    std::vector<JSON>& arr() {
        return std::get<std::vector<JSON>>(data);
    }
    const std::vector<JSON>& arr() const {
        return std::get<std::vector<JSON>>(data);
    }

    std::map<JSON, JSON>& obj() {
        return std::get<std::map<JSON, JSON>>(data);
    }
    const std::map<JSON, JSON>& obj() const {
        return std::get<std::map<JSON, JSON>>(data);
    }

    // comparison operator
    std::strong_ordering operator <=>(const JSON& other) const;
    bool operator == (const JSON& other) const = default;
    template<typename T>
    bool operator == (const T& other) const {
        if constexpr(std::is_convertible_v<T, JSON>) {
            return *this == JSON(other);
        } else {
            return false;
        }
    }

    //// set type (without argument and conversion) ////

    //! \brief Sets the type of the JSON object to a string.
    std::string& setS() {
        data.emplace<std::string>();
        return std::get<std::string>(data);
    }
    //! \brief Sets the type of the JSON object to an integer.
    int64_t& setI() {
        data.emplace<int64_t>();
        return std::get<int64_t>(data);
    }
    //! \brief Sets the type of the JSON object to a double.
    double& setD() {
        data.emplace<double>();
        return std::get<double>(data);
    }
    //! \brief Sets the type of the JSON object to a boolean.
    bool& setB() {
        data.emplace<bool>();
        return std::get<bool>(data);
    }
    //! \brief Sets the type of the JSON object to null.
    void setNull() {
        data.emplace<std::nullptr_t>();
    }
    //! \brief Sets the type of the JSON object to an array.
    std::vector<JSON>& setArr() {
        data.emplace<std::vector<JSON>>();
        return std::get<std::vector<JSON>>(data);
    }
    //! \brief Sets the type of the JSON object to an object.
    std::map<JSON, JSON>& setObj() {
        data.emplace<std::map<JSON, JSON>>();
        return std::get<std::map<JSON, JSON>>(data);
    }

    ///////// converters /////////
    void toString(std::string &out, bool wrapLines = false, int indent=0) const;
    std::string toString(bool wrapLines = false) const {
        std::string out;
        toString(out, wrapLines);
        return out;
    }

    bool toType(Type t){
        Type current = type();
        if (current == t) return true;
        switch(t){
            case Type::String:
                *this = toString();
                return true;
            case Type::Double: {
                double d;
                if (tryGet(d)) {
                    *this = d;
                    return true;
                }
                return false;
            }
            case Type::Integer: {
                int64_t i;
                if (tryGet(i)) {
                    *this = i;
                    return true;
                }
                return false;
            }
            case Type::Boolean: {
                bool b;
                if (tryGet(b)) {
                    *this = b;
                    return true;
                }
                return false;
            }
            default:
                return false;
        }
    }

    template<std::integral I>
    bool tryGet(I& out) const {
        return std::visit([&out](auto&& arg) -> bool {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, int64_t> || std::is_same_v<T, bool>) {
                out = static_cast<I>(arg);
                return true;
            } else {
                return false;
            }
        }, data);
    }
    template<std::floating_point F>
    bool tryGet(F& out) const {
        return std::visit([&out](auto&& arg) -> bool {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, double> || std::is_same_v<T, int64_t>) {
                out = static_cast<F>(arg);
                return true;
            } else {
                return false;
            }
        }, data);
    }
    bool tryGet(std::string& out) const {
        toString(out);
        return true;
    }
    template<class T>
    bool tryGet(std::vector<T>& out) const {
        if (type() != Type::Array) {
            return false;
        }
        out.resize(arr().size());
        for (size_t i = 0; i < arr().size(); ++i) {
            if (!arr()[i].tryGet(out[i])) {
                return false;
            }
        }
        return true;
    }
    template<class T1, class T2>
    bool tryGet(std::pair<T1, T2>& out) const {
        if (type() != Type::Array || arr().size() != 2) {
            return false;
        }
        return arr()[0].tryGet(out.first) && arr()[1].tryGet(out.second);
    }
    template<class ... T>
    bool tryGet(std::tuple<T...>& out) const {
        if (type() != Type::Array || arr().size() != sizeof...(T)) {
            return false;
        }
        return _tryGetTuple(out, std::index_sequence_for<T...>());
    }
    template<class K, class V, class cmp>
    bool tryGet(std::map<K, V, cmp>& out) const {
        if (type() != Type::Object) {
            return false;
        }
        for (const auto& [k, v] : obj()) {
            K key;
            if (!k.tryGet(key)) {
                return false;
            }
            if (!v.tryGet(out[key])) {
                return false;
            }
        }
        return true;
    }
    template<class T>
    void get(T& out) const {
        if (!tryGet(out)) {
            throw std::runtime_error("JSON::get(): type mismatch");
        }
    }

    template<class T>
    T as() const {
        T out;
        get(out);
        return out;
    }
    bool is(Type t) const {
        return type() == t;
    }

    //// container operators ////
    template<class I> requires std::is_convertible_v<I, JSON>
    JSON& operator[](const I& index) {
        return std::visit([&index](auto&& arg) -> JSON& {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::vector<JSON>> && std::is_integral_v<I>) {
                if constexpr(std::is_integral_v<I>) {
                    if (index < 0) {
                        index += arg.size();
                    } else if (index >= arg.size()) {
                        throw std::out_of_range(
                                "JSON index out of range (index = " + std::to_string(index) + ", size = " +
                                std::to_string(arg.size()) + ")");
                    }
                    return arg[index];
                }
            } else if constexpr (std::is_same_v<T, std::map<JSON, JSON>>) {
                return arg[index];
            } else {
                throw std::runtime_error("JSON::operator[]: type mismatch");
            }
        }, data);
    }
    template<class I> requires std::is_convertible_v<I, JSON>
    const JSON& at(const I& index) const {
        return std::visit([&index](auto&& arg) -> const JSON& {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::vector<JSON>> && std::is_integral_v<I>) {
                if constexpr (std::is_integral_v<I>) {
                    if (index < 0) {
                        index += arg.size();
                    } else if (index >= arg.size()) {
                        throw std::out_of_range("JSON::at(" + std::to_string(index) + "): index out of range"
                                                                                      " (size = " + std::to_string(arg.size()) + ")");
                    }
                    return arg[index];
                }
            } else if constexpr (std::is_same_v<T, std::map<JSON, JSON>>) {
                auto it = arg.find(index);
                if (it == arg.end()) {
                    throw std::out_of_range("JSON::at(" + JSON(index).toString() + "): key not found");
                }
                return it->second;
            } else {
                throw std::runtime_error("JSON::at: type mismatch");
            }
        }, data);
    }
    size_t size() const {
        return std::visit([](auto&& arg) -> size_t {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::vector<JSON>>) {
                return arg.size();
            } else if constexpr (std::is_same_v<T, std::map<JSON, JSON>>) {
                return arg.size();
            } else {
                throw std::runtime_error("JSON::size(): type mismatch");
            }
        }, data);
    }
    template<class T>
    void push_back(const T& val) {
        std::visit([&val](auto&& arg) {
            using I = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, std::vector<JSON>>) {
                arg.push_back(val);
            } else {
                throw std::runtime_error("JSON::push_back(): type mismatch");
            }
        }, data);
    }
    template<class K, class V> requires std::is_convertible_v<K, JSON> && std::is_convertible_v<V, JSON>
    void emplace(const K& key, const V& val) {
        std::visit([&key, &val](auto&& arg) {
            using I = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<I, std::map<JSON, JSON>>) {
                arg.emplace(key, val);
            } else {
                throw std::runtime_error("JSON::emplace(): type mismatch");
            }
        }, data);
    }
    template<class K> requires std::is_convertible_v<K, JSON>
    bool contains(const K& key) const {  // check if key exists in object or index exists in array
        return std::visit([&key](auto&& arg) -> bool {
            using I = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<I, std::map<JSON, JSON>>) {
                return arg.contains(key);
            } else if constexpr (std::is_same_v<I, std::vector<JSON>> && std::is_integral_v<K>) {
                if constexpr(std::is_integral_v<K>) {
                    return (int)key >= 0 && key < arg.size();
                }
            } else {
                throw std::runtime_error("JSON::contains(): type mismatch");
            }
        }, data);
    }
    //// arithmetic operators ////
    explicit operator bool() const;
    JSON operator-() const;
    JSON& operator+=(const JSON& rhs);
    JSON& operator-=(const JSON& rhs);
    JSON& operator*=(const JSON& rhs);
    JSON& operator/=(const JSON& rhs);
    JSON& operator%=(const JSON& rhs);
    JSON& operator&=(const JSON& rhs);
    JSON& operator|=(const JSON& rhs);
    JSON& operator^=(const JSON& rhs);
    JSON& operator<<=(const JSON& rhs);
    JSON& operator>>=(const JSON& rhs);
    JSON& operator++(){
        return *this += 1;
    }
    JSON& operator--() {
        return *this -= 1;
    }
    JSON operator+(const JSON& rhs) const{
        return JSON(*this) += rhs;
    }
    JSON operator-(const JSON& rhs) const{
        return JSON(*this) -= rhs;
    }
    JSON operator*(const JSON& rhs) const{
        return JSON(*this) *= rhs;
    }
    JSON operator/(const JSON& rhs) const{
        return JSON(*this) /= rhs;
    }
    JSON operator%(const JSON& rhs) const{
        return JSON(*this) %= rhs;
    }
    JSON operator&(const JSON& rhs) const{
        return JSON(*this) &= rhs;
    }
    JSON operator|(const JSON& rhs) const{
        return JSON(*this) |= rhs;
    }
    JSON operator^(const JSON& rhs) const{
        return JSON(*this) ^= rhs;
    }
    JSON operator<<(const JSON& rhs) const{
        return JSON(*this) <<= rhs;
    }
    JSON operator>>(const JSON& rhs) const{
        return JSON(*this) >>= rhs;
    }


    // input/output
    static JSON parse(const std::string& str, bool defaultToString = false);
    static JSON load(const std::string& filename);
    void write(std::ostream& out, bool wrapLines = false) const;
    void save(const std::string& filename, bool wrapLines = false) const;
private:
    template<class ... T, size_t ... I>
    bool _tryGetTuple(std::tuple<T...>& out, std::index_sequence<I...>) const {
        return (arr()[I].tryGet(std::get<I>(out)) && ...);
    }
};

std::ostream &operator<<(std::ostream &out, const JSON &json);


