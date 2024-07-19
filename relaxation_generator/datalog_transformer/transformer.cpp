#include "transformer.h"
#include "minizinc_printer.h"
#include "pretty_print.h"
#include "common.h"
#include <unordered_set>
#include <set>
#include <cassert>
#include <limits>

//#define MUTEX_FILTER_DEBUG_FLAG
//#define DEBUG_FLAG_PRINT_JOIN_TRACES
//#define DEBUG_FLAG_JO_BUILDER
//#define DEBUG_FLAG_PRINT_MUTEX_COVER_GOAL_EXT

struct PreMatch {
    ull atom_position;
    ull mutex_position;
};

struct DistinctParConstraint {
    ull predicate; //TODO: would make more sense to not track this here and create seperate containers per predicate
    ull pos1;
    ull pos2;

    bool operator==(const DistinctParConstraint& other) const = default;
};

namespace std {

    union ObjTransform {
        ObjectOrVarRef obj;
        ull num;
    };

// roughly: https://stackoverflow.com/questions/20511347/a-good-hash-function-for-a-vector
    template<typename T>
    struct hash<std::vector<T>> {
        std::size_t operator()(const std::vector<T> &n_ids) const noexcept {
            std::size_t seed = n_ids.size();
            for (auto &_x: n_ids) {
                std::size_t x = std::hash<T>{}(_x);
                x = ((x >> 16) ^ x) * 0x45d9f3b;
                x = ((x >> 16) ^ x) * 0x45d9f3b;
                x = (x >> 16) ^ x;
                seed ^= x + 0x9e3779b9 + (seed << 6) + (seed >> 2);
            }
            return seed;
        }
    };

    template<>
    struct hash<ObjectOrVarRef> {
        std::size_t operator()(const ObjectOrVarRef &objVar) const noexcept {
            ObjTransform tr{.obj=objVar};
            return tr.num;
        }
    };

    template<>
    struct hash<DistinctParConstraint> {
        std::size_t operator()(const DistinctParConstraint &c) const noexcept {
            return c.predicate ^ hash<std::pair<ull, ull>>{}(make_pair(c.pos1, c.pos2));
        }
    };

}

static void print_numeric_atom(const Atom &atom) {
    std::cout << atom.head;
    std::cout << "(";
    ull i = 0;
    for (auto &arg : atom.args) {
        if (arg._is_variable) {
            std::cout << "?";
        } else {
            std::cout << "o";
        }
        std::cout << arg.index;
        if (++i < atom.args.size()) {
            std::cout << ", ";
        }
    }
    std::cout << ")";
}

static void print_numeric_mutex_el(const MutexElement &el) {
    std::cout << el.head;
    std::cout << "(";
    ull i = 0;
    for (auto &arg : el.pars) {
        if (arg._is_variable) {
            std::cout << "?";
        } else {
            std::cout << "o";
        }
        std::cout << arg.index;
        std::cout << " : ";
        if (arg._is_counted) {
            std::cout << "counted";
        } else {
            std::cout << "ncounted";
        }
        if (++i < el.pars.size()) {
            std::cout << ", ";
        }
    }
    std::cout << ")";
}

static Atom reducer_copy(const Atom &body_atom, DatalogTask &task, std::unordered_map<ull,ull> &to_reducer_pred) {
    auto it = to_reducer_pred.find(body_atom.head);
    ull reducer_pred;
    if (it == to_reducer_pred.end()) {
        reducer_pred = task.predicates.size();
        task.predicates.push_back(Predicate{"reduced_" + task.predicates.at(body_atom.head).name});
    } else {
        reducer_pred = it->second;
    }

    return {reducer_pred, body_atom.args};
}

void sanity_check_before_print(DatalogTask &task) {
    ull max_arity = 0;
    for (ull i = 0; i < task.predicates.size(); i++) {
        auto arity = task.predicates.at(i).arity;
        max_arity = std::max(max_arity, arity);
    }

    // we will potentially create new variables, so we may need to fill up the task with new variable names
    auto org_size = task.vars.size();
    for (ull i = 0; i < std::max(((ll) max_arity) - ((ll) org_size), (ll) 0); i++) {
        task.vars.push_back(Variable{"Var_tmp_created_" + std::to_string(i)});
    }
}

void create_reducer(DatalogTask &task) {
    std::unordered_map<ull,ull> to_reducer_pred;
    std::vector<Rule> reducer_rules;
    std::unordered_set<PredicateRef> last_predicates;

    for (ull i = 0; i < task.predicates.size(); i++) {
        last_predicates.insert(i);
    }


    for (auto &rule : task.rules) {
        for (auto &atom : rule.body) {
            last_predicates.erase(atom.head);
        }
    }

    assert(last_predicates.size() > 0);

    for (auto p : last_predicates) {
        Atom pre;
        pre.head = p;
        auto arity = task.predicates.at(p).arity;
        for (ull i = 0; i < arity; i++) {
            pre.args.push_back(ObjectOrVarRef{._is_variable=true, .index=i});
        }
        Atom head = reducer_copy(pre, task, to_reducer_pred);
        reducer_rules.push_back(Rule{head, std::vector<Atom>{pre}});
    }

    for (auto &rule : task.rules) {
        auto &head_atom = rule.head;
        for (auto &body_atom : rule.body) {
            auto new_head = reducer_copy(body_atom, task, to_reducer_pred);
            auto from_head = reducer_copy(head_atom, task, to_reducer_pred);
            reducer_rules.push_back(Rule{new_head, std::vector<Atom>{from_head, body_atom}});
        }
    }

    task.rules = reducer_rules;
}

// replaces objects that can be generalized to one variable in mutex groups (for more mutex matches)
// currently just uses type objects with a unique type
void remove_unique_objects_from_mutex_group(DatalogTask &task) {
    if (task.mutex_groups.empty()) {
        return;
    }

    // determine unique object -> type mapping
    std::unordered_set<ull> type_predicates;
    for (auto &[_, pred] : task.type_predicates) {
        type_predicates.insert(pred);
    }

    std::unordered_map<ull, ull> atom_occurrences;
    std::unordered_map<ull, ull> last_object_occurrence;
    for (auto &atom : task.init) {
        if (type_predicates.contains(atom.head)) {
            if (!atom_occurrences.contains(atom.head)) {
                atom_occurrences.emplace(atom.head, 0);
            }
            atom_occurrences.at(atom.head)++;
            assert(atom.args.size() == 1);
            assert(!atom.args.at(0)._is_variable);
            auto obj = atom.args.at(0).index;
            last_object_occurrence.emplace(atom.head, obj);
        }
    }

    std::unordered_map<ull, ull> object_to_unique_type;
    for (auto &[pred, init_amount] : atom_occurrences) {
        if (init_amount == 1) {
            object_to_unique_type.emplace(last_object_occurrence.at(pred), pred);
        }
    }

    // replace mutex element pars accordingly
    std::unordered_map<ull, ull> obj_to_new_var;
    for (auto &rule : task.mutex_groups) {
        ull max_var = 0;
        for (auto &element : rule.elements) {
            for (auto &par: element.pars) {
                if (par._is_variable) {
                    max_var = std::max(par.index, max_var);
                }
            }
        }
        max_var++;

        for (auto &element : rule.elements) {
            for (auto &par : element.pars) {
                auto par_ind = par.index;
                if (!par._is_variable && object_to_unique_type.contains(par_ind)) {
                    if (!obj_to_new_var.contains(par_ind)) {
                        obj_to_new_var.emplace(par_ind, max_var++);
                    }
                    par._is_variable = true;
                    auto pred = object_to_unique_type.at(par_ind);
                    par.associated_type = pred;
                    par._is_counted = false;
                    par.index = obj_to_new_var.at(par_ind);
                }
            }
        }
        obj_to_new_var.clear();
    }
}

class MutexMatcher {
    std::vector<std::unordered_map<ull, std::vector<ull>>> predicate_to_mutex_position; // predicate -> mutex_group -> {positions in group}
    const std::vector<MutexGroup> &mutex_groups;

    bool can_match(const ObjectOrVarRef &atom_arg, const MutexPar &m_arg, std::unordered_map<ull, ull> &var_to_obj_constraints) {
        if (m_arg._is_variable) {
            return true;
        } else {
            if (atom_arg._is_variable) {
                if (var_to_obj_constraints.contains(atom_arg.index)) {
                    return var_to_obj_constraints.at(atom_arg.index) == m_arg.index;
                }

                var_to_obj_constraints.emplace(atom_arg.index, m_arg.index);
                return true;
            } else {
                return atom_arg.index == m_arg.index;
            }
        }
    }

    bool can_match(const Atom &atom, const MutexElement &element) {
        assert(atom.head == element.head);
        assert(atom.args.size() == element.pars.size());
#ifdef MUTEX_FILTER_DEBUG_FLAG
        std::cout << "Checking if ";
        print_numeric_atom(atom);
        std::cout << " matches mutex element ";
        print_numeric_mutex_el(element);
        std::cout << ":";
#endif

        std::unordered_map<ull, ull> var_to_obj_constraints;
        for (ull i = 0; i < atom.args.size(); i++) {
            auto &atom_arg = atom.args.at(i);
            auto &m_arg = element.pars.at(i);
            if (!can_match(atom_arg, m_arg, var_to_obj_constraints)) {
#ifdef MUTEX_FILTER_DEBUG_FLAG
                std::cout << "false" << std::endl;
#endif
                return false;
            }
        }

#ifdef MUTEX_FILTER_DEBUG_FLAG
        std::cout << "true" << std::endl;
#endif
        return true;
    }

public:
    MutexMatcher(const DatalogTask &task)
        : predicate_to_mutex_position(task.predicates.size()),
          mutex_groups(task.mutex_groups) {
        ull group_id = 0;
        for (auto &group : mutex_groups) {
            ull pos_in_group = 0;
            for (auto &element : group.elements) {
                auto pred = element.head;
                auto &mutex_to_positions = predicate_to_mutex_position.at(pred);

                if (!mutex_to_positions.contains(group_id)) {
                    mutex_to_positions.emplace(group_id, std::vector<ull>());
                }
                mutex_to_positions.at(group_id).push_back(pos_in_group);
                pos_in_group++;
            }
            group_id++;
        }
    }

    struct MutexMatch {
        ull matched_group_id;
        ull matched_positio; //TODO: rename (add n)
    };

    void match(const Atom &atom, std::vector<MutexMatch> &matched_groups) {
        for (auto &[group_id, atom_indices] : predicate_to_mutex_position.at(atom.head)) {
            auto &group_elements = mutex_groups.at(group_id).elements;
            for (auto atom_index : atom_indices) {
                if (can_match(atom, group_elements.at(atom_index))) {
                    matched_groups.push_back({group_id, atom_index});
                }
            }
        }
    }
};

static void fill_mutex_var_mapping(std::unordered_map<MutexPar, ObjectOrVarRef> &atom_mutex_var_mapping,
                                   const Atom &atom,
                                   const MutexElement &atom_mutex_el,
                                   bool get_enumerated /* TODO could make this template option */) {
    for (ull i = 0; i < atom_mutex_el.pars.size(); i++) {
        auto &arg = atom_mutex_el.pars.at(i);
        if (get_enumerated == (!arg._is_variable || arg._is_counted)) continue;
        atom_mutex_var_mapping.emplace(arg, atom.args.at(i));
    }
}

