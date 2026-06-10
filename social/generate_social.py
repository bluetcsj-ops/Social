from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOCIAL = ROOT / "social"
DRAFTS = SOCIAL / "drafts"
IMAGES = SOCIAL / "images"
CALENDAR = SOCIAL / "calendar"
SITE_URL = "https://worldcup.bluet.cc"
BRAND = "worldcup.bluet.cc"


TEAMS = [
    "Brazil",
    "Argentina",
    "France",
    "England",
    "Spain",
    "Portugal",
    "Germany",
    "USA",
    "Mexico",
    "Japan",
]

PRIORITY_TEAMS = TEAMS

GROUP_TEAMS = ["Brazil", "Argentina", "USA", "Mexico", "England"]

TEAM_MEMORIES = {
    "Brazil": [
        "Ronaldo's 2002 redemption arc still makes Brazil predictions feel different.",
        "That 2002 front line is still the World Cup memory I compare every Brazil attack to.",
        "Neymar dragging Brazil through big tournament moments is hard to forget.",
    ],
    "Argentina": [
        "Messi's 2022 run changed the whole feeling around Argentina in knockout games.",
        "That Messi and Di Maria 2022 final link-up still feels unreal.",
        "After that 2022 final, Argentina have main-character energy in every bracket chat.",
    ],
    "France": [
        "Mbappe in the 2022 final is still one of the wildest individual World Cup performances.",
        "France's 2018 pace and 2022 resilience make them feel built for tournament football.",
        "When a team has recent memories of Mbappe deciding games, every bracket looks dangerous.",
    ],
    "England": [
        "England's recent semi-final and final near-misses make every prediction feel loaded.",
        "Kane's World Cup goals and England's 2018 run still hang over the next prediction.",
        "England always has that mix of huge talent and tournament tension.",
    ],
    "Spain": [
        "Spain's 2010 team is still the cleanest example of control winning a World Cup.",
        "Iniesta's 2010 final goal is the kind of memory that makes Spain predictions feel romantic.",
        "The 2010 possession machine still shapes how I think about Spain in knockout games.",
    ],
    "Portugal": [
        "Ronaldo has given Portugal so many tournament moments that they never feel ordinary.",
        "Ronaldo's 2018 hat trick against Spain is still peak World Cup drama.",
        "Portugal always feels one Bruno pass or one Leao run away from a highlight clip.",
    ],
    "Germany": [
        "Germany's 2014 title run is the reminder to never write them off too early.",
        "That 7-1 in 2014 still pops up anytime Germany enter a knockout conversation.",
        "Germany in 2014 is still the reference point for a team peaking at the perfect time.",
    ],
    "USA": [
        "Donovan's 2010 stoppage-time goal is still the USA World Cup memory that gives me chills.",
        "The USA has enough home-crowd energy in 2026 to make every group match feel bigger.",
        "Pulisic's 2022 goal against Iran showed how tense and emotional this team can make a World Cup.",
    ],
    "Mexico": [
        "Ochoa turning into a World Cup wall is basically a tournament tradition now.",
        "Mexico beating Germany in 2018 is still the kind of memory that makes dark-horse talk fun.",
        "Mexico's World Cup story always has noise, pressure, and one match that feels massive.",
    ],
    "Japan": [
        "Japan beating Germany and Spain in 2022 is exactly why nobody should treat them lightly.",
        "Japan's 2022 comeback energy made them one of the easiest teams to root for.",
        "That 2022 group-stage run gave Japan a proper dark-horse identity.",
    ],
}

GENERAL_MEMORIES = [
    "Messi in 2022, Mbappe in that final, and James Rodriguez in 2014 are why early predictions are so addictive.",
    "Every World Cup has one player who suddenly owns the timeline. That is the fun part of guessing early.",
    "The best World Cup debates start with one highlight everyone remembers, then spiral into bracket takes.",
    "Golden Boot guesses are dangerous because one hot group stage can rewrite the whole conversation.",
]

