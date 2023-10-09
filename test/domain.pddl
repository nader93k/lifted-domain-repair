;Header and description

(define (domain grap)

;remove requirements that are not needed
(:requirements :strips :negative-preconditions)

(:types ;todo: enumerate types and their hierarchy here, e.g. car truck bus - vehiclecd
    coordinate
    thing
)

; un-comment following line if constants are needed
;(:constants )

(:predicates ;todo: define predicates here
    (connected ?c1 - coordinate ?c2 - coordinate)
    (tall ?x - thing)
    (holding ?x - thing)
    (empty)
    (robot-at ?c - coordinate)
    (obj-at ?o - thing ?c - coordinate)
    (wide ?x - thing)
)

;define actions here
(:action move
    :parameters (
        ?curpos - coordinate
        ?nextpos - coordinate
    )
    :precondition (and 
        (connected ?curpos ?nextpos) ; this is supposed to be a missing precondition
        (robot-at ?curpos)
    )
    :effect (and 
        (robot-at ?nextpos)
        (not (robot-at ?curpos)) ;this one could be deleted to create a flaw
    )
)

(:action pickup-from-top
    :parameters (
        ?target - thing
        ?curpos - coordinate
    )
    :precondition (and 
        (robot-at ?curpos)
        (obj-at ?target ?curpos)
        (empty)
        ;(not (tall ?target)) ;this can be removed for creating a flaw
    )
    :effect (and 
        (holding ?target)
        (not (obj-at ?target ?curpos))
        (not (empty))
    )
)

(:action pickup-from-side
    :parameters (
        ?target - thing
        ?curpos - coordinate
    )
    :precondition (and 
        (robot-at ?curpos)
        (obj-at ?target ?curpos)
        (empty)
        ;(not (wide ?target)) ;this can be removed for creating a flaw
    )
    :effect (and 
        (holding ?target)
        (not (obj-at ?target ?curpos))
        (not (empty))
    )
)

(:action putdown
    :parameters (
        ?target - thing
        ?curpos - coordinate
    )
    :precondition (and 
        (holding ?target)
        (robot-at ?curpos)
    )
    :effect (and 
        (empty) ;comment this, because this is a real mistask!
        (obj-at ?target ?curpos)
        (not (holding ?target))
    )
)
)