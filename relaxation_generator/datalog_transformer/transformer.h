#ifndef DATALOG_TRANSFORMER_TRANSFORMER_H
#define DATALOG_TRANSFORMER_TRANSFORMER_H

#include "parser.h"

typedef void (*DataLogTransformer)(DatalogTask &);

inline void no_transformation(DatalogTask &) {}

void create_reducer(DatalogTask &);

void remove_unique_objects_from_mutex_group(DatalogTask &task);

void mutex_filter(DatalogTask &task);

void linearize_action_task(DatalogTask &task);

void minzinc_constraints(DatalogTask &task);

void integrate_add_del_rules(DatalogTask &task);

void binarize_rules(DatalogTask &task);

void superset_pars(DatalogTask &task);

void extend_goal_rule(DatalogTask &task);

void add_max_mutex(DatalogTask &task);

void equalize_guaranteed_atoms(DatalogTask &task);

void equalize_add_guaranteed_atoms(DatalogTask &task);

void sanity_check_before_print(DatalogTask &task);

void reintegrate_mutex_rules(DatalogTask &task);

void add_none_rules(DatalogTask &task);

void print_grounded_mutexes(DatalogTask &task);

void add_hacky_zero_if_not_unique(DatalogTask &task);

void add_repair_actions(DatalogTask &task);

void zero_ary_relaxation(DatalogTask &task);

void unary_relaxation(DatalogTask &task);

void print_domain(DatalogTask &task);

void print_problem(DatalogTask &task);

inline void standard_transformations(DatalogTask &task) {
    remove_unique_objects_from_mutex_group(task);
}

#endif //DATALOG_TRANSFORMER_TRANSFORMER_H
