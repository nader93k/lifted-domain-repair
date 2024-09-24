; domain_pprobBLOCKS-5-0-err-rate-0-5.pddl
; simplified domain:


(:action pick-up
	:precondition (and
		(clear ?x)
		(ontable ?x)
		(handempty)
	)
	:effect (and
		(not (ontable ?x))
		(not (clear ?x))
		(not (handempty))
		>>> (holding ?x)
	)
)

(:action unstack
	:precondition (and
		(on ?x ?y)
		(clear ?x)
		(handempty)
	)
	:effect (and
		(holding ?x)
		>>> (clear ?y)
		(not (clear ?x))
		(not (handempty))
		(not (on ?x ?y))	
	)
)

(:action put-down
	:precondition (holding ?x)
	:effect (and
		(not (holding ?x))
		(clear ?x)
		(handempty)
		(ontable ?x)
	)
)

(:action stack
	:precondition (and
		(holding ?x)
		(clear ?y)
	)
	:effect (and
		(not (holding ?x))
		(not (clear ?y))
		(clear ?x)
		(handempty )
		(on ?x ?y)
	)
)

