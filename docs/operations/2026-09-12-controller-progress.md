# Lyric MV 操作总结与进度

日期：2026-09-12。范围为仓库已有公开的 wind-dream 渲染候选；不包含私人运营信息，不代表成片发行或平台上传完成。

## 已完成的代码与历史验证

- `dfd632c473db23cb84f5b07ec22ab140aed9dfdb` 修复逐字 alpha 突变与 glyph crop 错位，并增加空白字像素差审计。
- `811c7a43561b3099072d5db21736cf9a62822287` 增加背景漂移、呼吸光晕、频谱、音符、微粒五层独立开关，复用已有音频特征缓存。
- 历史全曲审计：1664 帧、12957 次字形测量、最小 coverage 0.2187、空白字符 0，PASS；22 秒片段也有独立记录。本轮没有重新渲染、听校或运行审计。
- 可复查源记录：[修复与剩余事项](https://github.com/EOMZON/lyric-mv-kit/blob/811c7a43561b3099072d5db21736cf9a62822287/runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/HANDOFF-truncation.md)、[全曲审计](https://github.com/EOMZON/lyric-mv-kit/blob/811c7a43561b3099072d5db21736cf9a62822287/runs/wind-dream/lyric-paper-staff-v1/v20260910-01/03_render/blank-char-audit-full.json)。

## 当前保存与未完成边界

代码候选位于远端 `codex/mv03-v4-intro` 历史，当前该分支为 `64f66d906f3b159ec7abb6b7eba716905f93336a`，包含上述提交；不能把其后续改动自动归入本轮审核。main 为 `7dbdfc3fc41f0e74d9ee775120b0da832ddf5dec`，本报告不合并代码。

仍待处理：人工听校、对齐精度判断与主观观感终审；如需调整模板记录，应新建实验 run 或追加事实字段，不能改写历史 run 的模板归属。原输出视频及特征缓存是 ignored 的本地产物，代码已保存不等于二进制已经远端备份；其持久化副本本轮没有核验。

接续者需具备源素材与含 numpy 等依赖的渲染环境，再按上述源记录运行 `render_wind_dream_combined_v2.py` 与 `check_no_blank_chars.py`。现有记录的 Windows 现场运行环境本轮未连接，不能把 Git 文档检查写成实际成片验收。发行、上传、跨平台播放均不在已完成结论中。

## 本次报告交付

从当前 main 创建独立 `docs/controller-progress-20260912`，只提交本报告及精确报告分支的 Vercel 自动部署禁用配置。仓库原无该配置，未修改其他分支规则，未新增 workflow、上传素材或触发渲染。报告推送后核对精确远端 SHA 和报告内容。
