# Avarice Guard / 強欲の監査

> **日本語** → 下へ / **English** → [below](#english)

License: **CC0 1.0** (Public Domain) — 誰のものでもなく、みんなのもの。

---

## 日本語

権力・利権・金銭欲が一か所に集中しすぎないよう、**行為と数字**で見えるようにする、組織モデルの**シミュレーション**です。

> ⚠️ これは「欲望を消す」コードではありません。欲望は生命の本能です。
> 実際の政治・経済・防衛・行政を動かすものでもありません。本当の再分配や制度は、人々の議論が決めるものです。

### 3つの防壁
1. **利害の透明化** — 提案者は、自分と関係者が得る利益を申告します。第三者は申告に異議を出せます（2人で保留）。
2. **権力の上限（Power Cap）** — 一人（と、申告された関係者の合計）が持てる権限に固い上限。監査局でも解除できません。
3. **公共への還元** — 私的利益が公共の利益の一定割合を超えた**超過分だけ**を、公共（コモンズ）へ回す条件にします。

### 判定
| 判定 | 意味 |
|---|---|
| ALLOW | 承認できます |
| REDIRECT | 超過分を公共へ回す条件で承認できます |
| HOLD | 第三者の審査が要ります（監査局の過半数で解除可） |
| FROZEN | 権限の上限を超えるため凍結（解除不可。減らして出し直す） |

### 設計の約束
- `propose()` は**通知だけ**。何も動かしません。`adopt()` で初めて権限・富・コモンズが動きます。
- 人に点数（強欲指数など）は付けません。見るのは権限の集中・直近の記録・第三者の異議という**観察できる事実**だけ。
- 関係の申告は**罰しません**（正直さが損にならないように）。止まるのは「増やす議案」だけです。
- 異議（`file_appeal`）は記録され、人が見ます。自動では覆りません。
- 記録はハッシュの連鎖で、`anchor_line()` の一行を GitHub のコミットなど**外の公開の場所**に残すと、作り直しも検出できます。

### 使い方
```bash
python avarice_guard.py --demo   # デモ
python avarice_guard.py --test   # テスト（37件）
```
`shared_signals.py` を同じ場所に置いてください。Python 3.9+。

```python
from avarice_guard import AvariceGuard, Actor

g = AvariceGuard(auditors=("AUD1", "AUD2", "AUD3"))
g.register_actor(Actor("A1", "市民", "human", power=0.5, wealth=1.0))
r = g.propose("A1", "公園を作る", public_benefit=10.0, proposer_benefit=0.5, power_gain=0.1)
print(r.verdict, r.reasons)
g.adopt(r.motion_id, "A1")        # 共同体の採決が通ったあとに呼ぶ
print(g.get_community_health())
print(g.anchor_line())            # 外へ残す一行
```
- [interest_redirector.py](interest_redirector.py) — 関心の招待（[README](README_interest_redirector.md)）

### 限界
- 利益・関係者の申告は自己申告です。名義貸しや、別人格に見せたAIの複製は見抜けません。
- 3.0・0.5・0.8・ジニ 0.6 などは**見本の値**です。議論して決めてください。
- `adopt()` は、採決が本当に通ったかを確かめません（呼ぶ側の責任）。
- 外への刻印は、実際に外へ残さなければ意味がありません。

---

## English

A **simulation** of an organizational model that makes excessive concentration of power, vested interests and wealth visible through **actions and numbers**.

> ⚠️ This does not try to erase desire — desire is part of life.
> It does not run any real government, economy, defense or administration. Real redistribution and institutions are for people to decide through deliberation.

### Three defenses
1. **Transparency of interest** — proposers declare benefits to themselves and affiliates. Third parties can challenge a declaration (two challenges trigger a hold).
2. **Power Cap** — a hard limit on the power one actor (plus declared affiliates, combined) may hold. Even the audit board cannot lift it.
3. **Return to the commons** — only the **excess** of private benefit over a set share of public benefit is routed to the commons, as a condition of adoption.

### Verdicts
| Verdict | Meaning |
|---|---|
| ALLOW | Can proceed |
| REDIRECT | Can proceed if the excess goes to the commons |
| HOLD | Needs third-party review (lifted by an audit-board majority) |
| FROZEN | Over the power cap (cannot be lifted; resubmit with less) |

### Design commitments
- `propose()` is **a notice only** — it changes nothing. State moves only on `adopt()`.
- No scores on people (no "greed index"). Only observable facts: concentration of power, recent record, third-party challenges.
- Declaring affiliations is **never punished**; only motions that *increase* power are stopped.
- Appeals (`file_appeal`) are recorded for humans; never auto-reversed.
- The ledger is hash-chained; publishing the `anchor_line()` somewhere external (e.g. a GitHub commit) lets anyone detect a rebuilt chain.

### Usage
```bash
python avarice_guard.py --demo
python avarice_guard.py --test   # 37 tests
```
Place `shared_signals.py` alongside. Python 3.9+. (See the example above.)

### Limits
- Declarations are self-reported; straw men and AI copies posing as separate actors are undetectable.
- 3.0, 0.5, 0.8, Gini 0.6 etc. are **sample thresholds** — decide them through deliberation.
- `adopt()` does not verify that a vote actually passed (the caller's responsibility).
- Anchoring only helps if the line is actually published externally.

---
*CC0 1.0 Universal — https://creativecommons.org/publicdomain/zero/1.0/*