static bool different_elements_of_mutex_group(const Atom &atom_1,
                                              const ull atom_1_mutex_position,
                                              const Atom &atom_2,
                                              const ull atom_2_mutex_position,
                                              const MutexGroup &mutex_group,
                                              const std::unordered_set<std::pair<ull,ull>> &distinct_vars) {
    if (atom_1.head != atom_2.head) {
        return true;
    }

    auto &atom_1_mutex_el = mutex_group.elements.at(atom_1_mutex_position);
    auto &atom_2_mutex_el = mutex_group.elements.at(atom_2_mutex_position);

    // enumerated vars are the same
    std::unordered_map<MutexPar, ObjectOrVarRef> atom_1_mutex_var_mapping;
    std::unordered_map<MutexPar, ObjectOrVarRef> atom_2_mutex_var_mapping;
    assert(atom_1_mutex_el.pars.size() == atom_1.args.size());
    assert(atom_1_mutex_el.pars.size() == atom_2.args.size());
    assert(atom_2_mutex_el.pars.size() == atom_2.args.size());

    fill_mutex_var_mapping(atom_1_mutex_var_mapping, atom_1, atom_1_mutex_el, true);
    fill_mutex_var_mapping(atom_2_mutex_var_mapping, atom_2, atom_2_mutex_el, true);
    assert(atom_1_mutex_var_mapping.size() == atom_2_mutex_var_mapping.size());

    for (auto &[var, inst] : atom_1_mutex_var_mapping) {
        assert(var._is_variable);
        if (!atom_2_mutex_var_mapping.contains(var)) continue;

        if (atom_2_mutex_var_mapping.at(var) != inst) {
            return false;
        }
    }

    // at leas one counted var differs
    atom_1_mutex_var_mapping.clear();
    atom_2_mutex_var_mapping.clear();
    fill_mutex_var_mapping(atom_1_mutex_var_mapping, atom_1, atom_1_mutex_el, false);
    fill_mutex_var_mapping(atom_2_mutex_var_mapping, atom_2, atom_2_mutex_el, false);
    assert(atom_1_mutex_var_mapping.size() == atom_2_mutex_var_mapping.size());

    for (auto &[var, inst] : atom_1_mutex_var_mapping) {
        if (!atom_2_mutex_var_mapping.contains(var)) continue;

        if (var._is_variable) {
            if (atom_2_mutex_var_mapping.at(var) != inst) {
                return true;
            }
        } else {
            assert(atom_2_mutex_var_mapping.at(var) == inst);
        }
    }

    return false;
}


void create_pred_to_args_map(const DatalogTask &task, std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> &pred_to_args) {
    pred_to_args = std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>>(task.predicates.size());
    ull i = 0;
    for (auto &atom : task.init) {
        pred_to_args.at(atom.head).insert(make_pair(atom.args, i));
        i++;
    }
}

void create_pred_to_args(const DatalogTask &task, std::vector<std::unordered_set<std::vector<ull>>> &pred_to_args) {
    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args_map;
    create_pred_to_args_map(task, pred_to_args_map);

    for (auto &m : pred_to_args_map) {
        std::unordered_set<std::vector<ull>> s;
        for (auto &[k, _] : m) {
            std::vector<ull> arg_container;
            for (auto arg : k) {
                assert(!arg._is_variable);
                arg_container.push_back(arg.index);
            }
            s.insert(arg_container);
        }
        pred_to_args.push_back(s);
    }
}

static void get_var_args(const Atom &atom, std::unordered_set<ull> var_refs) {
    for (auto &arg : atom.args) {
        if (arg._is_variable) {
            var_refs.insert(arg.index);
        }
    }
}

static void add_guranteed_atom(std::vector<Atom> &atoms,
                               DatalogTask &task,
                               ull i,
                               std::unordered_map<ull,ull> &guaranteed_pred_map,
                               std::vector<Predicate> &additional_predicates) {
    auto &atom_to_copy = atoms.at(i);

    if (!guaranteed_pred_map.contains(atom_to_copy.head)) {
        auto &old_pred = task.predicates.at(atom_to_copy.head);
        std::string new_name = old_pred.name + std::string("__guaranteed");
        auto old_arity = old_pred.arity;
        guaranteed_pred_map.emplace(atom_to_copy.head, task.predicates.size() + additional_predicates.size());
        additional_predicates.push_back(Predicate{new_name, old_arity});
    }
    assert(guaranteed_pred_map.contains(atom_to_copy.head));
    atoms.push_back(Atom{guaranteed_pred_map.at(atom_to_copy.head), atom_to_copy.args});
}

ull non_guar_hack_count = 0;
static void mutex_filter_rule(Rule &rule,
                         MutexMatcher &matcher,
                         DatalogTask &task,
                         const std::unordered_set<PredicateRef> &distinct_predicates,
                         const std::unordered_set<DistinctParConstraint> &distinct_par_constraints,
                         std::unordered_map<ull,ull> &guaranteed_pred_map,
                         std::vector<Rule> &additional_rules,
                         std::vector<Predicate> &additional_predicates,
                         Atom &false_atom) {
    // split into pre, add, del
    std::vector<ull> pre_positions;
    std::vector<ull> add_positions;
    std::vector<ull> del_positions;
    std::vector<ull> positions_to_keep;

    ull atom_pos = 0;
    for (auto &atom : rule.body) {
        if (task.add_to_normal_pred.contains(atom.head)) {
            assert(starts_with(task.predicates.at(rule.body.at(atom_pos).head).name, ADD_PRED_START));
            add_positions.push_back(atom_pos);
        } else if (task.del_to_normal_pred.contains(atom.head)) {
            assert(starts_with(task.predicates.at(rule.body.at(atom_pos).head).name, DEL_PRED_START));
            del_positions.push_back(atom_pos);
        } else {
            pre_positions.push_back(atom_pos);
            positions_to_keep.push_back(atom_pos);
        }
        atom_pos++;
    }

    // determine distinct vars in rule
    std::unordered_set<ull> var_refs;
    std::unordered_set<std::pair<ull,ull>> distinct_vars;
    for (auto i : pre_positions) {
        auto &pre = rule.body.at(i);
        auto pred = pre.head;

        if (distinct_predicates.contains(pred)) {
            get_var_args(pre, var_refs);
            for (auto v1 : var_refs) {
                for (auto v2 : var_refs) {
                    if (v1 != v2) {
                        distinct_vars.emplace(v1, v2);
                    }
                }
            }
            var_refs.clear();
        } else {
            //TODO: once we have different containers per predicate we can return here if container is empty

            auto &args = pre.args;
            for (ull i = 0; i < args.size(); i++) {
                auto &arg_i = args.at(i);
                if (!arg_i._is_variable) continue;
                for (ull j = 0; j < args.size(); j++) {
                    auto &arg_j = args.at(j);
                    if (!arg_j._is_variable) continue;
                    if (arg_i.index == arg_j.index) continue;
                    if (i == j) continue;
                    if (distinct_par_constraints.contains({pre.head, i, j})) {
                        auto i_index = arg_i.index;
                        auto j_index = arg_j.index;
                        distinct_vars.emplace(i_index, j_index);
                    }
                }
            }
        }
    }

    // compute matches for pre (mutex_group -> {original atom position})
    std::vector<std::vector<PreMatch>> pre_mutex_matches(task.mutex_groups.size());
    for (auto i : pre_positions) {
        auto &pre = rule.body.at(i);
        std::vector<MutexMatcher::MutexMatch> matched_groups;
        matcher.match(pre, matched_groups);

        for (auto match : matched_groups) {
            pre_mutex_matches.at(match.matched_group_id).push_back({i, match.matched_positio});
        }
    }

    std::unordered_map<ull, std::vector<MutexMatcher::MutexMatch>> index_to_mutex_matches;
    // filter add
    for (auto i : add_positions) {
        auto &_add = rule.body.at(i);
        std::vector<MutexMatcher::MutexMatch> matched_groups;
        Atom add{task.add_to_normal_pred.at(_add.head), _add.args};
        matcher.match(add, matched_groups);
        index_to_mutex_matches.emplace(i, matched_groups);

        for (auto matched_group : matched_groups) {
            for (auto j : pre_mutex_matches.at(matched_group.matched_group_id)) {
                auto &pre = rule.body.at(j.atom_position);
                if (different_elements_of_mutex_group(add,
                                                      matched_group.matched_positio,
                                                      pre,
                                                      j.mutex_position,
                                                      task.mutex_groups.at(matched_group.matched_group_id),
                                                      distinct_vars)) {
                    positions_to_keep.push_back(i);
                    break;
                }
            }
            if (positions_to_keep.back() == i) {
                break;
            }
        }
    }

    // map predicate to preconditions
    std::unordered_map<ull, std::vector<ull>> pred_to_atoms;
    for (auto i : pre_positions) {
        auto pred = rule.body.at(i).head;
        if (!pred_to_atoms.contains(pred)) {
            pred_to_atoms.emplace(pred, std::vector<ull>());
        }
        pred_to_atoms.at(pred).push_back(i);
    }

    // filter del
    for (auto j : del_positions) {
        auto &del = rule.body.at(j);
        auto org_p_id = task.del_to_normal_pred.at(del.head);

        // insertion is only for non-guaranteed hack
        std::vector<MutexMatcher::MutexMatch> matched_groups;
        Atom _del{org_p_id, del.args};
        matcher.match(_del, matched_groups);
        index_to_mutex_matches.emplace(j, matched_groups);

        if (!pred_to_atoms.contains(org_p_id)) continue;
        for (auto i : pred_to_atoms.at(org_p_id)) {
            assert(task.del_to_normal_pred.at(del.head) == rule.body.at(i).head);
            if (del.args == rule.body.at(i).args) {
                positions_to_keep.push_back(j);
                assert(starts_with(task.predicates.at(rule.body.at(j).head).name, DEL_PRED_START));
                break;
            }
        }
    }

    // put back together
    std::unordered_map<std::pair<ull,ull>, ull> match_preds;
    //TODO: could do this in O(n) by flagging positions to keep, and getting rid of lookup (probably not so important given the typical amount of atoms in lifted actions)
    std::unordered_set<ull> positions_to_keep_lookup(positions_to_keep.begin(), positions_to_keep.end());
    std::unordered_set<ull> to_rm;
    for (auto &v : {add_positions, del_positions})
    for (auto i : v) {
        if (!positions_to_keep_lookup.contains(i)) {
            // hack for non-guaranteed info
            auto hack_id = task.predicates.size() + additional_predicates.size();
            additional_predicates.push_back(Predicate{.name=RULE_HACK_STUB+std::to_string(non_guar_hack_count++)});
            Atom hack_atom{hack_id, std::vector<ObjectOrVarRef>{}};

            std::vector<Atom> body{rule.body.at(i), false_atom};
            for (auto &match : index_to_mutex_matches.at(i)) {
                std::pair<ull, ull> match_pair{match.matched_group_id, match.matched_positio};
                if (!match_preds.contains(match_pair)) {
                    auto match_id = task.predicates.size() + additional_predicates.size();
                    additional_predicates.push_back(Predicate{.name="match_"
                                    + std::to_string(match_pair.first)
                                    + "_" + std::to_string(match_pair.second)});
                }
                Atom mutex_atom{match_preds.at(match_pair), std::vector<ObjectOrVarRef>{}};
                body.push_back(mutex_atom);
            }
            additional_rules.push_back(Rule{hack_atom, body});

            positions_to_keep.push_back(rule.body.size());
            rule.body.push_back(hack_atom);

            positions_to_keep.push_back(i);
        } else {
            positions_to_keep.push_back(rule.body.size());
            add_guranteed_atom(rule.body, task, i, guaranteed_pred_map, additional_predicates);
            to_rm.insert(i);
        }
    }

    std::vector<ull> new_positions_to_keep;
    for (auto i : positions_to_keep) {
        if (!to_rm.contains(i))
            new_positions_to_keep.push_back(i);
    }
    positions_to_keep = new_positions_to_keep;

    std::sort(positions_to_keep.begin(), positions_to_keep.end());
    keep_indices(rule.body, positions_to_keep);
}

