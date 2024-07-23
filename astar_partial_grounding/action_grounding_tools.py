def read_action_names(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(';'):
                result.append(line)
    return result


def _one_action_groundings(action, domain, task):
    """
    Compute possible groundings for a lifted action.

    :param action: The lifted action
    :param domain: The domain
    :param task: The task
    :return: A list of possible groundings (variable mappings)
    """
    possible_groundings = []
    objects = task.objects + domain.constants

    def recursive_ground(param_index, current_grounding):
        if param_index == len(action.parameters):
            possible_groundings.append(current_grounding.copy())
            return

        param = action.parameters[param_index]
        for obj in objects:
            if obj.type == param.type:
                current_grounding[param.name] = obj
                recursive_ground(param_index + 1, current_grounding)

    recursive_ground(0, {})
    return possible_groundings

def all_action_groundings(file_path, domain, task):
    white_action_names = read_action_names(file_path)

    all_groundings = {}
    for name in white_action_names:
        all_groundings[name] = []
        lifted_action = domain.get_action(name)
        grounded_action = _one_action_groundings(lifted_action, domain, task)
        for g in grounded_action:
            s = '(' + lifted_action.name
            for param in lifted_action.parameters:
                s = s + ' ' + g[param.name].name
            s = s + ')'
            all_groundings[name].append(s)

    return all_groundings
