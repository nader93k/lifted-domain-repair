#include "initial_adds.h"
#include "search.h"
#include "utils.h"

#include "../open_lists/greedy_open_list.h"
#include "../states/extensional_states.h"
#include "../states/sparse_states.h"
#include "../successor_generators/successor_generator.h"
#include "../utils/timer.h"

template <class PackedStateT>
utils::ExitCode InitialAdds<PackedStateT>::search(const Task &task, SuccessorGenerator &generator, Heuristic &heuristic) {
    // get initially achieved atoms
    DBState state = task.initial_state;
    std::vector<bool> initial_nullaries = task.initial_state.get_nullary_atoms();
    std::vector<Relation> initial_relations = task.initial_state.get_relations();

    for (size_t i = 0; i < task.static_info.get_nullary_atoms().size(); i++) {
        if (task.static_info.get_nullary_atoms()[i]) {
            initial_nullaries[i] = true;
        }
    }

    for (auto &r : task.static_info.get_relations()) {
        for (auto &inst : r.tuples) {
            initial_relations[r.predicate_symbol].tuples.insert(inst);
        }
    }

    std::vector<bool> nullaries_achieved(task.initial_state.get_nullary_atoms().size(), false);
    std::vector<Relation> relations;
    for (size_t i = 0; i < task.predicates.size(); i++) {
        Relation r;
        r.predicate_symbol = i;
        relations.push_back(r);
    }

    // get achievable atoms
    for (const auto& action:task.get_action_schemas()) {
        auto applicable = generator.get_applicable_actions(action, state);

        for (const LiftedOperatorId& op_id:applicable) {
            DBState s = generator.generate_successor(op_id, action, state);
            for (size_t i = 0; i < s.get_nullary_atoms().size(); i++) {
                if (s.get_nullary_atoms()[i] && !initial_nullaries[i]) {
                    nullaries_achieved[i] = true;
                }
            }
            for (auto &r : s.get_relations()) {
                for (auto &inst : r.tuples) {
                    relations[r.predicate_symbol].tuples.insert(inst);
                }
            }
        }
    }

    for (auto &r : initial_relations) {
        for (auto &inst : r.tuples) {
            relations[r.predicate_symbol].tuples.erase(inst);
        }
    }

    // print atoms
    std::cout << "Atoms reachable:" << std::endl;

    for (size_t i = 0; i < nullaries_achieved.size(); i++) {
        if (nullaries_achieved[i]) {
            std::cout << task.predicates[i].get_name() << "()" << std::endl;
        }
    }

    for (size_t i = 0; i < relations.size(); i++) {
        auto &r = relations[i];

        for (auto &inst : r.tuples) {
            std::cout << task.predicates[i].get_name() << "(";
            size_t i = 0;
            for (auto obj : inst) {
                std::cout << task.objects[obj].get_name();
                if (i < inst.size()-1) {
                    std::cout << ", ";
                }
                i++;
            }
            std::cout << ")" << std::endl;
        }
    }

    std::cout << "Done." << std::endl;
    exit(0);  //TODO: just return 0?
}