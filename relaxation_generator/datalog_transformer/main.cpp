#include <iostream>
#include "parser.h"
#include "transformer.h"
#include "pretty_print.h"

std::unordered_map<std::string, DataLogTransformer> valid_args {
        {"none", no_transformation},
        {"reducer", create_reducer},
        {"mutex-filter", mutex_filter},
        {"minizinc-constraints", minzinc_constraints},
        {"linearize-action-task", linearize_action_task},
        {"integrate-add-del-rules", integrate_add_del_rules},
        {"superset-pars", superset_pars},
        {"binarize-rules", binarize_rules},
        {"add-max-mutex", add_max_mutex},
        {"equalize-guaranteed-atoms", equalize_guaranteed_atoms},
        {"extend-goal-rule", extend_goal_rule},
        {"equalize-add-guaranteed-atoms", equalize_add_guaranteed_atoms},
        {"reintegrate-mutex-rules", reintegrate_mutex_rules},
        {"add-none-rules", add_none_rules},
        {"print-grounded-mutexes", print_grounded_mutexes},
        {"add-hacky-zero-if-not-unique", add_hacky_zero_if_not_unique},
        {"add-repair-actions", add_repair_actions},
        {"zero-ary-relaxation", zero_ary_relaxation},
        {"unary-relaxation", unary_relaxation},
        {"print-domain", print_domain},
        {"print-problem", print_problem}
};

int main(int argc, char* argv[]) {
    // check for valid cmd line argument
    if (argc != 2 || !valid_args.contains(argv[1])) {
        std::cerr << "Please provide exactly one of the following args defining the transformation: " << std::endl;
        for (auto &[arg, _] : valid_args) {
            std::cerr << " - " << arg << std::endl;
        }
        std::cerr << std::endl;
        std::cerr << "The Datalog file is read from stdin." << std::endl;
        exit(1);
    }

    Parser parser(std::cin); // could theoretically allow to read from file instead
    parser.parse();
    auto &task = parser.result;

    // normalize task
    standard_transformations(task);

    // transform task
    valid_args.at(argv[1])(task);

    // print task
    sanity_check_before_print(task);
    pretty_print(task, std::cout);

    return 0;
}