std::string add_guaranteed(const std::string &original) {
    return original + GUARANTEED_PRED_END;
}

std::string get_counter_part(const std::string &original) {
    assert(ADD_PRED_START.size() == DEL_PRED_START.size());

    std::ostringstream oss;
    if (is_add_predicate(original)) {
        oss << DEL_PRED_START;
    } else {
        assert(is_del_predicate(original));
        oss << ADD_PRED_START;
    }
    oss << original.substr(ADD_PRED_START.size());

    return oss.str();
}

void create_guaranteed_maps(const DatalogTask &task,
                            std::unordered_map<std::string, ull> &guaranteed_pred_names,
                            std::unordered_map<PredicateRef, PredicateRef> &counter_part,
                            std::unordered_map<PredicateRef, PredicateRef> &guaranteed_variant // maps original pred to either add_original_guaranteed or del_original_guaranteed
) {
    //TODO: important: counterpart is no longer needed

    ull i = 0;
    for (auto &p : task.predicates) {
        if (is_guranteed_predicate(p.name)) {
            guaranteed_pred_names.insert({p.name, i});
        }
        i++;
    }

    // links guaranteed adds to guaranteed deletes and vice versa
    i = 0;
    for (auto &p : task.predicates) {
        if (is_guranteed_predicate(p.name)) {
            if (counter_part.contains(i)) {
                i++;
                continue;
            }
            auto counter_part_name = get_counter_part(p.name);
            if (guaranteed_pred_names.contains(counter_part_name)) {
                auto cp_ind = guaranteed_pred_names.at(counter_part_name);
                counter_part.insert({i, cp_ind});
                counter_part.insert({cp_ind, i});
            }
        } else {
            auto w_guaranteed_name = add_guaranteed(DEL_PRED_START + p.name);
            if (guaranteed_pred_names.contains(w_guaranteed_name)) {
                auto g_ind = guaranteed_pred_names.at(w_guaranteed_name);
                guaranteed_variant.insert({i, g_ind});
                assert(guaranteed_pred_names.contains(add_guaranteed(ADD_PRED_START + p.name)));
            } else {
                assert(!guaranteed_pred_names.contains(add_guaranteed(ADD_PRED_START + p.name)));
            }
        }
        i++;
    }
}

static bool all_args_distinc(const Atom &atom, std::unordered_set<ull> &seen_so_far) { //TODO: rename to distinct
    for (auto arg : atom.args) {
        assert(!arg._is_variable);
        seen_so_far.insert(arg.index);
    }

    ull seen_amount = seen_so_far.size();
    seen_so_far.clear();
    return atom.args.size() == seen_amount;
}

void zero_ary_relaxation(DatalogTask &task) {
    for (auto &pred : task.predicates) {
        pred.arity = 0;
    }
    for (auto &rule : task.rules) {
        rule.head.args.clear();
        for (auto &atom : rule.body) {
            atom.args.clear();
        }
    }
    for (auto &atom : task.init) {
        atom.args.clear();
    }
}

void to_unary(std::vector<Atom> to_transform, std::unordered_map<ull, std::vector<ull>> &pred_translation) {
    std::vector<Atom> old_atoms;
    std::set<std::tuple<ull, ull, ull>> new_init;
    for (auto &atom : to_transform) {
        if (pred_translation.contains(atom.head)) {
            int i = 0;
            for (auto sub_preds : pred_translation.at(atom.head)) {
                auto &arg =  atom.args.at(i);
                ull is_var = arg._is_variable;
                ull index = arg.index;
                new_init.insert({sub_preds, is_var, index});
                i++;
            }
        } else {
            old_atoms.push_back(atom);
        }
    }

    to_transform = old_atoms;
    for (auto &p : new_init) {
        to_transform.push_back(Atom{.head=get<0>(p), .args={ObjectOrVarRef{._is_variable=get<1>(p), .index=get<2>(p)}}});
    }
}

void unary_relaxation(DatalogTask &task) {
    std::vector<Predicate> new_preds;
    std::unordered_map<ull, std::vector<ull>> pred_translation;

    ull p_id = 0;
    for (auto &pred : task.predicates) {
        if (pred.arity > 1) {
            std::vector<ull> new_subpreds;
            for (int i = 0; i < pred.arity; i++) {
                new_subpreds.push_back(new_preds.size());
                new_preds.push_back(Predicate{.name=pred.name+"___ur"+std::to_string(i), .arity=1});
            }
            pred_translation.emplace(p_id, new_subpreds);
        } else {
            new_preds.push_back(pred);
        }
        p_id++;
    }
    task.predicates = new_preds;

    std::vector<Rule> new_rules;
    for (auto &rule : task.rules) {
        to_unary(rule.body, pred_translation);

        std::vector<Atom> head_args{rule.head};
        to_unary(head_args, pred_translation);
        for (auto &head : head_args) {
            new_rules.push_back(Rule{.head=head, .body=rule.body});
        }
    }
    task.rules = new_rules;

    to_unary(task.init, pred_translation);
}

void add_repair_actions(DatalogTask &task) {
    std::unordered_set<PredicateRef> to_ignore;
    std::vector<Predicate> additional_predicates;

    ull goal_pred = 0;
    for (auto &p : task.predicates) {
        if (p.name == GOAL_NAME) {
            to_ignore.insert(goal_pred);
            break;
        }
        goal_pred++;
    }
    assert(to_ignore.size() == 1);

    for (auto &[_, pred] : task.type_predicates) {
        to_ignore.insert(pred);
    }

    ull pred_id = 0;
    for (auto &pred : task.predicates) {
        if (to_ignore.contains(pred_id)) {
            pred_id++;
            continue;
        }

        std::vector<ObjectOrVarRef> standard_args;
        for (ull i = 0; i < pred.arity; i++) {
            standard_args.push_back(ObjectOrVarRef{._is_variable=true, .index=i});
        }
        Atom standard_atom{.head=pred_id, .args=standard_args};

        auto activate_pred_id = task.predicates.size() + additional_predicates.size();
        additional_predicates.push_back(Predicate{.name="activate_pred_" + pred.name, .arity=0});
        Atom activate_atom{.head=activate_pred_id, .args={}};

        task.rules.push_back(Rule{.head=standard_atom, .body={activate_atom}});
        task.rules.push_back(Rule{.head=activate_atom, .body={}});

        pred_id++;
    }

    for (auto &pred : additional_predicates) {
        task.predicates.push_back(pred);
    }
}


void print_problem(DatalogTask &task) {
    std::cout << "(define (problem generated_problem)\n";
    std::cout << "  (:domain generated_domain)\n\n";


    std::unordered_set<ull> collected_constants;
    for (const auto& rule : task.rules) {
        for (const auto& atom : rule.body) {
            for (const auto& arg : atom.args) {
                if (!arg._is_variable) {
                    collected_constants.insert(arg.index);
                }
            }
        }
        for (const auto& arg : rule.head.args) {
            if (!arg._is_variable) {
                collected_constants.insert(arg.index);
            }
        }
    }

    // Print objects
    std::cout << "  (:objects\n";
    ull o = 0;
    for (const auto& object : task.objects) {
        if (!collected_constants.contains(o)) {
            std::cout << "    " << object.name << " - object\n";
        }
        o++;
    }
    std::cout << "  )\n\n";

    // Print initial state
    std::cout << "  (:init\n";
    for (const auto& atom : task.init) {
        std::cout << "    (" << task.predicates[atom.head].name;
        for (const auto& arg : atom.args) {
            assert(!arg._is_variable);
            std::cout << " " << task.objects[arg.index].name;
        }
        std::cout << ")\n";
    }
    std::cout << "  )\n\n";

    // Print goal state
    std::cout << "  (:goal\n";
    std::cout << "    (" << GOAL_NAME << ")\n";
    std::cout << "  )\n";
    std::cout << ")\n";

    exit(0);
}
void print_domain(DatalogTask &task) {
    std::cout << "(define (domain generated_domain)\n\n";

    // Print types
    std::cout << "  (:types object)\n\n";

    // Print predicates
    std::cout << "  (:predicates\n";
    for (const auto& predicate : task.predicates) {
        std::cout << "    (" << predicate.name;
        for (ull i = 0; i < predicate.arity; ++i) {
            std::cout << " ?v" << i << " - object";
        }
        std::cout << ")\n";
    }
    std::cout << "  )\n\n";

    // Print actions
    ull i = 0;
    std::unordered_set<ull> collected_constants;
    for (const auto& rule : task.rules) {
        std::cout << "  (:action action_" << i << "\n";
        std::cout << "    :parameters (";
        for (ull i = 0; i < rule.head.args.size(); ++i) {
            if (rule.head.args[i]._is_variable) {
                std::cout << "?v" << rule.head.args[i].index << " - object ";
            }
        }
        std::cout << ")\n";

        std::cout << "    :precondition (and\n";
        for (const auto& atom : rule.body) {
            std::cout << "      (" << task.predicates[atom.head].name;
            for (const auto& arg : atom.args) {
                if (arg._is_variable) {
                    std::cout << " " << task.vars[arg.index].name;
                } else {
                    std::cout << " " << task.objects[arg.index].name;
                    collected_constants.insert(arg.index);
                }
            }
            std::cout << ")\n";
        }
        std::cout << "    )\n";

        std::cout << "    :effect (and\n";
        std::cout << "      (" << task.predicates[rule.head.head].name;
        for (const auto& arg : rule.head.args) {
            if (arg._is_variable) {
                std::cout << " " << task.vars[arg.index].name;
            } else {
                std::cout << " " << task.objects[arg.index].name;
                collected_constants.insert(arg.index);
            }
        }
        std::cout << ")\n";
        std::cout << "    )\n";
        std::cout << "  )\n\n";
        i++;
    }


    // Print objects
    std::cout << "  (:constants\n";
    ull o = 0;
    for (const auto& constant : collected_constants) {
        std::cout << "    " << task.objects[o].name << " - object\n";
        o++;
    }
    std::cout << "  )\n\n";

    std::cout << ")\n";
    exit(0);
}