HASHTAGS = {
    "team_prediction": ["#WorldCup2026", "#Football"],
    "schedule": ["#WorldCup2026"],
    "poll": ["#WorldCup2026", "#Football"],
    "product_light": ["#WorldCup2026"],
}

BANNED_PHRASES = [
    "check out my amazing website",
    "best world cup site",
    "don't miss this",
    "dont miss this",
    "please share",
    "please upvote",
    "smash like",
    "go viral",
]


@dataclass(frozen=True)
class TeamCard:
    team: str
    champion_pick: str
    summary: str
    path: list[str]
    accent: tuple[int, int, int]
    deep: tuple[int, int, int]


CARDS = {
    "Brazil": TeamCard("Brazil", "Brazil", "Fast wingers, tournament swagger, and enough midfield control to go deep.", ["Group winner", "R16 vs runner-up", "QF classic", "SF heavyweight", "Final"], (24, 155, 75), (8, 82, 48)),
    "Argentina": TeamCard("Argentina", "Argentina", "Still feels built for knockout chaos if the midfield rhythm clicks.", ["Group winner", "R16 control", "QF tight one", "SF moment", "Final"], (92, 180, 230), (20, 85, 140)),
    "France": TeamCard("France", "France", "Scary depth, transition speed, and match-winners everywhere.", ["Group winner", "R16", "QF", "SF", "Final"], (35, 73, 161), (12, 31, 83)),
    "England": TeamCard("England", "England", "If the attack stays brave, this squad has a real path.", ["Group winner", "R16", "QF pressure test", "SF", "Final"], (210, 36, 48), (70, 24, 36)),
    "Spain": TeamCard("Spain", "Spain", "Possession with bite: young legs, sharp passing, big upside.", ["Group winner", "R16", "QF", "SF", "Final"], (198, 28, 46), (102, 20, 28)),
    "Portugal": TeamCard("Portugal", "Portugal", "A balanced squad with enough creators to punish any open game.", ["Group winner", "R16", "QF", "SF", "Final"], (0, 126, 68), (86, 20, 28)),
    "Germany": TeamCard("Germany", "Germany", "Never ignore Germany when a tournament bracket starts getting weird.", ["Group winner", "R16", "QF", "SF", "Final"], (245, 196, 0), (36, 36, 36)),
    "USA": TeamCard("USA", "USA dark-horse run", "Home crowd energy plus pace could make this a noisy bracket.", ["Group battle", "R16 upset", "QF test", "Statement run"], (44, 82, 160), (160, 30, 45)),
    "Mexico": TeamCard("Mexico", "Mexico quarter-final run", "Home-region energy and knockout grit make this one fun to track.", ["Group battle", "R16 edge", "QF dream"], (0, 104, 71), (190, 40, 48)),
    "Japan": TeamCard("Japan", "Japan dark horse", "Organized, technical, fearless against bigger names.", ["Group surprise", "R16 upset", "QF danger"], (190, 0, 45), (34, 45, 78)),
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def rounded_rect(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_flag(draw: ImageDraw.ImageDraw, team: str, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    draw.rounded_rectangle(box, radius=18, fill=(245, 245, 245))

    if team == "Brazil":
        draw.rounded_rectangle(box, radius=18, fill=(0, 155, 58))
        draw.polygon([(x1 + w / 2, y1 + 20), (x2 - 22, y1 + h / 2), (x1 + w / 2, y2 - 20), (x1 + 22, y1 + h / 2)], fill=(255, 223, 0))
        draw.ellipse((x1 + w / 2 - 42, y1 + h / 2 - 42, x1 + w / 2 + 42, y1 + h / 2 + 42), fill=(0, 39, 118))
    elif team == "Argentina":
        draw.rounded_rectangle(box, radius=18, fill=(116, 172, 223))
        draw.rectangle((x1, y1 + h / 3, x2, y1 + 2 * h / 3), fill=(255, 255, 255))
        draw.ellipse((x1 + w / 2 - 18, y1 + h / 2 - 18, x1 + w / 2 + 18, y1 + h / 2 + 18), fill=(246, 180, 14))
    elif team == "France":
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255))
        draw.rectangle((x1, y1, x1 + w / 3, y2), fill=(0, 35, 149))
        draw.rectangle((x1 + 2 * w / 3, y1, x2, y2), fill=(237, 41, 57))
    elif team == "England":
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255))
        draw.rectangle((x1 + w * 0.43, y1, x1 + w * 0.57, y2), fill=(200, 16, 46))
        draw.rectangle((x1, y1 + h * 0.40, x2, y1 + h * 0.60), fill=(200, 16, 46))
    elif team == "Spain":
        draw.rounded_rectangle(box, radius=18, fill=(198, 28, 46))
        draw.rectangle((x1, y1 + h * 0.25, x2, y1 + h * 0.75), fill=(255, 196, 0))
    elif team == "Portugal":
        draw.rounded_rectangle(box, radius=18, fill=(0, 102, 0))
        draw.rectangle((x1 + w * 0.42, y1, x2, y2), fill=(255, 0, 0))
        draw.ellipse((x1 + w * 0.42 - 24, y1 + h / 2 - 24, x1 + w * 0.42 + 24, y1 + h / 2 + 24), fill=(255, 215, 0))
    elif team == "Germany":
        draw.rounded_rectangle(box, radius=18, fill=(0, 0, 0))
        draw.rectangle((x1, y1 + h / 3, x2, y1 + 2 * h / 3), fill=(221, 0, 0))
        draw.rectangle((x1, y1 + 2 * h / 3, x2, y2), fill=(255, 206, 0))
    elif team == "USA":
        draw.rounded_rectangle(box, radius=18, fill=(178, 34, 52))
        stripe_h = h / 13
        for i in range(13):
            if i % 2:
                draw.rectangle((x1, y1 + i * stripe_h, x2, y1 + (i + 1) * stripe_h), fill=(255, 255, 255))
        draw.rectangle((x1, y1, x1 + w * 0.45, y1 + stripe_h * 7), fill=(60, 59, 110))
    elif team == "Mexico":
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255))
        draw.rectangle((x1, y1, x1 + w / 3, y2), fill=(0, 104, 71))
        draw.rectangle((x1 + 2 * w / 3, y1, x2, y2), fill=(206, 17, 38))
        draw.ellipse((x1 + w / 2 - 16, y1 + h / 2 - 16, x1 + w / 2 + 16, y1 + h / 2 + 16), outline=(128, 96, 32), width=5)
    elif team == "Japan":
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255))
        draw.ellipse((x1 + w / 2 - 44, y1 + h / 2 - 44, x1 + w / 2 + 44, y1 + h / 2 + 44), fill=(188, 0, 45))
    draw.rounded_rectangle(box, radius=18, outline=(255, 255, 255), width=3)


