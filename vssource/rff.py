from __future__ import annotations

import warnings
from copy import deepcopy
from itertools import count
from typing import Sequence

from vstools import CustomRuntimeError, T, flatten, remap_frames, vs

__all__ = [
    'apply_rff_array', 'apply_rff_video',
    'cut_array_on_ranges'
]


def apply_rff_array(old_array: Sequence[T], rff: Sequence[int], tff: Sequence[int], prog_seq: Sequence[int]) -> list[T]:
    array_double_rate = list[T]()

    for prog, arr, rffv, tffv in zip(prog_seq, old_array, rff, tff):
        repeat_amount = (3 if rffv else 2) if prog == 0 else ((6 if tffv else 4) if rffv else 2)

        array_double_rate.extend([arr] * repeat_amount)

    assert (len(array_double_rate) % 2) == 0

    for f1, f2 in zip(array_double_rate[::2], array_double_rate[1::2]):
        if f1 != f2:
            warnings.warn(
                f'Ambiguous pattern due to rff {f1}!={f2}\n'
                'This probably just means telecine happened across chapters boundary.'
            )

    return array_double_rate[::2]


def apply_rff_video(
    node: vs.VideoNode, rff: list[int], tff: list[int], prog: list[int], prog_seq: list[int]
) -> vs.VideoNode:
    assert len(node) == len(rff) == len(tff) == len(prog) == len(prog_seq)

    fields = list[dict[str, int]]()
    tfffs = node.std.RemoveFrameProps(['_FieldBased', '_Field']).std.SeparateFields(True)

    for i, current_prg_seq, current_prg, current_rff, current_tff in zip(count(), prog_seq, prog, rff, tff):
        if not current_prg_seq:
            if current_tff:
                first_field = 2 * i
                second_field = 2 * i + 1
            else:
                first_field = 2 * i + 1
                second_field = 2 * i

            fields += [
                {'n': first_field, 'tf': current_tff, 'prg': False},
                {'n': second_field, 'tf': not current_tff, 'prg': False}
            ]

            if current_rff:
                assert current_prg
                fields += [deepcopy(fields[-2])]
        else:
            assert current_prg

            cnt = 1
            if current_rff:
                cnt += 1 + int(current_tff)

            fields += [{'n': 2 * i, 'tf': 1, 'prg': True}, {'n': 2 * i + 1, 'tf': 0, 'prg': True}] * cnt

    # TODO: mark known progressive frames as progressive

    assert (len(fields) % 2) == 0

    for a, (tf, bf) in enumerate(zip(fields[::2], fields[1::2])):
        if tf['tf'] == bf['tf']:
            bf['tf'] = not bf['tf']

            warnings.warn(f'Invalid field transition @{a}')

    for fcurr, fnext in zip(fields[::2], fields[1::2]):
        if fcurr['tf'] == fnext['tf']:
            raise CustomRuntimeError(
                f'Found invalid stream with two consecutive {"top" if fcurr["tf"] else "bottom"} fields!'
            )

    final = remap_frames(tfffs, [x['n'] for x in fields])

    def _set_field(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        f = f.copy()

        f.props.pop('_FieldBased', None)
        f.props._Field = fields[n]['tf']

        return f

    final = final.std.ModifyFrame(final, _set_field)

    woven = final.std.DoubleWeave()[::2]

    def _update_progressive(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        tf = fields[n * 2]
        bf = fields[n * 2 + 1]

        if tf['prg'] and bf['prg']:
            fout.props['_FieldBased'] = 0

        return fout

    return woven.std.ModifyFrame(woven, _update_progressive)


def cut_array_on_ranges(array: list[T], ranges: list[tuple[int, int]]) -> list[T]:
    return [array[i] for i in flatten([range(rrange[0], rrange[1] + 1) for rrange in ranges])]  # type: ignore
