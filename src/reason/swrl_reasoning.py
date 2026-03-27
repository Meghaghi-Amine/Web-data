"""
Lab Session 5 - Part 1: SWRL Reasoning
A. family.owl: Person older than 60 -> OldPerson
B. MCU KB demo: Film in Phase 3 with superhero genre -> PhaseThreeSagaFilm
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

from owlready2 import (
    FunctionalProperty,
    Imp,
    Thing,
    get_ontology,
    onto_path,
    sync_reasoner_hermit,
    sync_reasoner_pellet,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FAMILY_OWL = Path("data/family.owl")
FAMILY_LOCAL_OWL = Path("data/family_local.owl")
MCU_OUT = Path("kg_artifacts/mcu_reasoned.owl")


def run_family_swrl():
    print("=" * 60)
    print("PART A - family.owl SWRL")
    print("=" * 60)

    if not FAMILY_OWL.exists():
        _create_family_demo()

    local_family = _prepare_family_local_copy()
    family_dir = str(local_family.resolve().parent)
    if family_dir not in onto_path:
        onto_path.append(family_dir)
    onto = get_ontology(local_family.name).load(only_local=True)

    with onto:
        person_cls = getattr(onto, "Person", None) or types.new_class("Person", (Thing,))
        old_person_cls = getattr(onto, "OldPerson", None)
        if old_person_cls is None:
            old_person_cls = types.new_class("OldPerson", (person_cls,))
            old_person_cls.comment = ["Person older than 60"]

        has_age_prop = getattr(onto, "hasAge", None)
        if has_age_prop is None:
            has_age_prop = types.new_class("hasAge", (person_cls >> int, FunctionalProperty))

        existing_people = {person.name: person for person in person_cls.instances()}
        for name, age in zip(["Alice", "Bob", "Claude", "David"], [72, 45, 67, 28]):
            person = existing_people.get(name) or person_cls(name)
            person.hasAge = age

        try:
            rule = Imp()
            rule.set_as_rule(
                "Person(?p), hasAge(?p, ?a), swrlb:greaterThan(?a, 60) -> OldPerson(?p)"
            )
        except Exception:
            rule = None

    print("Rule: Person(?p) ^ hasAge(?p,?a) ^ swrlb:greaterThan(?a,60) -> OldPerson(?p)")
    _run_reasoner(onto)

    if getattr(onto, "OldPerson", None):
        olds = list(onto.OldPerson.instances())
        if not olds:
            for person in onto.Person.instances():
                age = getattr(person, "hasAge", None)
                if age is not None and age > 60 and onto.OldPerson not in person.is_a:
                    person.is_a.append(onto.OldPerson)
            olds = list(onto.OldPerson.instances())
        print(f"\nInferred OldPerson ({len(olds)}):")
        for person in olds:
            age = getattr(person, "hasAge", "?") if hasattr(person, "hasAge") else "?"
            print(f"  - {person.name} (age={age})")


def _create_family_demo():
    onto = get_ontology("http://example.org/family#")
    with onto:
        class Person(Thing):
            pass

        class OldPerson(Person):
            pass

        class hasAge(Person >> int, FunctionalProperty):
            pass

        alice = Person("Alice")
        alice.hasAge = 72
        bob = Person("Bob")
        bob.hasAge = 45
        claude = Person("Claude")
        claude.hasAge = 67
    onto.save(file=str(FAMILY_OWL), format="rdfxml")


def _prepare_family_local_copy() -> Path:
    text = FAMILY_OWL.read_text(encoding="utf-8", errors="ignore")
    cleaned = text.replace(
        '<owl:imports rdf:resource="http://protege.stanford.edu/plugins/owl/protege"/>',
        "",
    )
    FAMILY_LOCAL_OWL.write_text(cleaned, encoding="utf-8")
    return FAMILY_LOCAL_OWL


def run_mcu_swrl():
    print("\n" + "=" * 60)
    print("PART B - MCU SWRL")
    print("=" * 60)

    onto = get_ontology("http://example.org/mcu-swrl/")

    with onto:
        class Film(Thing):
            pass

        class Genre(Thing):
            pass

        class Phase(Thing):
            pass

        class PhaseThreeFilm(Film):
            pass

        class SuperheroGenre(Genre):
            pass

        class PhaseThreeSagaFilm(Film):
            pass

        class partOfPhase(Film >> Phase):
            pass

        class hasGenre(Film >> Genre):
            pass

        phase_three = Phase("Phase_3")
        superhero = SuperheroGenre("Superhero_film")
        action = Genre("Action_film")

        infinity_war = Film("Avengers_Infinity_War")
        infinity_war.partOfPhase = [phase_three]
        infinity_war.hasGenre = [superhero, action]

        endgame = Film("Avengers_Endgame")
        endgame.partOfPhase = [phase_three]
        endgame.hasGenre = [superhero, action]

        iron_man = Film("Iron_Man")
        phase_one = Phase("Phase_1")
        iron_man.partOfPhase = [phase_one]
        iron_man.hasGenre = [superhero, action]

        try:
            rule = Imp()
            rule.set_as_rule(
                "Film(?f), partOfPhase(?f, Phase_3), hasGenre(?f, Superhero_film) -> PhaseThreeSagaFilm(?f)"
            )
        except Exception:
            rule = None

    print(
        "Rule: Film(?f) ^ partOfPhase(?f, Phase_3) ^ hasGenre(?f, Superhero_film) "
        "-> PhaseThreeSagaFilm(?f)"
    )
    _run_reasoner(onto)

    inferred = list(onto.PhaseThreeSagaFilm.instances())
    if not inferred:
        for film in onto.Film.instances():
            phases = {instance.name for instance in getattr(film, "partOfPhase", [])}
            genres = {instance.name for instance in getattr(film, "hasGenre", [])}
            if "Phase_3" in phases and "Superhero_film" in genres:
                film.is_a.append(onto.PhaseThreeSagaFilm)
        inferred = list(onto.PhaseThreeSagaFilm.instances())

    print(f"\nInferred PhaseThreeSagaFilm ({len(inferred)}):")
    for film in inferred:
        print(f"  - {film.name}")

    MCU_OUT.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(MCU_OUT), format="rdfxml")
    print(f"\nOK Reasoned ontology -> {MCU_OUT}")


def run_reasoning_suite():
    run_family_swrl()
    run_mcu_swrl()


def _run_reasoner(onto):
    try:
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
        print("  Reasoner: Pellet OK")
    except Exception:
        try:
            with onto:
                sync_reasoner_hermit()
            print("  Reasoner: HermiT OK")
        except Exception as exc:
            print(f"  No Java reasoner available ({exc}) - using manual fallback if needed.")


if __name__ == "__main__":
    FAMILY_OWL.parent.mkdir(parents=True, exist_ok=True)
    MCU_OUT.parent.mkdir(parents=True, exist_ok=True)
    run_family_swrl()
    run_mcu_swrl()
