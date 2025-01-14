(define (problem B0)
    (:domain BLOCKS)
    (:objects A B C)
    (:INIT 

        (CLEAR A)
        (CLEAR B)
        (CLEAR C)
    
        (ONTABLE A)
        (ONTABLE B)
        (ONTABLE C)
        
        (HANDEMPTY)
    )
    (
        :goal (HANDEMPTY)
    )
)