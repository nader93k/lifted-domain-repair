#include "parser.h"
#include <iostream>

// #define DEBUG_PRINT_TRIGGERED_RULE // enable to see automaton like trace of parse

void Parser::append_char(char c) {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "append_char(" << c << ")" << std::endl;
#endif
    buffer << c;
}

void Parser::increase_depth() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "increase_depth()" << std::endl;
#endif
    assert(depth == 0);
    depth = 1;
    overwrite_current_predicate();
}

void Parser::overwrite_current_predicate() {
    current_predicate = buffer.str();
    buffer.str("");
}

void Parser::push_arg() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "push_arg()" << std::endl;
#endif
    current_args.push_back(buffer.str());
    if (current_args.back().empty()) current_args.pop_back();
    buffer.str("");
}

void Parser::decrease_depth() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "decrease_depth()" << std::endl;
#endif
    assert(depth == 1);
    depth = 0;
    push_arg();
}

void Parser::push_atom() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "push_atom()" << std::endl;
#endif
    if (current_predicate.empty()) {
        // Happens if there was no depth decrease due to atom without parameters (written up without parens)
        overwrite_current_predicate();
    }
    if (!current_predicate.empty()) {
        current_atoms.emplace_back();
        auto &new_atom = current_atoms.back();
        new_atom.head = get_current_predicate_ref();
        insert_current_args_into(new_atom.args);
        current_predicate = "";
    }
}

PredicateRef Parser::get_predicate_ref(const std::string &current_predicate) { //TODO: rn arg
    auto it = predicate_map.find(current_predicate);
    if (it == predicate_map.end()) {
        auto id = result.predicates.size();
        predicate_map.emplace(current_predicate, id);
        if (is_activate_pred(current_predicate)) {
            activate_preds.insert(id);
        }
        result.predicates.push_back(Predicate{.name=current_predicate, .arity=current_args.size()});
        if (is_type_predicate(current_predicate)) {
            result.type_predicates.emplace(get_type_from_pred(current_predicate), id);
        }
        if (is_add_predicate(current_predicate)) {
            auto org_pred = current_predicate.substr(ADD_PRED_START.size());
            if (is_guranteed_predicate(org_pred)) {
                org_pred = org_pred.substr(0, org_pred.size()-GUARANTEED_PRED_END.size());
            }
            auto org_id = get_predicate_ref(org_pred);
            result.add_to_normal_pred.emplace(id, org_id);
        }
        if (is_del_predicate(current_predicate)) {
            auto org_pred = current_predicate.substr(DEL_PRED_START.size());
            if (is_guranteed_predicate(org_pred)) {
                org_pred = org_pred.substr(0, org_pred.size()-GUARANTEED_PRED_END.size());
            }
            auto org_id = get_predicate_ref(org_pred);
            result.del_to_normal_pred.emplace(id, org_id);
        }
        return id;
    }
    assert(result.predicates.at(it->second).arity == current_args.size());
    return it->second;
}

PredicateRef Parser::get_current_predicate_ref() {
    return get_predicate_ref(current_predicate);
}

void Parser::create_atom() {
    assert(current_atoms.size() == 1);
    result.init.push_back(*current_atoms.begin());
}

void Parser::create_rule() {
    assert(current_atoms.size() >= 1);
    result.rules.emplace_back();
    auto &rule = result.rules.back();
    rule.head = *current_atoms.begin();
    for (auto it = ++current_atoms.begin(); it != current_atoms.end(); it++) {
        rule.body.push_back(*it);
    }
}

void Parser::enumerate() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "enumerate()" << std::endl;
#endif
    if (depth == 1) {
        push_arg();
    } else {
        assert(depth == 0);
        push_atom();
    }
}

template<typename T>
static ull get_or_create_ref(const std::string &s, std::unordered_map<std::string, ull> &_m, std::vector<T> &collection) {
    auto it = _m.find(s);
    if (it == _m.end()) {
        auto id = collection.size();
        _m.emplace(s, id);
        collection.push_back(T{s});
        return id;
    }
    return it->second;
}

