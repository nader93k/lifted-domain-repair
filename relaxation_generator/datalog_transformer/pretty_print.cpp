#include "pretty_print.h"

const char COMMA[] = ",";
const char WHITE_SPACE[] = " ";
const char COMMA_WITH_SPACE[] = ", ";
const char LINE_END[] = ".\n";

static void output_starting_from(const std::string &s, const ull &start, std::ostream &outs) {
    for (ull i = start; i < s.size(); i++) {
        outs << s.at(i);
    }
}

template<typename T, const char *appends=COMMA, bool only_between=true>
static void pretty_print(const DatalogTask &task, const std::vector<T> &v, std::ostream &outs) {
    ull x = 0;
    for (auto &el : v) {
        pretty_print(task, el, outs);
        if (!only_between || (++x != v.size())) outs << appends;
    }
}

static void pretty_print(const DatalogTask &task, const ObjectOrVarRef& obj_or_var, std::ostream &outs) {
    if (obj_or_var._is_variable) {
        outs << task.vars.at(obj_or_var.index).name;
    } else {
        outs << task.objects.at(obj_or_var.index).name;
    }
}

void pretty_print(const DatalogTask &task, const Atom &atom, std::ostream &outs) {
    outs << task.predicates.at(atom.head).name << "(";
    pretty_print(task, atom.args, outs);
    outs << ")";
}

static void pretty_print(const DatalogTask &task, const MutexPar &m_el, std::ostream &outs) {
    if (!m_el._is_variable) {
        outs << task.objects.at(m_el.index).name;
    } else {
        outs << (m_el._is_counted ? "C" : "V") << m_el.index << ":";
        output_starting_from(task.predicates.at(m_el.associated_type).name, TYPE_PRED_START.size(), outs);
    }
}

static void pretty_print(const DatalogTask &task, const MutexElement &m_el, std::ostream &outs) {
    outs << task.predicates.at(m_el.head).name;
    if (!m_el.pars.empty()) {
        outs << " ";
        pretty_print<MutexPar, WHITE_SPACE>(task, m_el.pars, outs);
    }
}

static void pretty_print(const DatalogTask &task, const MutexGroup &m_group, std::ostream &outs) {
    outs << "{";
    pretty_print<MutexElement, COMMA_WITH_SPACE>(task, m_group.elements, outs);
    outs << "}";
    if (m_group.is_unique) {
        outs << ":=1";
    }
}

void pretty_print(const DatalogTask &task, const Rule &rule, std::ostream &outs) {
    pretty_print(task, rule.head, outs);
    outs << ":-";
    pretty_print(task, rule.body, outs);
}

void pretty_print(const DatalogTask &task, std::ostream &outs) {
    pretty_print<Atom, LINE_END, false>(task, task.init, outs);
    pretty_print<Rule, LINE_END, false>(task, task.rules, outs);

    // DanFis mutex format
    if (!task.mutex_groups.empty()) {
        outs << "< ";
        ull x = 0;
        for (auto &m_group: task.mutex_groups) {
            pretty_print(task, m_group, outs);
            outs << "\n";
            if (++x != task.mutex_groups.size()) outs << ", ";
        }
        outs << ">\n";
    }
    outs << std::endl; // to flush once
}