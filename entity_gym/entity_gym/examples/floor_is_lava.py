from dataclasses import dataclass
import numpy as np
import random
from typing import Dict, Mapping

from entity_gym.environment import (
    CategoricalAction,
    CategoricalActionMask,
    Environment,
    CategoricalActionSpace,
    ActionSpace,
    EpisodeStats,
    ObsSpace,
    Observation,
    Action,
)
from entity_gym.dataclass_utils import obs_space_from_dataclasses, extract_features


@dataclass
class Lava:
    x: float
    y: float


@dataclass
class HighGround:
    x: float
    y: float


@dataclass
class Player:
    x: float
    y: float


class FloorIsLava(Environment):
    """
    The player is surrounded by 8 tiles, 7 of which are lava and 1 of which is high ground.
    The player must move to one of the tiles.
    The player receives a reward of 1 if they move to the high ground, and 0 otherwise.
    """

    @classmethod
    def obs_space(cls) -> ObsSpace:
        return obs_space_from_dataclasses(Lava, HighGround, Player)

    @classmethod
    def action_space(cls) -> Dict[str, ActionSpace]:
        return {
            "move": CategoricalActionSpace(["n", "ne", "e", "se", "s", "sw", "w", "nw"])
        }

    def reset_filter(self, obs_space: ObsSpace) -> Observation:
        width = 1000
        x = random.randint(-width, width)
        y = random.randint(-width, width)
        self.player = Player(x, y)
        self.lava = random.sample(
            [
                Lava(x + i, y + j)
                for i in range(-1, 2)
                for j in range(-1, 2)
                if not (i == 0 and j == 0)
            ],
            random.randint(1, 8),
        )
        safe = random.randint(0, len(self.lava) - 1)
        self.high_ground = HighGround(self.lava[safe].x, self.lava[safe].y)
        self.lava.pop(safe)
        obs = self.observe(obs_space)
        return obs

    def reset(self) -> Observation:
        return self.reset_filter(FloorIsLava.obs_space())

    def act_filter(
        self, action: Mapping[str, Action], obs_filter: ObsSpace
    ) -> Observation:
        for action_name, a in action.items():
            assert isinstance(a, CategoricalAction) and action_name == "move"
            dx, dy = [
                (0, 1),
                (1, 1),
                (1, 0),
                (1, -1),
                (0, -1),
                (-1, -1),
                (-1, 0),
                (-1, 1),
            ][a.actions[0]]
            self.player.x += dx
            self.player.y += dy
        obs = self.observe(obs_filter, done=True)
        return obs

    def act(self, action: Mapping[str, Action]) -> Observation:
        return self.act_filter(
            action,
            FloorIsLava.obs_space(),
        )

    def observe(self, obs_filter: ObsSpace, done: bool = False) -> Observation:
        if (
            done
            and self.player.x == self.high_ground.x
            and self.player.y == self.high_ground.y
        ):
            reward = 1.0
        else:
            reward = 0.0
        return Observation(
            features=extract_features(
                {
                    "Player": [self.player],
                    "Lava": self.lava,
                    "HighGround": [self.high_ground],
                },
                obs_filter,
            ),
            actions={
                "move": CategoricalActionMask(actor_types=["Player"]),
            },
            ids={"Player": [0]},
            reward=reward,
            done=done,
            end_of_episode_info=EpisodeStats(1, reward) if done else None,
        )
