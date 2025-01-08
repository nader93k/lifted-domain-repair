(define (problem strips-mprime-y-1)
   (:domain mystery-prime-strips)
   (:objects grapefruit chocolate cantelope ham haroset snickers
             muffin chicken pistachio lemon bacon learning love rest
             intoxication expectation understanding triumph aesthetics
             prostatitis grief dread depression sciatica abrasion hangover
             loneliness anger angina alsace quebec kentucky earth saturn
             neptune mars)
   (:init 
       (eats ham muffin)
       (eats muffin ham)
       (eats chicken muffin)
       (eats grapefruit ham)

       (locale grapefruit quebec)
       (locale muffin quebec)
       (locale ham quebec)
       (locale cantelope quebec)

       (craves love muffin)
       (craves learning grapefruit)

       (pleasure learning)

       (attacks alsace quebec)

       (food muffin)
       (food ham)
       (food grapefruit)
    )

   (:goal
       (and (craves prostatitis cantelope))
   )
)
