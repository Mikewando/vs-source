from __future__ import annotations

from dataclasses import dataclass
from .sector import SectorReadHelper

__all__ = [
    'AUDIO_FORMAT_AC3',
    'AUDIO_FORMAT_LPCM',

    'VTSVideoAttr',
    'AudioAttr',
    'VTSIMat'
]


AUDIO_FORMAT_AC3 = 0
AUDIO_FORMAT_LPCM = 4


@dataclass
class VTSVideoAttr:
    mpeg_version: int
    video_format: int
    picture_size: int


@dataclass
class AudioAttr:
    audio_format: int
    language: str


@dataclass
class VTSIMat:
    vts_video_attr: VTSVideoAttr
    vts_audio_attr: list[AudioAttr]

    def __init__(self, reader: SectorReadHelper):
        vb0, vb1, = reader._seek_unpack_byte(0x0200, 1, 1)

        mpeg_version = (vb0 & 0b11000000) >> 6
        video_format = (vb0 & 0b00110000) >> 4
        picture_size = (vb1 & 0b00110000) >> 4

        vts_video_attr = VTSVideoAttr(mpeg_version, video_format, picture_size)

        vts_audio_attr = []
        num_audio, = reader._seek_unpack_byte(0x0202, 2)

        for _ in range(num_audio):
            buf = reader.ifo.read(8)

            lang_type = (buf[0] & 0b1100) >> 2
            audio_format = (buf[0] & 0b11100000) >> 5

            if lang_type:
                lang = chr(buf[2]) + chr(buf[3])
            else:
                lang = "xx"

            vts_audio_attr += [AudioAttr(audio_format, lang)]

        self.vts_video_attr = vts_video_attr
        self.vts_audio_attr = vts_audio_attr
