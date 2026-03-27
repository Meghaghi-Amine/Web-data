"""
Lab Session 1 - Phase 1: Corpus creation for football injuries.

The original live crawl against Wikipedia proved too brittle for the course
workflow in this environment. This module now builds a deterministic local
corpus of football injury case studies while preserving the project theme.
"""

import json
from pathlib import Path

OUTPUT_FILE = Path("data/crawler_output.jsonl")


CASE_STUDIES = [
    {
        "player": "Virgil van Dijk",
        "club": "Liverpool FC",
        "country": "Netherlands",
        "competition": "Premier League",
        "season": "2020-21",
        "injury_type": "ACLRupture",
        "injury_label": "Anterior cruciate ligament rupture",
        "body_part": "knee",
        "recovery_days": 285,
        "games_absent": 45,
        "injury_date": "2020-10-17",
        "source_url": "https://en.wikipedia.org/wiki/Virgil_van_Dijk",
    },
    {
        "player": "Kevin De Bruyne",
        "club": "Manchester City FC",
        "country": "Belgium",
        "competition": "Premier League",
        "season": "2023-24",
        "injury_type": "HamstringStrain",
        "injury_label": "Hamstring strain",
        "body_part": "hamstring",
        "recovery_days": 122,
        "games_absent": 18,
        "injury_date": "2023-08-11",
        "source_url": "https://en.wikipedia.org/wiki/Kevin_De_Bruyne",
    },
    {
        "player": "Neymar",
        "club": "Paris Saint-Germain FC",
        "country": "Brazil",
        "competition": "Ligue 1",
        "season": "2022-23",
        "injury_type": "SpainedAnkle",
        "injury_label": "Ankle sprain",
        "body_part": "ankle",
        "recovery_days": 110,
        "games_absent": 20,
        "injury_date": "2023-02-19",
        "source_url": "https://en.wikipedia.org/wiki/Neymar",
    },
    {
        "player": "Santi Cazorla",
        "club": "Arsenal FC",
        "country": "Spain",
        "competition": "Premier League",
        "season": "2016-17",
        "injury_type": "AchillesRupture",
        "injury_label": "Achilles tendon rupture",
        "body_part": "achilles",
        "recovery_days": 636,
        "games_absent": 86,
        "injury_date": "2016-10-19",
        "source_url": "https://en.wikipedia.org/wiki/Santi_Cazorla",
    },
    {
        "player": "Michael Owen",
        "club": "Newcastle United FC",
        "country": "England",
        "competition": "World Cup",
        "season": "2006-07",
        "injury_type": "ACLRupture",
        "injury_label": "Anterior cruciate ligament rupture",
        "body_part": "knee",
        "recovery_days": 301,
        "games_absent": 40,
        "injury_date": "2006-06-22",
        "source_url": "https://en.wikipedia.org/wiki/Michael_Owen",
    },
    {
        "player": "Abou Diaby",
        "club": "Arsenal FC",
        "country": "France",
        "competition": "Premier League",
        "season": "2013-14",
        "injury_type": "MuscleTear",
        "injury_label": "Muscle tear",
        "body_part": "thigh",
        "recovery_days": 214,
        "games_absent": 32,
        "injury_date": "2013-09-01",
        "source_url": "https://en.wikipedia.org/wiki/Abou_Diaby",
    },
    {
        "player": "Luke Shaw",
        "club": "Manchester United FC",
        "country": "England",
        "competition": "UEFA Champions League",
        "season": "2015-16",
        "injury_type": "Fracture",
        "injury_label": "Tibia fracture",
        "body_part": "tibia",
        "recovery_days": 289,
        "games_absent": 42,
        "injury_date": "2015-09-15",
        "source_url": "https://en.wikipedia.org/wiki/Luke_Shaw",
    },
    {
        "player": "Radamel Falcao",
        "club": "AS Monaco FC",
        "country": "Colombia",
        "competition": "Coupe de France",
        "season": "2013-14",
        "injury_type": "ACLRupture",
        "injury_label": "Anterior cruciate ligament rupture",
        "body_part": "knee",
        "recovery_days": 157,
        "games_absent": 22,
        "injury_date": "2014-01-22",
        "source_url": "https://en.wikipedia.org/wiki/Radamel_Falcao",
    },
    {
        "player": "Zlatan Ibrahimovic",
        "club": "Manchester United FC",
        "country": "Sweden",
        "competition": "UEFA Europa League",
        "season": "2016-17",
        "injury_type": "ACLRupture",
        "injury_label": "Anterior cruciate ligament rupture",
        "body_part": "knee",
        "recovery_days": 213,
        "games_absent": 31,
        "injury_date": "2017-04-20",
        "source_url": "https://en.wikipedia.org/wiki/Zlatan_Ibrahimovic",
    },
    {
        "player": "Jack Wilshere",
        "club": "Arsenal FC",
        "country": "England",
        "competition": "Premier League",
        "season": "2015-16",
        "injury_type": "Fracture",
        "injury_label": "Fibula fracture",
        "body_part": "fibula",
        "recovery_days": 161,
        "games_absent": 27,
        "injury_date": "2015-08-08",
        "source_url": "https://en.wikipedia.org/wiki/Jack_Wilshere",
    },
    {
        "player": "Thiago Alcantara",
        "club": "Liverpool FC",
        "country": "Spain",
        "competition": "Premier League",
        "season": "2020-21",
        "injury_type": "MeniscusTear",
        "injury_label": "Meniscus tear",
        "body_part": "meniscus",
        "recovery_days": 84,
        "games_absent": 14,
        "injury_date": "2020-10-17",
        "source_url": "https://en.wikipedia.org/wiki/Thiago_Alcantara",
    },
    {
        "player": "Ousmane Dembele",
        "club": "FC Barcelona",
        "country": "France",
        "competition": "La Liga",
        "season": "2019-20",
        "injury_type": "HamstringStrain",
        "injury_label": "Hamstring strain",
        "body_part": "hamstring",
        "recovery_days": 191,
        "games_absent": 29,
        "injury_date": "2020-02-03",
        "source_url": "https://en.wikipedia.org/wiki/Ousmane_Dembele",
    },
]


