from dataclasses import dataclass, field
from typing import List
from enum import Enum

class tier(Enum):
    IRON = "Iron"
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    EMERALD = "Emerald"
    DIAMOND = "Diamond"
    MASTER = "Master"
    GRANDMASTER = "Grandmaster"
    CHALLENGER = "Challenger"

@dataclass
class Rank:
    # or it's called tier
    rank: tier
    # 0-4 top 3 rank has no division
    division: int
    lp: int

@dataclass
class PlayerData:
    name: str
    rank: Rank
    duration: str
    last_stage: str
    # icon: https://www.metatft.com/icons/announce_icon_combat.png
    damage_to_players: int
    # icon: https://www.metatft.com/icons/gold2.png
    board_value: int

class TraitColors(Enum):
    Bronze = "bronze"
    Silver = "silver"
    Gold = "gold"
    Diamond = "diamond"
    Unique = "unique"

@dataclass
class TraitData:
    color: TraitColors

@dataclass
class SummaryData:
    # .PlayerMatchSummaryPlacement > 7
    player_placement: str
    # .PlayerMatchSummaryQueue > Ranked
    queue: str
    # .PlayerMatchSummarySecondary > 12 hours ago
    played_at: str
    # .PlayerMatchSummarySecondary > 28:24 • 5-4
    duration: str
    stage: str
    # .PlayerMatchTactician > img .TacticianPortait
    # https://cdn.metatft.com/file/metatft/tacticians/507e80f2-42e2-4355-a4cd-167f280b740a.png
    player_tactician_src: str
    player_tactician_link_base: str
    # .PlayerMatchTactician > .PlayerLevel > 9
    player_level: str
    # .PlayerMatchRankIcon > img src alt > EMERALD rank badge
    # https://cdn.metatft.com/file/metatft/ranks/emerald.png
    # .PlayerMatchRankIcon > PlayerRankDivision2 IV
    player_rank: Rank
    # .LPContainer > PlayerRankLP > 10 LP
    # .LPContainer > LPChange > +22 LP
    lp_change: str
    # level: str
    # name: str
    # tag: str
    # stage: str
    # damage_done: str
    # board_value: str
    # traits: List[dict] = field(default_factory=list)
    # units: List[UnitData] = field(default_factory=list)

# TW2_308169786
@dataclass
class MatchData:
    id: str
    summarydata: SummaryData
    name: str
    tier: str
    items: List[str] = field(default_factory=list)