def fit_lines(text: str, max_chars: int) -> list[str]:
    return wrap(text, width=max_chars, break_long_words=False)


def draw_card(card: TeamCard, size: tuple[int, int], out: Path) -> None:
    w, h = size
    img = Image.new("RGB", size, (248, 249, 246))
    draw = ImageDraw.Draw(img)
    accent = card.accent
    deep = card.deep

    for y in range(h):
        ratio = y / max(1, h - 1)
        color = tuple(int((1 - ratio) * 250 + ratio * c) for c in (236, 239, 235))
        draw.line((0, y, w, y), fill=color)

    draw.rectangle((0, 0, w, 20), fill=accent)
    draw.rectangle((0, h - 22, w, h), fill=deep)
    draw.ellipse((w - 360, -180, w + 140, 320), fill=tuple(min(255, c + 40) for c in accent))

    margin = int(w * 0.07)
    title_font = font(56 if w > 1100 else 48, True)
    team_font = font(92 if w > 1100 else 72, True)
    label_font = font(27 if w > 1100 else 25, True)
    body_font = font(29 if w > 1100 else 27)
    small_font = font(24 if w > 1100 else 22, True)

    flag_w = int(w * 0.22)
    flag_h = int(flag_w * 0.62)
    draw_flag(draw, card.team, (margin, margin + 8, margin + flag_w, margin + 8 + flag_h))

    draw.text((margin + flag_w + 34, margin + 12), "My World Cup 2026 Prediction", font=title_font, fill=(24, 32, 40))
    draw.text((margin + flag_w + 36, margin + 88), card.team, font=team_font, fill=deep)

    box_y = margin + flag_h + (38 if h <= 700 else 70)
    rounded_rect(draw, (margin, box_y, w - margin, box_y + 150), 24, fill=(255, 255, 255), outline=(225, 229, 224), width=2)
    draw.text((margin + 34, box_y + 24), "Champion pick", font=label_font, fill=accent)
    draw.text((margin + 34, box_y + 68), card.champion_pick, font=font(46 if w > 1100 else 40, True), fill=(23, 28, 36))

    summary_y = box_y + (162 if h <= 700 else 180)
    summary_lines = fit_lines(card.summary, 88 if h <= 700 else 42)
    summary_limit = 1 if h <= 700 else 3
    summary_font = font(25 if h <= 700 else 29)
    for i, line in enumerate(summary_lines[:summary_limit]):
        draw.text((margin, summary_y + i * 38), line, font=summary_font, fill=(36, 44, 50))

    path_y = h - (130 if h <= 700 else 146)
    step_gap = (w - 2 * margin) / max(1, len(card.path) - 1)
    for i, step in enumerate(card.path):
        x = margin + i * step_gap
        draw.ellipse((x - 14, path_y - 14, x + 14, path_y + 14), fill=accent, outline=deep, width=3)
        if i < len(card.path) - 1:
            draw.line((x + 16, path_y, margin + (i + 1) * step_gap - 16, path_y), fill=(120, 130, 125), width=3)
        for j, line in enumerate(fit_lines(step, 12)[:2]):
            tw = draw.textlength(line, font=small_font)
            draw.text((x - tw / 2, path_y + 24 + j * 27), line, font=small_font, fill=(31, 38, 43))

    brand = f"{BRAND}  |  fan predictions, schedules, team pages"
    brand_w = draw.textlength(brand, font=small_font)
    draw.text((w - margin - brand_w, h - 52), brand, font=small_font, fill=(255, 255, 255))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def make_draft(platform: str, category: str, text: str, team: str | None = None, image: str | None = None) -> dict:
    item = {
        "platform": platform,
        "category": category,
        "team": team,
        "text": text,
        "image": image,
        "url": SITE_URL,
    }
    return {k: v for k, v in item.items() if v is not None}


