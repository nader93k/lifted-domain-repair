#ifndef DATALOG_TRANSFORMER_MINIZINC_PRINTER_H
#define DATALOG_TRANSFORMER_MINIZINC_PRINTER_H


#include <iostream>

#include "parser.h"

class MiniZincPrinter {
    static constexpr auto &outs = std::cout;
    static void print_atom_likes(const DatalogTask &task, const Atom &atom);
    static void print_atom_likes(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args);
    static void print_atom_likes(const DatalogTask &task, const std::string &pred_name, const std::vector<ull> &args);
public:
    static void print_negated_var_init(const DatalogTask &task, PredicateRef original, PredicateRef negated, const std::vector<ull> &args);
    static void print_action_init(const DatalogTask &task, const std::string &name, ull cost);
    static void print_action_init(const DatalogTask &task, PredicateRef p, ull cost);
    static void print_eq_constraint(const DatalogTask &task, PredicateRef p, const std::vector<ull> &args, ull cost);
    static void print_zero_init(const DatalogTask &task, PredicateRef original, std::vector<ull> &args);
    static void print_unconstrained_init(const DatalogTask &task, PredicateRef original, const std::vector<ull> &args);
    static void print_less_constraint(const DatalogTask &task, const Rule &rule);
    static void maximize(const DatalogTask &task, const std::vector<Atom> &parts);
    static void output(const DatalogTask &task, const std::vector<Atom> &atoms);
    static void print_less_constraint_const(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args, const ull c);
    static void print_greater_constraint_const(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args, const ull c);
};


#endif //DATALOG_TRANSFORMER_MINIZINC_PRINTER_H
