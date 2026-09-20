"""Selection-time facts about a music catalog record.

Why this module exists
----------------------
2026-09-20 the lyric-MV selection flow judged "released on many platforms" by
looking only at whether ``links[].platform`` **keys exist**, and picked a track
that had six platform keys with *empty* URLs (a DistroKid distribution
placeholder). The record had **zero** real channels, but the whole downstream
chain (run scaffold, cover render, three-repo issue churn) had already been
started on top of that false premise.

``catalog.json`` contains 131 / 1307 records of exactly that shape, so any
conversation that reads the raw ``links[]`` structure will repeat the mistake.
This module is the **single gate** every selection flow must pass through.

Two independent traps, two rules
--------------------------------
1. **Placeholder links** — ``platform`` key present, URL empty/whitespace.
   Rule: a channel only counts when ``url.strip()`` is non-empty.
2. **Context links are not channels** — ``official`` (label site), ``github``
   (source repo), ``royazon`` (artist homepage) all carry real URLs but are
   **not distribution channels**. Counting them inflates a 2-channel record
   into a fake 5-channel one.
   Rule: only :data:`DISTRIBUTION_PLATFORMS` are counted by default.

This module *consumes* the channel-status semantics owned by
``music-board#74`` (VERIFIED / PRESENT_UNVERIFIED / MISSING / ...). It does
**not** redefine them and never mutates catalog data.

Pure read-only helpers: no I/O, no network, no global state, safe to call from
scripts, tests, notebooks and agent loops.
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping, Sequence

__all__ = [
    "DISTRIBUTION_PLATFORMS",
    "NON_DISTRIBUTION_PLATFORMS",
    "iter_links",
    "real_platforms",
    "context_platforms",
    "all_linked_platforms",
    "has_placeholder_links",
    "link_audit",
    "is_multi_channel",
    "select_real_distributed",
]

# --------------------------------------------------------------------------
# Platform taxonomy
# --------------------------------------------------------------------------

#: Keys that denote a real music distribution / streaming channel.
DISTRIBUTION_PLATFORMS: frozenset[str] = frozenset(
    {
        "netease",
        "spotify",
        "youtube",
        "youtubemusic",
        "apple",
        "tiktok",
        "qq",
        "qishui",
        "amazon",
        "deezer",
        "tidal",
        "pandora",
        "iheart",
        "qobuz",
        "jiosaavn",
        "saavn",
        "rdio",
        "anghami",
        "boomplay",
        "joox",
        "kusaimedia",
        "kuackmedia",
        "imusica",
        "flo",
        "beats",
        "feedfm",
        "instagram",
    }
)

#: Keys that carry a URL but must never count as a distribution channel.
NON_DISTRIBUTION_PLATFORMS: frozenset[str] = frozenset(
    {"official", "github", "royazon"}
)


# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------


def iter_links(record: Any) -> Iterator[Mapping[str, Any]]:
    """Yield every well-formed link mapping in ``record``.

    Tolerates the shapes that actually occur in the wild: missing ``links``,
    ``links=None``, heterogeneous lists, non-``dict`` members. Never raises.
    """
    if not isinstance(record, Mapping):
        return
    links = record.get("links")
    if not isinstance(links, Iterable) or isinstance(links, (str, bytes)):
        return
    for link in links:
        if isinstance(link, Mapping):
            yield link


def _has_url(link: Mapping[str, Any]) -> bool:
    url = link.get("url")
    return isinstance(url, str) and bool(url.strip())


def all_linked_platforms(record: Any, *, platforms: Sequence[str] | None = None) -> set[str]:
    """Every platform key with a non-empty URL, distribution or not.

    Use this only for diagnostics — never for "is it released" decisions.
    """
    out: set[str] = set()
    for link in iter_links(record):
        if not _has_url(link):
            continue
        key = link.get("platform")
        if not isinstance(key, str) or not key:
            continue
        if platforms is None or key in platforms:
            out.add(key)
    return out


def real_platforms(record: Any, *, platforms: Sequence[str] | None = None) -> set[str]:
    """Return the set of **verified distribution channels** of a record.

    A channel counts only when *all* of the following hold:

    * the link entry is a mapping (tolerated otherwise),
    * ``platform`` is a non-empty string,
    * ``platform`` is a distribution channel (:data:`DISTRIBUTION_PLATFORMS`),
    * ``url`` exists and ``url.strip()`` is non-empty.

    Placeholder rows (key present, URL empty) therefore fall out automatically.
    """
    allow = DISTRIBUTION_PLATFORMS if platforms is None else frozenset(platforms)
    out: set[str] = set()
    for link in iter_links(record):
        if not _has_url(link):
            continue
        key = link.get("platform")
        if isinstance(key, str) and key and key in allow:
            out.add(key)
    return out


def context_platforms(record: Any) -> set[str]:
    """Non-distribution context links (official site / repo / artist page)."""
    return {
        link["platform"]
        for link in iter_links(record)
        if isinstance(link.get("platform"), str)
        and link["platform"] in NON_DISTRIBUTION_PLATFORMS
        and _has_url(link)
    }


def has_placeholder_links(record: Any) -> bool:
    """True when the record declares channels whose URL is still empty.

    Such a record means "submitted for distribution, links not back-filled".
    It is **not** evidence of release.
    """
    for link in iter_links(record):
        key = link.get("platform")
        if isinstance(key, str) and key and key in DISTRIBUTION_PLATFORMS:
            if not _has_url(link):
                return True
    return False


def duplicate_titles(records: Iterable[Any], *, min_records: int = 2) -> dict[str, list[Any]]:
    """Group records that share a normalised title, keeping only real duplicates.

    Identity here is deliberately **title-only and unverified** — ``先把自己哄好``
    exists both as 音右 and as ROYAZON EOM, and unioning their channels would
    silently turn two 2-channel records into a fake 4-channel "work". Whether
    those are the same song is a judgment the catalog owner has not made
    (``identityBasis: same_title_collision; not merged``), so this helper only
    *surfaces* them for review; nothing should merge their channels by default.
    """
    groups: dict[str, list[Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        title = str(record.get("title") or "").strip().casefold()
        if title:
            groups.setdefault(title, []).append(record)
    return {title: group for title, group in groups.items() if len(group) >= min_records}


def link_audit(record: Any) -> dict[str, Any]:
    """Full read-only picture of one record, for logs and evidence comments."""
    return {
        "id": record.get("id") if isinstance(record, Mapping) else None,
        "title": record.get("title") if isinstance(record, Mapping) else None,
        "artist": record.get("artist") if isinstance(record, Mapping) else None,
        "real_platforms": sorted(real_platforms(record)),
        "context_platforms": sorted(context_platforms(record)),
        "all_linked_platforms": sorted(all_linked_platforms(record)),
        "has_placeholder_links": has_placeholder_links(record),
    }


# --------------------------------------------------------------------------
# The gate itself
# --------------------------------------------------------------------------


def is_multi_channel(
    record: Any,
    min_n: int = 3,
    *,
    platforms: Sequence[str] | None = None,
    require: Iterable[str] = (),
) -> bool:
    """The gate every selection flow must call before committing to a song.

    Parameters
    ----------
    min_n:
        Minimum number of verified distribution channels. Catalog reality
        (2026-09-20): no record has netease + apple + spotify + youtube at
        once; realistic multi-channel records carry 3–5 channels, so 3 is the
        sane default and anything above 4 selects almost nothing.
    platforms:
        Restrict counting to this allow-list (default: distribution channels).
    require:
        Channels that must all be present, e.g. ``require=("netease",)`` for a
        domestic-only release line.

    Notes
    -----
    Deliberately *not* named after business intent ("is_released",
    "is_promotable"): this answers one question only — how many channels are
    verifiably linked — so it cannot be quietly overloaded later.
    """
    found = real_platforms(record, platforms=platforms)
    if len(found) < min_n:
        return False
    return frozenset(require) <= found


def select_real_distributed(
    records: Iterable[Any],
    min_n: int = 3,
    *,
    platforms: Sequence[str] | None = None,
    require: Iterable[str] = (),
    song_types: Iterable[str] = ("song",),
) -> list[dict[str, Any]]:
    """Filter records through :func:`is_multi_channel`, richest first.

    Returns :func:`link_audit` dictionaries sorted by channel count desc, then
    title, so the output is stable and reviewable in an issue comment.
    """
    wanted_types = frozenset(song_types)
    hits: list[tuple[int, str, dict[str, Any]]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        if wanted_types and record.get("type") not in wanted_types:
            continue
        if not is_multi_channel(record, min_n, platforms=platforms, require=require):
            continue
        audit = link_audit(record)
        hits.append((len(audit["real_platforms"]), str(audit["title"] or ""), audit))
    hits.sort(key=lambda row: (-row[0], row[1]))
    return [row[2] for row in hits]
