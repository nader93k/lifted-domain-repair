"""
This package allows transforming PDDL input files. Usually, in a
Machetli script you will use it in the following way:

.. code-block:: python

    from machetli import pddl
    initial_state = pddl.generate_initial_state("path/to/domain.pddl", "path/to/problem.pddl")
    successor_generators = [pddl.RemoveActions(), ...]

You can then start your Machetli search using the initial PDDL problem
``initial_state`` and a set of PDDL successor generators
``successor_generators``. Finally, write out your results using

.. code-block:: python

    pddl.write_files(result, "path/to/result-domain.pddl", "path/to/result-problem.pddl")

where ``result`` is the value returned by the
:meth:`search<machetli.search>` function.

The successor generators described below denote possible transformations.
"""

from .files import temporary_files, write_files

# We specify the imported functions and classes in __all__ so they will be
# documented when the documentation of this package is generated.
__all__ = ["temporary_files", "write_files"]
