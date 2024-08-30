(define (problem blocks-4-0)               (:domain blocks)               (:objects b - object
d - object
a - object
c - object)                (:init (current_plan_step n0)
(clear a)
(ontable d)
(ontable c)
(clear b)
(ontable a)
(ontable b)
(clear c)
(handempty )
(clear d))                (:goal (and
		(applied_plan_step n0)
		(applied_plan_step n1)
		(applied_plan_step n2)
		(applied_plan_step n3)
		(applied_plan_step n4)
		(applied_plan_step n5)))                )