void mutex_filter(DatalogTask &task) {
    MutexMatcher mutex_matcher(task);

    std::unordered_set<PredicateRef> distinct_predicates;
    for (ull i = 0; i < task.predicates.size(); i++) {
        distinct_predicates.insert(i);
    }

    // determine predicates that imply distinct parameters
    std::unordered_set<ull> hacky_set; // to continously use the same set
    for (auto &atom : task.init) {
        if (!distinct_predicates.contains(atom.head)) continue;
        if (!all_args_distinc(atom, hacky_set)) {
            distinct_predicates.erase(atom.head);
        }
    }

    // determine par positions per predicates that imply distinct parameters
    std::unordered_set<DistinctParConstraint> distinct_par_constraints;
    for (ull i = 0; i < task.predicates.size(); i++) {
        if (!distinct_predicates.contains(i)) {
            auto &pred = task.predicates.at(i);
            for (ull j = 0; j < pred.arity; j++) {
                for (ull k = 0; k < pred.arity; k++) {
                    if (j != k) {
                        distinct_par_constraints.insert({i, j, k});
                    }
                }
            }
        }
    }

    std::vector<ull> objects_seen; //tracks objects seen
    std::vector<std::vector<ull>> object_to_positions(task.objects.size()); // maps object indexes to the positions in the atom where they occured
    for (auto &atom : task.init) {
        auto pred = atom.head;

        ull i = 0;
        for (auto &arg: atom.args) {
            assert(!arg._is_variable);
            objects_seen.push_back(arg.index);
            object_to_positions.at(arg.index).push_back(i);
            i++;
        }

        for (auto obj: objects_seen) {
            auto &positions = object_to_positions.at(obj);
            for (auto pos1: positions) {
                for (auto pos2: positions) {
                    if (pos1 != pos2) {
                        distinct_par_constraints.insert({atom.head, pos1, pos2});
                    }
                }
            }
            positions.clear();
        }
        objects_seen.clear();
    }

#ifndef NDEBUG
    for (auto &v : object_to_positions) {
        assert(v.empty());
    }
    assert(objects_seen.empty());
#endif

    std::vector<Rule> additional_rules;
    std::vector<Predicate> additional_predicates;
    Atom false_atom{task.predicates.size(), std::vector<ObjectOrVarRef>{}};
    task.predicates.push_back(Predicate{FALSE_PRED, 0});
    std::unordered_map<ull,ull> guaranteed_map;
    for (auto &rule : task.rules) {
        mutex_filter_rule(rule,
                          mutex_matcher,
                          task,
                          distinct_predicates,
                          distinct_par_constraints,
                          guaranteed_map,
                          additional_rules,
                          additional_predicates,
                          false_atom);
    }

    for (auto &r : additional_rules) {
        task.rules.push_back(r);
    }

    for (auto &p : additional_predicates) {
        assert(p.arity == 0 || is_guranteed_predicate(p.name));
        if (p.arity == 0) {
            task.init.push_back(Atom{task.predicates.size(), std::vector<ObjectOrVarRef>{}});
        }
        task.predicates.push_back(p);
    }
}

static void get_action_preds(std::unordered_set<PredicateRef> &action_preds, const DatalogTask &task) {
    ull p_id = 0;
    for (auto &p : task.predicates) {
        if (is_action_pred(p.name)) {
            action_preds.insert(p_id);
        }
        p_id++;
    }
}

MutexMatcher::MutexMatch get_mutex_match(const std::string &s) {
    std::istringstream stream(s);
    char ch;

    for (int i = 0; i < 6; ++i) {
        if (stream.get(ch) || ch != "match_"[i]) {
            assert(false && "Shouldn't happen");
        }
    }

    ull num_a;
    stream >> num_a;

    if (stream.get(ch) || ch != '_') {
        assert(false && "Shouldn't happen");
    }

    ull num_b;
    assert(!stream.get(ch));

    return MutexMatcher::MutexMatch{num_a, num_b};
}

struct MutexAnnotation {
    Atom atom;
    std::vector<MutexMatcher::MutexMatch> matches;
};
struct MutexIdPair {
    ull min_id;
    ull max_id;
};
void reintegrate_mutex_rules(DatalogTask &task) {
    std::unordered_map<ull, MutexAnnotation> annotations;
    std::unordered_map<ull, std::vector<Atom>> conditions;
    std::unordered_set<ull> rules_to_delete;

    ull min_mutex_count = 0;
    for (auto &pred : task.predicates) {
        if (is_max_mutex_pred(pred.name)) {
            min_mutex_count++;
        }
    }
#ifndef NDEBUG
    ull __max_mutex_count = 0;

    for (auto &pred : task.predicates) {
        if (is_min_mutex_pred(pred.name)) {
            __max_mutex_count++;
        }
    }

    assert(__max_mutex_count == min_mutex_count);
#endif

    // parse mutex annotations
    ull i = 0;
    for (auto &rule : task.rules) {
        if (is_rule_hack(task.predicates.at(rule.head.head).name)) {
            assert(rule.body.size() >= 2);
            assert(is_false_pred(task.predicates.at(rule.body.at(1).head).name));

            std::vector<MutexMatcher::MutexMatch> matches;
            for (ull i = 2; i < rule.body.size(); i++) {
                matches.push_back(get_mutex_match(task.predicates.at(rule.body.at(i).head).name));
            }

            auto &atom = *rule.body.begin();
            assert(!annotations.contains(rule.head.head));
            annotations.emplace(rule.head.head, MutexAnnotation{atom, matches});
            rules_to_delete.insert(i);
        }
        i++;
    }

    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args;
    create_pred_to_args_map(task, pred_to_args);

    std::unordered_map<std::string, ull> guaranteed_pred_names;
    std::unordered_map<PredicateRef, PredicateRef> counter_part;
    std::unordered_map<PredicateRef, PredicateRef> guaranteed_variant;
    create_guaranteed_maps(task, guaranteed_pred_names, counter_part, guaranteed_variant);

    // construct conditions
    std::unordered_map<ull, MutexIdPair> new_mutexes;
    for (auto &[annotation_pred, mutex_annotation] : annotations) {
        std::vector<Atom> produced_atoms;
        auto h = mutex_annotation.atom.head;
        bool is_add = task.add_to_normal_pred.contains(h);
#ifndef NDEBUG
        if (is_add) {
            assert(is_add_predicate(task.predicates.at(h).name));
        } else {
            assert(is_del_predicate(task.predicates.at(h).name));
        }
#endif

        auto normal_pred = is_add ? task.add_to_normal_pred.at(h)
                                  : task.del_to_normal_pred.at(h);

        if (!guaranteed_variant.contains(normal_pred)) {
            for (auto &START : {ADD_PRED_START, DEL_PRED_START}) {
                // create pred
                auto new_pred = task.predicates.size();
                auto &old_pred = task.predicates.at(normal_pred);
                auto s = START+old_pred.name+GUARANTEED_PRED_END;
                guaranteed_pred_names.emplace(s, new_pred);
                task.predicates.push_back(Predicate{s, old_pred.arity});

                // copy atoms
                for (auto &[args, _] : pred_to_args.at(h)) {
                    task.init.push_back(Atom{new_pred, args});
                }
            }

            guaranteed_variant.emplace(normal_pred, task.predicates.size()-1);
            counter_part.emplace(task.predicates.size()-1, task.predicates.size()-2);
            counter_part.emplace(task.predicates.size()-2, task.predicates.size()-1);
        }

        auto guaranteed_pred = guaranteed_variant.at(normal_pred);
        auto _guaranteed_pred = guaranteed_pred;
        assert(is_del_predicate(task.predicates.at(_guaranteed_pred).name));
        if (is_add) {
            _guaranteed_pred = counter_part.at(_guaranteed_pred);
            assert(is_add_predicate(task.predicates.at(_guaranteed_pred).name));
        }
        Atom guar_atom{_guaranteed_pred, mutex_annotation.atom.args};
        produced_atoms.push_back(guar_atom);

        if (mutex_annotation.matches.size() == 0) {
            // create additional mutexes
            if (!new_mutexes.contains(h)) {
                // create pred
                auto new_pred = task.predicates.size();
                auto &old_pred = task.predicates.at(normal_pred);
                auto m_name = MUTEX_PRED; //+"_atom_"+old_pred.name
                task.predicates.push_back(Predicate{m_name, 0});

                // create_mutex_rule
                Atom head{new_pred, {}};
                std::vector<ObjectOrVarRef> all_vars_enumerated;
                for (ull i = 0; i < mutex_annotation.atom.args.size(); i++) {
                    all_vars_enumerated.push_back(ObjectOrVarRef{._is_variable=true, .index=task.vars.size()});
                    task.vars.push_back(Variable{.name="Var_enumerated_"+std::to_string(i)+"_"+NONE_T});
                }

                Atom body_atom{normal_pred, all_vars_enumerated};
                task.rules.push_back(Rule{head, std::vector<Atom>{body_atom}});

                // create max/min mutex preds
                auto min_pred = task.predicates.size();
                task.predicates.push_back(Predicate{to_min_mutex_pred(min_mutex_count), 0});

                auto max_pred = task.predicates.size();
                task.predicates.push_back(Predicate{to_max_mutex_pred(min_mutex_count), 0});

                new_mutexes.emplace(h, MutexIdPair{.min_id=min_pred, .max_id=max_pred});
                min_mutex_count++;

                // create max/min mutex rules
                assert(is_del_predicate(task.predicates.at(guaranteed_pred).name));
                Atom max_head{max_pred, all_vars_enumerated};
                Atom del_atom{guaranteed_pred, all_vars_enumerated};
                task.rules.push_back(Rule{max_head, std::vector<Atom>{del_atom}});

                Atom min_head{min_pred, all_vars_enumerated};
                Atom add_atom{counter_part.at(guaranteed_pred), all_vars_enumerated};
                task.rules.push_back(Rule{min_head, std::vector<Atom>{add_atom}});

                // copy atoms
                for (auto &[args, _] : pred_to_args.at(h)) {
                    task.init.push_back(Atom{min_pred, args});
                    task.init.push_back(Atom{max_pred, args});
                }
            }

            auto &hit = new_mutexes.at(h);
            auto new_h = is_add ? hit.max_id : hit.min_id;
            produced_atoms.push_back(Atom{new_h, mutex_annotation.atom.args});
        } else {
            assert(false && "TODO implement me");
        }

        conditions.emplace(annotation_pred, produced_atoms);
    }

    // delete rules
    std::vector<Rule> new_rules;
    for (ull i = 0; i < task.rules.size(); i++) {
        if (!rules_to_delete.contains(i)) {
            new_rules.push_back(task.rules.at(i));
        }
    }
    task.rules = new_rules;

    // substitute atoms
    for (auto &rule : task.rules) {
        std::vector<Atom> new_body;
        for (auto &atom : rule.body) {
            if (conditions.contains(atom.head)) {
                for (auto &atom2 : conditions.at(atom.head)) {
                    new_body.push_back(atom2);
                }
            } else  {
                new_body.push_back(atom);
            }
        }
        rule.body = new_body;
    }
}

void integrate_add_del_rules(DatalogTask &task) {
    task.rules.clear();

    for (auto &mp : {task.add_to_normal_pred, task.del_to_normal_pred})
    for (auto &[pred_copy, normal_pred] : mp) {
        std::vector<ObjectOrVarRef> distinct_args;
        assert(task.predicates.at(pred_copy).arity == task.predicates.at(normal_pred).arity);
        for (ull i = 0; i < task.predicates.at(pred_copy).arity; i++) {
            distinct_args.push_back(ObjectOrVarRef{true, i});
        }
        Atom copy_atom{pred_copy, distinct_args};
        Atom normal_atom{normal_pred, distinct_args};

        task.rules.push_back(Rule{copy_atom, std::vector<Atom>{normal_atom}});
    }
}


void create_ext_pred(DatalogTask &task, ull id, size_t size) {
    task.predicates.push_back(Predicate{std::string("tmp_ext_")
                                        + std::to_string(id),
                                        size});
}

void superset_pars(DatalogTask &task) {
    std::vector<Rule> extra_rules;
    ull id = 0;
    for (auto &rule : task.rules) {
        if (rule.body.size() <= 1) {
            continue;
        }

        ull ext_pred = task.predicates.size();
        std::unordered_set<ull> all_body_vars;
        for (auto &atom : rule.body) {
            for (auto &arg : atom.args) {
                if (arg._is_variable) all_body_vars.insert(arg.index);
            }
        }
        std::vector<ObjectOrVarRef> ext_args;
        for (auto v : all_body_vars) {
            ext_args.push_back(ObjectOrVarRef{true, v});
        }
        create_ext_pred(task, id++, ext_args.size());
        Atom ext_atom{ext_pred, ext_args};

        extra_rules.push_back(Rule{rule.head, {ext_atom}});
        rule.head = ext_atom;
    }

    for (auto &rule : extra_rules) {
        task.rules.push_back(rule);
    }
}

