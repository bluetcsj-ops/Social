from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
except ImportError:  # QR support is optional.
    qrcode = None


ROOT = Path(__file__).resolve().parents[1]
SOCIAL = ROOT / "social"
DRAFTS = SOCIAL / "drafts"
IMAGES = SOCIAL / "images"
REAL_PLAYER_ASSETS = SOCIAL / "real-player-assets"
CALENDAR = SOCIAL / "calendar"
SITE_URL = "https://worldcup.bluet.cc"
BRAND = "worldcup.bluet.cc"
FOOTER_BRAND = "World Cup 2026 Fan Hub"

# Real player portraits must come from licensed/source-approved assets in
# social/real-player-assets. This generator intentionally does not synthesize
# fake player faces, because football fans notice and it hurts trust.


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

GOLDEN_BOOT_PICKS = {
    "Brazil": "Vinicius Jr",
    "Argentina": "Julian Alvarez",
    "France": "Kylian Mbappe",
    "England": "Harry Kane",
    "Spain": "Lamine Yamal",
    "Portugal": "Cristiano Ronaldo",
    "Germany": "Jamal Musiala",
    "USA": "Christian Pulisic",
    "Mexico": "Santiago Gimenez",
    "Japan": "Takefusa Kubo",
}

DARK_HORSE_PICKS = {
    "Brazil": "Japan",
    "Argentina": "Mexico",
    "France": "USA",
    "England": "Japan",
    "Spain": "Portugal",
    "Portugal": "Mexico",
    "Germany": "USA",
    "USA": "USA",
    "Mexico": "Mexico",
    "Japan": "Japan",
}

GENERAL_MEMORIES = [
    "Messi in 2022, Mbappe in that final, and James Rodriguez in 2014 are why early predictions are so addictive.",
    "Every World Cup has one player who suddenly owns the timeline. That is the fun part of guessing early.",
    "The best World Cup debates start with one highlight everyone remembers, then spiral into bracket takes.",
    "Golden Boot guesses are dangerous because one hot group stage can rewrite the whole conversation.",
]

HASHTAGS = {
    "team_prediction": ["#WorldCup2026", "#Football"],
    "dark_horse": ["#WorldCup2026", "#Football"],
    "funny": ["#WorldCup2026", "#Football"],
    "fan_life": ["#WorldCup2026", "#Football"],
    "hot_take": ["#WorldCup2026", "#Football"],
    "schedule": ["#WorldCup2026"],
    "poll": ["#WorldCup2026", "#Football"],
    "product_light": ["#WorldCup2026"],
}

CATEGORY_GOALS = {
    "team_prediction": "Champion prediction debate",
    "dark_horse": "Underdog discussion",
    "funny": "Humor and replies",
    "fan_life": "Fan habits and matchday conversation",
    "hot_take": "Football-only disagreement",
    "schedule": "Planning and saves",
    "poll": "Quick audience signal",
    "product_light": "Soft website discovery",
}

CATEGORY_ZH = {
    "team_prediction": "冠军预测",
    "dark_horse": "黑马讨论",
    "funny": "足球搞笑",
    "fan_life": "球迷日常",
    "hot_take": "足球争议观点",
    "schedule": "赛程讨论",
    "poll": "投票帖",
    "product_light": "网站轻推广",
}

DEFAULT_IMAGE_BY_CATEGORY = {
    "dark_horse": "/social/images/topic-dark-horse.png",
    "funny": "/social/images/topic-funny.png",
    "fan_life": "/social/images/topic-fan-life.png",
    "hot_take": "/social/images/topic-hot-take.png",
    "schedule": "/social/images/topic-schedule.png",
    "poll": "/social/images/topic-poll.png",
    "product_light": "/social/images/topic-product-light.png",
}

TEAM_ZH = {
    "Brazil": "巴西",
    "Argentina": "阿根廷",
    "France": "法国",
    "England": "英格兰",
    "Spain": "西班牙",
    "Portugal": "葡萄牙",
    "Germany": "德国",
    "USA": "美国",
    "Mexico": "墨西哥",
    "Japan": "日本",
}

