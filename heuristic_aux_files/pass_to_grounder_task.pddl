(define (problem blocks-5-0)               (:domain blocks)               (:objects a - object
c - object
d - object
e - object
b - object)                (:init (ontable c)
(current_plan_step n0)
(clear c)
(ontable a)
(on b a)
(on e b))                (:goal (and
		(applied_plan_step n0)))                )