void linearize_action_task(DatalogTask &task) {
    std::unordered_set<PredicateRef> action_preds;
    get_action_preds(action_preds, task);

    // drop rules eff :- action
    std::vector<ull> pos_to_keep;
    ull i = 0;
    for (auto &rule : task.rules) {
        if (!(rule.body.size() == 1 && action_preds.contains(rule.body.at(0).head))) {
#ifndef NDEBUG
            // verify that if an action predicate occurs in the body, it is the only body element
            for (auto &el : rule.body) {
                assert(!action_preds.contains(el.head));
            }
#endif
            pos_to_keep.push_back(i);
        }
        i++;
    }
    keep_indices(task.rules, pos_to_keep);

    // drop action parameter
    for (auto &rule : task.rules) {
        if (action_preds.contains(rule.head.head)) {
            rule.head.args.clear();
        }
    }

#ifndef NDEBUG
    // verify rule graph is now acyclic
    std::vector<std::vector<ull>> edges(task.predicates.size());
    for (auto &rule : task.rules) {
        auto to = rule.head.head;
        for (auto &el : rule.body) {
            auto from = el.head;
            edges.at(from).push_back(to);
        }
    }
    std::unordered_set<ull> global_seen; //TODO: could be bool vector

    for (ull p = 0; p < task.predicates.size(); p++) {
        //TODO: first checks here are probably not needed
        if (edges.at(p).empty()) {
            continue;
        }
        if (global_seen.contains(p)) {
            continue;
        }

        // perform DFS over graph structure
        std::unordered_set<ull> local_seen_set{p};
        std::vector<std::pair<ull, ull>> local_seen{std::make_pair(p, 0)}; // (node, edgecount)

        while (!local_seen.empty()) {
            auto &[current_node, current_count] = local_seen.back();
            auto &current_edges = edges.at(current_node);

            if (current_edges.size() == current_count) {
                global_seen.insert(current_node);
                local_seen_set.erase(current_node);
                local_seen.pop_back();
                if (!local_seen.empty()) {
                    local_seen.back().second++;
                }
                continue;
            }
            assert(current_edges.size() > current_count);

            if (global_seen.contains(current_node)) {
                current_count++;
                continue;
            }

            auto to = current_edges.at(current_count);
            local_seen.emplace_back(to, 0);
            assert(!local_seen_set.contains(to));
            local_seen_set.insert(to);
        }
    }
#endif
}

struct JoinElement {
    static constexpr ull NO_ELEMENT = std::numeric_limits<ull>::max();
    std::vector<ull> pars_tracked; //TODO: rn to join pars
    ull from;
    ull to;
};

void print_order(const DatalogTask &task, const Rule &rule, std::vector<JoinElement> &order) {
    for (auto &jel : order) {
        pretty_print(task, rule.body.at(jel.from), std::cout);
        std::cout << " --";
        for (auto par : jel.pars_tracked) {
            std::cout << task.vars.at(par).name << ";";
        }
        std::cout << "-> ";
        if (jel.to != JoinElement::NO_ELEMENT) {
            pretty_print(task, rule.body.at(jel.to), std::cout);
        } else {
            std::cout << "NONE";
        }
        std::cout << ", ";
    }
}

static std::set<ull> get_pars(const Atom &atom) {
    std::set<ull> pars;
    for (auto &ref : atom.args) {
        if (ref._is_variable) {
            pars.insert(ref.index);
        }
    }

    return pars;
}

static void compute_join_order(DatalogTask &task, std::vector<std::vector<JoinElement>> &join_traces, const Rule &rule) {
    std::vector<JoinElement> join_order;
    if (rule.body.size() > 1) {
        // structures needed for GYO algorithm
        auto result_pars = get_pars(rule.head);
        std::vector<std::set<ull>> pars_per_body_element;
        for (auto &body_el: rule.body) {
            pars_per_body_element.push_back(get_pars(body_el));
        }

        std::unordered_map<ull, ull> par_count;
        for (auto &pars: pars_per_body_element) {
            for (auto par: pars) {
                if (!par_count.contains(par)) {
                    par_count.emplace(par, 0);
                }
                par_count.at(par)++;
            }
        }

        // ordering for tie breaking in GYO algorithm
        std::vector<ull> custom_elements;
        for (ull i = 0; i < rule.body.size(); i++) {
            custom_elements.push_back(i);
        }
        std::sort(custom_elements.begin(), custom_elements.end(),
                  [pars_per_body_element, result_pars](const ull l, const ull r) {
                      auto &ls = pars_per_body_element.at(l);
                      auto &rs = pars_per_body_element.at(r);

                      auto l_elemen = intersection_size(ls, result_pars);
                      auto r_elemen = intersection_size(rs, result_pars);

                      // nesc. to maintain head parameters at the end of trace
                      if (l_elemen < r_elemen) {
                          return true;
                      }
                      if (r_elemen < l_elemen) {
                          return false;
                      }

                      // intuitively makes sense to be more likely to find a match in the squared loop early on
                      if (ls.size() < rs.size()) {
                          return true;
                      }
                      if (rs.size() < ls.size()) {
                          return false;
                      }

                      // for correctness
                      return l < r;
                  });

        std::vector<ull> order_ids(rule.body.size());
        for (ull i = 0; i < rule.body.size(); i++) {
            order_ids[custom_elements.at(i)] = i;
        }

        auto cmp = [order_ids](const ull l, const ull r) {
            return order_ids.at(l) < order_ids.at(r);
        };
        std::set<ull, decltype(cmp)> elements_left(cmp);
        for (ull i = 0; i < rule.body.size(); i++) {
            elements_left.insert(i);
        }

        // GYO algorithm for ordering
        std::set<ull> comp_set;
        std::vector<ull> pars_to_erase;
        while (elements_left.size() > 1) {
#ifndef NDEBUG
            auto j_size = join_order.size();
#endif
            for (auto i: elements_left) {
                for (auto j: elements_left) {
                    if (i == j) {
                        continue;
                    }

                    comp_set = pars_per_body_element.at(i);
                    for (auto p: comp_set) { // TODO: could probably use iterator manually and erase instantly
                        assert(par_count.at(p) >= 0);
                        if (par_count.at(p) == 1) {
                            pars_to_erase.push_back(p);
                        }
                    }

                    for (auto p: pars_to_erase) {
                        comp_set.erase(p);
                    }
                    if (comp_set.empty()) {
                        std::vector<ull> res_pars;
                        set_intersection(pars_per_body_element.at(i).begin(), pars_per_body_element.at(i).end(),
                                         result_pars.begin(), result_pars.end(), std::back_inserter(res_pars));
                        join_order.push_back(JoinElement{.pars_tracked=res_pars, .from=i, .to=JoinElement::NO_ELEMENT});
                        for (auto p: pars_per_body_element.at(i)) {
                            par_count.at(p)--;
                        }
                        comp_set.clear();
                        pars_to_erase.clear();
                        break;
                    }

                    auto &j_set = pars_per_body_element.at(j);
                    if (std::includes(j_set.begin(), j_set.end(), comp_set.begin(), comp_set.end())) {
                        std::vector<ull> res_pars;
                        set_intersection(comp_set.begin(), comp_set.end(), pars_per_body_element.at(j).begin(),
                                         pars_per_body_element.at(j).end(), std::back_inserter(res_pars));
                        join_order.push_back(JoinElement{.pars_tracked=res_pars, .from=i, .to=j});
                        for (auto p: pars_per_body_element.at(i)) {
                            par_count.at(p)--;
                        }
                        comp_set.clear();
                        pars_to_erase.clear();
                        break;
                    }

                    comp_set.clear();
                    pars_to_erase.clear();
                }
                if (!join_order.empty() && join_order.back().from == i) {
                    break;
                }
            }
            elements_left.erase(join_order.back().from); //TODO: could use iterator
#ifdef DEBUG_FLAG_JO_BUILDER
            std::cout << "current join order is:" << std::endl;
            print_order(task, rule, join_order);
            std::cout << std::endl;
            std::cout << "elements left are:" << std::endl;
            for (auto el_left : elements_left) {
                pretty_print(task, rule.body.at(el_left), std::cout);
                std::cout << ", ";
            }
            std::cout << std::endl;
#endif
            assert(false && "need option here in case not acyclic");
#ifndef NDEBUG
            assert(join_order.size() == j_size+1);
#endif
        }
    } else {
        auto pars = get_pars(rule.head);
        join_order.push_back(JoinElement{.pars_tracked=std::vector<ull>(pars.begin(), pars.end()), .from=0, .to=JoinElement::NO_ELEMENT});
    }
    assert(!join_order.empty());

    std::unordered_map<ull,ull> waiting;
    for (auto rit = join_order.rbegin(); rit < join_order.rend(); rit++) {
        auto &el = *rit;
        if (!waiting.contains(el.from)) {
            assert(el.to == JoinElement::NO_ELEMENT); // TODO: swap with if condition
            waiting.emplace(el.from, join_traces.size());
            join_traces.emplace_back();
        }
        join_traces.at(el.from).push_back(el);
    }

#ifndef NDEBUG
    // no join drops parameters that occurs again later
    for (auto &reversed_join_order : join_traces) {
        std::set<ull> vars_local; // dropped pars
        for (auto rit = reversed_join_order.rbegin(); rit < reversed_join_order.rend(); rit++) {
            auto &el = *rit;

            auto just_from = get_pars(rule.body.at(el.from));
            for (auto p : get_pars(rule.body.at(el.from))) {
                just_from.erase(p);
                assert(!vars_local.contains(p));
            }

            for (auto p : just_from) {
                vars_local.insert(p);
            }
        }
    }

    // join of last elements results in res pars
    std::set<ull> ending;
    std::set<ull> ending_inters;
    for (auto &reversed_join_order : join_traces) {
        for (auto p : get_pars(rule.body.at(reversed_join_order.begin()->from))) {
            ending.insert(p);
        }
        for (auto p : reversed_join_order.begin()->pars_tracked) {
            ending_inters.insert(p);
        }
    }
    auto res_pars = get_pars(rule.head);
    assert(ending_inters == res_pars);
    assert(std::includes(ending.begin(), ending.end(), res_pars.begin(), res_pars.end()));

    // all elements have unique from
    std::unordered_set<ull> froms;
    for (auto &jo : join_traces) {
        for (auto &el : jo) {
            froms.insert(el.from);
            assert(0 >= el.from);
            assert(el.from < rule.body.size());
        }
    }
    assert(froms.size() == rule.body.size());

    // traces seperate variables
    std::set<ull> vars_tracked;
    for (auto &reversed_join_order : join_traces) {
        std::set<ull> vars_local;
        for (auto rit = reversed_join_order.rbegin(); rit < reversed_join_order.rend(); rit++) {
            auto &el = *rit;
            for (auto p : get_pars(rule.body.at(el.from))) {
                vars_local.insert(p);
            }
        }
        assert(!intersection_size(vars_local, vars_tracked));
        for (auto p : vars_local) {
            vars_tracked.insert(p);
        }
    }
#endif
}