TEXT_ZH_OVERRIDES = {
    "World Cup 2026 is still far away, but the group chat is already choosing champions.": "世界杯 2026 还没开始，朋友群已经开始选冠军了。",
    "Every early World Cup prediction should come with one rule: we are allowed to change our minds after the draw.": "所有早期世界杯预测都应该有一个规则：抽签后可以改主意。",
    "There is always one team people ignore in June and suddenly fear by the knockout stage.": "总有一支球队六月没人聊，到了淘汰赛前大家突然开始担心。",
    "The first big upset will make half the internet rewrite its World Cup bracket.": "第一场大冷门出现后，半个互联网都会重写自己的世界杯预测。",
    "World Cup debates are better when nobody treats a prediction like a final answer.": "世界杯讨论最好玩的地方，就是预测永远不是最终答案。",
    "One strong group-stage performance can turn a quiet team into everyone's dark-horse pick.": "一场强势小组赛，就能让一支安静的球队变成大家口中的黑马。",
    "The best World Cup watch parties always have one person checking the table every five minutes.": "最好的世界杯观赛局里，总有人每五分钟查一次积分榜。",
    "Kickoff times will decide which matches become breakfast games, lunch games, or late-night games.": "开球时间会决定哪些比赛变成早餐场、午餐场或深夜场。",
    "Every tournament has one player who makes people search for his club five minutes after the match.": "每届大赛都会有一个球员，让大家赛后五分钟就去查他在哪个俱乐部。",
    "Group-stage football feels calm until the underdog scores first.": "小组赛看起来很平静，直到弱队先进球。",
    "A good World Cup page should make three things clear: who plays, when it starts, and why the match matters.": "一个好用的世界杯页面应该讲清楚三件事：谁踢、几点踢、为什么值得看。",
    "Not every World Cup debate has to be about the champion. Sometimes the better question is which team nobody wants to face.": "世界杯讨论不一定都要聊冠军，有时候更好的问题是：哪支队最没人想碰？",
    "Some fans look at tactics. Some fans look at form. The best World Cup arguments need both.": "有些球迷看战术，有些球迷看状态。最好的世界杯争论两者都需要。",
    "World Cup 2026 will create plenty of new matchday routines because the kickoff times will not feel the same everywhere.": "世界杯 2026 会制造很多新的观赛习惯，因为每个地区的开球时间都不一样。",
    "What is your early World Cup 2026 take right now?": "你现在对世界杯 2026 最早的判断是什么？",
    "What is the first prediction you might change later?": "你觉得自己之后最可能改掉哪一个预测？",
    "What is the most World Cup-specific habit you suddenly develop every tournament?": "每到世界杯，你最容易突然养成什么专属习惯？",
    "What is your matchday routine going to be in 2026?": "到 2026 年，你的比赛日观赛习惯会是什么？",
    "Keep it football-only: what part of this take is wrong?": "只讨论足球：这个观点哪部分不对？",
    "What is the strongest counterargument?": "最有力的反驳是什么？",
    "Who wins World Cup 2026? Brazil, Argentina, France, or Spain?": "谁会赢得世界杯 2026？巴西、阿根廷、法国，还是西班牙？",
    "Brazil 2002, Spain 2010, Germany 2014, Argentina 2022: which champion style feels most likely to work in 2026?": "巴西 2002、西班牙 2010、德国 2014、阿根廷 2022：哪种冠军风格最可能在 2026 年奏效？",
    "Who is your early World Cup 2026 dark horse? Japan's 2022 run is still the blueprint for me.": "你现在最早看好的世界杯 2026 黑马是谁？对我来说，日本 2022 的表现仍然是模板。",
    "Which group would be the most fun: pure chaos, one giant favorite, or four teams with Mexico-vs-Germany-2018 energy?": "哪种小组最有看点：完全混乱、一个超级热门，还是四支队都有 2018 墨西哥对德国那种爆冷气质？",
    "Early Golden Boot pick? Mbappe's 2022 final still makes me afraid to pick against him.": "早期金靴你选谁？姆巴佩 2022 决赛的表现让我很难不选他。",
    "Who has the better 2026 setup right now: France depth, Brazil flair, Argentina control, or Spain tempo?": "现在谁的 2026 基础更好：法国的深度、巴西的天赋、阿根廷的控制，还是西班牙的节奏？",
    "Most annoying team to face in a World Cup: elite attack, locked-in defense, or a fearless underdog like Japan in 2022?": "世界杯里最难缠的对手是哪种：顶级进攻、稳固防守，还是像 2022 日本那样无所畏惧的黑马？",
    "If one host team makes a big run in 2026, is it USA home energy, Mexico tournament noise, or Canada surprise factor?": "如果 2026 有一支东道主球队走得很远，会是美国的主场能量、墨西哥的大赛气氛，还是加拿大的惊喜因素？",
    "Which 2026 final has the best storyline: Argentina aura, Mbappe's France, Brazil chasing magic, or England stress levels?": "哪组 2026 决赛故事线最好看：阿根廷的冠军气场、姆巴佩的法国、追逐魔法的巴西，还是压力拉满的英格兰？",
    "Got excited for World Cup 2026 and started building a small fan hub in my spare time. Mostly schedules, team pages, predictions, and little games for matchday brain.": "因为太期待世界杯 2026，我开始用业余时间做一个小型球迷中心。主要是赛程、球队页、预测和一些比赛日小游戏。",
    "Trying to make following the World Cup a little more fun: localized schedules, team guides, prediction cards, and fan games. Keeping it casual.": "我想让看世界杯变得更有趣一点：本地化赛程、球队指南、预测卡和球迷小游戏。整体保持轻松。",
    "I built a tiny World Cup 2026 hub because I wanted one place for fixtures, teams, and prediction messing around.": "我做了一个小型世界杯 2026 网站，因为我想有一个地方能同时看赛程、球队和各种预测玩法。",
    "World Cup planning mode has started way too early for me, so I made a fan hub to track teams and predictions without making it feel like homework.": "我进入世界杯计划模式太早了，所以做了一个球迷网站，用来跟踪球队和预测，但不想让它像作业一样无聊。",
    "Working on a World Cup 2026 fan site for people who love brackets, fixtures, and arguing about dark horses before the draw even behaves.": "我在做一个世界杯 2026 球迷网站，给那些喜欢预测表、赛程，以及抽签前就开始争论黑马的人用。",
    "Spent the weekend polishing a little World Cup 2026 fan hub. The goal is simple: schedules, team pages, predictions, and fun matchday stuff.": "周末我打磨了一个小型世界杯 2026 球迷中心。目标很简单：赛程、球队页、预测和有趣的比赛日内容。",
    "I wanted a cleaner way to follow World Cup 2026 in local time, so I started building one. Still fan-made, still very much powered by tournament excitement.": "我想用更清楚的方式按本地时间关注世界杯 2026，所以开始做这个网站。它仍然是球迷自制，也完全来自对大赛的期待。",
    "I am keeping it fan-focused: schedules, team pages, predictions, and simple games rather than anything too serious. Feedback from football people would genuinely help.": "我会保持球迷视角：赛程、球队页、预测和简单小游戏，而不是做得太严肃。真正懂球的人给点反馈会很有帮助。",
    "Brazil will not win World Cup 2026. Too much attacking talent, not enough knockout calm. Convince me I am wrong.": "巴西不会赢得世界杯 2026。他们进攻天赋太多，但淘汰赛里的冷静还不够。说服我这个判断是错的。",
    "Everyone talks about Argentina repeating. Nobody talks enough about how hard it is to carry that aura into a new cycle.": "大家都在聊阿根廷卫冕，但很少有人讨论把冠军气场延续到新周期到底有多难。",
    "Spain might be the team people underrate because control is less loud than star power.": "西班牙可能会被低估，因为控制力没有球星光环那么显眼。",
    "France have the depth, but being the obvious pick is exactly what makes World Cup predictions dangerous.": "法国确实阵容深厚，但他们太像热门选择，这也正是世界杯预测危险的地方。",
    "England's biggest opponent in 2026 might be the weight of the sentence 'this is finally the year.'": "英格兰 2026 最大的对手，可能是“这次终于轮到我们了”这句话本身的压力。",
    "Hot take, football-only:": "足球争议观点：",
    "Dark-horse debate for World Cup 2026:": "世界杯 2026 黑马讨论：",
    "Dark-horse thread:": "黑马讨论帖：",
    "That does not mean they are winning it, but it does make them dangerous enough to ruin somebody's bracket. Convince me I am wrong.": "这不代表他们会夺冠，但足以说明他们危险到可以毁掉别人的预测表。说服我这个判断是错的。",
    "What would have to go right for them to make a noisy run?": "他们需要哪些条件都走对，才可能打出一段让人关注的征程？",
    "Give me the case against them before I get too carried away.": "在我太看好他们之前，给我一个反对理由。",
    "Am I overrating them or is the path actually there?": "我是高估他们了，还是这条路真的存在？",
    "as a 2026 dark horse sounds risky until you remember:": "作为 2026 黑马听起来有风险，直到你想起：",
    "Dark-horse watch:": "黑马观察：",
    "If the 2026 bracket opens up,": "如果 2026 的晋级路线打开，",
    "are exactly the kind of team I would not want to face in a knockout match.": "正是我不想在淘汰赛碰到的那类球队。",
    "Has anyone started planning around the": "有没有人已经开始围绕",
    "group-stage schedule yet?": "的小组赛赛程做计划了？",
    "I like having fixtures, local time, and team notes in one place before the tournament starts. Which group match are you circling first?": "我喜欢在大赛开始前，把赛程、本地时间和球队信息放在一个地方看。你最先圈出来的是哪场小组赛？",
    "group-stage schedule is one I want to track early.": "的小组赛赛程是我想早点关注的内容。",
    "Which match feels like the swing game?": "哪场比赛最像关键转折点？",
    "So yeah, the": "所以，",
    "group-stage schedule is going straight into my calendar.": "的小组赛赛程会直接进我的日历。",
    "That is why the": "这也是为什么",
    "group path feels spicy from match one.": "的小组路线从第一场开始就很有看点。",
    "I keep checking possible": "我一直在看",
    "kickoff times.": "可能的开球时间。",
    "Timezone pain is part of the World Cup package.": "时区压力也是世界杯体验的一部分。",
    "group-stage watch plan: clear the calendar, then remember": "小组赛观赛计划：先清空日历，然后记住",
    "If": "如果",
    "start hot in the group, I am instantly changing my bracket.": "小组赛开局火热，我会立刻修改自己的预测表。",
    "Ronaldo's 2002 redemption arc still makes Brazil predictions feel different.": "罗纳尔多 2002 年的救赎故事，依然让巴西预测显得不一样。",
    "That 2002 front line is still the World Cup memory I compare every Brazil attack to.": "那条 2002 年锋线，仍然是我衡量巴西进攻时会想起的世界杯记忆。",
    "Neymar dragging Brazil through big tournament moments is hard to forget.": "内马尔在大赛关键时刻带着巴西前进的画面很难忘记。",
    "Messi's 2022 run changed the whole feeling around Argentina in knockout games.": "梅西 2022 年的征程，改变了大家对阿根廷淘汰赛气质的感受。",
    "That Messi and Di Maria 2022 final link-up still feels unreal.": "梅西和迪马利亚在 2022 决赛里的连线，到现在仍然让人觉得不可思议。",
    "After that 2022 final, Argentina have main-character energy in every bracket chat.": "那场 2022 决赛之后，阿根廷在每次预测讨论里都自带主角气质。",
    "Mbappe in the 2022 final is still one of the wildest individual World Cup performances.": "姆巴佩在 2022 决赛里的表现，仍然是世界杯最疯狂的个人演出之一。",
    "France's 2018 pace and 2022 resilience make them feel built for tournament football.": "法国 2018 的速度和 2022 的韧性，让他们看起来就是为杯赛而生。",
    "When a team has recent memories of Mbappe deciding games, every bracket looks dangerous.": "当一支球队刚有姆巴佩决定比赛的记忆时，任何预测表都会变得危险。",
    "England's recent semi-final and final near-misses make every prediction feel loaded.": "英格兰近年的半决赛和决赛擦肩而过，让每一次预测都带着压力。",
    "Kane's World Cup goals and England's 2018 run still hang over the next prediction.": "凯恩的世界杯进球和英格兰 2018 的征程，仍然影响着下一次预测。",
    "England always has that mix of huge talent and tournament tension.": "英格兰总是同时拥有巨大天赋和大赛压力。",
    "Spain's 2010 team is still the cleanest example of control winning a World Cup.": "西班牙 2010 仍然是用控制力赢得世界杯的最清晰例子。",
    "Iniesta's 2010 final goal is the kind of memory that makes Spain predictions feel romantic.": "伊涅斯塔 2010 决赛进球，是那种让西班牙预测带着浪漫感的记忆。",
    "The 2010 possession machine still shapes how I think about Spain in knockout games.": "2010 年那台控球机器，仍然影响我看待西班牙淘汰赛的方式。",
    "Ronaldo has given Portugal so many tournament moments that they never feel ordinary.": "C 罗给葡萄牙留下了太多大赛时刻，让他们从来不会显得普通。",
    "Ronaldo's 2018 hat trick against Spain is still peak World Cup drama.": "C 罗 2018 对西班牙的帽子戏法，仍然是世界杯戏剧性的顶点。",
    "Portugal always feels one Bruno pass or one Leao run away from a highlight clip.": "葡萄牙总让人觉得，只差一次 B 费传球或莱奥突破，就能变成集锦画面。",
    "Germany's 2014 title run is the reminder to never write them off too early.": "德国 2014 的夺冠征程提醒我们，永远不要太早看低他们。",
    "That 7-1 in 2014 still pops up anytime Germany enter a knockout conversation.": "只要德国进入淘汰赛讨论，2014 年那场 7-1 总会被想起。",
    "Germany in 2014 is still the reference point for a team peaking at the perfect time.": "2014 年的德国，仍然是球队在最佳时机达到巅峰的参考样本。",
    "Donovan's 2010 stoppage-time goal is still the USA World Cup memory that gives me chills.": "多诺万 2010 年补时进球，仍然是最让我起鸡皮疙瘩的美国世界杯记忆。",
    "The USA has enough home-crowd energy in 2026 to make every group match feel bigger.": "美国在 2026 有足够的主场能量，让每场小组赛都显得更重要。",
    "Pulisic's 2022 goal against Iran showed how tense and emotional this team can make a World Cup.": "普利西奇 2022 对伊朗的进球，说明这支球队能让世界杯变得多么紧张和情绪化。",
    "Ochoa turning into a World Cup wall is basically a tournament tradition now.": "奥乔亚在世界杯变成门前高墙，几乎已经是大赛传统。",
    "Mexico beating Germany in 2018 is still the kind of memory that makes dark-horse talk fun.": "墨西哥 2018 击败德国，仍然是让黑马讨论变得有趣的那类记忆。",
    "Mexico's World Cup story always has noise, pressure, and one match that feels massive.": "墨西哥的世界杯故事总有声浪、压力，以及一场分量极重的比赛。",
    "Japan beating Germany and Spain in 2022 is exactly why nobody should treat them lightly.": "日本 2022 击败德国和西班牙，正说明没人应该轻视他们。",
    "Japan's 2022 comeback energy made them one of the easiest teams to root for.": "日本 2022 的逆转能量，让他们成为最容易让人支持的球队之一。",
    "That 2022 group-stage run gave Japan a proper dark-horse identity.": "2022 年的小组赛表现，让日本真正有了黑马身份。",
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
    "guaranteed winner",
    "free money",
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


def make_qr(size: int) -> Image.Image | None:
    if qrcode is None:
        return None
    qr = qrcode.QRCode(border=1, box_size=8)
    qr.add_data(SITE_URL)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((size, size))


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_chars: int, font_obj, fill, line_height: int, max_lines: int = 2) -> None:
    x, y = xy
    for i, line in enumerate(fit_lines(text, max_chars)[:max_lines]):
        draw.text((x, y + i * line_height), line, font=font_obj, fill=fill)


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
    footer_h = 56 if h <= 700 else 72
    draw.rectangle((0, h - footer_h, w, h), fill=deep)
    draw.ellipse((w - 360, -180, w + 140, 320), fill=tuple(min(255, c + 40) for c in accent))

    margin = int(w * 0.07)
    title_font = font(48 if w > 1100 else 44, True)
    team_font = font(76 if w > 1100 else 70, True)
    label_font = font(25 if w > 1100 else 24, True)
    body_font = font(28 if w > 1100 else 27)
    small_font = font(24 if w > 1100 else 22, True)

    flag_w = int(w * 0.22)
    flag_h = int(flag_w * 0.62)
    draw_flag(draw, card.team, (margin, margin + 8, margin + flag_w, margin + 8 + flag_h))

    headline = f"I picked {card.team} to win World Cup 2026"
    if h <= 700:
        headline = "My World Cup 2026 Prediction"
    draw.text((margin + flag_w + 34, margin + 12), headline, font=title_font, fill=(24, 32, 40))
    draw.text((margin + flag_w + 36, margin + 84), card.team, font=team_font, fill=deep)

    box_y = margin + flag_h + (38 if h <= 700 else 70)
    bracket_h = 150 if h <= 700 else 360
    rounded_rect(draw, (margin, box_y, w - margin, box_y + bracket_h), 24, fill=(255, 255, 255), outline=(225, 229, 224), width=2)
    draw.text((margin + 34, box_y + 24), "Prediction Bracket", font=label_font, fill=accent)

    path_y = box_y + (104 if h <= 700 else 150)
    step_gap = (w - 2 * margin - 80) / max(1, len(card.path) - 1)
    for i, step in enumerate(card.path):
        x = margin + 40 + i * step_gap
        draw.ellipse((x - 16, path_y - 16, x + 16, path_y + 16), fill=accent, outline=deep, width=3)
        if i < len(card.path) - 1:
            draw.line((x + 18, path_y, margin + 40 + (i + 1) * step_gap - 18, path_y), fill=(120, 130, 125), width=4)
        compact_step = step
        if h <= 700:
            compact_step = compact_step.replace("Group winner", "Group")
            compact_step = compact_step.replace("Group battle", "Group")
            compact_step = compact_step.replace("R16 vs runner-up", "R16")
            compact_step = compact_step.replace("QF pressure test", "QF")
            compact_step = compact_step.replace("QF classic", "QF")
            compact_step = compact_step.replace("QF dream", "QF")
            compact_step = compact_step.replace("QF danger", "QF")
            compact_step = compact_step.replace("QF test", "QF")
            compact_step = compact_step.replace("SF heavyweight", "SF")
            compact_step = compact_step.replace("Statement run", "Run")
            compact_step = compact_step.replace("R16 upset", "R16")
            compact_step = compact_step.replace("R16 edge", "R16")
            compact_step = compact_step.replace("R16 control", "R16")
        max_step_lines = 1 if h <= 700 else 2
        for j, line in enumerate(fit_lines(compact_step, 12)[:max_step_lines]):
            tw = draw.textlength(line, font=small_font)
            draw.text((x - tw / 2, path_y + 28 + j * 26), line, font=small_font, fill=(31, 38, 43))

    if h > 700:
        draw_wrapped(draw, (margin + 34, box_y + 240), card.summary, 48, body_font, (36, 44, 50), 38, 2)

    pick_y = box_y + bracket_h + (16 if h <= 700 else 34)
    pick_h = 88 if h <= 700 else 132
    pick_gap = 18
    pick_w = int((w - 2 * margin - 2 * pick_gap) / 3)
    picks = [
        ("Champion", card.champion_pick),
        ("Golden Boot", GOLDEN_BOOT_PICKS[card.team]),
        ("Dark Horse", DARK_HORSE_PICKS[card.team]),
    ]
    for i, (label, value) in enumerate(picks):
        x1 = margin + i * (pick_w + pick_gap)
        rounded_rect(draw, (x1, pick_y, x1 + pick_w, pick_y + pick_h), 20, fill=(255, 255, 255), outline=(225, 229, 224), width=2)
        draw.text((x1 + 22, pick_y + 14), label, font=label_font, fill=accent)
        draw_wrapped(draw, (x1 + 22, pick_y + 47), value, 16 if h <= 700 else 14, font(28 if h <= 700 else 34, True), (23, 28, 36), 34, 2)

    brand = f"{FOOTER_BRAND}  |  {BRAND}"
    qr = make_qr(88 if h <= 700 else 108)
    if qr:
        qr_x = margin
        qr_y = h - (footer_h + qr.height + 10)
        draw.rounded_rectangle((qr_x - 8, qr_y - 8, qr_x + qr.width + 8, qr_y + qr.height + 8), radius=14, fill=(255, 255, 255))
        img.paste(qr, (qr_x, qr_y))
        brand_x = qr_x + qr.width + 24
    else:
        brand_x = margin
    brand_w = draw.textlength(brand, font=small_font)
    draw.text((max(brand_x, w - margin - brand_w), h - 40), brand, font=small_font, fill=(255, 255, 255))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def draw_topic_image(category: str, title: str, subtitle: str, accent: tuple[int, int, int], out: Path) -> None:
    size = (1200, 630)
    w, h = size
    deep = tuple(max(12, int(c * 0.42)) for c in accent)
    img = Image.new("RGB", size, (246, 248, 247))
    draw = ImageDraw.Draw(img)

    for y in range(h):
      ratio = y / max(1, h - 1)
      color = tuple(int((1 - ratio) * 248 + ratio * c) for c in (226, 235, 230))
      draw.line((0, y, w, y), fill=color)

    draw.rectangle((0, 0, w, h), outline=(218, 226, 232), width=2)
    draw.rectangle((0, 0, w, 18), fill=accent)
    draw.ellipse((760, -180, 1320, 380), fill=tuple(min(255, c + 36) for c in accent))
    draw.ellipse((900, 80, 1110, 290), fill=(248, 249, 246), outline=deep, width=10)
    draw.rectangle((990, 285, 1024, 420), fill=deep)
    draw.polygon([(920, 420), (1095, 420), (1138, 505), (878, 505)], fill=deep)

    for x in range(90, 1120, 150):
        draw.arc((x, 445, x + 160, 600), 180, 360, fill=(210, 218, 222), width=4)
    draw.line((0, 510, w, 510), fill=(210, 218, 222), width=4)
    draw.line((0, 560, w, 560), fill=(230, 235, 238), width=3)

    title_font = font(64, True)
    subtitle_font = font(31)
    small_font = font(25, True)
    draw.text((70, 64), "World Cup 2026", font=small_font, fill=deep)
    draw.text((70, 122), title, font=title_font, fill=(20, 31, 42))
    draw_wrapped(draw, (74, 222), subtitle, 38, subtitle_font, (68, 82, 96), 42, max_lines=3)

    chips = {
        "funny": ["group chat", "matchday talk", "fan replies"],
        "fan_life": ["watch party", "kickoff time", "fan habits"],
        "hot_take": ["debate", "convince me", "football only"],
        "dark_horse": ["underdog", "bracket noise", "upset watch"],
        "schedule": ["fixtures", "local time", "save this"],
        "poll": ["quick vote", "fan signal", "comments"],
        "product_light": ["fan hub", "schedule", "prediction cards"],
    }.get(category, ["football", "fans", "discussion"])
    x = 74
    for chip in chips:
        tw = int(draw.textlength(chip, font=small_font)) + 34
        rounded_rect(draw, (x, 404, x + tw, 448), 22, fill=(255, 255, 255), outline=(218, 226, 232), width=2)
        draw.text((x + 17, 413), chip, font=small_font, fill=deep)
        x += tw + 14

    draw.text((70, h - 58), f"{FOOTER_BRAND}  |  {BRAND}", font=small_font, fill=(255, 255, 255))
    draw.rectangle((0, h - 72, w, h), fill=deep)
    draw.text((70, h - 52), f"{FOOTER_BRAND}  |  {BRAND}", font=small_font, fill=(255, 255, 255))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def make_utm(platform: str, category: str, team: str | None = None) -> str:
    campaign = f"wc2026-{category}"
    content = slug(team or "general")
    return f"{SITE_URL}?utm_source={platform}&utm_medium=social&utm_campaign={campaign}&utm_content={content}"


