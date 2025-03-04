from typing import Any
import torch
import torch.nn as nn

# N: Batch size
# L: max number of visible objects
# C: number of channels/features on each object
def unbatched_relative_positions(
    origin: torch.Tensor,  # (N, 2)
    direction: torch.Tensor,  # (N, 2)
    positions: torch.Tensor,  # (N, L, 2)
) -> torch.Tensor:  # (N, L, 2)
    n, _ = origin.size()
    _, l, _ = positions.size()

    origin = origin.view(n, 1, 2)
    direction = direction.view(n, 1, 2)
    positions = positions.view(n, l, 2)

    positions = positions - origin

    angle = -torch.atan2(direction[:, :, 1], direction[:, :, 0])
    rotation = torch.cat(
        [
            torch.cat(
                [angle.cos().view(n, 1, 1, 1), angle.sin().view(n, 1, 1, 1)],
                dim=2,
            ),
            torch.cat(
                [-angle.sin().view(n, 1, 1, 1), angle.cos().view(n, 1, 1, 1)],
                dim=2,
            ),
        ],
        dim=3,
    )

    positions_rotated = torch.matmul(rotation, positions.view(n, l, 2, 1)).view(n, l, 2)

    return positions_rotated


class ZeroPaddedCylindricalConv2d(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
    ) -> None:
        super(ZeroPaddedCylindricalConv2d, self).__init__()

        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size)
        self.padding = kernel_size // 2

    def forward(self, input: Any) -> Any:
        raise NotADirectoryError("Not implemented")
