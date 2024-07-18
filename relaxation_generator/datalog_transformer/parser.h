#ifndef DATALOG_TRANSFORMER_PARSER_H
#define DATALOG_TRANSFORMER_PARSER_H

#include <climits>
#include <cassert>
#include <vector>
#include <unordered_map>
#include <string>
#include <istream>
#include <sstream>

#include "common.h"

struct Predicate {
    std::string name;
    ull arity;
};

struct Object {
    std::string name;
};

struct Variable {
    std::string name;
};

typedef ull PredicateRef;

struct ObjectOrVarRef {
    ull _is_variable: 1;
    ull index: size_minus<ull>(1);

    bool operator==(const ObjectOrVarRef& other) const = default;
    bool operator!=(const ObjectOrVarRef& other) const = default;
};

struct Atom {
    PredicateRef head;
    std::vector<ObjectOrVarRef> args;

    bool operator==(const Atom& other) const = default;
    bool operator!=(const Atom& other) const = default;
};

struct Rule {
    Atom head;
    std::vector<Atom> body;
};

struct MutexPar {
    ull _is_variable: 1;
    ull index: size_minus<ull>(1);
    ull _is_counted: 1;
    ull associated_type: size_minus<ull>(1);

    bool operator==(const MutexPar& other) const = default;
    bool operator!=(const MutexPar& other) const = default;
};

struct MutexParToUll {
    union {
        MutexPar par;
        std::pair<ull, ull> pair;
    };
};
static_assert(sizeof(MutexPar) == sizeof(std::pair<ull,ull>));

namespace std{

template<>
struct hash<MutexPar> {
    std::size_t operator()(const MutexPar &par) const noexcept {
        MutexParToUll pair{.par=par};
        return hash<std::pair<ull, ull>>{}(pair.pair);
    }
};

}

struct MutexElement {
    ull head;
    std::vector<MutexPar> pars;
};

struct MutexGroup {
    bool is_unique;
    std::vector<MutexElement> elements;
};

struct DatalogTask {
    // task definition
    std::vector<Predicate> predicates;
    std::vector<Object> objects;
    std::vector<Variable> vars;
    std::vector<Rule> rules;
    std::vector<Atom> init;

    // additional info
    std::unordered_map<std::string, PredicateRef> type_predicates;
    std::vector<MutexGroup> mutex_groups;

    std::unordered_map<ull,ull> add_to_normal_pred;
    std::unordered_map<ull,ull> del_to_normal_pred;
};

class Parser {
    std::istream &ins;
    char depth = 0; // shouldn't be increased to more than 2 (level 0 is normal, level 1 is inside paren, level 2 is error)

    void increase_depth();
    void decrease_depth();
    void push_arg();
    void enumerate();
    void start_rule_body();
    void line_stop();
    void push_atom();
    void create_atom();
    void create_rule();
    void overwrite_current_predicate();
    void transform_last_rule_to_mutex_group();
    PredicateRef get_current_predicate_ref();
    PredicateRef get_predicate_ref(const std::string &pred_name);
    void insert_current_args_into(std::vector<ObjectOrVarRef> &);

    bool is_rule = false;
    std::stringstream buffer;
    std::string current_predicate;
    std::vector<std::string> current_args;
    std::vector<Atom> current_atoms;

    std::unordered_map<std::string, ull> predicate_map;
    std::unordered_map<std::string, ull> object_map;
    std::unordered_map<std::string, ull> var_map;

    void handle_char(char c);
    void append_char(char c);
public:
    Parser(std::istream &ins) : ins(ins) {}
    DatalogTask result;
    void parse();
};

#endif //DATALOG_TRANSFORMER_PARSER_H
