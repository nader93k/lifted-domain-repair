;;; repair: pick-up,(not (handempty )),effNeg,-1

(define 
(problem BLOCKS-4-0)


(:domain
  BLOCKS
)

(:objects 
  A B C D
)

(:INIT
  (CLEAR A) (CLEAR B) (CLEAR C) (CLEAR D)
  (ONTABLE A) (ONTABLE B) (ONTABLE C) (ONTABLE D)
  (HANDEMPTY)
)

(:goal 
  (AND
    (ON D C) (ON C B) (ON B A)
  )
)


)
