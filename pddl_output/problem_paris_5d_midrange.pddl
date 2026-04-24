;; ============================================================
;; PDDL PROBLEM FILE — AUTO-GENERATED
;; Trip  : Paris (5 days, 2 traveller(s))
;; Budget: $3,000 USD  |  Hotel style: midrange
;; Interests: culture, food, shopping
;; Generated: 2026-04-24 11:09:33
;; ============================================================

(define (problem trip-paris-5d)

  (:domain travel-planner)

  ;; ── Object Declarations ────────────────────────────────────
  (:objects
    traveller1                                   - agent
    new_york paris                        - city
    hotel_du_marais                                   - hotel
    eiffel_tower louvre_museum notre_dame_cathedral musée_dorsay palace_of_versailles montmartre_&_sacré_cœur seine_river_cruise champs_élysées sainte_chapelle  - attraction
    metro                               - transport-mode
  )

  ;; ── Initial State ──────────────────────────────────────────
  (:init

    ;; Agent starts at origin
    (at traveller1 new_york)

    ;; Flight route exists
    (connected new_york paris)
    (connected paris new_york)    ; return leg

    ;; Hotel is in destination city
    (hotel-in hotel_du_marais paris)

    ;; Transport available in destination
    (transport-available metro paris)

        (attraction-in eiffel_tower paris)
        (attraction-open eiffel_tower)
        (attraction-in louvre_museum paris)
        (attraction-open louvre_museum)
        (attraction-in notre_dame_cathedral paris)
        (attraction-open notre_dame_cathedral)
        (attraction-in musée_dorsay paris)
        (attraction-open musée_dorsay)
        (attraction-in palace_of_versailles paris)
        (attraction-open palace_of_versailles)
        (attraction-in montmartre_&_sacré_cœur paris)
        (attraction-open montmartre_&_sacré_cœur)
        (attraction-in seine_river_cruise paris)
        (attraction-open seine_river_cruise)
        (attraction-in champs_élysées paris)
        (attraction-open champs_élysées)
        (attraction-in sainte_chapelle paris)
        (attraction-open sainte_chapelle)

    ;; Budget / affordability atoms
    ; budget-insufficient — planner cannot proceed

        (affordable-hotel hotel_du_marais traveller1)
        (affordable-entry eiffel_tower traveller1)
        (affordable-entry louvre_museum traveller1)
        (affordable-entry notre_dame_cathedral traveller1)
        (affordable-entry musée_dorsay traveller1)
        (affordable-entry palace_of_versailles traveller1)
        (affordable-entry montmartre_&_sacré_cœur traveller1)
        (affordable-entry seine_river_cruise traveller1)
        (affordable-entry champs_élysées traveller1)
        (affordable-entry sainte_chapelle traveller1)
  )

  ;; ── Goal State ─────────────────────────────────────────────
  ;; The planner must achieve ALL of these predicates
  (:goal
    (and
      ;; 1. Agent has flown to destination
      (at traveller1 paris)

      ;; 2. Accommodation established
      (staying-at traveller1 hotel_du_marais)
      (base-established traveller1 paris)

      ;; 3. Local transport arranged
      (transport-arranged traveller1 paris)

      ;; 4. Attractions visited (interest-filtered)
        (visited traveller1 eiffel_tower)
        (visited traveller1 louvre_museum)
        (visited traveller1 notre_dame_cathedral)
        (visited traveller1 musée_dorsay)
        (visited traveller1 palace_of_versailles)
        (visited traveller1 montmartre_&_sacré_cœur)
        (visited traveller1 seine_river_cruise)
        (visited traveller1 champs_élysées)
        (visited traveller1 sainte_chapelle)

      ;; 5. Cultural immersion achieved
      (culture-experienced traveller1 paris)

      ;; 6. Trip complete
      (trip-complete traveller1 paris)
    )
  )

)
;; ── End of problem ─────────────────────────────────────────