static ull extract_action_cost(const std::string &s) {
    assert(s.find("with__cost") != std::string::npos);
    ull end = s.size();
    while (s.at(--end) != '_'/*-*/);

    /*
     * ░░▄███▄███▄
     * ░░█████████
     * ░░▒▀█████▀░
     * ░░▒░░▀█▀
     * ░░▒░░█░
     * ░░▒░█
     * ░░░█
     * ░░█░░░░███████
     * ░██░░░██▓▓███▓██▒
     * ██░░░█▓▓▓▓▓▓▓█▓████
     * ██░░██▓▓▓(◐)▓█▓█▓█
     * ███▓▓▓█▓▓▓▓▓█▓█▓▓▓▓█
     * ▀██▓▓█░██▓▓▓▓██▓▓▓▓▓█
     * ░▀██▀░░█▓▓▓▓▓▓▓▓▓▓▓▓▓█
     * ░░░░▒░░░█▓▓▓▓▓█▓▓▓▓▓▓█
     * ░░░░▒░░░█▓▓▓▓█▓█▓▓▓▓▓█
     * ░▒░░▒░░░█▓▓▓█▓▓▓█▓▓▓▓█
     * ░▒░░▒░░░█▓▓▓█░░░█▓▓▓█
     * ░▒░░▒░░██▓██░░░██▓▓██
     * ████████████████████████
     *
     * Not sure what is going on here.
     * But you found the elephant. :)
     * Lovely!
     */

    return std::stoi(s.substr(end+1));
}

typedef MiniZincPrinter LPPrinter; // to potentially create template for different printouts later on

void create_tmp_pred(DatalogTask &task, ull rule_id, ull order_id, ull join_id, size_t size) {
    task.predicates.push_back(Predicate{std::string("tmp_join_pred_")
                                        + std::to_string(rule_id)
                                        + std::string("_")
                                        + std::to_string(order_id)
                                        + std::string("_")
                                        + std::to_string(join_id),
                                        size});
}

void add_max_mutex(DatalogTask &task) {
    //task.rules.clear();

    ull i = 0;
    for (auto &mutex : task.mutex_groups) {
        std::unordered_set<ull> fixed_pars;
        for (auto &el : mutex.elements) {
            for (auto &par : el.pars) {
                if (par._is_variable && !par._is_counted) {
                    fixed_pars.insert(par.index);
                }
            }
        }

        Predicate mutex_pred{to_max_mutex_pred(i), fixed_pars.size()};
        auto mutex_pred_id = task.predicates.size();
        task.predicates.push_back(mutex_pred);

        Predicate min_mutex_pred{to_min_mutex_pred(i), fixed_pars.size()};
        auto min_mutex_pred_id = task.predicates.size();
        task.predicates.push_back(min_mutex_pred);

        std::vector<ObjectOrVarRef> mutex_atom_args;
        for (auto par : fixed_pars) {
            mutex_atom_args.push_back(ObjectOrVarRef{._is_variable=true,.index=par});
        }
        Atom mutex_atom{mutex_pred_id, mutex_atom_args};
        Atom min_mutex_atom{min_mutex_pred_id, mutex_atom_args};

        std::unordered_map<std::string, ull> guaranteed_pred_names;
        std::unordered_map<PredicateRef, PredicateRef> counter_part;
        std::unordered_map<PredicateRef, PredicateRef> guaranteed_variant;
        create_guaranteed_maps(task, guaranteed_pred_names, counter_part, guaranteed_variant);

        for (auto &el : mutex.elements) {
            if (!guaranteed_variant.contains(el.head)) {
                continue;
            }
            auto guar_head = guaranteed_variant.at(el.head);
            auto counter_head = counter_part.at(guar_head);

            std::vector<ObjectOrVarRef> body_atom_args;
            for (auto &par : el.pars) {
                body_atom_args.push_back(ObjectOrVarRef{._is_variable=par._is_variable,.index=par.index});
            }
            Atom body_atom{guar_head, body_atom_args};
            Atom min_body_atom{counter_head, body_atom_args};

            Rule max_mutex_rule{mutex_atom,std::vector<Atom>{body_atom}};
            task.rules.push_back(max_mutex_rule);

            Rule min_mutex_rule{min_mutex_atom,std::vector<Atom>{min_body_atom}};
            task.rules.push_back(min_mutex_rule);
        }
        i++;
    }
}

void binarize_rules(DatalogTask &task) {
    std::vector<Rule> new_rules;

    std::vector<std::vector<JoinElement>> join_traces;
    ull rule_id = 0;
    for (auto &rule : task.rules) {
        if (rule.body.size() == 0)
            continue;

        compute_join_order(task, join_traces, rule);
        assert(join_traces.size() > 0);

        ull order_id = 0;
        std::vector<Atom> current_atom;
        std::vector<Atom> last_atoms;
        for (auto &atom : rule.body) {
            current_atom.push_back(atom);
        }
#ifdef DEBUG_FLAG_PRINT_JOIN_TRACES
        std::cout << "Order for: ";
        pretty_print(task, rule, std::cout);
        std::cout << std::endl;
        for (auto &order : join_traces) {
            std::cout << "- ";
            print_order(task, rule, order);
            std::cout << std::endl;
        }
        std::cout << "----" << std::endl;
#endif
        for (auto &order : join_traces) {
#ifndef NDEBUG
            // in each trace only the last element maps to NO_ELEMENT
            for (ull i = 0; i < order.size()-1; i++) {
                assert(order.at(i).to != JoinElement::NO_ELEMENT);
            }
            assert(order.at(order.size()-1).to == JoinElement::NO_ELEMENT);
#endif
            ull join_id = 0;
            for (auto &join : order) {
                ull tmp_pred_id = task.predicates.size();

                if (join.to != JoinElement::NO_ELEMENT) {
                    create_tmp_pred(task, rule_id, order_id, join_id, join.pars_tracked.size());
                    std::vector<ObjectOrVarRef> join_pars;
                    for (auto par : join.pars_tracked) {
                        join_pars.push_back(ObjectOrVarRef{true, par});
                    }
                    Atom tmp_atom{tmp_pred_id, join_pars};
                    task.rules.push_back(Rule{tmp_atom, std::vector<Atom>{current_atom.at(join.from), current_atom.at(join.to)}});
                    current_atom.at(join.to) = tmp_atom;
                } else {
                    create_tmp_pred(task, rule_id, order_id, join_id, 0);
                    Atom tmp_atom{tmp_pred_id, {}};
                    task.rules.push_back(Rule{tmp_atom, std::vector<Atom>{current_atom.at(join.from)}});
                    last_atoms.push_back(tmp_atom);
                }
                join_id++;
            }
            order_id++;
        }

        rule.body = last_atoms;

        join_traces.clear();
        rule_id++;
    }

    for (auto &rule : new_rules) {
        task.rules.push_back(rule);
    }
}

static bool head_vars_less(const Rule &rule) {
    auto head_vars = get_pars(rule.head);

    for (auto &atom : rule.body) {
        auto bod_vars = get_pars(atom);
        if (!std::includes(head_vars.begin(), head_vars.end(),bod_vars.begin(),bod_vars.end())) {
            return true;
        }
    }
    return false;
}

static void create_gfunc(std::unordered_map<ull, ull> &grounding_function,
                         const Atom &supersetting_atom,
                         const std::vector<ull> &grounding) {
    assert(grounding.size() == supersetting_atom.args.size());
    for (ull i = 0; i < grounding.size(); i++) {
        auto &arg = supersetting_atom.args.at(i);
        if (arg._is_variable) {
            auto var = arg.index;
            auto val = grounding.at(i);
            assert(!grounding_function.contains(var) || grounding_function.at(var) == val);
            grounding_function.emplace(var, val);
        }
    }
}

static Atom ground_atom(const Atom &atom, const std::unordered_map<ull, ull> &grounding_function) {
    std::vector<ObjectOrVarRef> ground_args;
    for (auto &arg : atom.args) {
        if (arg._is_variable) {
            assert(grounding_function.contains(arg.index));
            ground_args.push_back(ObjectOrVarRef{false, grounding_function.at(arg.index)});
        } else {
            ground_args.push_back(arg);
        }
    }

    return Atom{atom.head, ground_args};
}

static Rule ground_rule(const Rule &rule, const std::unordered_map<ull, ull> &grounding_function) {
    Atom ground_head(ground_atom(rule.head, grounding_function));
    std::vector<Atom> ground_body;
    for (auto &atom : rule.body) {
        ground_body.push_back(ground_atom(atom, grounding_function));
    }
    return Rule{ground_head, ground_body};
}

// returns true if creation was succesful
bool create_repl_map(const std::vector<ObjectOrVarRef> &lifted_atom,
                     const std::vector<ObjectOrVarRef> &grounded_atom,
                     std::unordered_map<ull, ull> &repl_map) {
    assert(lifted_atom.size() == grounded_atom.size());

    for (ull i = 0; i < lifted_atom.size(); i++) {
        auto &lifted_arg = lifted_atom.at(i);
        auto &grounded_arg = grounded_atom.at(i);
        assert(!grounded_arg._is_variable);

        if (lifted_arg._is_variable) {
            if (!repl_map.contains(lifted_arg.index)) {
                repl_map.insert(std::make_pair(lifted_arg.index, grounded_arg.index));
            } else {
                if (repl_map.at(lifted_arg.index) != grounded_arg.index) {
                    return false;
                }
            }
        } else {
            if (lifted_arg.index != grounded_arg.index) {
                return false;
            }
        }
    }

    return true;
}

void replace_atom(const Atom &atom,
                  const std::unordered_map<ull, ull> &repl_map,
                  std::vector<ObjectOrVarRef> &replaced_args) {
    for (auto &arg : atom.args) {
        if (arg._is_variable) {
            assert(repl_map.contains(arg.index));
            replaced_args.push_back(ObjectOrVarRef{._is_variable=false, .index=repl_map.at(arg.index)});
        } else {
            replaced_args.push_back(arg);
        }
    }
}

std::string make_add(const std::string &s) {
    assert(is_del_predicate(s));
    return ADD_PRED_START + s.substr(DEL_PRED_START.size());
}

std::string cut_guaranteed(const std::string &s) {
    assert(ends_with(s, GUARANTEED_PRED_END));
    auto new_s = s.substr(0, s.size()-GUARANTEED_PRED_END.size());
    assert(!ends_with(new_s, "_"));
    return new_s;
}

