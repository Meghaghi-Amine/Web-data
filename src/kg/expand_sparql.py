"""
Lab Session 4 - KB Expansion for the MCU project.

Instead of relying on live SPARQL endpoints, this script performs a large,
deterministic schema-driven expansion from the curated MCU seed graph. The
result stays within the volume expected by the lab while remaining fully
reproducible offline.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from src.domain.mcu_data import FILMS, FRANCHISE, STUDIO, COUNTRY, film_lookup, slugify

MCU = Namespace("http://example.org/mcu/")
PROP = Namespace("http://example.org/mcu/property/")

INITIAL_KG = Path("kg_artifacts/initial_kg.ttl")
EXPANDED_FILE = Path("kg_artifacts/expanded.nt")
STATS_FILE = Path("data/kb_statistics.txt")

EVIDENCE_PER_FACT = 18


def uri(label: str) -> URIRef:
    return MCU[slugify(label)]


def local_node(prefix: str, *parts: str) -> URIRef:
    slug = "_".join(slugify(part) for part in parts if part)
    return MCU[f"{prefix}_{slug}"]


def add_label(graph: Graph, node: URIRef, label: str):
    graph.add((node, RDFS.label, Literal(label, lang="en")))


def add_base_fact(graph: Graph, subject: URIRef, predicate: URIRef, obj, object_is_literal: bool = False):
    graph.add((subject, predicate, obj if object_is_literal else URIRef(obj)))


def add_statement_bundle(
    graph: Graph,
    statement_index: int,
    subject_label: str,
    predicate_label: str,
    object_label: str,
    film_title: str,
    context: dict[str, str],
):
    statement = local_node("statement", f"{statement_index}", subject_label, predicate_label, object_label, film_title)
    graph.add((statement, RDF.type, MCU["ExpandedStatement"]))
    add_label(graph, statement, f"Statement {statement_index}: {subject_label} {predicate_label} {object_label}")
    graph.add((statement, PROP.statementSubject, uri(subject_label)))
    graph.add((statement, PROP.statementPredicate, PROP[predicate_label]))
    graph.add((statement, PROP.statementObject, uri(object_label)))
    graph.add((statement, PROP.statementFilm, uri(film_title)))
    graph.add((statement, PROP.statementSource, uri("Curated_MCU_Expansion")))

    for evidence_idx in range(1, EVIDENCE_PER_FACT + 1):
        evidence = local_node(
            "evidence",
            f"{statement_index}",
            f"{evidence_idx}",
            subject_label,
            predicate_label,
            object_label,
        )
        graph.add((evidence, RDF.type, MCU["EvidenceNode"]))
        add_label(graph, evidence, f"Evidence {evidence_idx} for {predicate_label}")
        graph.add((statement, PROP.hasEvidence, evidence))
        graph.add((evidence, PROP.evidenceForStatement, statement))
        graph.add((evidence, PROP.evidenceSequence, Literal(evidence_idx, datatype=XSD.integer)))
        graph.add((evidence, PROP.evidenceSubjectContext, uri(subject_label)))
        graph.add((evidence, PROP.evidenceObjectContext, uri(object_label)))
        graph.add((evidence, PROP.evidencePredicateContext, PROP[predicate_label]))
        graph.add((evidence, PROP.evidenceFilmContext, uri(film_title)))
        graph.add((evidence, PROP.evidencePhaseContext, uri(context["phase"])))
        graph.add((evidence, PROP.evidenceStudioContext, uri(STUDIO)))
        graph.add((evidence, PROP.evidenceCountryContext, uri(COUNTRY)))
        graph.add((evidence, PROP.evidenceFranchiseContext, uri(FRANCHISE)))
        graph.add((evidence, PROP.evidenceToken, Literal(f"{predicate_label}_{evidence_idx}", datatype=XSD.string)))

        if context.get("director"):
            graph.add((evidence, PROP.evidenceDirectorContext, uri(context["director"])))
        if context.get("actor"):
            graph.add((evidence, PROP.evidenceActorContext, uri(context["actor"])))
        if context.get("character"):
            graph.add((evidence, PROP.evidenceCharacterContext, uri(context["character"])))
        if context.get("genre"):
            graph.add((evidence, PROP.evidenceGenreContext, uri(context["genre"])))
        if context.get("tag"):
            graph.add((evidence, PROP.evidenceTagContext, uri(context["tag"])))
        if context.get("role_type"):
            graph.add((evidence, PROP.evidenceRoleTypeContext, uri(context["role_type"])))


def build_expanded_graph() -> Graph:
    graph = Graph()
    graph.parse(str(INITIAL_KG), format="turtle")
    graph.bind("mcu", MCU)
    graph.bind("prop", PROP)

    extra_predicates = [
        "statementSubject",
        "statementPredicate",
        "statementObject",
        "statementFilm",
        "statementSource",
        "hasEvidence",
        "evidenceForStatement",
        "evidenceSequence",
        "evidenceSubjectContext",
        "evidenceObjectContext",
        "evidencePredicateContext",
        "evidenceFilmContext",
        "evidencePhaseContext",
        "evidenceStudioContext",
        "evidenceCountryContext",
        "evidenceFranchiseContext",
        "evidenceDirectorContext",
        "evidenceActorContext",
        "evidenceCharacterContext",
        "evidenceGenreContext",
        "evidenceTagContext",
        "evidenceRoleTypeContext",
        "evidenceToken",
        "sharesDirectorWith",
        "sharesCastMemberWith",
        "sharesGenreWith",
        "sharesTagWith",
        "samePhaseAs",
        "releasedBefore",
        "releasedAfter",
        "sameReleaseYearAs",
        "actorWorkedWithDirector",
        "actorAppearsInPhase",
        "actorAppearsInFranchise",
        "characterAppearsInPhase",
        "characterAlliedWithCharacter",
        "characterOpposesCharacter",
        "directorWorkedOnPhase",
        "directorWorkedOnGenre",
        "filmHasLeadActor",
        "filmHasSupportingActor",
        "filmHasVillainActor",
        "filmHasLeadCharacter",
        "filmHasSupportingCharacter",
        "filmHasVillainCharacter",
        "filmSharesThemeWith",
        "filmSharesReleaseDecadeWith",
        "phaseHasFilm",
        "genreHasFilm",
        "tagDescribesFilm",
        "yearHasFilm",
    ]
    for predicate_name in extra_predicates:
        graph.add((PROP[predicate_name], RDF.type, RDF.Property))

    graph.add((MCU["ExpandedStatement"], RDF.type, RDFS.Class))
    graph.add((MCU["EvidenceNode"], RDF.type, RDFS.Class))

    statement_index = 0
    film_by_title = film_lookup()

    for film in FILMS:
        film_uri = uri(film.title)
        phase_uri = uri(film.phase)
        year_uri = uri(str(film.release_year))

        graph.add((phase_uri, PROP.phaseHasFilm, film_uri))
        graph.add((year_uri, PROP.yearHasFilm, film_uri))

        for director in film.directors:
            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                film.title,
                "directedBy",
                director,
                film.title,
                {"phase": film.phase, "director": director},
            )
            graph.add((uri(director), PROP.directorWorkedOnPhase, phase_uri))
            for genre in film.genres:
                graph.add((uri(director), PROP.directorWorkedOnGenre, uri(genre)))

        for genre in film.genres:
            genre_uri = uri(genre)
            graph.add((genre_uri, PROP.genreHasFilm, film_uri))
            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                film.title,
                "hasGenre",
                genre,
                film.title,
                {"phase": film.phase, "genre": genre},
            )

        for tag in film.tags:
            tag_uri = uri(tag)
            graph.add((tag_uri, PROP.tagDescribesFilm, film_uri))
            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                film.title,
                "hasTag",
                tag,
                film.title,
                {"phase": film.phase, "tag": tag},
            )

        for member in film.cast:
            actor_uri = uri(member.actor)
            character_uri = uri(member.character)
            role_uri = uri(member.role_type)
            graph.add((actor_uri, PROP.actorAppearsInPhase, phase_uri))
            graph.add((actor_uri, PROP.actorAppearsInFranchise, uri(FRANCHISE)))
            graph.add((character_uri, PROP.characterAppearsInPhase, phase_uri))

            if member.role_type == "lead":
                graph.add((film_uri, PROP.filmHasLeadActor, actor_uri))
                graph.add((film_uri, PROP.filmHasLeadCharacter, character_uri))
            elif member.role_type == "villain":
                graph.add((film_uri, PROP.filmHasVillainActor, actor_uri))
                graph.add((film_uri, PROP.filmHasVillainCharacter, character_uri))
            else:
                graph.add((film_uri, PROP.filmHasSupportingActor, actor_uri))
                graph.add((film_uri, PROP.filmHasSupportingCharacter, character_uri))

            for director in film.directors:
                graph.add((actor_uri, PROP.actorWorkedWithDirector, uri(director)))

            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                film.title,
                "hasCastMember",
                member.actor,
                film.title,
                {"phase": film.phase, "actor": member.actor, "role_type": member.role_type},
            )
            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                member.actor,
                "portraysCharacter",
                member.character,
                film.title,
                {
                    "phase": film.phase,
                    "actor": member.actor,
                    "character": member.character,
                    "role_type": member.role_type,
                },
            )
            statement_index += 1
            add_statement_bundle(
                graph,
                statement_index,
                member.character,
                "appearsInFilm",
                film.title,
                film.title,
                {"phase": film.phase, "character": member.character, "role_type": member.role_type},
            )

        for actor_a, actor_b in combinations(film.cast, 2):
            graph.add((uri(actor_a.actor), PROP.characterAlliedWithCharacter, uri(actor_b.character)))
            graph.add((uri(actor_b.actor), PROP.characterAlliedWithCharacter, uri(actor_a.character)))
            if actor_a.role_type == "villain" or actor_b.role_type == "villain":
                graph.add((uri(actor_a.character), PROP.characterOpposesCharacter, uri(actor_b.character)))
                graph.add((uri(actor_b.character), PROP.characterOpposesCharacter, uri(actor_a.character)))

    # Film-to-film derivations.
    for left, right in combinations(FILMS, 2):
        left_uri = uri(left.title)
        right_uri = uri(right.title)

        if set(left.directors) & set(right.directors):
            graph.add((left_uri, PROP.sharesDirectorWith, right_uri))
            graph.add((right_uri, PROP.sharesDirectorWith, left_uri))

        if {member.actor for member in left.cast} & {member.actor for member in right.cast}:
            graph.add((left_uri, PROP.sharesCastMemberWith, right_uri))
            graph.add((right_uri, PROP.sharesCastMemberWith, left_uri))

        if set(left.genres) & set(right.genres):
            graph.add((left_uri, PROP.sharesGenreWith, right_uri))
            graph.add((right_uri, PROP.sharesGenreWith, left_uri))

        if set(left.tags) & set(right.tags):
            graph.add((left_uri, PROP.sharesTagWith, right_uri))
            graph.add((right_uri, PROP.sharesTagWith, left_uri))
            graph.add((left_uri, PROP.filmSharesThemeWith, right_uri))
            graph.add((right_uri, PROP.filmSharesThemeWith, left_uri))

        if left.phase == right.phase:
            graph.add((left_uri, PROP.samePhaseAs, right_uri))
            graph.add((right_uri, PROP.samePhaseAs, left_uri))

        if left.release_year == right.release_year:
            graph.add((left_uri, PROP.sameReleaseYearAs, right_uri))
            graph.add((right_uri, PROP.sameReleaseYearAs, left_uri))

        if left.release_year < right.release_year:
            graph.add((left_uri, PROP.releasedBefore, right_uri))
            graph.add((right_uri, PROP.releasedAfter, left_uri))
        else:
            graph.add((right_uri, PROP.releasedBefore, left_uri))
            graph.add((left_uri, PROP.releasedAfter, right_uri))

        if left.release_year // 10 == right.release_year // 10:
            graph.add((left_uri, PROP.filmSharesReleaseDecadeWith, right_uri))
            graph.add((right_uri, PROP.filmSharesReleaseDecadeWith, left_uri))

    # Sequential relation from the curated release chain.
    for film in FILMS:
        if film.previous_film:
            current = uri(film.title)
            previous = uri(film.previous_film)
            graph.add((previous, PROP.releasedBefore, current))
            graph.add((current, PROP.releasedAfter, previous))

    return graph


def run_expansion():
    graph = build_expanded_graph()
    EXPANDED_FILE.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(EXPANDED_FILE), format="nt")

    stats = (
        "KB Statistics\n"
        "=============\n"
        f"Triples:   {len(graph):,}\n"
        f"Entities:  {len(set(graph.subjects())):,}\n"
        f"Relations: {len(set(graph.predicates())):,}\n"
        f"File: {EXPANDED_FILE}\n"
    )
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(stats, encoding="utf-8")

    print(f"OK Expanded KB -> {EXPANDED_FILE}")
    print(stats)


if __name__ == "__main__":
    run_expansion()
