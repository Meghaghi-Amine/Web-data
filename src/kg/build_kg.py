"""
Lab Session 4 - KB Construction
Ontologie et graphe RDF pour les blessures de footballeurs
Classes: Player, Club, Injury, BodyPart, Competition, Country, MedicalStaff
"""

import csv
import re
import sys
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FOOTY  = Namespace("http://example.org/football/")
PROP   = Namespace("http://example.org/football/property/")
DBO    = Namespace("http://dbpedia.org/ontology/")

ENTITIES_CSV  = Path("data/extracted_knowledge.csv")
RELATIONS_CSV = Path("data/extracted_relations.csv")
ONTOLOGY_FILE = Path("kg_artifacts/ontology.ttl")
KG_FILE       = Path("kg_artifacts/initial_kg.ttl")


def to_uri(text: str) -> URIRef:
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", text.strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return FOOTY[slug]

def pred_uri(verb: str) -> URIRef:
    known = {
        "suffersInjury": PROP["suffersInjury"],
        "injuryType": PROP["injuryType"],
        "affectsBodyPart": PROP["affectsBodyPart"],
        "playsFor": PROP["playsFor"],
        "missedDueTo": PROP["missedDueTo"],
        "occuredDuring": PROP["occuredDuring"],
        "represents": PROP["represents"],
        "recoveryDays": PROP["recoveryDays"],
        "gamesAbsent": PROP["gamesAbsent"],
        "injuryDate": PROP["injuryDate"],
    }
    if verb in known:
        return known[verb]
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", verb.strip())
    return PROP[slug]


# ── Ontologie domaine Blessures Football ───────────────────────────────────────
def build_ontology() -> Graph:
    g = Graph()
    g.bind("footy", FOOTY)
    g.bind("prop",  PROP)
    g.bind("dbo",   DBO)
    g.bind("owl",   OWL)
    g.bind("rdfs",  RDFS)

    # ── Classes ────────────────────────────────────────────────────────────────
    classes = {
        "Player":        "A professional football player.",
        "Club":          "A football club or team.",
        "Injury":        "A specific injury suffered by a player.",
        "InjuryType":    "A category of injury (e.g. ACL rupture, fracture).",
        "BodyPart":      "The body part affected by an injury.",
        "Competition":   "A football tournament or league.",
        "Country":       "A nation associated with a player or club.",
        "Season":        "A football season (e.g. 2022-23).",
        "MedicalStaff":  "A doctor or physiotherapist involved in treatment.",
    }
    for name, comment in classes.items():
        uri = FOOTY[name]
        g.add((uri, RDF.type,        OWL.Class))
        g.add((uri, RDFS.label,      Literal(name, lang="en")))
        g.add((uri, RDFS.comment,    Literal(comment, lang="en")))
        g.add((uri, RDFS.subClassOf, OWL.Thing))

    # Sous-classes d'InjuryType
    injury_subtypes = [
        ("ACLRupture",        "Anterior Cruciate Ligament rupture."),
        ("HamstringStrain",   "Strain or tear of the hamstring muscle."),
        ("AchillesRupture",   "Rupture of the Achilles tendon."),
        ("Fracture",          "Bone fracture."),
        ("MetatarsalFracture","Fracture of a metatarsal bone in the foot."),
        ("Concussion",        "Brain concussion from impact."),
        ("MuscleTear",        "Tear of a muscle fibre."),
        ("SpainedAnkle",      "Ankle sprain."),
        ("MeniscusTear",      "Tear of the meniscus cartilage."),
    ]
    for name, comment in injury_subtypes:
        uri = FOOTY[name]
        g.add((uri, RDF.type,        OWL.Class))
        g.add((uri, RDFS.label,      Literal(name, lang="en")))
        g.add((uri, RDFS.comment,    Literal(comment, lang="en")))
        g.add((uri, RDFS.subClassOf, FOOTY["InjuryType"]))

    # ── Object Properties ──────────────────────────────────────────────────────
    obj_props = [
        ("suffersInjury",   "Player",       "Injury",       "The player suffered this injury."),
        ("injuryType",      "Injury",       "InjuryType",   "The type/category of the injury."),
        ("affectsBodyPart", "Injury",       "BodyPart",     "The body part affected by the injury."),
        ("playsFor",        "Player",       "Club",         "The player plays or played for this club."),
        ("missedDueTo",     "Player",       "Injury",       "Games or events missed due to the injury."),
        ("treatedBy",       "Injury",       "MedicalStaff", "Medical staff who treated the injury."),
        ("occuredDuring",   "Injury",       "Competition",  "Competition during which the injury occurred."),
        ("represents",      "Player",       "Country",      "National team represented by the player."),
        ("locatedIn",       "Club",         "Country",      "Country where the club is based."),
        ("competesIn",      "Club",         "Competition",  "Competition the club participates in."),
        ("causesSurgery",   "Injury",       "Injury",       "Injury that required surgery."),
    ]
    for name, domain, range_, comment in obj_props:
        uri = PROP[name]
        g.add((uri, RDF.type,       OWL.ObjectProperty))
        g.add((uri, RDFS.label,     Literal(name, lang="en")))
        g.add((uri, RDFS.comment,   Literal(comment, lang="en")))
        g.add((uri, RDFS.domain,    FOOTY[domain]))
        g.add((uri, RDFS.range,     FOOTY[range_]))

    # ── Datatype Properties ────────────────────────────────────────────────────
    dt_props = [
        ("injuryDate",        "Injury",  XSD.date,    "Date when the injury occurred."),
        ("recoveryDays",      "Injury",  XSD.integer, "Number of days of recovery."),
        ("gamesAbsent",       "Injury",  XSD.integer, "Number of games missed."),
        ("injuryDescription", "Injury",  XSD.string,  "Textual description of the injury."),
        ("nationality",       "Player",  XSD.string,  "Nationality of the player."),
        ("position",          "Player",  XSD.string,  "Playing position (e.g. Midfielder)."),
        ("birthDate",         "Player",  XSD.date,    "Player's date of birth."),
        ("foundedYear",       "Club",    XSD.gYear,   "Year the club was founded."),
    ]
    for name, domain, dtype, comment in dt_props:
        uri = PROP[name]
        g.add((uri, RDF.type,      OWL.DatatypeProperty))
        g.add((uri, RDFS.label,    Literal(name, lang="en")))
        g.add((uri, RDFS.comment,  Literal(comment, lang="en")))
        g.add((uri, RDFS.domain,   FOOTY[domain]))
        g.add((uri, RDFS.range,    dtype))

    # ── BodyPart instances (fixed vocabulary) ──────────────────────────────────
    body_parts = [
        "knee", "ankle", "hamstring", "thigh", "calf", "achilles",
        "foot", "metatarsal", "shoulder", "groin", "back", "hip",
        "head", "wrist", "fibula", "tibia", "meniscus",
    ]
    for bp in body_parts:
        uri = FOOTY[bp.capitalize()]
        g.add((uri, RDF.type,   FOOTY["BodyPart"]))
        g.add((uri, RDFS.label, Literal(bp, lang="en")))

    # ── InjuryType instances (fixed vocabulary) ────────────────────────────────
    known_injuries = [
        ("ACL_rupture",         "Anterior cruciate ligament rupture", "ACLRupture"),
        ("hamstring_strain",    "Hamstring muscle strain",            "HamstringStrain"),
        ("achilles_rupture",    "Achilles tendon rupture",            "AchillesRupture"),
        ("metatarsal_fracture", "Metatarsal fracture",                "MetatarsalFracture"),
        ("concussion",          "Head concussion",                    "Concussion"),
        ("muscle_tear",         "Muscle fibre tear",                  "MuscleTear"),
        ("ankle_sprain",        "Ankle sprain",                       "SpainedAnkle"),
        ("meniscus_tear",       "Meniscus cartilage tear",            "MeniscusTear"),
        ("fibula_fracture",     "Fibula fracture",                    "Fracture"),
        ("tibia_fracture",      "Tibia fracture",                     "Fracture"),
    ]
    for slug, label, subclass in known_injuries:
        uri = FOOTY[slug]
        g.add((uri, RDF.type,        FOOTY[subclass]))
        g.add((uri, RDFS.label,      Literal(label, lang="en")))

    return g


