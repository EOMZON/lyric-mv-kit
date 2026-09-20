"""Replay tests for the selection gate (lyric-mv-kit#9).

Fixtures are faithful copies of real ``music-board/catalog.json`` records as
of 2026-09-20; they are the two cases that caused the live mis-selection and
must never regress.

Trap A — placeholder links: every platform key present, every URL empty
         (DistroKid "submitted, links not back-filled"). Real channels: 0.
Trap B — context links counted as channels: official site / GitHub repo /
         artist homepage carry real URLs but are not distribution channels.

Running:
    python -m pytest tests/test_dataset_selection_gate.py -q
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from lyric_mv.dataset import (
    DISTRIBUTION_PLATFORMS,
    NON_DISTRIBUTION_PLATFORMS,
    all_linked_platforms,
    context_platforms,
    duplicate_titles,
    has_placeholder_links,
    is_multi_channel,
    link_audit,
    real_platforms,
    select_real_distributed,
)

# --- Trap A: the record that caused the 2026-09-20 mis-selection ------------
SILENCE_STILL_PLACEHOLDER = {
    "id": "distrokid-track-A6DCD6B3-56C7-4330-B4B0B8110C3C0928-8",
    "title": "Silence Still",
    "artist": "ROYAZON EOM",
    "type": "song",
    "links": [
        {"platform": "spotify", "label": "Spotify", "url": ""},
        {"platform": "apple", "label": "Apple Music", "url": ""},
        {"platform": "tiktok", "label": "TikTok", "url": ""},
        {"platform": "youtube", "label": "YouTube Music", "url": ""},
        {"platform": "netease", "label": "网易云", "url": ""},
        {"platform": "qq", "label": "QQ 音乐", "url": ""},
    ],
}

# Same title, second record in the catalog: no links at all.
SILENCE_STILL_EMPTY = {
    "id": "distrokid-track-0E0FD286-2189-46E1-B1E4103A616BD336-6",
    "title": "Silence Still",
    "artist": "ROYAZON EOM",
    "type": "song",
    "links": [],
}

# --- Trap B: context links inflate a 2-channel record into "5 channels" -----
WO_JUJUE_BEI_DINGYI = {
    "id": "netease-song-3422948585",
    "title": "我拒绝被定义",
    "artist": "音右",
    "type": "song",
    "links": [
        {"platform": "netease", "label": "网易云 · 单曲",
         "url": "https://music.163.com/#/song?id=3422948585"},
        {"platform": "official", "label": "官网 · music.zondev.top",
         "url": "https://music.zondev.top"},
        {"platform": "youtube", "label": "YouTube · Lyric MV",
         "url": "https://www.youtube.com/watch?v=rxPFQV7zfMg"},
        {"platform": "github", "label": "GitHub · lyric-mv-kit",
         "url": "https://github.com/EOMZON/lyric-mv-kit"},
        {"platform": "royazon", "label": "ROYAZON 音乐主页",
         "url": "https://music.zondev.top"},
    ],
}

# --- A healthy multi-channel record used as the "selectable" baseline -------
PERFORATED_DREAM = {
    "id": "distrokid-track-<christmas>",
    "title": "Perforated Dream",
    "artist": "ROYAZON EOM",
    "type": "song",
    "links": [
        {"platform": "spotify", "label": "Spotify", "url": "https://open.spotify.com/track/x"},
        {"platform": "apple", "label": "Apple Music", "url": "https://music.apple.com/x"},
        {"platform": "youtube", "label": "YouTube", "url": "https://www.youtube.com/watch?v=x"},
        {"platform": "youtubemusic", "label": "YouTube Music", "url": "https://music.youtube.com/x"},
        {"platform": "tiktok", "label": "TikTok", "url": ""},
        {"platform": "netease", "label": "网易云", "url": ""},
        {"platform": "qq", "label": "QQ 音乐", "url": ""},
    ],
}


# --------------------------------------------------------------------------
# Acceptance case 1 — Trap A must never pass the gate
# --------------------------------------------------------------------------


def test_placeholder_record_has_zero_real_channels():
    assert real_platforms(SILENCE_STILL_PLACEHOLDER) == set()


def test_placeholder_record_is_not_multi_channel_even_at_min_n_1():
    for min_n in (1, 2, 3, 4):
        assert is_multi_channel(SILENCE_STILL_PLACEHOLDER, min_n) is False


def test_placeholder_record_is_flagged():
    assert has_placeholder_links(SILENCE_STILL_PLACEHOLDER) is True
    # a record with no links at all is empty, not "pending back-fill"
    assert has_placeholder_links(SILENCE_STILL_EMPTY) is False


def test_record_without_links_has_zero_channels():
    assert real_platforms(SILENCE_STILL_EMPTY) == set()


def test_whitespace_only_url_does_not_count():
    record = {"links": [{"platform": "spotify", "url": "   \t\n"}]}
    assert real_platforms(record) == set()


# --------------------------------------------------------------------------
# Acceptance case 2 — context links must not inflate channel count
# --------------------------------------------------------------------------


def test_context_links_are_excluded_from_real_platforms():
    assert real_platforms(WO_JUJUE_BEI_DINGYI) == {"netease", "youtube"}


def test_context_platforms_are_reported_separately():
    assert context_platforms(WO_JUJUE_BEI_DINGYI) == {"official", "github", "royazon"}


def test_all_linked_platforms_still_shows_the_inflated_view_for_diagnostics():
    assert all_linked_platforms(WO_JUJUE_BEI_DINGYI) == {
        "netease", "youtube", "official", "github", "royazon",
    }


def test_two_real_channels_does_not_satisfy_default_gate():
    assert is_multi_channel(WO_JUJUE_BEI_DINGYI) is False
    assert is_multi_channel(WO_JUJUE_BEI_DINGYI, 2) is True


# --------------------------------------------------------------------------
# Healthy record + require filter
# --------------------------------------------------------------------------


def test_healthy_record_passes_default_gate():
    assert real_platforms(PERFORATED_DREAM) == {
        "spotify", "apple", "youtube", "youtubemusic",
    }
    assert is_multi_channel(PERFORATED_DREAM) is True
    assert is_multi_channel(PERFORATED_DREAM, 4) is True


def test_require_filters_out_records_missing_a_channel():
    assert is_multi_channel(PERFORATED_DREAM, 3, require=("netease",)) is False
    assert is_multi_channel(WO_JUJUE_BEI_DINGYI, 2, require=("netease",)) is True


def test_select_real_distributed_sorts_richest_first():
    rows = select_real_distributed(
        [SILENCE_STILL_PLACEHOLDER, WO_JUJUE_BEI_DINGYI, PERFORATED_DREAM, SILENCE_STILL_EMPTY],
        min_n=3,
    )
    assert [r["title"] for r in rows] == ["Perforated Dream"]


def test_select_real_distributed_respects_type_filter():
    album = {"id": "x", "title": "Album", "type": "album", "links": PERFORATED_DREAM["links"]}
    rows = select_real_distributed([album], min_n=3)
    assert rows == []
    rows = select_real_distributed([album], min_n=3, song_types=("album",))
    assert [r["title"] for r in rows] == ["Album"]


def test_duplicate_titles_surfaces_collisions_without_merging():
    # 《先把自己哄好》exists as 音右 (netease+spotify) and as ROYAZON EOM
    # (spotify+youtube+youtubemusic). Unioning them would fabricate a
    # 4-channel "work" the catalog owner has not adjudicated, so the gate must
    # report per-record and only *surface* the collision.
    first = dict(WO_JUJUE_BEI_DINGYI)
    first["title"] = "先把自己哄好"
    second = dict(PERFORATED_DREAM)
    second["title"] = "先把自己哄好"

    groups = duplicate_titles([first, second, PERFORATED_DREAM])
    assert list(groups) == ["先把自己哄好"]
    assert len(groups["先把自己哄好"]) == 2

    # nothing was merged behind our back: each record keeps its own channels
    assert real_platforms(first) == {"netease", "youtube"}
    assert real_platforms(second) == {
        "spotify", "apple", "youtube", "youtubemusic",
    }


def test_duplicate_titles_is_case_insensitive_and_ignores_blanks():
    a = {"title": " Silence Still ", "links": []}
    b = {"title": "silence still", "links": []}
    assert len(duplicate_titles([a, b])) == 1
    assert duplicate_titles([{"title": "  "}, {"links": []}, None]) == {}


# --------------------------------------------------------------------------
# Robustness — malformed input must degrade, never crash
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        None,
        {},
        {"links": None},
        {"links": "https://not-a-list"},
        {"links": [None, 42, "spotify"]},
        {"links": [{"platform": None, "url": "https://x"}]},
        {"links": [{"platform": "spotify"}]},  # url missing entirely
        {"links": [{"url": "https://x"}]},  # platform missing entirely
        {"links": {"weird": "shape"}},
    ],
)
def test_malformed_records_do_not_raise(record):
    assert real_platforms(record) == set()
    assert is_multi_channel(record) is False


def test_missing_url_field_counts_as_placeholder():
    # platform declared, url key absent -> "submitted, link missing"
    assert has_placeholder_links({"links": [{"platform": "spotify"}]}) is True


def test_unnamed_or_context_link_does_not_count_as_placeholder():
    # no platform key -> nothing was ever claimed for that channel
    assert has_placeholder_links({"links": [{"url": "https://x"}]}) is False
    # context links are outside the distribution gate entirely
    assert has_placeholder_links({"links": [{"platform": "github"}]}) is False


def test_non_distribution_keys_are_never_counted():
    for key in NON_DISTRIBUTION_PLATFORMS:
        record = {"links": [{"platform": key, "url": "https://x"}]}
        assert real_platforms(record) == set()
        assert key not in DISTRIBUTION_PLATFORMS


def test_link_audit_shape_is_serialisable():
    audit = link_audit(PERFORATED_DREAM)
    assert json.loads(json.dumps(audit)) == audit
    assert audit["has_placeholder_links"] is True  # tiktok/netease/qq empty
    assert audit["real_platforms"] == ["apple", "spotify", "youtube", "youtubemusic"]


# --------------------------------------------------------------------------
# Optional: replay against the real catalog when it is present locally
# --------------------------------------------------------------------------

CATALOG_CANDIDATES = (
    Path.home() / "codex" / "music-board" / "catalog.json",
    Path("D:/ZON/codex/music-board/catalog.json"),
)


def _load_real_catalog() -> list[dict] | None:
    for path in CATALOG_CANDIDATES:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data["items"] if isinstance(data, dict) else data
            return items  # type: ignore[return-value]
    return None


@pytest.mark.skipif(_load_real_catalog() is None, reason="music-board/catalog.json not present")
def test_replay_against_real_catalog():
    items = _load_real_catalog()
    assert items is not None
    by_title = {str(it.get("title", "")).strip(): it for it in items}

    silence = by_title["Silence Still"]
    assert real_platforms(silence) == set(), "placeholder record must stay at 0 channels"

    rows = select_real_distributed(items, min_n=3)
    titles = {r["title"] for r in rows}
    assert "Silence Still" not in titles
    assert len(rows) > 0
