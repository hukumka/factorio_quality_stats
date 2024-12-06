from typing import Self
from dataclasses import dataclass

quality_levels = [0.025, 0.032, 0.04, 0.047, 0.062]
MAX_QUALITY = 4

@dataclass
class Config:
    mod_bonus: float = quality_levels[-1]


@dataclass
class QualityDistribution:
    amounts: list[float]

    @classmethod
    def zero(cls) -> Self:
        return cls([0] * (MAX_QUALITY + 1))

    def copy(self) -> 'QualityDistribution':
        return QualityDistribution(self.amounts[:])

    @classmethod
    def from_craft(cls, initial_quality: int, amount: float, upgraded_frac: float) -> Self:
        result = cls.zero()
        result.amounts[initial_quality] = amount * (1 - upgraded_frac) 
        upgraded_amount = amount * upgraded_frac
        for i in range(initial_quality + 1, MAX_QUALITY):
            result.amounts[i] += upgraded_amount * 0.9
            upgraded_amount *= 0.1

        result.amounts[MAX_QUALITY] = upgraded_amount
        return result

    @classmethod
    def from_upgrade(cls, initial_quality: int, upgraded_amount: float) -> Self:
        result = cls.zero()
        for i in range(initial_quality + 1, MAX_QUALITY):
            result.amounts[i] += upgraded_amount * 0.9
            upgraded_amount *= 0.1

        result.amounts[MAX_QUALITY] = upgraded_amount
        return result

    def __mul__(self, k: float) -> 'QualityDistribution':
        return QualityDistribution([a * k for a in self.amounts])

    def __add__(self, other: Self) -> 'QualityDistribution':
        return QualityDistribution([
            a + b
            for a, b in zip(self.amounts, other.amounts)
        ])


def self_recycle_to(config: Config, items: QualityDistribution, target_quality: int) -> QualityDistribution:
    """
    COmpute number of items produced from self recyling (Such as plastic, biter eggs, or biolabs) items until only items of target_quality or above remain. 
    """
    result = items.copy()
    for i in range(target_quality):
        result = result + QualityDistribution.from_upgrade(i, self_recycly_ungrades_per_item(config) * result.amounts[i])
        result.amounts[i] = 0

    return result


def craft_recycle_to(
    config: Config,
    ingredients: QualityDistribution,
    target_quality: int,
    mod_count: int = 5,
    prod_bonus: float = 0.5,
) -> QualityDistribution:
    """
    Given enough ingredients to craft `ingredients` amount of items for each quality,
    compute expected number of resulted items, if any item of quality lower then `target_quality`
    is recyled to be crafted again. 
    """
    craft_quality = mod_count * config.mod_bonus
    result = QualityDistribution.zero()
    ingredients = ingredients.copy()
    for i in range(target_quality):
        if ingredients.amounts[i] > 0:
            # First recycle any items of this tier to ingredients
            ingredients += QualityDistribution.from_craft(i, result.amounts[i] * 0.25, config.mod_bonus * 4)
            result.amounts[i] = 0
            # Amount of items made from craft
            upped = QualityDistribution.from_craft(i, ingredients.amounts[i] * (1 + prod_bonus), craft_quality)
            # Amount of items returned from recyling items
            ingredient_return = QualityDistribution.from_craft(i, upped.amounts[i] * 0.25, config.mod_bonus * 4)
            # Since we get a refund, we only spent fraction of items. Lets apply multiplier to figure out real return
            loop_multiplier = ingredients.amounts[i] / (ingredients.amounts[i] - ingredient_return.amounts[i]) 
            upped *= loop_multiplier
            ingredient_return *= loop_multiplier
            result += upped
            result.amounts[i] = 0
            ingredients += ingredient_return
            ingredients.amounts[i] = 0

    result += ingredients * (1 + prod_bonus)

    return result



def self_recycly_ungrades_per_item(config: Config):
    quality = 4 * config.mod_bonus
    normal_items_return = 0.25 * (1 - quality)
    return 0.25 * quality / (1 - normal_items_return)


for bonus in quality_levels:
    print(craft_recycle_to(Config(bonus), QualityDistribution([1, 0, 0, 0, 0]), MAX_QUALITY))

