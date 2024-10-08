from enum import Enum
from cachetools import TTLCache, cached
from poe_profit_calc.bossing.bosses import *
from poe_profit_calc.setup.setup import App
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(
    prefix="/bosses",
)

price_fetcher = App.get_instance().price_fetcher


class BossId(str, Enum):
    the_searing_exarch = "the_searing_exarch"
    the_searing_exarch_uber = "the_searing_exarch_uber"
    the_eater_of_worlds = "the_eater_of_worlds"
    the_eater_of_worlds_uber = "the_eater_of_worlds_uber"
    the_shaper = "the_shaper"
    the_shaper_uber = "the_shaper_uber"
    the_elder = "the_elder"
    the_elder_uber = "the_elder_uber"
    the_elder_uber_uber = "the_elder_uber_uber"
    sirus = "sirus"
    sirus_uber = "sirus_uber"
    the_maven = "the_maven"
    the_maven_uber = "the_maven_uber"
    venarius = "venarius"
    venarius_uber = "venarius_uber"


BOSS_ID_TO_BOSS: dict[BossId, Boss] = {
    BossId.the_searing_exarch: TheSearingExarch,
    BossId.the_searing_exarch_uber: TheSearingExarchUber,
    BossId.the_eater_of_worlds: TheEaterOfWorlds,
    BossId.the_eater_of_worlds_uber: TheEaterOfWorldsUber,
    BossId.the_shaper: TheShaper,
    BossId.the_shaper_uber: TheShaperUber,
    BossId.the_elder: TheElder,
    BossId.the_elder_uber: TheElderUber,
    BossId.the_elder_uber_uber: TheElderUberUber,
    BossId.sirus: Sirus,
    BossId.sirus_uber: SirusUber,
    BossId.the_maven: TheMaven,
    BossId.the_maven_uber: TheMavenUber,
    BossId.venarius: Venarius,
    BossId.venarius_uber: VenariusUber,
}


class Drop(BaseModel):
    name: str
    price: float
    droprate: float
    reliable: bool
    trade_link: str | None
    img: str | None

    @staticmethod
    def from_item(item: Item):
        return Drop(
            name=item.name,
            price=item.price,
            droprate=item.droprate,
            reliable=item.reliable,
            trade_link=item.trade_link,
            img=item.img,
        )


class EntranceCost(BaseModel):
    name: str
    price: float
    quantity: int
    img: str | None

    @staticmethod
    def from_item(item: Item, quantity: int):
        return EntranceCost(
            name=item.name,
            price=item.price,
            quantity=quantity,
            img=item.img,
        )


class BossData(BaseModel):
    name: str
    id: BossId
    drops: list[Drop]
    entrance_items: list[EntranceCost]

    @staticmethod
    def from_boss_id(boss_id: BossId):
        id, boss = boss_id.value, BOSS_ID_TO_BOSS[boss_id]
        return BossData(
            name=boss.name,
            id=boss_id,
            drops=[Drop.from_item(item) for item in boss.drops],
            entrance_items=[
                EntranceCost.from_item(item, quantity)
                for item, quantity in boss.entrance_items.items()
            ],
        )


class BossSummary(BaseModel):
    name: str
    id: BossId
    value: float
    reliable: bool
    img: str | None


@router.get("/boss/{boss_id}")
def get_boss_data(boss_id: BossId) -> BossData:
    boss_data = BOSS_ID_TO_BOSS[boss_id]
    price_fetcher.price_items(boss_data.items())
    return BossData.from_boss_id(boss_id)


@router.get("/all")
@cached(cache=TTLCache(maxsize=128, ttl=1800))
def get_bosses() -> list[BossData]:
    all_item_sets = [boss.items() for boss in BOSS_ID_TO_BOSS.values()]
    all_items = set.union(*all_item_sets)
    price_fetcher.price_items(all_items)
    return [BossData.from_boss_id(boss) for boss in BOSS_ID_TO_BOSS.keys()]


@router.get("/summary")
@cached(cache=TTLCache(maxsize=128, ttl=1800))
def get_summary() -> list[BossSummary]:
    summaries: list[BossSummary] = []
    all_item_sets = [boss.items() for boss in BOSS_ID_TO_BOSS.values()]
    all_items = set.union(*all_item_sets)
    price_fetcher.price_items(all_items)
    for boss_id, boss in BOSS_ID_TO_BOSS.items():
        value = 0
        value += sum(item.price * item.droprate for item in boss.drops)
        value -= sum(item.price * quantity for item, quantity in boss.entrance_items.items())
        summaries.append(
            BossSummary(
                name=boss.name,
                id=boss_id,
                value=value,
                reliable=all(item.reliable for item in boss.items()),
                img=boss.get_img(),
            )
        )
    summaries.sort(key=lambda x: x.value, reverse=True)
    return summaries
