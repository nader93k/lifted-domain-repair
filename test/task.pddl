(define 
    (problem task) 
    (:domain grap)
(:objects
    node-0-0 node-0-1 node-0-2 node-1-0 node-1-1 node-1-2 node-2-0 node-2-1 node-2-2 - coordinate
    obj-1 obj-2 obj-3 obj-4 - thing
)

(:init
    ;todo: put the initial state's facts and numeric values here
    (connected node-0-0 node-0-1)
    (connected node-0-0 node-1-0)
    (connected node-0-1 node-0-2)
    (connected node-0-1 node-0-0)
    (connected node-0-1 node-1-1)
    (connected node-0-2 node-1-2)
    (connected node-0-2 node-0-1)
    (connected node-1-0 node-1-1)
    (connected node-1-0 node-0-0)
    (connected node-1-0 node-2-0)
    (connected node-1-1 node-1-0)
    (connected node-1-1 node-2-1)
    (connected node-1-1 node-1-2)
    (connected node-1-1 node-0-1)
    (connected node-1-2 node-1-1)
    (connected node-1-2 node-2-2)
    (connected node-1-2 node-0-2)
    (connected node-2-0 node-2-1)
    (connected node-2-0 node-1-0)
    (connected node-2-1 node-2-0)
    (connected node-2-1 node-2-2)
    (connected node-2-1 node-1-1)
    (connected node-2-2 node-2-1)
    (connected node-2-2 node-1-2)
    (tall obj-1)
    (wide obj-2)
    (wide obj-3)
    (obj-at obj-1 node-0-1)
    (obj-at obj-2 node-1-0)
    (obj-at obj-3 node-1-1)
    (obj-at obj-4 node-0-0)
    (robot-at node-0-0)
    (empty)
)

(:goal (and
    ;todo: put the goal condition here
    (obj-at obj-4 node-0-0)
    (obj-at obj-1 node-0-2)
    (obj-at obj-2 node-1-2)
    (obj-at obj-3 node-0-2)
))

;un-comment the following line if metric is needed
;(:metric minimize (???))
)
