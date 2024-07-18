#include "minizinc_printer.h"

//TODO: maybe wanna get rid of endl

auto constexpr ENDL = "\n";

void MiniZincPrinter::print_atom_likes(const DatalogTask &task, const Atom &atom) {
    //TODO: would probably make more sense to use a "grounded data type" directly
    std::vector<ull> args;
    for (auto &arg : atom.args) {
        assert(!arg._is_variable);
        args.push_back(arg.index);
    }
    print_atom_likes(task, atom.head, args);
}

void MiniZincPrinter::print_atom_likes(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args) {
    print_atom_likes(task, task.predicates.at(pred).name, args);
}

void MiniZincPrinter::print_atom_likes(const DatalogTask &task, const std::string &pred_name, const std::vector<ull> &args) {
    outs << pred_name << "_endpred_";
    for (auto arg : args) {
        outs << task.objects.at(arg).name << "___";
    }
}

void MiniZincPrinter::print_zero_init(const DatalogTask &task, PredicateRef original, std::vector<ull> &args) {
    outs << "var float: ";
    print_atom_likes(task, original, args);
    outs << " = 0;" << ENDL;
}

void MiniZincPrinter::print_action_init(const DatalogTask &task, PredicateRef p, ull cost) {
    print_action_init(task, task.predicates.at(p).name, cost);
}

void MiniZincPrinter::maximize(const DatalogTask &task, const std::vector<Atom> &parts) {
    outs << "solve maximize ";
    ull i = 0;
    for (auto &atom : parts) {
        print_atom_likes(task, atom);
        if (++i < parts.size()) outs << " + ";
    }
    outs << ";" << ENDL;
}

void MiniZincPrinter::print_eq_constraint(const DatalogTask &task, PredicateRef p, const std::vector<ull> &args, ull cost) {
    outs << "constraint ";
    print_atom_likes(task, p, args);
    outs << " = " << cost << ";" << ENDL;
}

void MiniZincPrinter::print_action_init(const DatalogTask &task, const std::string &s, ull cost) {
    std::vector<ull> args;
    outs << "constraint ";
    print_atom_likes(task, s, args);
    outs << " <= " << cost << ";" << ENDL;
}


void MiniZincPrinter::print_less_constraint_const(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args, const ull c) {
    outs << "constraint ";
    print_atom_likes(task, pred, args);
    outs << " <= " << c << ";" << ENDL;
}

void MiniZincPrinter::print_greater_constraint_const(const DatalogTask &task, PredicateRef pred, const std::vector<ull> &args, const ull c) {
    outs << "constraint ";
    print_atom_likes(task, pred, args);
    outs << " >= " << c << ";" << ENDL;
}

void MiniZincPrinter::print_less_constraint(const DatalogTask &task, const Rule &rule) {
    outs << "constraint ";
    print_atom_likes(task, rule.head);
    outs << " >= ";
    ull atom_id = 0;
    for (auto &atom : rule.body) {
        print_atom_likes(task, atom);
        if (++atom_id < rule.body.size()) {
            outs << " + ";
        }
    }
    outs << ";" << ENDL;
}

void MiniZincPrinter::print_negated_var_init(const DatalogTask &task, PredicateRef original, PredicateRef negated,
                                             const std::vector<ull> &args) {
    outs << "var float: ";
    print_atom_likes(task, original, args);
    outs << " = -";
    print_atom_likes(task, negated, args);
    outs << ";" << ENDL;
}

std::string zinc_bound("1000");
void MiniZincPrinter::print_unconstrained_init(const DatalogTask &task, PredicateRef original, const std::vector<ull> &args) {
    outs << "var -" << zinc_bound << ".0.." << zinc_bound << ".0: ";
    print_atom_likes(task, original, args);
    outs << ";" << ENDL;
}

void MiniZincPrinter::output(const DatalogTask &task, const std::vector<Atom> &atoms) {
    outs << "output [";

    ull i = 0;
    for (auto &atom : atoms) {
        outs << '"';
        print_atom_likes(task, atom);
        outs << "=\\(";
        print_atom_likes(task, atom);
        outs << ")\\n" << '"';
        if (++i < atoms.size()) outs << "," << ENDL;
    }

    outs << "];";
}