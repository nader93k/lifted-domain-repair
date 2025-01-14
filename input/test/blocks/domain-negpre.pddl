(define (domain blocks)
  (:requirements :strips :negative-preconditions :typing)
  (:types
	object)
  (:constants )
  (:predicates
	(on ?x - object ?y - object)
	(ontable ?x - object)
	(clear ?x - object)
	(handempty )
	(holding ?x - object)
	)
  (:functions )

(:action pick-up
	:parameters (?x - object)
	:precondition (and
		(clear ?x)
		(ontable ?x)
		(handempty )
		)
	:effect (and
		(not (ontable ?x))
		(not (clear ?x))
		(not (handempty )) ; Nader removed
		; (holding ?x)) ; Nader removed
	)
)

(:action stack
	:parameters (?x - object
		?y - object)
	:precondition (and
		(holding ?x)
		(clear ?y)
		(not (handempty )) ; Nader added
		)
	:effect (and
		(not (holding ?x))
		(not (clear ?y))
		(clear ?x)
		(handempty )
		(on ?x ?y)))

(:action put-down
	:parameters (?x - object)
	:precondition (and
		(holding ?x)
		(not (handempty )) ; Nader added
		)
	:effect (and
		(not (holding ?x))
		(clear ?x)
		(handempty )
		(ontable ?x)))

(:action unstack
	:parameters (?x - object
		?y - object)
	:precondition (and
		(on ?x ?y)
		(clear ?x)
		(handempty ))
	:effect (and
		(holding ?x)
		(clear ?y)
		(not (clear ?x))
		(not (handempty ))
		(not (on ?x ?y))))
)
