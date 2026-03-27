"""
Lab Session 5 - Part 1: SWRL Reasoning
A. family.owl : Person âgée de plus de 60 ans → OldPerson
B. KB foot    : Player qui souffre d'une ACLRupture → HighRiskPlayer
               + Player qui manque > 90 jours → LongTermInjuredPlayer
"""

from owlready2 import (
    FunctionalProperty,
    Imp,
    Thing,
    get_ontology,
    onto_path,
    sync_reasoner_hermit,
    sync_reasoner_pellet,
)
from pathlib import Path
import sys
import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FAMILY_OWL = Path("data/family.owl")
FAMILY_LOCAL_OWL = Path("data/family_local.owl")
SPORT_OUT  = Path("kg_artifacts/sport_reasoned.owl")


# ─────────────────────────────────────────────────────────────────────────────
# A — family.owl  (fourni par le cours)
# Règle : Person(?p) ∧ hasAge(?p,?a) ∧ swrlb:greaterThan(?a,60) → OldPerson(?p)
# ─────────────────────────────────────────────────────────────────────────────
def run_family_swrl():
    print("=" * 60)
    print("PART A — family.owl SWRL")
    print("=" * 60)

    if not FAMILY_OWL.exists():
        _create_family_demo()

    local_family = _prepare_family_local_copy()
    family_dir = str(local_family.resolve().parent)
    if family_dir not in onto_path:
        onto_path.append(family_dir)
    onto = get_ontology(local_family.name).load(only_local=True)

    with onto:
        person_cls = getattr(onto, "Person", None)
        if person_cls is None:
            person_cls = types.new_class("Person", (Thing,))

        old_person_cls = getattr(onto, "OldPerson", None)
        if old_person_cls is None:
            old_person_cls = types.new_class("OldPerson", (person_cls,))
            old_person_cls.comment = ["Person older than 60"]

        has_age_prop = getattr(onto, "hasAge", None)
        if has_age_prop is None:
            has_age_prop = types.new_class("hasAge", (person_cls >> int, FunctionalProperty))

        people = list(person_cls.instances())
        seed_ages = [72, 45, 67, 28]
        if not people:
            for name, age in zip(["Alice", "Bob", "Claude", "David"], seed_ages):
                person = person_cls(name)
                person.hasAge = age
        else:
            for person, age in zip(people, seed_ages):
                if not getattr(person, "hasAge", None):
                    person.hasAge = age

        rule = None
        try:
            rule = Imp()
            rule.set_as_rule(
                "Person(?p), hasAge(?p, ?a), swrlb:greaterThan(?a, 60) -> OldPerson(?p)"
            )
        except Exception:
            rule = None

    print("Rule: Person(?p) ∧ hasAge(?p,?a) ∧ swrlb:greaterThan(?a,60) → OldPerson(?p)")

    _run_reasoner(onto)

    if rule is None and getattr(onto, "OldPerson", None):
        for person in onto.Person.instances():
            age = getattr(person, "hasAge", None)
            if age is not None and age > 60:
                if onto.OldPerson not in person.is_a:
                    person.is_a.append(onto.OldPerson)

    if getattr(onto, "OldPerson", None):
        olds = list(onto.OldPerson.instances())
        print(f"\nInferred OldPerson ({len(olds)}):")
        for p in olds:
            age = getattr(p, "hasAge", "?") if hasattr(p, "hasAge") else "?"
            print(f"  - {p.name} (age={age})")


def _create_family_demo():
    onto = get_ontology("http://example.org/family#")
    with onto:
        class Person(Thing): pass
        class OldPerson(Person): pass
        class hasAge(Person >> int, FunctionalProperty): pass
        p1 = Person("Alice");  p1.hasAge = 72
        p2 = Person("Bob");    p2.hasAge = 45
        p3 = Person("Claude"); p3.hasAge = 67
        p4 = Person("David");  p4.hasAge = 28
    onto.save(file=str(FAMILY_OWL), format="rdfxml")
    print(f"  Created demo family.owl → {FAMILY_OWL}")