def x_text(base: str, category: str) -> str:
    tags = HASHTAGS[category][:2]
    return f"{base} {' '.join(tags)}"


def team_memory(team: str, index: int = 0) -> str:
    memories = TEAM_MEMORIES[team]
    return memories[index % len(memories)]


def team_article(team: str) -> str:
    return "an" if team in {"Argentina", "England"} else "a"


def build_drafts() -> tuple[list[dict], list[dict], list[dict]]:
    x_posts: list[dict] = []
    fb_posts: list[dict] = []
    discord_posts: list[dict] = []

    team_templates = [
        "{memory} My way-too-early {team} 2026 take: if the vibe clicks, they can make noise.",
        "{team} bracket talk always starts with a clip in my head. {memory} How far are we taking them in 2026?",
        "Made a {team} prediction card and immediately started overthinking it. {memory} This is how the World Cup gets me every time.",
        "{team} fans, be real: what is the 2026 ceiling? {memory} I can talk myself into a run so fast.",
    ]
    for idx, team in enumerate(TEAMS):
        image = f"/social/images/{slug(team)}-prediction.png"
        text = x_text(team_templates[idx % len(team_templates)].format(team=team, memory=team_memory(team, idx)), "team_prediction")
        x_posts.append(make_draft("x", "team_prediction", text, team, image))

        fb = (
            f"I made {team_article(team)} {team} World Cup 2026 prediction card and now I am way too invested. "
            f"{team_memory(team, idx + 1)}\n\n"
            f"My question is simple: are they built for those ugly knockout matches, or just the fun open games? "
            f"Early call: {CARDS[team].champion_pick}. What are you changing?"
        )
        fb_posts.append(make_draft("facebook", "team_prediction", fb, team, image))

        discord = (
            f"{team} prediction thread idea: {team_memory(team, idx + 2)} "
            f"My gut says: {CARDS[team].summary} Card is here if anyone wants to argue the path: {SITE_URL}"
        )
        discord_posts.append(make_draft("discord", "team_prediction", discord, team, image))

    schedule_templates = [
        "{memory} So yeah, the {team} group-stage schedule is going straight into my calendar.",
        "{memory} That is why the {team} group path feels spicy from match one.",
        "I keep checking possible {team} kickoff times. {memory} Timezone pain is part of the World Cup package.",
        "{team} group-stage watch plan: clear the calendar, then remember {memory_lc}",
        "If {team} start hot in the group, I am instantly changing my bracket. {memory}",
    ]
    for idx, team in enumerate(GROUP_TEAMS):
        memory = team_memory(team, idx + 1)
        text = x_text(schedule_templates[idx].format(team=team, memory=memory, memory_lc=memory[0].lower() + memory[1:]), "schedule")
        x_posts.append(make_draft("x", "schedule", text, team))

        fb_posts.append(
            make_draft(
                "facebook",
                "schedule",
                f"Has anyone started planning around the {team} group-stage schedule yet? {team_memory(team, idx + 2)}\n\n"
                f"I like having fixtures, local time, and team notes in one place before the tournament starts. Which group match are you circling first?",
                team,
            )
        )
        discord_posts.append(
            make_draft(
                "discord",
                "schedule",
                f"{team} group-stage schedule is one I want to track early. {team_memory(team, idx)} Which match feels like the swing game?",
                team,
            )
        )

    polls = [
        "Brazil 2002, Spain 2010, Germany 2014, Argentina 2022: which champion style feels most likely to work in 2026?",
        "Who is your early World Cup 2026 dark horse? Japan's 2022 run is still the blueprint for me.",
        "Which group would be the most fun: pure chaos, one giant favorite, or four teams with Mexico-vs-Germany-2018 energy?",
        "Early Golden Boot pick? Mbappe's 2022 final still makes me afraid to pick against him.",
        "Who has the better 2026 setup right now: France depth, Brazil flair, Argentina control, or Spain tempo?",
        "Most annoying team to face in a World Cup: elite attack, locked-in defense, or a fearless underdog like Japan in 2022?",
        "If one host team makes a big run in 2026, is it USA home energy, Mexico tournament noise, or Canada surprise factor?",
        "Which 2026 final has the best storyline: Argentina aura, Mbappe's France, Brazil chasing magic, or England stress levels?",
    ]
    for text in polls:
        x_posts.append(make_draft("x", "poll", x_text(text, "poll")))
        discord_posts.append(make_draft("discord", "poll", text))

    product_light = [
        "Got excited for World Cup 2026 and started building a small fan hub in my spare time. Mostly schedules, team pages, predictions, and little games for matchday brain.",
        "Trying to make following the World Cup a little more fun: localized schedules, team guides, prediction cards, and fan games. Keeping it casual.",
        "I built a tiny World Cup 2026 hub because I wanted one place for fixtures, teams, and prediction messing around.",
        "World Cup planning mode has started way too early for me, so I made a fan hub to track teams and predictions without making it feel like homework.",
        "Working on a World Cup 2026 fan site for people who love brackets, fixtures, and arguing about dark horses before the draw even behaves.",
        "Spent the weekend polishing a little World Cup 2026 fan hub. The goal is simple: schedules, team pages, predictions, and fun matchday stuff.",
        "I wanted a cleaner way to follow World Cup 2026 in local time, so I started building one. Still fan-made, still very much powered by tournament excitement.",
    ]
    for text in product_light:
        x_posts.append(make_draft("x", "product_light", x_text(text, "product_light")))

    for i, text in enumerate(product_light[:5]):
        fb_posts.append(
            make_draft(
                "facebook",
                "product_light",
                f"{text}\n\nI am keeping it fan-focused: schedules, team pages, predictions, and simple games rather than anything too serious. Feedback from football people would genuinely help.",
            )
        )
        discord_posts.append(make_draft("discord", "product_light", f"{text} {SITE_URL}"))

    return x_posts, fb_posts, discord_posts


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def validate(drafts: list[dict]) -> None:
    seen = set()
    for item in drafts:
        text = item["text"]
        normalized = normalize_text(text)
        if normalized in seen:
            raise ValueError(f"Duplicate draft found: {text}")
        seen.add(normalized)

        lower = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lower:
                raise ValueError(f"Banned phrase found: {phrase}")

        if item["platform"] == "x":
            tags = re.findall(r"#\w+", text)
            if len(tags) > 2:
                raise ValueError(f"Too many X hashtags: {text}")
            if len(text) > 280:
                raise ValueError(f"X post over 280 chars: {len(text)} {text}")


