from __future__ import annotations
import os
import subprocess
from vstools import SPath, core
from .D2VWitch import D2VWitch

__all__ = [
    'DGIndex'
]

import shutil


class DGIndex(D2VWitch):
    _bin_path = 'dgindex'
    _ext = 'd2v'
    _source_func = core.lazy.d2v.Source  # type: ignore

    def get_cmd(
        self, files: list[SPath], output: SPath,
        idct_algo: int = 5, field_op: int = 2, yuv_to_rgb: int = 1
    ) -> list[str]:
        is_linux = os.name != "nt"

        if is_linux:
            output = SPath("Z:\\" + str(output)[1:])
            files = [subprocess.check_output(['winepath', '-w', f]).decode("utf-8").strip() for f in files]

        for f in files:
            assert not (" " in f)
        lst = list(map(str, [
            self._get_bin_path(),
            "-IF=[" + ','.join([f'{str(path)}' for path in files]) + ']',
            "-IA=" + str(idct_algo), "-FO=" + str(field_op), "-YR=" + str(yuv_to_rgb),
            "-OM=0", "-OF=[" + str(output).replace(".d2v", "") + "]", "-HIDE", "-EXIT"
        ]))

        return lst