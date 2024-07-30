from collections import defaultdict
from pathlib import Path
from exptools import generate_instances
import csv
from io import StringIO


benchmark_path = Path('/Users/nader/Downloads/domain-repair-accessible-main/benchmarks-G1')


class insight:
    def __init__(self, name, plan_length, avg_parameters, avg_objects_per_type):
        self.name = name
        self.plan_length = plan_length
        self.avg_parameters = avg_parameters
        self.avg_objects_per_type = avg_objects_per_type
        self.avg_branching_factor = round(self.avg_objects_per_type ** self.avg_parameters, 1)

    def __eq__(self, other):
        if not isinstance(other, insight):
            return NotImplemented
        return (self.name == other.name and
                self.plan_length == other.plan_length and
                self.avg_parameters == other.avg_parameters and
                self.avg_objects_per_type == other.avg_objects_per_type)

    def __hash__(self):
        return hash((self.name, self.plan_length, self.avg_parameters, self.avg_objects_per_type))


def insights_to_csv(insights, filepath):
    # Define the column names in the specified order
    fieldnames = ['Avg Branching Factor', 'Plan Length', 'Avg Parameters', 'Avg Objects per Type', 'Name']

    try:
        with open(filepath, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames,
                                    delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # Write the header
            writer.writeheader()

            # Write the data for each insight
            for insight in insights:
                writer.writerow({
                    'Avg Branching Factor': f"{insight.avg_branching_factor:10.1f}",
                    'Plan Length': f"{insight.plan_length:4d}",
                    'Avg Parameters': f"{insight.avg_parameters:7.2f}",
                    'Avg Objects per Type': f"{insight.avg_objects_per_type:10.2f}",
                    'Name': insight.name
                })

        print(f"CSV file successfully written to {filepath}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


if __name__ == "__main__":
    insights = []
    for instance in generate_instances(benchmark_path):
        instance.load_to_memory()

        name = instance.domain_class + '_' + instance.instance_name
        name = name.split("-err")[0]

        plan_length = len(instance.lifted_plan)

        action_parameters = [len(a.parameters) for a in instance.planning_domain._actions]
        avg_parameters = sum(action_parameters) / len(action_parameters)

        type_counts = defaultdict(int)
        for o in instance.planning_task.objects:
            type_counts[o.type] += 1

        avg_objects_per_type = sum(type_counts.values()) / len(type_counts)

        insights.append(
            insight(
                name=name,
                plan_length=plan_length,
                avg_parameters=round(avg_parameters, 1),
                avg_objects_per_type=round(avg_objects_per_type, 1)
            )
        )

    insights = list(set(insights))
    sorted_insights = sorted(insights, key=lambda x: x.avg_branching_factor, reverse=False)

    print(len(set(i.name for i in insights)))
    insights_to_csv(sorted_insights, 'insights.csv')