void Parser::insert_current_args_into(std::vector<ObjectOrVarRef> &res) {
    for (auto &arg_as_string : current_args) {
        assert(!arg_as_string.empty());
        res.emplace_back();
        auto &next_el = res.back();
        if (is_var(arg_as_string)) {
            next_el._is_variable = true;
            next_el.index = get_or_create_ref(arg_as_string, var_map, result.vars);
        } else {
            next_el._is_variable = false;
            next_el.index = get_or_create_ref(arg_as_string, object_map, result.objects);
        }
    }
    current_args.clear();
}

void Parser::start_rule_body() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "start_rule_body()" << std::endl;
#endif
    push_atom();
    assert(!is_rule);
    assert(current_atoms.size() == 1);
    is_rule = true;
}

static bool defines_mutex(const DatalogTask &task, const Rule &rule) {
    return defines_mutex(task.predicates.at(rule.head.head).name);
}

static void parse_num_type_from_str(const std::string &associated_var_str, ull &num, ull &_type, const DatalogTask &result) {
    ull first_stop = 0; // position of leftmost "_"
    ull second_stop = 0; //next "_" following after
    ull third_stop = 0; // next "_" following after
    for (ull i = 0; i < associated_var_str.size() && !third_stop; i++) {
        char c = associated_var_str.at(i);

        if (c == '_') {
            if (!first_stop) {
                first_stop = i+1;
            } else if (!second_stop) {
                second_stop = i+1;
            } else {
                third_stop = i+1;
            }
        }
    }
    assert(first_stop);
    assert(second_stop);
    assert(third_stop);

    std::string type_name = associated_var_str.substr(third_stop);
    assert(result.type_predicates.contains(type_name));
    _type = result.type_predicates.at(type_name);

    std::string num_as_str = associated_var_str.substr(second_stop, third_stop-second_stop-1);
    num = std::stoi(num_as_str);
}

void Parser::transform_last_rule_to_mutex_group() {
    auto &rule = result.rules.back();
    result.mutex_groups.emplace_back();
    auto &new_mutex = result.mutex_groups.back();
    new_mutex.is_unique = ends_with(result.predicates.at(rule.head.head).name, "_unique");

    for (auto &atom : rule.body) {
        new_mutex.elements.emplace_back();
        auto &new_element = new_mutex.elements.back();

        new_element.head = atom.head;
        for (auto &arg : atom.args) {
            if (arg._is_variable) {
                auto &associated_var_str = result.vars.at(arg.index).name;
                bool is_counted = starts_with(associated_var_str, "Var_counted");
                ull num;
                ull _type;
                parse_num_type_from_str(associated_var_str, num, _type, result);

                new_element.pars.push_back(MutexPar{
                        ._is_variable=true,
                        .index=num,
                        ._is_counted=is_counted,
                        .associated_type=_type
                });
            } else {
                new_element.pars.push_back(MutexPar{
                    ._is_variable=false,
                    .index=arg.index,
                    ._is_counted=false,
                    .associated_type=static_cast<ull>(-1/*undetermined for now*/)
                });
            }
        }
    }

    result.rules.pop_back();
}

void Parser::line_stop() {
#ifdef DEBUG_PRINT_TRIGGERED_RULE
    std::cout << "triggered " << "line_stop()" << std::endl;
#endif
    assert(depth == 0);
    push_atom();
    if (!is_rule && activate_preds.contains(current_atoms.begin()->head)) {
        is_rule = true;
    }

    if (is_rule) {
        create_rule();
        if (defines_mutex(result, result.rules.back())) {
            // hack to introduce mutex by defining rules Xmutex[_unique] :- <mutexgroup>
            transform_last_rule_to_mutex_group();
        }
        is_rule = false;
    } else {
        create_atom();
    }
    current_atoms.clear();
}

void Parser::handle_char(char c) {
    switch (c) {
        case '(': {
            increase_depth();
            break;
        }
        case ':': {
            if (Parser::ins.peek() == '-') {
                start_rule_body();
                Parser::ins.get();
            } else {
                append_char(c);
            }
            break;
        }
        case ')': {
            decrease_depth();
            break;
        }
        case ',': {
            enumerate();
            break;
        }
        case '.': {
            line_stop();
            break;
        }
        default: {
            append_char(c);
        }
    }
}

void Parser::parse() {
    char c;

    while (Parser::ins.get(c)) {
        if (!std::isspace(c)) {
            handle_char(c);
        }
    }
}