void extend_goal_rule(DatalogTask &task) {
#ifndef NDEBUG
    ull saw_goal = 0;
    for (auto &p : task.predicates) {
        if (p.name == GOAL_NAME) {
            saw_goal++;
        }
    }
    assert(saw_goal == 1);
    for (auto &r : task.rules) {
        if (task.predicates.at(r.head.head).name == GOAL_NAME) {
            saw_goal++;
        }
    }
    assert(saw_goal == 2);
#endif

    ull rule_ind = 0;
    for (auto &r : task.rules) {
        if (task.predicates.at(r.head.head).name == GOAL_NAME) {
            break;
        }
        rule_ind++;
    }
    auto goal_rule_body = task.rules.at(rule_ind).body;

    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args; // first access: pred, then maps args to init position
    create_pred_to_args_map(task, pred_to_args);

    std::unordered_map<std::string, ull> guaranteed_pred_names;
    std::unordered_map<PredicateRef, PredicateRef> counter_part;
    std::unordered_map<PredicateRef, PredicateRef> guaranteed_variant;
    create_guaranteed_maps(task, guaranteed_pred_names, counter_part, guaranteed_variant);

    std::vector<Atom> adjusted_goal_body;
    std::unordered_set<ull> goal_ids;
    for (auto &atom : goal_rule_body) {
        if (guaranteed_variant.contains(atom.head)) {
#ifndef NDEBUG
            ull optimization_criterion_size_old = goal_ids.size();
#endif
            auto guaranteed_try = guaranteed_variant.at(atom.head);
            if (pred_to_args.at(guaranteed_try).contains(atom.args)) {
                goal_ids.insert(pred_to_args.at(atom.head).at(atom.args));
            }
#ifndef NDEBUG
            assert(optimization_criterion_size_old+1 == goal_ids.size());
#endif
            adjusted_goal_body.push_back(Atom{guaranteed_try, atom.args});
        } else {
            assert(false && "TODO");
        }
    }
    goal_rule_body = adjusted_goal_body;

    std::unordered_set<PredicateRef> max_mutex_preds;
    {
        PredicateRef i = 0;
        for (auto &pred: task.predicates) {
            if (is_max_mutex_pred(pred.name)) {
                max_mutex_preds.insert(i);
            }
            i++;
        }
    }

    std::unordered_set<ull> mutex_atoms_ids;
    {
        ull i = 0;
        for (auto &atom : task.init) {
            if (max_mutex_preds.contains(atom.head)) {
                mutex_atoms_ids.insert(i);
            }
            i++;
        }
    }

    std::unordered_map<ull, std::vector<ull>> mutex_to_desc;
    for (auto &rule : task.rules) {
        auto &atom = rule.head;

        if (!max_mutex_preds.contains(atom.head)) {
            continue;
        }

        assert(rule.body.size() == 1);
        for (auto &body_atom : rule.body) {
            for (auto &[args, init_index] : pred_to_args.at(body_atom.head)) {
                std::unordered_map<ull, ull> repl_map;
                if (!create_repl_map(body_atom.args, args, repl_map)) {
                    continue;
                }

                std::vector<ObjectOrVarRef> replaced_body_args;
                replace_atom(body_atom, repl_map, replaced_body_args);
                auto body = pred_to_args.at(body_atom.head).at(replaced_body_args);
                assert(is_guranteed_predicate(task.predicates.at(body_atom.head).name));

                std::vector<ObjectOrVarRef> replaced_head_args;
                replace_atom(atom, repl_map, replaced_head_args);
                auto head = pred_to_args.at(atom.head).at(replaced_head_args);
                if (!mutex_to_desc.contains(head)) {
                    mutex_to_desc.emplace(head, std::vector<ull>{});
                }
                mutex_to_desc.at(head).push_back(body);
            }
        }
    }

    std::unordered_set<ull> atom_ids_covered_by_mutex;
    std::vector<ull> mutexes_not_covered_by_goal;

    //TODO: care about duality
    for (auto mutex_atom_id : mutex_atoms_ids) {
        bool found_goal = false;
        for (auto atom_id : mutex_to_desc.at(mutex_atom_id)) {
#ifdef DEBUG_FLAG_PRINT_MUTEX_COVER_GOAL_EXT
            std::cout << "Mutex ";
            pretty_print(task, task.init.at(mutex_atom_id), std::cout);
            std::cout << " covers ";
            pretty_print(task, task.init.at(atom_id), std::cout);
            std::cout << std::endl;
#endif
            atom_ids_covered_by_mutex.insert(atom_id);
            if (goal_ids.contains(atom_id)) {
                found_goal = true;
            }
        }

        if (!found_goal) {
            mutexes_not_covered_by_goal.push_back(mutex_atom_id);
        }
    }

    for (auto &atom : goal_rule_body) {
#ifdef DEBUG_FLAG_PRINT_MUTEX_COVER_GOAL_EXT
        std::cout << "Atom ";
        pretty_print(task, atom, std::cout);
        std::cout << " covered as goal." << std::endl;
#endif
        atom_ids_covered_by_mutex.insert(pred_to_args.at(atom.head).at(atom.args));
    }

    for (auto mutex_id : mutexes_not_covered_by_goal) {
        goal_rule_body.push_back(task.init.at(mutex_id));
    }

    std::unordered_set<ull> is_guranteed;
    {
        ull i = 0;
        for (auto &p: task.predicates) {
            if (is_guranteed_predicate(p.name)) {
                is_guranteed.insert(i);
            }
            i++;
        }
    }

    Atom false_atom{task.predicates.size(), std::vector<ObjectOrVarRef>{}};
    task.predicates.push_back(Predicate{FALSE_PRED, 0});

    ull annotation_score = 0;
    for (auto &p : task.predicates) {
        if (is_rule_hack(p.name)) {
            annotation_score++;
        }
    }

    //TODO: rename -- actually add
    std::unordered_map<PredicateRef, PredicateRef> reverse_del_variant;
    for (auto &[k, v] : task.add_to_normal_pred) {
        if (is_guranteed.contains(k)) {
            assert(!reverse_del_variant.contains(v));
            reverse_del_variant.emplace(v, k);
        }
    }

    std::unordered_map<PredicateRef, PredicateRef> reverse_guaranteed_variant;
    for (auto &[k, v] : guaranteed_variant) {
        assert(!reverse_guaranteed_variant.contains(v));
        if (reverse_del_variant.contains(v)) {
            reverse_guaranteed_variant.emplace(reverse_del_variant.at(v), k);
        }
    }

    std::vector<Atom> additional_init;
    ull i = 0;
    for (auto &atom : task.init) {
        if (is_guranteed.contains(atom.head) && !atom_ids_covered_by_mutex.contains(i)) {
            auto h = atom.head;
            auto counter_pred = counter_part.at(h);
            assert(pred_to_args.at(counter_pred).contains(atom.args));
            auto other_guaranteed = pred_to_args.at(counter_pred).at(atom.args);
            assert(task.init.at(other_guaranteed).args == atom.args);

#ifdef DEBUG_FLAG_PRINT_MUTEX_COVER_GOAL_EXT
            std::cout << "Considering extension for ";
            pretty_print(task, atom, std::cout);
            std::cout << std::endl;
#endif

            if (atom_ids_covered_by_mutex.contains(other_guaranteed)) {
#ifdef DEBUG_FLAG_PRINT_MUTEX_COVER_GOAL_EXT
                std::cout << "Extension not needed as it was performed for ";
                Atom other{counter_pred, atom.args};
                pretty_print(task, other, std::cout);
                std::cout << "." << std::endl;
#endif
                i++;
                continue;
            }

            bool is_add = task.add_to_normal_pred.contains(h);
#ifndef NDEBUG
            if (is_add) {
                assert(is_add_predicate(task.predicates.at(h).name));
            } else {
                assert(is_del_predicate(task.predicates.at(h).name));
            }
#endif

            // add + weight(atom)
            auto del_guaranteed_pred = is_add ? counter_pred : h;
            Atom del_guaranteed_atom{del_guaranteed_pred, atom.args};
#ifndef NDEBUG
            for (auto &arg : del_guaranteed_atom.args) {
                assert(!arg._is_variable);
            }
#endif
            goal_rule_body.push_back(del_guaranteed_atom);

            // add annotation that equates to - weight(atom) + mutex_maximization (which results in just adding the mutex maximization)
            // we do it in this complicated way to use the annotation technique to substite in the same way
            // TODO: rename actually creates add
            if (!reverse_guaranteed_variant.contains(del_guaranteed_pred)) {
                // create pred
                auto del_non_guaranteed_pred = task.predicates.size();
                auto del_non_guaranteed_pred_name = make_add(cut_guaranteed(task.predicates.at(del_guaranteed_pred).name));
                task.predicates.push_back(Predicate{del_non_guaranteed_pred_name, atom.args.size()});

                // copy atoms
                for (auto &[args, _] : pred_to_args.at(del_guaranteed_pred)) {
                    additional_init.push_back(Atom{del_non_guaranteed_pred, args});
                }

                // mark creation
                reverse_guaranteed_variant.emplace(del_guaranteed_pred, del_non_guaranteed_pred);
            }
            auto del_non_guaranteed_pred = reverse_guaranteed_variant.at(del_guaranteed_pred);
            Atom del_non_guaranteed_atom{del_non_guaranteed_pred, atom.args};

            auto annotation_id = task.predicates.size();
            task.predicates.push_back(Predicate{.name=RULE_HACK_STUB+std::to_string(annotation_score++)});
            Atom annotation_atom{annotation_id, {}};
            task.rules.push_back(Rule{annotation_atom, {del_non_guaranteed_atom, false_atom}});
            goal_rule_body.push_back(annotation_atom);
            additional_init.push_back(annotation_atom);

            assert(!atom_ids_covered_by_mutex.contains(i));
            atom_ids_covered_by_mutex.insert(i);
        }
        i++;
    }

    for (auto &atom : additional_init) {
        task.init.push_back(atom);
    }

    task.rules.at(rule_ind).body = goal_rule_body;
}

auto get_guaranteed(std::string &s) {
    return s + GUARANTEED_PRED_END;
}

void print_grounded_mutexes(DatalogTask &task) {
    std::vector<Rule> new_rules;

    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args;
    create_pred_to_args_map(task, pred_to_args);

    std::unordered_set<ull> max_mutex_preds;
    for (ull i = 0; i < task.predicates.size(); i++) {
        if (is_max_mutex_pred(task.predicates.at(i).name)) {
            max_mutex_preds.insert(i);
        }
    }

    for (auto &rule : task.rules) {
        if (max_mutex_preds.contains(rule.head.head)) {
            assert(rule.body.size() == 1);

            auto &body_atom = *rule.body.begin();
            for (auto &[args, _] : pred_to_args.at(body_atom.head)) {
                Atom new_body{body_atom.head, args};
#ifndef NDEBUG
                for (auto &arg : args) {
                    assert(!arg._is_variable);
                }
#endif
                assert(args.size() == body_atom.args.size());

                std::unordered_map<ull, ull> var_to_obj;
                for (ull i = 0; i < body_atom.args.size(); i++) {
                    assert(!args.at(i)._is_variable);
                    if (body_atom.args.at(i)._is_variable) {
                        assert(!var_to_obj.contains(body_atom.args.at(i).index)
                               || var_to_obj.at(body_atom.args.at(i).index) == args.at(i).index);
                        auto ind = body_atom.args.at(i).index;
                        var_to_obj.emplace(ind, args.at(i).index);
                    }
                }

                std::vector<ObjectOrVarRef> projected_args;
                for (auto &arg : rule.head.args) {
                    assert(arg._is_variable);
                    assert(var_to_obj.contains(arg.index));
                    projected_args.push_back(ObjectOrVarRef{._is_variable=false, .index=var_to_obj.at(arg.index)});
                }
                Atom new_head{rule.head.head, projected_args};

                new_rules.push_back(Rule{.head=new_head, .body={new_body}});
            }
        }
    }

    task.rules = new_rules;
    task.init.clear();
}