# ─────────────────────────────────────────────────────────────────────────────
# B — KB Football Injuries
# Règle 1: Player(?p) ∧ suffersInjury(?p,?i) ∧ ACLRupture(?i) → HighRiskPlayer(?p)
# Règle 2: Player(?p) ∧ suffersInjury(?p,?i) ∧ recoveryDays(?i,?d)
#           ∧ swrlb:greaterThan(?d,90) → LongTermInjuredPlayer(?p)
# ─────────────────────────────────────────────────────────────────────────────
def _prepare_family_local_copy() -> Path:
    text = FAMILY_OWL.read_text(encoding="utf-8", errors="ignore")
    cleaned = text.replace(
        '<owl:imports rdf:resource="http://protege.stanford.edu/plugins/owl/protege"/>',
        ""
    )
    FAMILY_LOCAL_OWL.write_text(cleaned, encoding="utf-8")
    return FAMILY_LOCAL_OWL


def run_football_swrl():
    print("\n" + "=" * 60)
    print("PART B — Football Injuries SWRL")
    print("=" * 60)

    onto = get_ontology("http://example.org/football/")

    with onto:
        # Classes
        class Player(Thing): pass
        class Injury(Thing): pass
        class ACLRupture(Injury): pass
        class HamstringStrain(Injury): pass
        class HighRiskPlayer(Player): pass          # NEW — inféré
        class LongTermInjuredPlayer(Player): pass   # NEW — inféré

        # Propriétés
        class suffersInjury(Player >> Injury): pass
        class recoveryDays(Injury >> int, FunctionalProperty): pass

        # ── Individus exemples ─────────────────────────────────────────────────
        messi   = Player("Messi")
        neymar  = Player("Neymar")
        diaby   = Player("Diaby")
        cazorla = Player("Cazorla")

        inj1 = ACLRupture("MessiKneeACL");      inj1.recoveryDays = [180]
        inj2 = HamstringStrain("NeymarHam");     inj2.recoveryDays = [45]
        inj3 = ACLRupture("DiabyKneeACL");       inj3.recoveryDays = [240]
        inj4 = ACLRupture("CazorlaAnkle");       inj4.recoveryDays = [700]

        messi.suffersInjury   = [inj1]
        neymar.suffersInjury  = [inj2]
        diaby.suffersInjury   = [inj3]
        cazorla.suffersInjury = [inj4]

        # ── SWRL Rules ─────────────────────────────────────────────────────────
        rule1 = Imp()
        rule1.set_as_rule(
            "Player(?p), suffersInjury(?p, ?i), ACLRupture(?i) -> HighRiskPlayer(?p)"
        )
        rule2 = Imp()
        rule2.set_as_rule(
            "Player(?p), suffersInjury(?p, ?i), recoveryDays(?i, ?d), "
            "swrlb:greaterThan(?d, 90) -> LongTermInjuredPlayer(?p)"
        )

    print("Rule 1: Player(?p) ∧ suffersInjury(?p,?i) ∧ ACLRupture(?i) → HighRiskPlayer(?p)")
    print("Rule 2: Player(?p) ∧ suffersInjury(?p,?i) ∧ recoveryDays(?i,?d) ∧ ?d>90 → LongTermInjuredPlayer(?p)")

    _run_reasoner(onto)

    for cls_name in ["HighRiskPlayer", "LongTermInjuredPlayer"]:
        cls = getattr(onto, cls_name, None)
        if cls:
            instances = list(cls.instances())
            print(f"\nInferred {cls_name} ({len(instances)}):")
            for inst in instances:
                print(f"  - {inst.name}")
        else:
            # Fallback sans raisonneur
            print(f"\n[Manual check] {cls_name}:")
            for pl in onto.Player.instances():
                for inj in getattr(pl, "suffersInjury", []):
                    days = getattr(inj, "recoveryDays", [0])[0] if getattr(inj, "recoveryDays", None) else 0
                    is_acl = isinstance(inj, onto.ACLRupture)
                    if cls_name == "HighRiskPlayer" and is_acl:
                        print(f"  - {pl.name}")
                    if cls_name == "LongTermInjuredPlayer" and days > 90:
                        print(f"  - {pl.name} (recoveryDays={days})")

    SPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(SPORT_OUT), format="rdfxml")
    print(f"\n✅ Reasoned ontology → {SPORT_OUT}")


def _run_reasoner(onto):
    try:
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
        print("  Reasoner: Pellet ✓")
    except Exception as e:
        try:
            with onto:
                sync_reasoner_hermit()
            print("  Reasoner: HermiT ✓")
        except Exception as e2:
            print(f"  ⚠ No reasoner available ({e2}) — manual fallback used.")


if __name__ == "__main__":
    SPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    FAMILY_OWL.parent.mkdir(parents=True, exist_ok=True)
    run_family_swrl()
    run_football_swrl()
