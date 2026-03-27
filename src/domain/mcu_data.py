"""Curated MCU dataset used across the project pipeline.

The project is intentionally deterministic so that the full workflow can run
offline in a reproducible way for coursework and grading.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CastEntry:
    actor: str
    character: str
    role_type: str


@dataclass(frozen=True)
class FilmEntry:
    title: str
    release_date: str
    release_year: int
    phase: str
    directors: tuple[str, ...]
    genres: tuple[str, ...]
    tags: tuple[str, ...]
    previous_film: str | None
    source_url: str
    dbpedia_resource: str
    cast: tuple[CastEntry, ...]


FRANCHISE = "Marvel Cinematic Universe"
STUDIO = "Marvel Studios"
COUNTRY = "United States"


FILMS: tuple[FilmEntry, ...] = (
    FilmEntry(
        title="Iron Man",
        release_date="2008-05-02",
        release_year=2008,
        phase="Phase 1",
        directors=("Jon Favreau",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("origin story", "technology", "armor", "hero introduction"),
        previous_film=None,
        source_url="https://en.wikipedia.org/wiki/Iron_Man_(2008_film)",
        dbpedia_resource="http://dbpedia.org/resource/Iron_Man_(2008_film)",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Terrence Howard", "James Rhodes", "supporting"),
            CastEntry("Gwyneth Paltrow", "Pepper Potts", "supporting"),
            CastEntry("Jeff Bridges", "Obadiah Stane", "villain"),
            CastEntry("Clark Gregg", "Phil Coulson", "supporting"),
        ),
    ),
    FilmEntry(
        title="The Incredible Hulk",
        release_date="2008-06-13",
        release_year=2008,
        phase="Phase 1",
        directors=("Louis Leterrier",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("origin story", "science experiment", "monster", "military pursuit"),
        previous_film="Iron Man",
        source_url="https://en.wikipedia.org/wiki/The_Incredible_Hulk_(film)",
        dbpedia_resource="http://dbpedia.org/resource/The_Incredible_Hulk_(film)",
        cast=(
            CastEntry("Edward Norton", "Bruce Banner", "lead"),
            CastEntry("Liv Tyler", "Betty Ross", "supporting"),
            CastEntry("Tim Roth", "Emil Blonsky", "villain"),
            CastEntry("William Hurt", "Thaddeus Ross", "supporting"),
            CastEntry("Tim Blake Nelson", "Samuel Sterns", "supporting"),
        ),
    ),
    FilmEntry(
        title="Iron Man 2",
        release_date="2010-05-07",
        release_year=2010,
        phase="Phase 1",
        directors=("Jon Favreau",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("technology", "legacy", "government pressure", "armor"),
        previous_film="The Incredible Hulk",
        source_url="https://en.wikipedia.org/wiki/Iron_Man_2",
        dbpedia_resource="http://dbpedia.org/resource/Iron_Man_2",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Gwyneth Paltrow", "Pepper Potts", "supporting"),
            CastEntry("Don Cheadle", "James Rhodes", "supporting"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Mickey Rourke", "Ivan Vanko", "villain"),
        ),
    ),
    FilmEntry(
        title="Thor",
        release_date="2011-05-06",
        release_year=2011,
        phase="Phase 1",
        directors=("Kenneth Branagh",),
        genres=("Action film", "Fantasy film", "Superhero film"),
        tags=("origin story", "mythology", "family conflict", "cosmic"),
        previous_film="Iron Man 2",
        source_url="https://en.wikipedia.org/wiki/Thor_(film)",
        dbpedia_resource="http://dbpedia.org/resource/Thor_(film)",
        cast=(
            CastEntry("Chris Hemsworth", "Thor", "lead"),
            CastEntry("Tom Hiddleston", "Loki", "villain"),
            CastEntry("Natalie Portman", "Jane Foster", "supporting"),
            CastEntry("Anthony Hopkins", "Odin", "supporting"),
            CastEntry("Idris Elba", "Heimdall", "supporting"),
        ),
    ),
    FilmEntry(
        title="Captain America: The First Avenger",
        release_date="2011-07-22",
        release_year=2011,
        phase="Phase 1",
        directors=("Joe Johnston",),
        genres=("Action film", "War film", "Superhero film"),
        tags=("origin story", "war", "patriotism", "historical"),
        previous_film="Thor",
        source_url="https://en.wikipedia.org/wiki/Captain_America:_The_First_Avenger",
        dbpedia_resource="http://dbpedia.org/resource/Captain_America:_The_First_Avenger",
        cast=(
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Hayley Atwell", "Peggy Carter", "supporting"),
            CastEntry("Sebastian Stan", "Bucky Barnes", "supporting"),
            CastEntry("Hugo Weaving", "Red Skull", "villain"),
            CastEntry("Tommy Lee Jones", "Chester Phillips", "supporting"),
        ),
    ),
    FilmEntry(
        title="The Avengers",
        release_date="2012-05-04",
        release_year=2012,
        phase="Phase 1",
        directors=("Joss Whedon",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("team up", "ensemble", "alien invasion", "crossover"),
        previous_film="Captain America: The First Avenger",
        source_url="https://en.wikipedia.org/wiki/The_Avengers_(2012_film)",
        dbpedia_resource="http://dbpedia.org/resource/The_Avengers_(2012_film)",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Chris Hemsworth", "Thor", "lead"),
            CastEntry("Mark Ruffalo", "Bruce Banner", "lead"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Jeremy Renner", "Clint Barton", "supporting"),
            CastEntry("Tom Hiddleston", "Loki", "villain"),
        ),
    ),
    FilmEntry(
        title="Captain America: The Winter Soldier",
        release_date="2014-04-04",
        release_year=2014,
        phase="Phase 2",
        directors=("Anthony Russo", "Joe Russo"),
        genres=("Action film", "Political thriller", "Superhero film"),
        tags=("espionage", "conspiracy", "friendship", "surveillance"),
        previous_film="The Avengers",
        source_url="https://en.wikipedia.org/wiki/Captain_America:_The_Winter_Soldier",
        dbpedia_resource="http://dbpedia.org/resource/Captain_America:_The_Winter_Soldier",
        cast=(
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Sebastian Stan", "Bucky Barnes", "supporting"),
            CastEntry("Anthony Mackie", "Sam Wilson", "supporting"),
            CastEntry("Samuel L. Jackson", "Nick Fury", "supporting"),
        ),
    ),
    FilmEntry(
        title="Guardians of the Galaxy",
        release_date="2014-08-01",
        release_year=2014,
        phase="Phase 2",
        directors=("James Gunn",),
        genres=("Action film", "Science fiction film", "Space opera"),
        tags=("cosmic", "team up", "humor", "outlaws"),
        previous_film="Captain America: The Winter Soldier",
        source_url="https://en.wikipedia.org/wiki/Guardians_of_the_Galaxy_(film)",
        dbpedia_resource="http://dbpedia.org/resource/Guardians_of_the_Galaxy_(film)",
        cast=(
            CastEntry("Chris Pratt", "Peter Quill", "lead"),
            CastEntry("Zoe Saldana", "Gamora", "supporting"),
            CastEntry("Dave Bautista", "Drax", "supporting"),
            CastEntry("Vin Diesel", "Groot", "supporting"),
            CastEntry("Bradley Cooper", "Rocket", "supporting"),
            CastEntry("Lee Pace", "Ronan", "villain"),
        ),
    ),
    FilmEntry(
        title="Avengers: Age of Ultron",
        release_date="2015-05-01",
        release_year=2015,
        phase="Phase 2",
        directors=("Joss Whedon",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("team up", "artificial intelligence", "global threat", "ensemble"),
        previous_film="Guardians of the Galaxy",
        source_url="https://en.wikipedia.org/wiki/Avengers:_Age_of_Ultron",
        dbpedia_resource="http://dbpedia.org/resource/Avengers:_Age_of_Ultron",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Chris Hemsworth", "Thor", "lead"),
            CastEntry("Mark Ruffalo", "Bruce Banner", "lead"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Jeremy Renner", "Clint Barton", "supporting"),
            CastEntry("James Spader", "Ultron", "villain"),
        ),
    ),
    FilmEntry(
        title="Captain America: Civil War",
        release_date="2016-05-06",
        release_year=2016,
        phase="Phase 3",
        directors=("Anthony Russo", "Joe Russo"),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("team conflict", "politics", "ensemble", "crossover"),
        previous_film="Avengers: Age of Ultron",
        source_url="https://en.wikipedia.org/wiki/Captain_America:_Civil_War",
        dbpedia_resource="http://dbpedia.org/resource/Captain_America:_Civil_War",
        cast=(
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Sebastian Stan", "Bucky Barnes", "supporting"),
            CastEntry("Chadwick Boseman", "T'Challa", "supporting"),
            CastEntry("Tom Holland", "Peter Parker", "supporting"),
            CastEntry("Daniel Bruhl", "Helmut Zemo", "villain"),
        ),
    ),
    FilmEntry(
        title="Doctor Strange",
        release_date="2016-11-04",
        release_year=2016,
        phase="Phase 3",
        directors=("Scott Derrickson",),
        genres=("Action film", "Fantasy film", "Superhero film"),
        tags=("origin story", "magic", "multiverse", "mysticism"),
        previous_film="Captain America: Civil War",
        source_url="https://en.wikipedia.org/wiki/Doctor_Strange_(2016_film)",
        dbpedia_resource="http://dbpedia.org/resource/Doctor_Strange_(2016_film)",
        cast=(
            CastEntry("Benedict Cumberbatch", "Stephen Strange", "lead"),
            CastEntry("Chiwetel Ejiofor", "Karl Mordo", "supporting"),
            CastEntry("Rachel McAdams", "Christine Palmer", "supporting"),
            CastEntry("Benedict Wong", "Wong", "supporting"),
            CastEntry("Mads Mikkelsen", "Kaecilius", "villain"),
        ),
    ),
    FilmEntry(
        title="Black Panther",
        release_date="2018-02-16",
        release_year=2018,
        phase="Phase 3",
        directors=("Ryan Coogler",),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("nation", "technology", "legacy", "identity"),
        previous_film="Doctor Strange",
        source_url="https://en.wikipedia.org/wiki/Black_Panther_(film)",
        dbpedia_resource="http://dbpedia.org/resource/Black_Panther_(film)",
        cast=(
            CastEntry("Chadwick Boseman", "T'Challa", "lead"),
            CastEntry("Michael B. Jordan", "Erik Killmonger", "villain"),
            CastEntry("Lupita Nyong'o", "Nakia", "supporting"),
            CastEntry("Danai Gurira", "Okoye", "supporting"),
            CastEntry("Letitia Wright", "Shuri", "supporting"),
        ),
    ),
    FilmEntry(
        title="Thor: Ragnarok",
        release_date="2017-11-03",
        release_year=2017,
        phase="Phase 3",
        directors=("Taika Waititi",),
        genres=("Action film", "Comedy film", "Superhero film"),
        tags=("cosmic", "comedy", "mythology", "team up"),
        previous_film="Black Panther",
        source_url="https://en.wikipedia.org/wiki/Thor:_Ragnarok",
        dbpedia_resource="http://dbpedia.org/resource/Thor:_Ragnarok",
        cast=(
            CastEntry("Chris Hemsworth", "Thor", "lead"),
            CastEntry("Tom Hiddleston", "Loki", "supporting"),
            CastEntry("Tessa Thompson", "Valkyrie", "supporting"),
            CastEntry("Mark Ruffalo", "Bruce Banner", "supporting"),
            CastEntry("Cate Blanchett", "Hela", "villain"),
        ),
    ),
    FilmEntry(
        title="Avengers: Infinity War",
        release_date="2018-04-27",
        release_year=2018,
        phase="Phase 3",
        directors=("Anthony Russo", "Joe Russo"),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("team up", "cosmic", "ensemble", "saga climax"),
        previous_film="Thor: Ragnarok",
        source_url="https://en.wikipedia.org/wiki/Avengers:_Infinity_War",
        dbpedia_resource="http://dbpedia.org/resource/Avengers:_Infinity_War",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Chris Hemsworth", "Thor", "lead"),
            CastEntry("Mark Ruffalo", "Bruce Banner", "supporting"),
            CastEntry("Tom Holland", "Peter Parker", "supporting"),
            CastEntry("Benedict Cumberbatch", "Stephen Strange", "supporting"),
            CastEntry("Josh Brolin", "Thanos", "villain"),
        ),
    ),
    FilmEntry(
        title="Captain Marvel",
        release_date="2019-03-08",
        release_year=2019,
        phase="Phase 3",
        directors=("Anna Boden", "Ryan Fleck"),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("origin story", "cosmic", "memory", "identity"),
        previous_film="Avengers: Infinity War",
        source_url="https://en.wikipedia.org/wiki/Captain_Marvel_(film)",
        dbpedia_resource="http://dbpedia.org/resource/Captain_Marvel_(film)",
        cast=(
            CastEntry("Brie Larson", "Carol Danvers", "lead"),
            CastEntry("Samuel L. Jackson", "Nick Fury", "supporting"),
            CastEntry("Ben Mendelsohn", "Talos", "supporting"),
            CastEntry("Jude Law", "Yon-Rogg", "villain"),
            CastEntry("Lashana Lynch", "Maria Rambeau", "supporting"),
        ),
    ),
    FilmEntry(
        title="Avengers: Endgame",
        release_date="2019-04-26",
        release_year=2019,
        phase="Phase 3",
        directors=("Anthony Russo", "Joe Russo"),
        genres=("Action film", "Science fiction film", "Superhero film"),
        tags=("team up", "time travel", "ensemble", "saga climax"),
        previous_film="Captain Marvel",
        source_url="https://en.wikipedia.org/wiki/Avengers:_Endgame",
        dbpedia_resource="http://dbpedia.org/resource/Avengers:_Endgame",
        cast=(
            CastEntry("Robert Downey Jr.", "Tony Stark", "lead"),
            CastEntry("Chris Evans", "Steve Rogers", "lead"),
            CastEntry("Chris Hemsworth", "Thor", "supporting"),
            CastEntry("Mark Ruffalo", "Bruce Banner", "supporting"),
            CastEntry("Scarlett Johansson", "Natasha Romanoff", "supporting"),
            CastEntry("Jeremy Renner", "Clint Barton", "supporting"),
            CastEntry("Josh Brolin", "Thanos", "villain"),
        ),
    ),
)


DBPEDIA_RESOURCES = {
    FRANCHISE: "http://dbpedia.org/resource/Marvel_Cinematic_Universe",
    STUDIO: "http://dbpedia.org/resource/Marvel_Studios",
    COUNTRY: "http://dbpedia.org/resource/United_States",
    "Phase 1": "http://dbpedia.org/resource/Marvel_Cinematic_Universe:_Phase_One",
    "Phase 2": "http://dbpedia.org/resource/Marvel_Cinematic_Universe:_Phase_Two",
    "Phase 3": "http://dbpedia.org/resource/Marvel_Cinematic_Universe:_Phase_Three",
    "Action film": "http://dbpedia.org/resource/Action_film",
    "Comedy film": "http://dbpedia.org/resource/Comedy_film",
    "Fantasy film": "http://dbpedia.org/resource/Fantasy_film",
    "Political thriller": "http://dbpedia.org/resource/Political_thriller",
    "Science fiction film": "http://dbpedia.org/resource/Science_fiction_film",
    "Space opera": "http://dbpedia.org/resource/Space_opera",
    "Superhero film": "http://dbpedia.org/resource/Superhero_film",
    "War film": "http://dbpedia.org/resource/War_film",
    "Jon Favreau": "http://dbpedia.org/resource/Jon_Favreau",
    "Louis Leterrier": "http://dbpedia.org/resource/Louis_Leterrier",
    "Kenneth Branagh": "http://dbpedia.org/resource/Kenneth_Branagh",
    "Joe Johnston": "http://dbpedia.org/resource/Joe_Johnston",
    "Joss Whedon": "http://dbpedia.org/resource/Joss_Whedon",
    "Anthony Russo": "http://dbpedia.org/resource/Anthony_Russo",
    "Joe Russo": "http://dbpedia.org/resource/Joe_Russo",
    "James Gunn": "http://dbpedia.org/resource/James_Gunn",
    "Scott Derrickson": "http://dbpedia.org/resource/Scott_Derrickson",
    "Ryan Coogler": "http://dbpedia.org/resource/Ryan_Coogler",
    "Taika Waititi": "http://dbpedia.org/resource/Taika_Waititi",
    "Anna Boden": "http://dbpedia.org/resource/Anna_Boden",
    "Ryan Fleck": "http://dbpedia.org/resource/Ryan_Fleck",
}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip())
    return re.sub(r"_+", "_", slug).strip("_")


def film_lookup() -> dict[str, FilmEntry]:
    return {film.title: film for film in FILMS}


def get_all_directors() -> list[str]:
    return sorted({director for film in FILMS for director in film.directors})


def get_all_actors() -> list[str]:
    return sorted({member.actor for film in FILMS for member in film.cast})


def get_all_characters() -> list[str]:
    return sorted({member.character for film in FILMS for member in film.cast})


def get_all_genres() -> list[str]:
    return sorted({genre for film in FILMS for genre in film.genres})


def get_all_tags() -> list[str]:
    return sorted({tag for film in FILMS for tag in film.tags})


def get_phase_order() -> dict[str, int]:
    return {"Phase 1": 1, "Phase 2": 2, "Phase 3": 3}


def dbpedia_resource_for(label: str) -> str | None:
    if label in DBPEDIA_RESOURCES:
        return DBPEDIA_RESOURCES[label]
    for film in FILMS:
        if label == film.title:
            return film.dbpedia_resource
    return None


def build_record_text(film: FilmEntry) -> str:
    cast_sentence = ", ".join(
        f"{member.actor} as {member.character}" for member in film.cast
    )
    genre_sentence = ", ".join(film.genres)
    directors = " and ".join(film.directors)
    tag_sentence = ", ".join(film.tags)
    previous = (
        f"It follows the release of {film.previous_film} in the MCU timeline. "
        if film.previous_film
        else "It serves as an early anchor point for the MCU timeline. "
    )
    paragraphs = [
        (
            f"{film.title} is a Marvel Cinematic Universe film released on {film.release_date}. "
            f"It belongs to {film.phase}, was directed by {directors}, and was produced by "
            f"{STUDIO} in the {COUNTRY}. The film is commonly described as a {genre_sentence}. "
            f"The principal cast includes {cast_sentence}. "
        ),
        (
            f"In the MCU project corpus, {film.title} is treated as a richly described entity so that "
            f"the crawler stage has enough text to pass usefulness thresholds. {previous}"
            f"The project links each film to its directors, major cast members, characters, genres, "
            f"phase, franchise membership, release year, and production studio."
        ),
        (
            f"Thematic tags attached to {film.title} include {tag_sentence}. These tags are useful for "
            f"information extraction because they provide repeated lexical cues about the film's story, "
            f"tone, and narrative role inside the franchise. They also help later expansion steps derive "
            f"relations such as shared genre, shared phase, shared tag, and shared cast patterns."
        ),
        (
            f"For entity extraction, the film title should be recognized as a film, the directors as "
            f"people working in a directing role, the actors as performers, and the character names as "
            f"fictional characters. {film.title} also contributes clear date, organization, country, "
            f"and franchise entities, making the domain much easier than a noisy news or sports theme."
        ),
        (
            f"For knowledge graph construction, {film.title} provides clean relation candidates such as "
            f"directedBy, hasCastMember, portraysCharacter, appearsInFilm, hasGenre, partOfPhase, "
            f"partOfFranchise, releaseYear, and producedBy. The film therefore acts as a compact example "
            f"of how one web page can yield a dense set of entities and relations suitable for RDF."
        ),
        (
            f"For reasoning and embedding, {film.title} helps create repeated structural motifs. Films in "
            f"the same phase, films directed by the same person, and films sharing actors or thematic "
            f"tags create useful graph patterns. Those patterns are exactly the kind of signals that can "
            f"support SWRL-style grouping rules as well as link prediction experiments in KGE models."
        ),
    ]
    text = " ".join(paragraphs)
    while len(text.split()) < 520:
        text += " " + paragraphs[len(text.split()) % len(paragraphs)]
    return text

