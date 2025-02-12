from __future__ import annotations

import subprocess
from typing import Sequence, SupportsFloat

from vstools import SupportsString

from .parsedvd import IFOX

__all__ = [
    'double_check_dvdnav',
    'absolute_time_from_timecode',
    'get_sectorranges_for_vobcellpair',

    'PTS_SYNC', 'PCR_CLOCK'
]


PTS_SYNC = 2880
PCR_CLOCK = 90_000


# d2vwitch needs this patch applied
# https://gist.github.com/jsaowji/ead18b4f1b90381d558eddaf0336164b

# https://gist.github.com/jsaowji/2bbf9c776a3226d1272e93bb245f7538
def double_check_dvdnav(iso: SupportsString, title: int) -> list[float] | None:
    try:
        ap = subprocess.check_output(["dvdsrc_dvdnav_title_ptt_test", str(iso), str(title)])

        return list(map(float, ap.splitlines()))
    except FileNotFoundError:
        ...

    return None


def absolute_time_from_timecode(timecodes: Sequence[SupportsFloat]) -> list[float]:
    absolutetime = list[float]([0.0])

    for i, a in enumerate(timecodes):
        absolutetime.append(absolutetime[i] + float(a))

    return absolutetime


def get_sectorranges_for_vobcellpair(current_vts: IFOX, pair_id: tuple[int, int]) -> list[tuple[int, int]]:
    return [
        (e.start_sector, e.last_sector)
        for e in current_vts.vts_c_adt.cell_adr_table
        if (e.vob_id, e.cell_id) == pair_id
    ]