def make_calendar(x_posts: list[dict]) -> list[dict]:
    start = date.today()
    categories = {
        "prediction": [p for p in x_posts if p["category"] == "team_prediction"],
        "discussion": [p for p in x_posts if p["category"] in {"poll", "schedule"}],
        "website": [p for p in x_posts if p["category"] == "product_light"],
    }
    calendar = []
    used_ids = set()

    for day in range(30):
        current = start + timedelta(days=day)
        if day % 7 == 0:
            bucket = categories["prediction"]
            rhythm = "prediction/share-card post"
        elif day % 7 in {2, 5}:
            bucket = categories["discussion"]
            rhythm = "football discussion post"
        elif day % 7 == 4:
            bucket = categories["website"]
            rhythm = "website-related post"
        else:
            bucket = x_posts
            rhythm = "daily X post"

        pick = next((p for p in bucket if id(p) not in used_ids), bucket[day % len(bucket)])
        used_ids.add(id(pick))
        calendar.append(
            {
                "date": current.isoformat(),
                "platform": "x",
                "rhythm": rhythm,
                "category": pick["category"],
                "team": pick.get("team"),
                "text": pick["text"],
                "image": pick.get("image"),
                "url": SITE_URL,
            }
        )
    return calendar


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_dashboard_data(x_posts: list[dict], fb_posts: list[dict], discord_posts: list[dict]) -> None:
    payload = json.dumps([x_posts, fb_posts, discord_posts], indent=2, ensure_ascii=False)
    (SOCIAL / "social-dashboard-data.js").write_text(
        f"window.SOCIAL_DASHBOARD_DRAFTS = {payload};\n",
        encoding="utf-8",
    )


def main() -> None:
    for team in PRIORITY_TEAMS:
        card = CARDS[team]
        draw_card(card, (1200, 630), IMAGES / f"{slug(team)}-prediction.png")
        draw_card(card, (1080, 1350), IMAGES / f"{slug(team)}-prediction-story.png")

    x_posts, fb_posts, discord_posts = build_drafts()
    all_drafts = x_posts + fb_posts + discord_posts
    validate(all_drafts)

    write_json(DRAFTS / "x-posts.json", x_posts)
    write_json(DRAFTS / "facebook-posts.json", fb_posts)
    write_json(DRAFTS / "discord-posts.json", discord_posts)
    write_json(CALENDAR / "30-day-calendar.json", make_calendar(x_posts))
    write_dashboard_data(x_posts, fb_posts, discord_posts)
    print(f"Generated {len(x_posts)} X drafts, {len(fb_posts)} Facebook drafts, {len(discord_posts)} Discord drafts.")
    print(f"Generated {len(PRIORITY_TEAMS) * 2} share images in {IMAGES}.")


if __name__ == "__main__":
    main()
