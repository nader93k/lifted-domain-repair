# Code and Resources for *Repairing Planning Domains Based on Lifted Test Plans*

This repository provides the code, benchmarks, experimental results, and supplementary materials accompanying our ECAI 2025 paper:

```bibtex
@InProceedings{Bavandpour2025LiftedTestPlans,
  author    = {Nader Karimi Bavandpour and Pascal Lauer and Songtuan Lin and Pascal Bercher},
  booktitle = {Proceedings of the 28th European Conference on Artificial Intelligence (ECAI 2025)},
  title     = {Repairing Planning Domains Based on Lifted Test Plans},
  year      = {2025},
  publisher = {IOS Press},
  abstract  = {Knowledge engineering for AI planning remains a significant challenge, particularly in the creation and maintenance of accurate domain models. A recent approach to correcting flawed models involves using test plans: non-solution plans that are intended to be solutions. However, these plans must be grounded, which restricts the modeler's ability to specify repairs at various levels of abstraction, especially when only partial information about the grounding is available. In this paper, we propose a novel approach that extends domain repair capabilities to handle lifted test plans, in which action parameters can remain unspecified. We introduce a novel search algorithm along with a heuristic function for solving the problem with lifted test plans. Our experimental results demonstrate that the proposed approach efficiently solves a wide range of problems and finds close approximations to optimal solutions in the majority of cases.}
}
```

---

## About This Repository

This repository exists solely for scientific transparency. It provides the exact code and resources that were used to produce the results reported in the paper.  

The archive **Code and Experiments** corresponds to the [v1.0.2 release on GitHub](https://github.com/nader93k/lifted-domain-repair/tree/v1.0.2).  
Since downloads from Zenodo may be slow, you may prefer to use the GitHub link above.

---

## Contents

Whether you download the Zenodo archive or access the GitHub release, you will find the following materials:

- **Benchmarks**  
- **Code** implementing the PDDL repair system  
- **Scripts** for running the repair system  
- **Log files** containing all generated outputs  
- **Evaluation scripts** for analyzing the outputs  

A comprehensive `README.md` file is included in the code repository, explaining the structure of the project and the usage of each folder and file. The repository is also **dockerized** for easier setup and adaptation.

---

## Contact

If you have questions or need clarification, feel free to contact:

- Nader Karimi Bavandpour – <u7899572@anu.edu.au>  
- Alternative email – <nader.karimi.b@gmail.com>  

---

## Recommendation

If you plan to **use or build upon this work**, we recommend using the **latest stable version** available on [GitHub](https://github.com/nader93k/lifted-domain-repair).
