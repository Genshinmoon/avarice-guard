# Interest Redirector / 関心の招待

> **日本語** → 下へ / **English** → [below](#english)

License: **CC0 1.0** (Public Domain) — 誰のものでもなく、みんなのもの。

---

## 日本語

権力・名声・富・刺激への強い関心を、罰するのではなく、公共の役に立つ取り組みへ**「招待」**する**シミュレーション**です。[avarice_guard.py](avarice_guard.py)（強欲の監査）と組み合わせて使います。

> ⚠️ 関心（勝ちたい・認められたい・動かしたい）は、命の本能です。消すものではありません。
> このコードは、人の内心を見抜くものでも、人を転換させるものでもありません。
> 例の取り組みは、すべてシミュレーション上の例で、実在の計画ではありません。

### 仕組み
1. **申告** — 本人が、自分の関心（`power` / `wealth` / `fame` / `thrill`）を申告します。推測はしません。いつでも取り下げられます。
2. **招待** — 理由は2つだけです。
   - 公開の記録の事実（強欲の監査の判定 `REDIRECT` / `HOLD` / `FROZEN`）
   - 本人からの希望
3. **選択** — 申告した関心に合う取り組みを最大3件並べます。**応じる / 断る / あとで考える**のどれも選べます。

### 設計の約束
- 人に点数（強欲指数・抵抗度・受け入れ確率）を付けません。承諾を決めるのは、本人の返事だけです。
- 文面は事実だけです。お世辞も、圧力も、守れない約束（「名が永遠に残る」など）も書きません。
- 承諾は**意思の記録**で、任命ではありません。実際の役割は、共同体の通常の手続きと強欲の監査を通ります。
- 断っても**不利益はありません**。断ったあとは30日、こちらからは招きません（本人が希望すれば、いつでも）。
- 招待は、権限の上限（Power Cap）や監査の**代わりではありません**。受けても断っても、全員に同じように働きます。
- 権力に関わる取り組みには、上限の範囲内・任期つき・公開の監査、という守りが付きます。
- 記録はハッシュの連鎖です。申告した関心の**中身は記録に書きません**（取り下げられるように）。`anchor_line()` の一行を、GitHub のコミットなど外の場所に残せば、作り直しも検出できます。

### 使い方
```bash
python interest_redirector.py --demo   # デモ
python interest_redirector.py --test   # テスト（17件）
```
`shared_signals.py` を同じ場所に置いてください。Python 3.9+。

```python
from interest_redirector import InterestRedirector

r = InterestRedirector()
r.declare_drives("P1", ["wealth"])                 # 本人の申告
inv = r.invite("P1", trigger="REDIRECT")           # 強欲の監査の判定を受けて
print(inv.status, inv.message)
print(r.respond("P1", "accept", inv.offers[0].id)) # 意思の記録（任命ではない）
print(r.anchor_line())                             # 外へ残す一行
```

### 限界
- 関心の申告は自己申告です。本人確認はしません（呼び出す側の責任）。
- 取り組みの例は見本です。本当の取り組みは、人々が議論して決めてください。
- 本当に人の関心が変わるかは、このコードでは分かりません。現実の場で確かめるものです。
- 外への刻印は、実際に外へ残さなければ意味がありません。

---

## English

A **simulation** that **invites** strong drives — power, fame, wealth, thrill — toward public-benefit projects instead of punishing them. Designed to work alongside [avarice_guard.py](avarice_guard.py).

> ⚠️ Drives are part of life; this does not try to erase them.
> It does not read minds or "convert" anyone. All example projects are simulated examples, not real plans.

### How it works
1. **Declare** — a person declares their own drives (`power` / `wealth` / `fame` / `thrill`). Nothing is inferred; it can be withdrawn at any time.
2. **Invite** — only for one of two reasons:
   - a fact in the public record (an Avarice Guard verdict: `REDIRECT` / `HOLD` / `FROZEN`)
   - the person's own request
3. **Choose** — up to 3 projects matching the declared drives are listed. The person may **accept, decline, or decide later**.

### Design commitments
- No scores on people (no greed index, resistance or acceptance probability). Only the person's own answer decides.
- Plain, factual wording: no flattery, no pressure, no promises that can't be kept.
- Accepting records **intent**, not appointment. Any real role goes through the community's normal process and the Avarice Guard.
- Declining carries **no penalty**; no re-invitation for 30 days unless the person asks.
- An invitation is **not a substitute** for the Power Cap or audits — they apply to everyone equally, whether one accepts or not.
- Power-related projects carry safeguards: within the cap, term-limited, publicly audited.
- The ledger is hash-chained; declared drives are **never written into it**. Publish the `anchor_line()` externally (e.g. a GitHub commit) to detect a rebuilt chain.

### Usage
```bash
python interest_redirector.py --demo
python interest_redirector.py --test   # 17 tests
```
Place `shared_signals.py` alongside. Python 3.9+. (See the example above.)

### Limits
- Declarations are self-reported; identity is not verified (the caller's responsibility).
- Example projects are samples; real ones should be decided through deliberation.
- Whether anyone's drives actually shift cannot be known from this code.
- Anchoring only helps if the line is actually published externally.

---
*CC0 1.0 Universal — https://creativecommons.org/publicdomain/zero/1.0/*