// create an add_guaranteed for each, create a del_guaranteed for each del
void equalize_add_guaranteed_atoms(DatalogTask &task) {
    std::unordered_map<std::string, ull> guar_to_index;
    for (ull p = 0; p < task.predicates.size(); p++) {
        auto &pred = task.predicates.at(p);
        if (is_guranteed_predicate(pred.name)) {
            guar_to_index.emplace(pred.name, p);
        }
    }

    for (auto &col : {task.del_to_normal_pred, task.add_to_normal_pred})
    for (auto &[add, _] : col) {
        auto &pred = task.predicates.at(add);
        if(is_guranteed_predicate(pred.name)) {
            continue;
        }

        auto guar = get_guaranteed(pred.name);
        if (!guar_to_index.contains(guar)) {
            guar_to_index.emplace(guar, task.predicates.size());
            task.predicates.push_back(Predicate{.name=guar, .arity=pred.arity});
        }

        auto guar_ind = guar_to_index.at(guar);
        auto &other_pred = task.predicates.at(guar_ind);
        assert(pred.arity == other_pred.arity);
        std::vector<ObjectOrVarRef> standard_args;
        for (ull i = 0; i < pred.arity; i++) {
            standard_args.push_back(ObjectOrVarRef{._is_variable=true, .index=i});
        }

        Atom other_pred_atom{guar_ind, standard_args};
        Atom here_pred_atom{add, standard_args};

        Rule translating_rule{other_pred_atom, std::vector<Atom>{here_pred_atom}};
        task.rules.push_back(translating_rule);
    }
}

// create a del_guaranteed for each add_guaranteed, vice versa
void equalize_guaranteed_atoms(DatalogTask &task) {
    std::unordered_map<std::string, ull> name_to_pred;
    for (ull i = 0; i < task.predicates.size(); i++) {
        name_to_pred.emplace(task.predicates.at(i).name, i);
    }

    ull pred_index = 0;
    for (auto &pred : task.predicates) {
        if (is_guranteed_predicate(pred.name)) {
            assert(is_add_predicate(pred.name) || is_del_predicate(pred.name));

            std::string other_name = get_counter_part(pred.name);
            if (!name_to_pred.contains(other_name)) {
                name_to_pred.emplace(other_name, task.predicates.size());
                task.predicates.push_back(Predicate{.name=other_name, .arity=pred.arity});
            }
            auto other = name_to_pred.at(other_name);
            auto &other_pred = task.predicates.at(other);

            assert(pred.arity == other_pred.arity);
            std::vector<ObjectOrVarRef> standard_args;
            for (ull i = 0; i < pred.arity; i++) {
                standard_args.push_back(ObjectOrVarRef{._is_variable=true, .index=i});
            }

            Atom other_pred_atom{other, standard_args};
            Atom here_pred_atom{pred_index, standard_args};

            Rule translating_rule{other_pred_atom, std::vector<Atom>{here_pred_atom}};
            task.rules.push_back(translating_rule);
        }
        pred_index++;
    }
}

void add_none_rules(DatalogTask &task) {
    std::unordered_map<std::string, ull> pred_name_to_index;
    ull i = 0;
    for (auto &p : task.predicates) {
        pred_name_to_index.emplace(p.name, i++);
    }

    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args;
    create_pred_to_args_map(task, pred_to_args);

    for (ull i = 0; i < task.mutex_groups.size(); i++) {
        if (task.mutex_groups.at(i).is_unique)
            continue;

        // get according / max min rules
        auto max_str = MAX_MUTEX_START + std::to_string(i);
        auto min_str = MIN_MUTEX_START + std::to_string(i);

        assert(pred_name_to_index.contains(max_str));
        assert(pred_name_to_index.contains(min_str));

        auto min_pred = pred_name_to_index.at(min_str);
        auto max_pred = pred_name_to_index.at(max_str);

        // create none predicates
        auto add_none = task.predicates.size();
        task.predicates.push_back(Predicate{ADD_PRED_START+NONE_STUB+std::to_string(i)+GUARANTEED_PRED_END, 0});

        auto del_none = task.predicates.size();
        task.predicates.push_back(Predicate{DEL_PRED_START+NONE_STUB+std::to_string(i)+GUARANTEED_PRED_END, 0});

        // create max/min mutex rules
        assert(task.predicates.at(max_pred).arity == task.predicates.at(min_pred).arity);

        std::vector<ObjectOrVarRef> cannonical_args;
        for (ull j = 0; j < task.predicates.at(max_pred).arity; j++) {
            cannonical_args.push_back(ObjectOrVarRef{._is_variable=true, .index=j});
        }

        Atom max_head{max_pred, cannonical_args};
        Atom del_atom{del_none, cannonical_args};
        task.rules.push_back(Rule{max_head, std::vector<Atom>{del_atom}});

        Atom min_head{min_pred, cannonical_args};
        Atom add_atom{add_none, cannonical_args};
        task.rules.push_back(Rule{min_head, std::vector<Atom>{add_atom}});

        // copy atoms
        for (auto &[args, _] : pred_to_args.at(max_pred)) {
            task.init.push_back(Atom{del_none, args});
            task.init.push_back(Atom{add_none, args});
        }
    }

    assert(false && "TODO: need to adjust action constraint to make up if a none would be added");
}

void add_hacky_zero_if_not_unique(DatalogTask &task) {
    std::unordered_map<std::string, ull> pred_name_to_index;
    ull i = 0;
    for (auto &p : task.predicates) {
        pred_name_to_index.emplace(p.name, i++);
    }

    std::vector<std::unordered_map<std::vector<ObjectOrVarRef>, ull>> pred_to_args;
    create_pred_to_args_map(task, pred_to_args);

    auto hacky_zero_pred = task.predicates.size();
    task.predicates.push_back(Predicate{.name="hack_zero_pred", .arity=0});
    Atom hacky_zero_atom{hacky_zero_pred, {}};

    for (ull i = 0; i < task.mutex_groups.size(); i++) {
        if (task.mutex_groups.at(i).is_unique)
            continue;

        // get according / max min rules
        auto max_str = MAX_MUTEX_START + std::to_string(i);
        auto min_str = MIN_MUTEX_START + std::to_string(i);

        assert(pred_name_to_index.contains(max_str));
        assert(pred_name_to_index.contains(min_str));

        auto min_pred = pred_name_to_index.at(min_str);
        auto max_pred = pred_name_to_index.at(max_str);

        assert(task.predicates.at(max_pred).arity == task.predicates.at(min_pred).arity);

        std::vector<ObjectOrVarRef> cannonical_args;
        for (ull j = 0; j < task.predicates.at(max_pred).arity; j++) {
            cannonical_args.push_back(ObjectOrVarRef{._is_variable=true, .index=j});
        }

        // add rule min <= 0
        Atom min_atom{min_pred, cannonical_args};
        task.rules.push_back(Rule{min_atom, {hacky_zero_atom}});

        // add rule max >= 0
        Atom max_atom{max_pred, cannonical_args};
        task.rules.push_back(Rule{max_atom, {hacky_zero_atom}});
    }

    task.init.push_back(hacky_zero_atom);
}

void minzinc_constraints(DatalogTask &task) {
    // hack to pass optimization criterion via one rule
    ull opt_pred = (ull) -1;
    for (ull p = 0; p < task.predicates.size(); p++) {
        auto &pred = task.predicates.at(p);
        if (pred.name == OPTIMIZATION_CRITERION_FACT) {
            opt_pred = p;
        }
    }
    assert(opt_pred != (ull) -1);

    std::vector<Atom> raw_optimization_criterion;
    std::vector<Rule> rules;
    for (ull r = 0; r < task.rules.size(); r++) {
        auto &rule = task.rules.at(r);
        if (rule.head.head != opt_pred) {
            rules.push_back(rule);
        } else {
            assert(raw_optimization_criterion.empty());
            raw_optimization_criterion = task.rules.at(r).body;
        }
    }
    task.rules = rules;

    // collect properties for predicates
    std::unordered_set<PredicateRef> action_preds;
    get_action_preds(action_preds, task);

    std::unordered_set<PredicateRef> no_null_preds;
    for (ull p = 0; p < task.predicates.size(); p++) {
        auto &s = task.predicates.at(p).name;
        if (indicates_tmp_pred(s) || is_goal_pred(s) || is_guranteed_predicate(s) || is_max_mutex_pred(s) ||
                is_min_mutex_pred(s)) {
            no_null_preds.insert(p);
        }
    }

    std::vector<std::unordered_set<std::vector<ull>>> pred_to_args;
    create_pred_to_args(task, pred_to_args);

    std::unordered_map<std::string, ull> guaranteed_pred_names;
    std::unordered_map<PredicateRef, PredicateRef> counter_part;
    std::unordered_map<PredicateRef, PredicateRef> guaranteed_variant;
    create_guaranteed_maps(task, guaranteed_pred_names, counter_part, guaranteed_variant);

    // create actual optimization_criterion by linking it to the guaranteed atoms
    std::vector<Atom> optimization_criterion;
    for (auto &atom : raw_optimization_criterion) {
        if (guaranteed_variant.contains(atom.head)) {
            auto guar_head = guaranteed_variant.at(atom.head);
            std::vector<ull> lookup;
            for (auto &arg : atom.args) {
                assert(!arg._is_variable);
                lookup.push_back(arg.index);
            }
            if (pred_to_args.at(guar_head).contains(lookup)) {
                optimization_criterion.push_back(Atom{.head=guar_head, .args=atom.args});
            }
        }
    }

    // print variable declarations
    // Todo should fix negation to always be the add first -- could do this by sorting predicates in the beginning
    for (ull p = 0; p < task.predicates.size(); p++) {
        if (counter_part.contains(p) && counter_part.at(p) < p) {
            for (auto &args : pred_to_args.at(p)) {
                if (pred_to_args.at(counter_part.at(p)).contains(args)) {
                    LPPrinter::print_negated_var_init(task, p, counter_part.at(p), args);
                } else {
                    LPPrinter::print_unconstrained_init(task, p, args);
                }
            }
        } else if (action_preds.contains(p)) {
            for (auto &args : pred_to_args.at(p)) {
                assert(args.empty());
                LPPrinter::print_unconstrained_init(task, p, args);
                LPPrinter::print_action_init(task, p, extract_action_cost(task.predicates.at(p).name));
            }
        } else {
            for (auto &args : pred_to_args.at(p)) {
                LPPrinter::print_unconstrained_init(task, p, args);
                // restrict non-guaranteed add / del rules
                if (!no_null_preds.contains(p)) {
                    LPPrinter::print_eq_constraint(task, p, args, 0);
                }
            }
        }
    }

    // print action constraints
    for (auto &rule : task.rules) {
        bool head_supersetting = !(rule.body.size() == 1 && head_vars_less(rule));
        assert(rule.body.size() == 1 || !head_vars_less(rule));
        auto &supersetting_atom = head_supersetting ? rule.head : *rule.body.begin();

        std::unordered_map<ull, ull> grounding_function;
        for (auto &grounding : pred_to_args.at(supersetting_atom.head)) {
            create_gfunc(grounding_function, supersetting_atom, grounding);
            LPPrinter::print_less_constraint(task, ground_rule(rule, grounding_function));
            grounding_function.clear();
        }
    }

    // print goal constraint
#ifndef NDEBUG
    bool saw_goal = false;
    for (auto &p : task.predicates) {
        if (p.name == GOAL_NAME) {
            saw_goal = true;
            break;
        }
    }
    assert(saw_goal);
#endif
    LPPrinter::print_action_init(task, GOAL_NAME, 0); // hack to print goal \leq 0


    // print optimization goal
    LPPrinter::maximize(task, optimization_criterion);

    // print output format
    std::set<PredicateRef> guaranteed_preds;
    for (auto &[_, p] : guaranteed_pred_names) {
        guaranteed_preds.insert(p);
    }

    std::vector<Atom> interesting_values;
    for (auto &atom : task.init) {
        if (guaranteed_preds.contains(atom.head)) {
            interesting_values.push_back(atom);
        }
    }

    //TODO: could remove add preds from prinout
    LPPrinter::output(task, interesting_values);

    // hack to only print minzinc constraints
    exit(0);
}
