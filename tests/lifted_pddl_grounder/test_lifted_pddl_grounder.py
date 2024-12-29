import sys
from pathlib import Path
import os
import unittest
from model.plan import Domain, Task
from search_partial_grounding.lifted_pddl_grounder import ground_pddl


# python3 tests/lifted_pddl_grounder/test_lifted_pddl_grounder.py 
class TestPDDLGrounder():
    def setUp(self):
        base = './tests/lifted_pddl_grounder/test_files/'
    
        # domain_path = base + "mprime/domain-pprob31-err-rate-0-5.pddl"
        # task_path = base + "mprime/pprob31-err-rate-0-5.pddl"
        domain_path = base + "miconic/domain-ps1-0-err-rate-0-1.pddl"
        task_path = base + "miconic/ps1-0-err-rate-0-1.pddl"

        with open(domain_path, 'r') as f:
            file_content = f.read()
            self.domain = Domain(file_content)
            # print(self.domain.to_pddl())

        with open(task_path, 'r') as f:
            file_content = f.read()
            self.task = Task(file_content)
            # print(self.task.to_pddl())

    def test_ground_simple_problem(self):
        result = ground_pddl(self.domain, self.task, "up", "test1")
        
        # # Basic checks that grounding worked
        # self.assertIsNotNone(result)
        # self.assertEqual(result.returncode, 0)  # Check process completed successfully

        print("\nGrounding output:")
        print(result)


if __name__ == '__main__':
    t = TestPDDLGrounder()
    t.setUp()
    t.test_ground_simple_problem()
