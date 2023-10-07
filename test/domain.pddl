;Header and description

(define (domain grap)

;remove requirements that are not needed
(:requirements :strips :negative-preconditions)

(:types ;todo: enumerate types and their hierarchy here, e.g. car truck bus - vehiclecd
    coordinate
    object
)

; un-comment following line if constants are needed
;(:constants )

(:predicates ;todo: define predicates here
    (connected ?c1 - coordinate ?c2 - coordinate)
    (tall ?x - object)
    (occupied ?c - coordinate)
    (holding ?x - object)
    (empty)
    (robot-at ?c - coordinate)
    (obj-at ?o - object ?c - coordinate)
    (wide ?x - object)
)

;define actions here
(:action move
    :parameters (
        ?curpos - coordinate
        ?nextpos - coordinate
    )
    :precondition (and 
        ; (connected ?curpos ?nextpos) ; this is supposed to be a missing precondition
        (robot-at ?curpos)
        (not (occupied ?curpos)) 
        ;this is to say that the robot cannot move through a position if it is occupied by an object
        ;this can also be considered to be removed for creating a flaw
    )
    :effect (and 
        (robot-at ?nextpos)
        (not (robot-at ?curpos)) ;this one could be deleted to create a flaw
    )
)

(:action pickup-from-top
    :parameters (
        ?target - object
        ?curpos - coordinate
    )
    :precondition (and 
        (robot-at ?curpos)
        (obj-at ?target ?curpos)
        (empty)
        (not (tall ?target)) ;this can be removed for creating a flaw
    )
    :effect (and 
        (holding ?target)
        (not (obj-at ?target ?curpos))
        (not (empty))
        ;if the target object is picked up, it will not occupy the position
        (not (occupied ?curpos))
    )
)

(:action pickup-from-side
    :parameters (
        ?target - object
        ?curpos - coordinate
    )
    :precondition (and 
        (robot-at ?curpos)
        (obj-at ?target ?curpos)
        (empty)
        (not (wide ?target)) ;this can be removed for creating a flaw
    )
    :effect (and 
        (holding ?target)
        (not (obj-at ?target ?curpos))
        (not (empty))
        ;if the target object is picked up, it will not occupy the position
        (not (occupied ?curpos))
    )
)

(:action putdown
    :parameters (
        ?target - object
        ?curpos - coordinate
    )
    :precondition (and 
        (holding ?target)
        (robot-at ?curpos)
    )
    :effect (and 
        (obj-at ?target ?curpos)
        ;when the target object is put down, it will occupy this position
        (occupied ?curpos)
        (not (holding ?target))
    )
)
)