#ifndef SEARCH_INITIAL_H_H
#define SEARCH_INITIAL_H_H

#include "search.h"
#include "search_space.h"

template <class PackedStateT>
class InitialH : public SearchBase {
protected:
    SearchSpace<PackedStateT> space;

    int heuristic_layer{};
public:
    using StatePackerT = typename PackedStateT::StatePackerT;

    utils::ExitCode search(const Task &task, SuccessorGenerator &generator, Heuristic &heuristic) override;
    void print_statistics() const override {}
};

#include "initial_h.tpp"

#endif  // SEARCH_INITIAL_H_H

