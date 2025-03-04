from dataclasses import dataclass, field
from entity_gym.environment.environment import ActionType
import numpy as np
import random
from typing import Dict, List, Mapping

from entity_gym.environment import (
    SelectEntityActionMask,
    Entity,
    Environment,
    EpisodeStats,
    ObsSpace,
    SelectEntityAction,
    SelectEntityActionSpace,
    ActionSpace,
    Observation,
    Action,
)


@dataclass
class Ball:
    color: int
    selected: bool = False


@dataclass
class PickMatchingBalls(Environment):
    """
    The PickMatchingBalls environment is initialized with a list of 32 balls of different colors.
    On each timestamp, the player can pick up one of the balls.
    The episode ends when the player picks up a ball of a different color from the last one.
    The player receives a reward equal to the number of balls picked up divided by the maximum number of balls of the same color.
    """

    max_balls: int = 32
    balls: List[Ball] = field(default_factory=list)
    one_hot: bool = False  # use one-hot encoding for the ball color feature
    randomize: bool = (
        False  # randomize the number of balls to be between 3 and max_balls
    )

    @classmethod
    def obs_space(cls) -> ObsSpace:
        return ObsSpace(
            {
                "Ball": Entity(
                    # TODO: better support for categorical features
                    [
                        "color0",
                        "color1",
                        "color2",
                        "color3",
                        "color4",
                        "color5",
                        "selected",
                    ],
                ),
                "Player": Entity([]),
            }
        )

    @classmethod
    def action_space(cls) -> Dict[ActionType, ActionSpace]:
        return {"Pick Ball": SelectEntityActionSpace()}

    def reset(self) -> Observation:
        num_balls = (
            self.max_balls if not self.randomize else random.randint(3, self.max_balls)
        )
        self.balls = [Ball(color=random.randint(0, 5)) for _ in range(num_balls)]
        self.step = 0
        return self.observe()

    def observe(self) -> Observation:
        done = len({b.color for b in self.balls if b.selected}) > 1 or all(
            b.selected for b in self.balls
        )
        if done:
            if all(b.selected for b in self.balls):
                reward = 1.0
            else:
                reward = (sum(b.selected for b in self.balls) - 1) / max(
                    [
                        len([b for b in self.balls if b.color == color])
                        for color in range(6)
                    ]
                )
        else:
            reward = 0.0

        return Observation(
            features={
                "Ball": np.array(
                    [
                        [float(b.color == c) for c in range(6)] + [float(b.selected)]
                        for b in self.balls
                    ]
                    if self.one_hot
                    else [
                        [float(b.color) for _ in range(6)] + [float(b.selected)]
                        for b in self.balls
                    ],
                    dtype=np.float32,
                ),
                "Player": np.zeros([1, 0], dtype=np.float32),
            },
            ids={
                "Ball": list(range(len(self.balls))),
                "Player": [len(self.balls)],
            },
            actions={
                "Pick Ball": SelectEntityActionMask(
                    actor_ids=[len(self.balls)],
                    actee_ids=[i for i, b in enumerate(self.balls) if not b.selected],
                ),
            },
            reward=reward,
            done=done,
            end_of_episode_info=EpisodeStats(self.step, reward) if done else None,
        )

    def act(self, actions: Mapping[ActionType, Action]) -> Observation:
        action = actions["Pick Ball"]
        assert isinstance(action, SelectEntityAction)
        for selected_ball in action.actees:
            assert not self.balls[selected_ball].selected
            self.balls[selected_ball].selected = True
        self.step += 1
        return self.observe()
