#ifndef DATALOG_TRANSFORMER_COMMON_H
#define DATALOG_TRANSFORMER_COMMON_H

#include <vector>
#include <climits>
#include <algorithm>
#include <unordered_set>
#include <cstddef>
#include <string>

typedef long long ll; // signed integer type commonly used within the project
typedef size_t ull; // unsigned integer type commonly used within the project

template<typename T>
constexpr size_t size_minus(size_t i) {
    return sizeof(T) * CHAR_BIT - i;
}

inline bool starts_with(const std::string &s, const std::string &to_check) {
    // https://stackoverflow.com/questions/1878001/how-do-i-check-if-a-c-stdstring-starts-with-a-certain-string-and-convert-a
    return s.rfind(to_check, 0) == 0;
}

inline bool ends_with(const std::string &s, const std::string &ending) {
    // https://stackoverflow.com/questions/874134/find-out-if-string-ends-with-another-string-in-c
    if (ending.size() > s.size()) return false;
    return std::equal(ending.rbegin(), ending.rend(), s.rbegin());
}

inline bool is_var(const std::string &s) {
    return starts_with(s, "Var_");
}

extern const std::string NONE_T;
extern const std::string NONE_STUB;
extern const std::string MUTEX_PRED;
inline bool defines_mutex(const std::string &s) {
    return starts_with(s, MUTEX_PRED);
}

extern const std::string ADD_PRED_START;
inline bool is_add_predicate(const std::string &s) {
    return starts_with(s, ADD_PRED_START);
}

extern const std::string GUARANTEED_PRED_END;
inline bool is_guranteed_predicate(const std::string &s) {
    return ends_with(s, GUARANTEED_PRED_END);
}

inline bool is_action_pred(const std::string &s) {
    return starts_with(s, "action_");
}

extern const std::string DEL_PRED_START;
inline bool is_del_predicate(const std::string &s) {
    return starts_with(s, DEL_PRED_START);
}

extern const std::string TYPE_PRED_START;
inline bool is_type_predicate(const std::string &s) {
    return starts_with(s, TYPE_PRED_START);
}

extern const std::string MAX_MUTEX_START;
inline bool is_max_mutex_pred(const std::string &s) {
    return starts_with(s, MAX_MUTEX_START);
}

inline std::string to_max_mutex_pred(const ull i) {
    return MAX_MUTEX_START+std::to_string(i);
}

extern const std::string MIN_MUTEX_START;
inline bool is_min_mutex_pred(const std::string &s) {
    return starts_with(s, MIN_MUTEX_START);
}

inline std::string to_min_mutex_pred(const ull i) {
    return MIN_MUTEX_START+std::to_string(i);
}

inline std::string get_type_from_pred(const std::string &s) {
    return s.substr(TYPE_PRED_START.length());
}

template<typename T>
inline void _unordered_set_intersect(const std::unordered_set<T> &s1, const std::unordered_set<T> &s2,  std::unordered_set<T> &result) {
    // TODO: change result to inserter
    for (auto &el : s1) {
        if (s2.contains(el)) {
            result.insert(el);
        }
    }
}

template<typename T>
inline void unordered_set_intersect(const std::unordered_set<T> &s1, const std::unordered_set<T> &s2,  std::unordered_set<T> &result) {
    if (s1.size() < s2.size()) {
        _unordered_set_intersect(s1, s2, result);
    } else {
        _unordered_set_intersect(s2, s1, result);
    }
}

template<typename T>
inline void keep_indices(std::vector<T> &vec, const std::vector<ull> &indices) {
#ifndef NDEBUG
    // verify indices are unique
    std::unordered_set<ull> indices_set(indices.begin(), indices.end());
    assert(indices_set.size() == indices.size());
#endif
    std::vector<T> new_vec;
    for (auto i : indices) {
        new_vec.push_back(vec.at(i));
    }
    vec = new_vec;
}

namespace std{

template <typename T1, typename T2>
struct hash<std::pair<T1, T2>> {
    std::size_t operator()(const std::pair<T1, T2> &p) const noexcept {
        return hash<T1>{}(p.first) ^ (hash<T2>{}(p.second) << sizeof(T2)/2);
    }
};

}

// https://stackoverflow.com/questions/32640327/how-to-compute-the-size-of-an-intersection-of-two-stl-sets-in-c
struct Counter {
    struct value_type { template<typename T> value_type(const T&) { } };
    void push_back(const value_type&) { ++count; }
    size_t count = 0;
};

template<typename T1, typename T2>
size_t intersection_size(const T1& s1, const T2& s2) {
    Counter c;
    set_intersection(s1.begin(), s1.end(), s2.begin(), s2.end(), std::back_inserter(c));
    return c.count;
}

extern const std::string GOAL_NAME;
inline bool is_goal_pred(const std::string &s) {
    return starts_with(s, GOAL_NAME);
}

extern const std::string OPTIMIZATION_CRITERION_FACT;

extern const std::string TMP_EXT_STUB;
inline bool indicates_tmp_pred(const std::string &s) {
    return starts_with(s, TMP_EXT_STUB);
}

extern const std::string RULE_HACK_STUB;
inline bool is_rule_hack(const std::string &s) {
    return starts_with(s, RULE_HACK_STUB);
}

extern const std::string FALSE_PRED;
inline bool is_false_pred(const std::string &s) {
    return s == FALSE_PRED;
}

extern const std::string ACTIVATE_PRED_START;
inline bool is_activate_pred(const std::string &s) {
    return starts_with(s, ACTIVATE_PRED_START);
}

#endif //DATALOG_TRANSFORMER_COMMON_H
