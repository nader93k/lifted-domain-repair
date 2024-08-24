#include "initial_h.h"
#include "search.h"
#include "utils.h"

#include "../open_lists/greedy_open_list.h"
#include "../states/extensional_states.h"
#include "../states/sparse_states.h"
#include "../successor_generators/successor_generator.h"
#include "../utils/timer.h"

template <class PackedStateT>
utils::ExitCode InitialH<PackedStateT>::search(const Task &task, SuccessorGenerator &generator, Heuristic &heuristic) {
    // get initially achieved atoms
    DBState state = task.initial_state;
    heuristic_layer = heuristic.compute_heuristic(task.initial_state, task);
    std::cout << "Initial heuristic value is: " << heuristic_layer << std::endl << std::endl;
    exit(0); //TODO: just return 0?
}