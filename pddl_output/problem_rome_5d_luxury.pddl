;; ============================================================
;; PDDL PROBLEM FILE — AUTO-GENERATED
;; Trip  : Rome (5 days, 2 traveller(s))
;; Budget: $8,750 USD  |  Hotel style: luxury
;; Interests: culture, food, shopping
;; Generated: 2026-04-24 10:31:59
;; ============================================================

(define (problem trip-rome-5d)

  (:domain travel-planner)

  ;; ── Object Declarations ────────────────────────────────────
  (:objects
    traveller1                                   - agent
    sydney rome                        - city
    hotel_de_russie                                   - hotel
    colosseum_&_roman_forum vatican_museums_&_sistine_chapel trevi_fountain pantheon borghese_gallery trastevere_neighborhood campo_de_fiori_market palatine_hill  - attraction
    bus_&_walking                               - transport-mode
  )

  ;; ── Initial State ──────────────────────────────────────────
  (:init

    ;; Agent starts at origin
    (at traveller1 sydney)

    ;; Flight route exists
    (connected sydney rome)
    (connected rome sydney)    ; return leg

    ;; Hotel is in destination city
    (hotel-in hotel_de_russie rome)

    ;; Transport available in destination
    (transport-available bus_&_walking rome)

        (attraction-in colosseum_&_roman_forum rome)
        (attraction-open colosseum_&_roman_forum)
        (attraction-in vatican_museums_&_sistine_chapel rome)
        (attraction-open vatican_museums_&_sistine_chapel)
        (attraction-in trevi_fountain rome)
        (attraction-open trevi_fountain)
        (attraction-in pantheon rome)
        (attraction-open pantheon)
        (attraction-in borghese_gallery rome)
        (attraction-open borghese_gallery)
        (attraction-in trastevere_neighborhood rome)
        (attraction-open trastevere_neighborhood)
        (attraction-in campo_de_fiori_market rome)
        (attraction-open campo_de_fiori_market)
        (attraction-in palatine_hill rome)
        (attraction-open palatine_hill)

    ;; Budget / affordability atoms
    ; budget-insufficient — planner cannot proceed


        (affordable-entry colosseum_&_roman_forum traveller1)
        (affordable-entry vatican_museums_&_sistine_chapel traveller1)
        (affordable-entry trevi_fountain traveller1)
        (affordable-entry pantheon traveller1)
        (affordable-entry borghese_gallery traveller1)
        (affordable-entry trastevere_neighborhood traveller1)
        (affordable-entry campo_de_fiori_market traveller1)
        (affordable-entry palatine_hill traveller1)
  )

  ;; ── Goal State ─────────────────────────────────────────────
  ;; The planner must achieve ALL of these predicates
  (:goal
    (and
      ;; 1. Agent has flown to destination
      (at traveller1 rome)

      ;; 2. Accommodation established
      (staying-at traveller1 hotel_de_russie)
      (base-established traveller1 rome)

      ;; 3. Local transport arranged
      (transport-arranged traveller1 rome)

      ;; 4. Attractions visited (interest-filtered)
        (visited traveller1 colosseum_&_roman_forum)
        (visited traveller1 vatican_museums_&_sistine_chapel)
        (visited traveller1 trevi_fountain)
        (visited traveller1 pantheon)
        (visited traveller1 borghese_gallery)
        (visited traveller1 trastevere_neighborhood)
        (visited traveller1 campo_de_fiori_market)
        (visited traveller1 palatine_hill)

      ;; 5. Cultural immersion achieved
      (culture-experienced traveller1 rome)

      ;; 6. Trip complete
      (trip-complete traveller1 rome)
    )
  )

)
;; ── End of problem ─────────────────────────────────────────