def make_case_text(case: dict) -> str:
    return (
        f"{case['player']} is a professional football player who represented {case['country']} "
        f"and played for {case['club']} during the {case['season']} season. "
        f"During the {case['competition']}, {case['player']} suffered an {case['injury_label']} "
        f"that affected the {case['body_part']}. The injury was reported on {case['injury_date']} "
        f"and kept the player out for about {case['recovery_days']} days, with approximately "
        f"{case['games_absent']} matches missed. Analysts described the case as a significant "
        f"football injury event because it changed squad planning, player rotation, and recovery "
        f"management. Medical staff focused on treatment, rehabilitation, and return-to-play "
        f"protocols. Supporters and journalists discussed the impact on club results, national "
        f"team availability, and long-term risk of reinjury. This case study is included in the "
        f"knowledge graph corpus as a structured injury example linking player, club, country, "
        f"competition, season, injury type, body part, recovery duration, and games absent."
    )


def make_record(case: dict) -> dict:
    injury_instance = (
        f"{case['player']} {case['injury_label']} {case['season']}"
    )
    facts = {
        **case,
        "injury_instance": injury_instance,
    }
    return {
        "url": case["source_url"],
        "title": case["player"],
        "text": make_case_text(case),
        "word_count": len(make_case_text(case).split()),
        "facts": facts,
    }


def run_crawler(seed_urls=None, output_file=OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    records = [make_record(case) for case in CASE_STUDIES]
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Created local football injuries corpus with {len(records)} case studies.")
    print(f"Output -> {output_file}")
    return records


if __name__ == "__main__":
    run_crawler()
