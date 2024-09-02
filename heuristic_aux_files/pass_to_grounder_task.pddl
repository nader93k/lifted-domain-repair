(define (problem blocks-4-0)               (:domain blocks)               (:objects d - object
a - object
b - object
c - object)                (:init (clear c)
(clear d)
(ontable d)
(ontable a)
(ontable b)
(handempty )
(ontable c)
(current_plan_step n0)
(clear a)
(clear b))                (:goal (and
		(applied_plan_step n0)
		(applied_plan_step n1)
		(applied_plan_step n2)
		(applied_plan_step n3)
		(applied_plan_step n4)
		(applied_plan_step n5)))                )
