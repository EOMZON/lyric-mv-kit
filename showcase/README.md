# Showcase

These images are rendered with the renderer in this repo — they are **not** frame
grabs from any production song. No audio, no full-frame video from any
reference song is included.

| File | Origin |
|------|--------|
| `cover.png` | `python -m lyric_mv cover --title "我拒绝被定义" --subtitle "ROYAZON · 极光歌词MV"` |
| `styles/A_editorial_air.png` … `styles/H_prism_kaleidoscope.png` | `python -m lyric_mv preview --style all --times 8` on a 16-second synthetic test tone |

All eight stills were produced from the same `plan.json` and
`audio_features.npz` to make the differences between styles legible: the audio
energy is identical, only the visual treatment changes. The actual lyrics are
a placeholder (`副歌来了别眨眼` — "the chorus is here, don't blink") so anyone
reading the source can see the same text shaping across radically different
visual treatments.

## Reference song and video

The renderer in this form was originally used to produce the aurora-ribbon
lyric MV for the song 《我拒绝被定义》 by ROYAZON / 音右:

- Bili: https://space.bilibili.com/ (see `docs/PORTING-TO-REMOTION.md` /
  this README for the canonical URL once the public video ships)
- NetEase: https://music.163.com/#/song?id=3422948585
- Brand: https://music.zondev.top

The reference MV is **not** redistributed in this repo. The cover above is
redrawn from the same tokens as the shipped video, which is why the look is
identical.