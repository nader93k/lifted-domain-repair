#ifndef DATALOG_TRANSFORMER_PRETTY_PRINT_H
#define DATALOG_TRANSFORMER_PRETTY_PRINT_H

#include "parser.h"

void pretty_print(const DatalogTask &task, std::ostream &outs);

void pretty_print(const DatalogTask &task, const Rule &rule, std::ostream &outs);

void pretty_print(const DatalogTask &task, const Atom &atom, std::ostream &outs);

#endif //DATALOG_TRANSFORMER_PRETTY_PRINT_H