def make_draft(platform: str, category: str, text: str, team: str | None = None, image: str | None = None) -> dict:
    image = image or DEFAULT_IMAGE_BY_CATEGORY.get(category)
    item = {
        "platform": platform,
        "category": category,
        "team": team,
        "text": text,
        "text_zh": chinese_preview(category, text, team),
        "image": image,
        "url": SITE_URL,
        "tracking_url": make_utm(platform, category, team),
        "goal": CATEGORY_GOALS.get(category, "Fan engagement"),
        "review_required": True,
        "safety_note": "仅限足球讨论，发布前请人工审核。",
    }
    return {k: v for k, v in item.items() if v is not None}


def chinese_preview(category: str, text: str, team: str | None = None) -> str:
    clean = re.sub(r"\s*#WorldCup2026\s*#Football\s*$", "", text).strip()
    clean = clean.replace(SITE_URL, "").strip()

    translated = clean
    for english in sorted(TEXT_ZH_OVERRIDES, key=len, reverse=True):
        translated = translated.replace(english, TEXT_ZH_OVERRIDES[english])
    translated = re.sub(r"\n{3,}", "\n\n", translated).strip()
    if translated and translated != clean and not re.search(r"[A-Za-z]{4,}", translated):
        return translated

    team_name = TEAM_ZH.get(team or "", team or "这支球队")
    category_name = CATEGORY_ZH.get(category, category)
    if category == "team_prediction":
        return f"围绕{team_name}的世界杯 2026 预测，主打早期冠军讨论和球迷争论。"
    if category == "dark_horse":
        return f"把{team_name}作为黑马话题抛出来，引导球迷讨论它是否真的有爆冷空间。"
    if category == "hot_take":
        return f"一条只限足球层面的争议观点，核心是让球迷反驳或补充关于{team_name}的判断。"
    if category == "schedule":
        return f"围绕{team_name}赛程和开球时间做讨论，适合引导用户查看赛程页。"
    if category == "poll":
        return "投票/提问型内容，用来快速收集球迷倾向和制造评论区互动。"
    if category == "product_light":
        return "轻量介绍网站功能，把赛程、球队页、预测卡和小游戏自然带出来，不做硬广告。"
    return f"{category_name}内容，用轻松语气引导球迷回复。"


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
        "{memory} My early {team} 2026 take: they have a real path if the knockout draw is kind.",
        "{team} bracket talk always starts with one big tournament memory. {memory} How far should we take them in 2026?",
        "Made a {team} prediction card and started comparing every possible knockout path. {memory}",
        "{team} fans, what is the realistic 2026 ceiling? {memory}",
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

    dark_horse_teams = ["Japan", "Mexico", "USA", "Portugal", "Spain"]
    dark_templates = [
        "{team} as a 2026 dark horse sounds risky until you remember: {memory} Am I overrating them or is the path actually there?",
        "Dark-horse watch: {team}. {memory} Give me the case against them before I get too carried away.",
        "If the 2026 bracket opens up, {team} are exactly the kind of team I would not want to face in a knockout match.",
    ]
    for idx, team in enumerate(dark_horse_teams):
        memory = team_memory(team, idx)
        x_posts.append(make_draft("x", "dark_horse", x_text(dark_templates[idx % len(dark_templates)].format(team=team, memory=memory), "dark_horse"), team))
        fb_posts.append(
            make_draft(
                "facebook",
                "dark_horse",
                f"Dark-horse debate for World Cup 2026: {team}.\n\n{memory} That does not mean they are winning it, but it does make them dangerous enough to ruin somebody's bracket. Convince me I am wrong.",
                team,
            )
        )
        discord_posts.append(
            make_draft(
                "discord",
                "dark_horse",
                f"Dark-horse thread: {team}. {memory} What would have to go right for them to make a noisy run?",
                team,
            )
        )

    funny_posts = [
        "World Cup 2026 is still far away, but the group chat is already choosing champions.",
        "Every early World Cup prediction should come with one rule: we are allowed to change our minds after the draw.",
        "There is always one team people ignore in June and suddenly fear by the knockout stage.",
        "The first big upset will make half the internet rewrite its World Cup bracket.",
        "World Cup debates are better when nobody treats a prediction like a final answer.",
        "One strong group-stage performance can turn a quiet team into everyone's dark-horse pick.",
    ]
    for idx, text in enumerate(funny_posts):
        x_posts.append(make_draft("x", "funny", x_text(text, "funny")))
        if idx < 3:
            fb_posts.append(make_draft("facebook", "funny", f"{text}\n\nWhat is your early World Cup 2026 take right now?"))
        discord_posts.append(make_draft("discord", "funny", f"{text} What is the first prediction you might change later?"))

    fan_life_posts = [
        "The best World Cup watch parties always have one person checking the table every five minutes.",
        "Kickoff times will decide which matches become breakfast games, lunch games, or late-night games.",
        "Every tournament has one player who makes people search for his club five minutes after the match.",
        "Group-stage football feels calm until the underdog scores first.",
        "A good World Cup page should make three things clear: who plays, when it starts, and why the match matters.",
        "Not every World Cup debate has to be about the champion. Sometimes the better question is which team nobody wants to face.",
        "Some fans look at tactics. Some fans look at form. The best World Cup arguments need both.",
        "World Cup 2026 will create plenty of new matchday routines because the kickoff times will not feel the same everywhere.",
    ]
    for idx, text in enumerate(fan_life_posts):
        x_posts.append(make_draft("x", "fan_life", x_text(text, "fan_life")))
        if idx < 4:
            fb_posts.append(make_draft("facebook", "fan_life", f"{text}\n\nWhat is the most World Cup-specific habit you suddenly develop every tournament?"))
        discord_posts.append(make_draft("discord", "fan_life", f"{text} What is your matchday routine going to be in 2026?"))

    hot_takes = [
        ("Brazil", "Brazil will not win World Cup 2026. Too much attacking talent, not enough knockout calm. Convince me I am wrong."),
        ("Argentina", "Everyone talks about Argentina repeating. Nobody talks enough about how hard it is to carry that aura into a new cycle."),
        ("Spain", "Spain might be the team people underrate because control is less loud than star power."),
        ("France", "France have the depth, but being the obvious pick is exactly what makes World Cup predictions dangerous."),
        ("England", "England's biggest opponent in 2026 might be the weight of the sentence 'this is finally the year.'"),
    ]
    for team, text in hot_takes:
        x_posts.append(make_draft("x", "hot_take", x_text(text, "hot_take"), team))
        fb_posts.append(make_draft("facebook", "hot_take", f"{text}\n\nKeep it football-only: what part of this take is wrong?", team))
        discord_posts.append(make_draft("discord", "hot_take", f"Hot take, football-only: {text} What is the strongest counterargument?", team))

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
        "Who wins World Cup 2026? Brazil, Argentina, France, or Spain?",
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
        "discussion": [p for p in x_posts if p["category"] in {"poll", "schedule", "dark_horse", "hot_take", "funny", "fan_life"}],
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
        elif day in {4, 15, 24}:
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
                "review_checklist": [
                    "No politics, religion, hate speech, or personal attacks",
                    "Question invites football discussion",
                    "Post is edited to sound human before publishing",
                ],
            }
        )
    return calendar


