#!/usr/bin/env python
"""Replay tests for the selection harness traps (lyric-mv-kit#9).

Fixtures mirror real records as of 2026-09-20. They cover the three ways a
single title can masquerade as a richer release than it is:

1. placeholder links — platform keys without URLs;
2. context links — real URLs that are not distribution channels;
3. same-title different-song — two records of `Neon Snow` whose lyric bodies
   score 0.02 against each other, versus 0.99-1.00 for the genuine pairings.

Running:
    pytest tests/test_selection_harness.py -q
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_catalog.py"
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("audit_catalog", SCRIPT)
assert _spec and _spec.loader
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

COVERAGE_ROW = {
    "recordId": "isrc-QT6G32510404",
    "title": "Neon Snow",
    "artist": "ROYAZON EOM",
    "identityBasis": "ISRC",
    "coverageClass": "possible_cross_record",
    "hasSpotify": True,
    "hasApple": True,
    "hasYoutube": True,
    "hasYoutubeMusic": True,
    "hasNetease": False,
    "spotifyUrl": "",
    "appleUrl": "https://music.apple.com/us/album/1",
    "youtubeMusicUrl": "https://music.youtube.com/watch?v=1",
    "neteaseUrl": "",
    "neteaseStatus": "missing",
}

CATALOG_RECORD = {
    "id": "netease-song-3401089173",
    "title": "Neon Snow",
    "artist": "音右",
    "type": "song",
    "lyrics": "作词 : 音右\nLights drip like melted stars\nNeon snow",
    "links": [{"platform": "netease", "url": "https://music.163.com/#/song?id=1"}],
}

SAME_SONG_OTHER_PLATFORM = {
    "id": "isrc-QT6G32510404",
    "title": "Neon Snow",
    "artist": "ROYAZON EOM",
    "type": "song",
    "lyrics": "Cliding on the ice so thin a crackle a whisper where to begin",
    "links": [],
}

REAL_PAIR_A = {
    "id": "isrc-QT6G22544446",
    "title": "Tropical Beat",
    "artist": "ROYAZON EOM",
    "type": "song",
    "lyrics": "[intro] warm air hums a secret song 温暖的空气哼着秘密的歌",
    "links": [
        {"platform": "apple", "url": "https://music.apple.com/x"},
        {"platform": "spotify", "url": "https://open.spotify.com/x"},
    ],
}

REAL_PAIR_B = {
    "id": "netease-song-3326694391",
    "title": "Tropical Beat",
    "artist": "音右",
    "type": "song",
    "lyrics": "作词 : 音右\n[intro] warm air hums a secret song 温暖的空气哼着秘密的歌",
    "links": [{"platform": "netease", "url": "https://music.163.com/#/song?id=2"}],
}


# --------------------------------------------------------------------------
# coverage ledger projection
# --------------------------------------------------------------------------


def test_coverage_row_projects_only_url_backed_channels():
    from lyric_mv.dataset import real_platforms

    record = audit.coverage_row_to_record(COVERAGE_ROW)
    # spotify is flagged but has no URL -> it is NOT a verified channel
    assert real_platforms(record) == {"apple", "youtube", "youtubemusic"}


def test_coverage_flag_only_channel_excluded_from_gate_but_kept_as_evidence():
    record = audit.coverage_row_to_record(COVERAGE_ROW)
    platforms = {link["platform"] for link in record["links"]}
    # the gate must not count a flag-without-URL as a real channel (the ledger
    # twin of the DistroKid placeholder trap); the evidence is preserved though
    assert "spotify" not in platforms
    assert record["meta"]["flag_only_channels"] == ["spotify"]
    assert any(l["url"].startswith("https://") for l in record["links"])


def test_load_records_detects_coverage_shape(tmp_path):
    path = tmp_path / "coverage.json"
    path.write_text('{"version":1,"rows":[%s]}' % _dump(COVERAGE_ROW), encoding="utf-8")
    records = audit.load_records(path)
    assert len(records) == 1
    assert records[0]["id"] == "isrc-QT6G32510404"


def test_load_records_still_handles_raw_catalog(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text('{"items":[%s]}' % _dump(CATALOG_RECORD), encoding="utf-8")
    records = audit.load_records(path)
    assert records[0]["id"] == "netease-song-3401089173"


# --------------------------------------------------------------------------
# same title != same song
# --------------------------------------------------------------------------


def test_same_title_different_lyrics_stay_separate_works():
    clusters = audit.content_clusters([CATALOG_RECORD, SAME_SONG_OTHER_PLATFORM])
    assert len(clusters) == 2, "two different songs must not become one work"


def test_same_title_matching_lyrics_merge():
    clusters = audit.content_clusters([REAL_PAIR_A, REAL_PAIR_B])
    assert len(clusters) == 1


def test_merge_never_invents_the_neon_snow_five_channel_work():
    from lyric_mv.dataset import real_platforms

    merged = audit.merge_identity_records([CATALOG_RECORD, SAME_SONG_OTHER_PLATFORM])
    channels = set().union(*(real_platforms(r) for r in merged))
    assert channels == {"netease"}, "Neon Snow is not a 5-channel work"


def test_neon_snow_excluded_from_four_channel_gate():
    from lyric_mv.dataset import real_platforms

    # ISRC record (flag-only spotify, real apple/youtube/youtubemusic) carries
    # the same dissociated lyrics as SAME_SONG_OTHER_PLATFORM; the 音右 record
    # carries different lyrics. They disagree (0.02) so content_clusters keeps
    # them as two works, neither of which reaches 4 verified channels.
    isrc_record = audit.coverage_row_to_record(COVERAGE_ROW)
    isrc_record["lyrics"] = SAME_SONG_OTHER_PLATFORM["lyrics"]
    merged = audit.merge_identity_records([isrc_record, dict(CATALOG_RECORD)])
    counts = sorted(len(real_platforms(r)) for r in merged)
    assert counts == [1, 3], "netease-only + apple/youtube/youtubemusic-only"
    assert all(len(real_platforms(r)) < 4 for r in merged)


def test_merge_produces_the_real_five_channel_work():
    from lyric_mv.dataset import is_multi_channel

    row = {
        # the global record for the same song the netease record belongs to
        "id": "isrc-QT6G22544446",
        "title": "Tropical Beat",
        "artist": "ROYAZON EOM",
        "type": "song",
        "lyrics": "[intro] warm air hums a secret song 温暖的空气哼着秘密的歌",
        "links": [
            {"platform": "apple", "url": "https://music.apple.com/x"},
            {"platform": "spotify", "url": "https://open.spotify.com/x"},
            {"platform": "youtube", "url": "https://www.youtube.com/watch?v=x"},
            {"platform": "youtubemusic", "url": "https://music.youtube.com/x"},
        ],
    }
    merged = audit.merge_identity_records([row, REAL_PAIR_B])
    assert len(merged) == 1
    assert is_multi_channel(merged[0], 5) is True


def test_records_without_lyrics_still_group_by_title():
    a = {"title": "X", "links": [], "artist": "音右"}
    b = {"title": "X", "links": [], "artist": "ROYAZON EOM"}
    assert len(audit.content_clusters([a, b])) == 1


def test_attach_lyrics_fills_missing_bodies(tmp_path):
    isrc_side = dict(SAME_SONG_OTHER_PLATFORM)  # same recordId as COVERAGE_ROW
    isrc_side["lyrics"] = "Neon snow\nIt glows so slow\nBurns the dark"
    catalog = tmp_path / "catalog.json"
    catalog.write_text('{"items":[%s]}' % _dump(isrc_side), encoding="utf-8")
    records = [audit.coverage_row_to_record(COVERAGE_ROW)]
    audit.attach_lyrics(records, catalog)
    assert "Neon snow" in records[0]["lyrics"]


def test_attach_lyrics_leaves_unknown_records_alone(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text('{"items":[]}', encoding="utf-8")
    records = [audit.coverage_row_to_record(COVERAGE_ROW)]
    audit.attach_lyrics(records, catalog)
    assert "lyrics" not in records[0]


def _dump(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)