# ── NER label → classe ontologie ───────────────────────────────────────────────
LABEL_TO_CLASS = {
    "PERSON": FOOTY["Player"],
    "ORG": FOOTY["Club"],
    "GPE": FOOTY["Country"],
    "LOC": FOOTY["Country"],
    "EVENT": FOOTY["Competition"],
    "COMPETITION": FOOTY["Competition"],
    "SEASON": FOOTY["Season"],
    "INJURY": FOOTY["Injury"],
    "INJURY_TYPE": FOOTY["InjuryType"],
    "BODY_PART": FOOTY["BodyPart"],
}


def build_kg(ontology: Graph) -> Graph:
    g = ontology

    entity_types: dict[str, str] = {}
    with open(ENTITIES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ent   = row["entity"].strip()
            label = row["label"].strip()
            entity_types[ent] = label

            cls = LABEL_TO_CLASS.get(label)
            if cls:
                uri = to_uri(ent)
                g.add((uri, RDF.type,   cls))
                g.add((uri, RDFS.label, Literal(ent, lang="en")))

    with open(RELATIONS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            subj = row["subject"].strip()
            pred = row["predicate"].strip()
            obj  = row["object"].strip()
            s = to_uri(subj)
            p = pred_uri(pred)
            object_type = row.get("object_type", "").strip()

            if pred in {"recoveryDays", "gamesAbsent"}:
                g.add((s, p, Literal(int(obj), datatype=XSD.integer)))
                continue

            if pred == "injuryDate":
                g.add((s, p, Literal(obj, datatype=XSD.date)))
                continue

            o = to_uri(obj)
            g.add((s, p, o))
            if (p, RDF.type, OWL.ObjectProperty) not in g and (p, RDF.type, OWL.DatatypeProperty) not in g:
                if object_type in {"NUMBER", "DATE"}:
                    g.add((p, RDF.type, OWL.DatatypeProperty))
                else:
                    g.add((p, RDF.type, OWL.ObjectProperty))
                g.add((p, RDFS.label, Literal(pred, lang="en")))

    return g


def main():
    ONTOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("Building ontology…")
    onto = build_ontology()
    onto.serialize(destination=str(ONTOLOGY_FILE), format="turtle")
    print(f"  ✓ {ONTOLOGY_FILE}")

    print("Building knowledge graph…")
    kg = build_kg(onto)
    kg.serialize(destination=str(KG_FILE), format="turtle")

    print(f"  ✓ {KG_FILE}")
    print(f"  📊 {len(kg)} triples | {len(set(kg.subjects()))} entities | {len(set(kg.predicates()))} predicates")


if __name__ == "__main__":
    main()