def make_recommendations(x_posts: list[dict]) -> list[dict]:
    buckets = [
        ("Low effort signal", "Post one poll and compare replies vs clicks after 24 hours.", "poll"),
        ("Prediction card test", "Use one champion card, then ask followers to change one knockout step.", "team_prediction"),
        ("Discussion hook", "Run a dark-horse question when prediction posts feel repetitive.", "dark_horse"),
        ("Humor reset", "Use a funny post after two serious football takes in a row.", "funny"),
        ("Debate spark", "Use a football-only hot take, then manually reply to the best counterarguments.", "hot_take"),
    ]
    recommendations = []
    for title, action, category in buckets:
        sample = next((p for p in x_posts if p["category"] == category), None)
        recommendations.append(
            {
                "title": title,
                "action": action,
                "category": category,
                "sample_text": sample["text"] if sample else "",
                "guardrail": "Human review only. Do not mass-post or automate platform actions.",
            }
        )
    return recommendations


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

    topic_images = [
        ("dark_horse", "Dark Horse Watch", "Underdog teams, noisy brackets, and the match nobody wants to face.", (190, 0, 45)),
        ("funny", "Football Talk", "Light football jokes for group chats, replies, and World Cup discussion.", (23, 105, 170)),
        ("fan_life", "Fan Life", "Watch parties, timezone routines, jersey temptations, and tournament habits.", (22, 132, 92)),
        ("hot_take", "Football Debate", "Strong opinions, clean arguments, and replies that stay about the game.", (210, 70, 52)),
        ("schedule", "Fixture Mode", "Kickoff times, saved calendars, and the games fans should not miss.", (214, 155, 22)),
        ("poll", "Fan Vote", "Quick questions that turn quiet followers into visible football opinions.", (80, 100, 190)),
        ("product_light", "Fan Hub", "Schedules, teams, prediction cards, and matchday tools without hard selling.", (28, 118, 122)),
    ]
    for category, title, subtitle, accent in topic_images:
        draw_topic_image(category, title, subtitle, accent, IMAGES / f"topic-{slug(category.replace('_', '-'))}.png")

    x_posts, fb_posts, discord_posts = build_drafts()
    all_drafts = x_posts + fb_posts + discord_posts
    validate(all_drafts)

    write_json(DRAFTS / "x-posts.json", x_posts)
    write_json(DRAFTS / "facebook-posts.json", fb_posts)
    write_json(DRAFTS / "discord-posts.json", discord_posts)
    write_json(CALENDAR / "30-day-calendar.json", make_calendar(x_posts))
    write_json(CALENDAR / "recommendations.json", make_recommendations(x_posts))
    write_dashboard_data(x_posts, fb_posts, discord_posts)
    print(f"Generated {len(x_posts)} X drafts, {len(fb_posts)} Facebook drafts, {len(discord_posts)} Discord drafts.")
    print(f"Generated {len(PRIORITY_TEAMS) * 2 + len(topic_images)} share images in {IMAGES}.")


if __name__ == "__main__":
    main()
