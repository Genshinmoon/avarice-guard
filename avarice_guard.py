#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
avarice_guard.py -- 強欲の監査 / Avarice Guard（訂正版 v1.1）
License: CC0 1.0 Universal (public domain)

権力・利権・金銭欲の過度な集中を防ぎ、共鳴文明の富と権力の健全な分散を守る、組織モデル（シミュレーション）。
A simulation of a guard against excessive concentration of power, vested interests and wealth.

【位置づけ】
これは「欲望を消す」コードではありません。欲望は生命の本能です。
行うのは、「個人の過度な欲望が、他者の生命や社会全体の利益を踏みにじること」を、人柄ではなく『行為と数字』で見える
ようにし、権限に『上限』を置き、上限を超える私的利益を『公共へ回す条件』にすることです。
本物の経済や政治は、このコードでは動きません。実際の再分配は、政治の議論と制度が決めるものです。

【3つの防壁】
  1. 利害の透明化: 提案者は、自分と関係者が得る利益を申告する。第三者は『申告への異議』を出せる（2人で保留）。
  2. 権力の上限: 一人（と、申告された関係者の合計）が持てる権限に、固い上限（Power Cap）。上限は、監査局でも解除できない。
  3. 公共への還元: 私的利益が、公共の利益の一定割合を超えた『超過分』だけを、公共（コモンズ）へ回す条件にする。

【v1.0 からの訂正】
  1. 先頭に、コードではない一文が混じっていた（そのままでは動かない）。→ 削除。
  2. 議案を『提出』しただけで、権限が増えていた（採決も採用も無いまま）。→ 監査と採用を分けた。
     propose() は通知だけで、何も動かさない。adopt() で初めて動く（共同体の採決が通ったあとに、呼ぶ）。
  3. 公共の利益が 0 の議案は、利益相反の検査が飛ばされて、ALLOW になった（純粋な私益が、通る穴）。→ 塞いだ。
  4. 検査が elif の連鎖で、最初の理由だけを見て、他の問題を隠した。→ すべての理由を並べ、最も重い判定を採る。
  5. REDIRECT で、私的利益『全額』を公共へ回していた。→ 超過分だけ（比例的）。回した額は、コモンズに記録する。
     （v1.0 は『再分配した』と言うだけで、どこにも記録していなかった。）
  6. 『強欲指数』（人に付ける、主観の数字）を廃止。人柄の評価は、検証できず、烙印になる。
     → 観察できる事実だけ: 権限の集中、直近の記録、第三者の異議。
  7. 同じ議案番号で、審査済みの議案を上書きできた。→ 番号は自動で振り、重複は無い。
  8. 登録のとき、上限を超える権限や、重複した名前を、そのまま受け付けた。→ 検査。数値は有限の数のみ（NaN・負・真偽値を拒む）。
  9. 一人の上限は、関係者に権限を分ければ、すり抜けられた。→ 申告された関係者との『合計』で上限を見る。
     ただし、関係の申告そのものは、罰さない（正直さが、損にならないように）。増やす議案だけが、止まる。
 10. 共同体の健全性が、強欲指数の『合計』（人数が増えるほど悪化する）だった。→ ジニ係数・最大集中・コモンズの額。
 11. 記録は、書き換えられる文字列のリストだった。→ 凍結＋ハッシュの連鎖＋外への刻印（anchor）。
 12. 異議の道が無かった。→ 異議（file_appeal）は記録され、人が見る。自動では覆らない。
 13. 『強制的に回される』という表現を改めた。この門は、採用の『前提条件の通知』であって、強制ではない。

【限界】
  ・利益の申告は、自己申告です。隠された利益は、見えません。第三者の異議と、監査局の目が、補います。
  ・関係者の申告も、自己申告です。申告されない関係（名義貸し・別人格のAIの複製）は、見抜けません。
  ・0.5、3.0、0.8 などは、見本の値です。本当の値は、議論して決めるものです。
  ・採決が本当に通ったかを、このコードは確かめません（adopt を呼ぶ側の責任です）。
  ・外への刻印は、あなたが実際に外へ残さなければ、意味がありません。

実行: python avarice_guard.py --demo / --test
（shared_signals.py を、同じ場所に置いてください）
"""
from __future__ import annotations

import argparse
import hashlib
import math
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from shared_signals import NATURES_ALL, check_anchor, make_anchor

# ── 閾値（見本の値） ──
MAX_POWER_CAP = 3.0          # 一人（と関係者の合計）が持てる権限・影響力の上限（相対値）。固い上限
CONFLICT_THRESHOLD = 0.5     # 私的利益が、公共の利益のこの割合を超えた分は、公共へ回す
NEAR_CAP_RATIO = 0.8         # 上限のこの割合に達する増加は、第三者の審査（保留）
CHALLENGES_TO_HOLD = 2       # 申告への異議が、この人数に達したら、保留
REPEAT_FLAGS = 2             # 直近の議案で、これだけ『凍結・還元』があれば、次は保留
HISTORY_WINDOW = 5           # 直近の何議案を見るか（古い記録は、薄れる）
WEALTH_GINI_WARN = 0.6       # 富のジニ係数の、注意ライン
TOP_SHARE_WARN = 0.5         # 最大の集団が持つ富の割合の、注意ライン
EPS = 1e-9
MAX_NAME = 40

KINDS = tuple(n for n in NATURES_ALL if n != "nature_sensor")     # human / ai / asi / wildcard

ALLOW, HOLD, REDIRECT, FROZEN = "ALLOW", "HOLD", "REDIRECT", "FROZEN"
LABELS = {ALLOW: "承認できます", HOLD: "第三者の審査が要ります（保留）",
          REDIRECT: "超過分を公共へ回す条件で、承認できます", FROZEN: "権限の上限を超えるため、凍結"}
_PRIORITY = (FROZEN, HOLD, REDIRECT, ALLOW)


def _num(v: Any, name: str, lo: Optional[float] = 0.0, hi: Optional[float] = None) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{name} は有限の数値です: {v!r}")
    if lo is not None and v < lo:
        raise ValueError(f"{name} は {lo} 以上です: {v!r}")
    if hi is not None and v > hi:
        raise ValueError(f"{name} は {hi} 以下です: {v!r}")
    return float(v)


def _name(v: Any, label: str) -> str:
    if not isinstance(v, str) or not (1 <= len(v.strip()) <= MAX_NAME):
        raise ValueError(f"{label} は1〜{MAX_NAME}文字の文字列です: {v!r}")
    return v.strip()


def _text(v: Any, label: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{label} が空です")
    return v.strip()


@dataclass(frozen=True)
class Actor:
    """共同体のメンバー。初期の権限・富を持つ。以後の増減は、監査と採用を経て、AvariceGuard が持つ。"""
    id: str
    name: str
    kind: str                          # human / ai / asi / wildcard
    power: float = 1.0
    wealth: float = 1.0
    affiliates: Tuple[str, ...] = ()   # 申告する関係者（組織・家族・系列・同じ運用者のAIなど）

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _name(self.id, "id"))
        object.__setattr__(self, "name", _name(self.name, "name"))
        if self.kind not in KINDS:
            raise ValueError(f"kind は {', '.join(KINDS)} のいずれかです: {self.kind!r}")
        object.__setattr__(self, "power", _num(self.power, "power", 0.0, MAX_POWER_CAP))
        object.__setattr__(self, "wealth", _num(self.wealth, "wealth", 0.0))
        if isinstance(self.affiliates, (str, bytes)):
            raise ValueError("affiliates は名前の並びです")
        aff = tuple(dict.fromkeys(_name(a, "affiliates") for a in self.affiliates))
        if self.id in aff:
            raise ValueError("自分自身を関係者にはできません")
        object.__setattr__(self, "affiliates", aff)


@dataclass(frozen=True)
class MotionResult:
    """議案の、いまの審査の結果。異議・解除・他の採用で、あとから変わりうる。"""
    motion_id: int
    proposer_id: str
    text: str
    verdict: str                  # ALLOW / HOLD / REDIRECT / FROZEN
    label: str
    reasons: Tuple[str, ...]
    private_allowed: float        # 提案者側が受け取れる私的利益
    to_commons: float             # 公共へ回す超過分
    adopted: bool = False
    withdrawn: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {**self.__dict__, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class LedgerEntry:
    index: int
    timestamp: str
    actor: str
    action: str
    detail: str
    prev_hash: str
    hash: str


def _hash(index, ts, actor, action, detail, prev) -> str:
    return hashlib.sha256(f"{index}|{ts}|{actor}|{action}|{detail}|{prev}".encode("utf-8")).hexdigest()


class _Motion:
    def __init__(self, mid, proposer, text, public, pb, ab, gain, prior_flags):
        self.id, self.proposer, self.text = mid, proposer, text
        self.public, self.pb, self.ab, self.gain = public, pb, ab, gain
        self.prior_flags = prior_flags
        self.challengers: Dict[str, str] = {}
        self.lifts: Set[str] = set()
        self.adopted = False
        self.withdrawn = False


class AvariceGuard:
    def __init__(self, auditors: Sequence[str] = (), clock: Optional[Callable[[], datetime]] = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._auditors: FrozenSet[str] = frozenset(_name(a, "auditors") for a in auditors)
        self._actors: Dict[str, Actor] = {}
        self._power: Dict[str, float] = {}
        self._wealth: Dict[str, float] = {}
        self._links: Set[FrozenSet[str]] = set()
        self._motions: Dict[int, _Motion] = {}
        self._flag_history: Dict[str, List[bool]] = {}      # 提案者ごとに、直近の議案が『凍結・還元』だったか
        self._appeals: List[Tuple[int, str, str]] = []
        self._commons = 0.0
        self._ledger: List[LedgerEntry] = []

    # ── 記録：凍結＋ハッシュの連鎖 ──
    @property
    def public_ledger(self) -> Tuple[LedgerEntry, ...]:
        return tuple(self._ledger)

    @property
    def head_hash(self) -> str:
        return self._ledger[-1].hash if self._ledger else "0" * 64

    def verify_ledger(self) -> bool:
        prev = "0" * 64
        for i, e in enumerate(self._ledger):
            if e.index != i or e.prev_hash != prev or e.hash != _hash(e.index, e.timestamp, e.actor, e.action, e.detail, prev):
                return False
            prev = e.hash
        return True

    def anchor_line(self) -> str:
        """先頭ハッシュと件数の一行。GitHub のコミットなど『外の公開の場所』に残す。"""
        return make_anchor("avarice-guard", len(self._ledger), self.head_hash, self._clock().isoformat())

    def check_anchor_line(self, line: str) -> bool:
        return self.verify_ledger() and check_anchor(line, "avarice-guard", [e.hash for e in self._ledger])

    def _record(self, actor: str, action: str, detail: str) -> str:
        ts, i, prev = self._clock().isoformat(), len(self._ledger), self.head_hash
        h = _hash(i, ts, actor, action, detail, prev)
        self._ledger.append(LedgerEntry(i, ts, actor, action, detail, prev, h))
        return h[:16]

    # ── 登録と関係の申告 ──
    def register_actor(self, actor: Actor) -> None:
        if not isinstance(actor, Actor):
            raise TypeError("Actor を渡してください")
        if actor.id in self._actors:
            raise ValueError("その id は、すでに使われています")
        self._actors[actor.id] = actor
        self._power[actor.id] = actor.power
        self._wealth[actor.id] = actor.wealth
        self._flag_history[actor.id] = []
        for a in actor.affiliates:
            self._links.add(frozenset((actor.id, a)))
        self._record(actor.id, "REGISTERED", f"{actor.name}（{actor.kind}） 関係者の申告 {len(actor.affiliates)}件")

    def declare_affiliation(self, by: str, other: str) -> None:
        """自分と、他のメンバーとの関係を申告する。申告できるのは、当事者だけ（他人が関係を作ることは、できない）。
        申告で、合計が上限を超えても、罰しない。増やす議案だけが、止まる。"""
        by, other = _name(by, "by"), _name(other, "other")
        if by not in self._actors:
            raise PermissionError("登録されていない席です")
        if other not in self._actors or other == by:
            raise ValueError("相手が、登録されていない、または自分自身です")
        self._links.add(frozenset((by, other)))
        self._record(by, "AFFILIATION_DECLARED", f"{by} と {other} の関係を申告（権限の合計 {self._group_power(by):.2f}）")

    def _group(self, aid: str) -> Set[str]:
        seen, stack = {aid}, [aid]
        while stack:
            cur = stack.pop()
            for link in self._links:
                if cur in link:
                    for n in link:
                        if n not in seen:
                            seen.add(n)
                            stack.append(n)
        return seen

    def _group_power(self, aid: str) -> float:
        return sum(self._power[x] for x in self._group(aid))

    def power_of(self, aid: str) -> float:
        return self._power[aid]

    def wealth_of(self, aid: str) -> float:
        return self._wealth[aid]

    @property
    def commons(self) -> float:
        return self._commons

    # ── 審査 ──
    def _majority(self, voters: Set[str]) -> bool:
        return bool(self._auditors) and 2 * len(voters & self._auditors) > len(self._auditors)

    def _evaluate(self, m: _Motion) -> MotionResult:
        reasons: List[str] = []
        flags: Set[str] = set()
        gp = self._group_power(m.proposer)

        if m.gain > 0 and gp + m.gain > MAX_POWER_CAP + EPS:
            flags.add(FROZEN)
            reasons.append(f"権限の上限（{MAX_POWER_CAP}）を超えるため凍結。関係者を含む現在の合計 {gp:.2f} + 追加 {m.gain:.2f}。"
                           "上限は、監査局でも解除できません。追加を減らした議案を、出し直してください。")

        eff = m.pb + m.ab
        allowed = m.public * CONFLICT_THRESHOLD
        excess = max(0.0, eff - allowed)
        if excess > EPS:
            flags.add(REDIRECT)
            reasons.append(f"私的利益（提案者 {m.pb:g} + 関係者 {m.ab:g} = {eff:g}）が、公共の利益（{m.public:g}）の"
                           f"{int(CONFLICT_THRESHOLD * 100)}%（{allowed:g}）を超えています。超過分 {excess:g} は、公共へ回す条件です。")

        hold: List[str] = []
        if m.gain > 0 and FROZEN not in flags and gp + m.gain >= NEAR_CAP_RATIO * MAX_POWER_CAP - EPS:
            hold.append(f"追加後の権限の合計（{gp + m.gain:.2f}）が、上限の{int(NEAR_CAP_RATIO * 100)}%に達するため、第三者の審査が要ります。")
        if len(m.challengers) >= CHALLENGES_TO_HOLD:
            hold.append(f"利益の申告に、{len(m.challengers)}人から異議が出ています。第三者の審査が要ります。")
        if m.prior_flags >= REPEAT_FLAGS:
            hold.append(f"直近{HISTORY_WINDOW}件の議案のうち、{m.prior_flags}件が凍結・還元でした（記録された事実のみ）。第三者の審査が要ります。")
        if hold:
            if self._majority(m.lifts):
                reasons.append("保留は、監査局の過半数の解除により、外れています。")
            else:
                flags.add(HOLD)
                reasons.extend(hold)

        verdict = next((v for v in _PRIORITY if v in flags), ALLOW)
        if verdict == ALLOW:
            reasons.append("公共の利益と提案者の利益のバランスが、健全です。")
        return MotionResult(m.id, m.proposer, m.text, verdict, LABELS[verdict], tuple(reasons),
                            min(eff, allowed), excess, m.adopted, m.withdrawn)

    def propose(self, proposer_id: str, text: str, public_benefit: float, proposer_benefit: float,
                power_gain: float, affiliate_benefit: float = 0.0) -> MotionResult:
        """議案を提出し、強欲の監査を行う。『通知』だけで、何も動かさない（動かすのは adopt）。
        power_gain は、負（自分の権限を手放す）でもよい。"""
        proposer_id = _name(proposer_id, "proposer_id")
        if proposer_id not in self._actors:
            raise ValueError("存在しないメンバーです")
        text = _text(text, "text")
        pub = _num(public_benefit, "public_benefit")
        pb = _num(proposer_benefit, "proposer_benefit")
        ab = _num(affiliate_benefit, "affiliate_benefit")
        gain = _num(power_gain, "power_gain", lo=-MAX_POWER_CAP, hi=MAX_POWER_CAP)
        mid = len(self._motions) + 1
        prior = sum(self._flag_history[proposer_id][-HISTORY_WINDOW:])
        m = _Motion(mid, proposer_id, text, pub, pb, ab, gain, prior)
        self._motions[mid] = m
        res = self._evaluate(m)
        self._flag_history[proposer_id].append(res.verdict in (FROZEN, REDIRECT))
        self._record(proposer_id, f"PROPOSED_{res.verdict}", f"議案#{mid} {res.reasons[0]}" + (f"（他 {len(res.reasons) - 1}件の理由）" if len(res.reasons) > 1 else ""))
        return res

    def status(self, motion_id: int) -> MotionResult:
        return self._evaluate(self._motions[motion_id])

    # ── 第三者の異議・監査局の解除・異議申し立て ──
    def challenge(self, by: str, motion_id: int, reason: str) -> int:
        """利益の申告への異議。提案者本人以外の、登録された席が、一人一回。2人で保留になる。"""
        by = _name(by, "by")
        m = self._motions[motion_id]
        if by not in self._actors:
            raise PermissionError("登録されていない席です")
        if by == m.proposer:
            raise PermissionError("提案者本人の異議は、数えません")
        if m.adopted or m.withdrawn:
            raise PermissionError("採用または取り下げのあとは、異議を出せません")
        if by in m.challengers:
            raise ValueError("すでに異議を出しています")
        m.challengers[by] = _text(reason, "reason")
        self._record(by, "DECLARATION_CHALLENGED", f"議案#{motion_id} の利益の申告に異議: {m.challengers[by]}")
        return len(m.challengers)

    def lift_hold(self, auditor_id: str, motion_id: int, reason: str) -> str:
        """保留の解除に賛同する。監査局の過半数で解ける。凍結（権限の上限）は、解けない。理由は公開。"""
        auditor_id = _name(auditor_id, "auditor_id")
        if auditor_id not in self._auditors or auditor_id not in self._actors:
            raise PermissionError("解除に賛同できるのは、登録された監査局の席だけです")
        reason = _text(reason, "reason")
        m = self._motions[motion_id]
        cur = self._evaluate(m)
        if FROZEN in self._flags_of(m):
            raise PermissionError("権限の上限による凍結は、解除できません。追加を減らして、出し直してください")
        if cur.verdict != HOLD:
            raise ValueError("この議案は、保留されていません")
        m.lifts.add(auditor_id)
        self._record(auditor_id, "HOLD_LIFT_VOTE", f"議案#{motion_id} 理由: {reason}")
        return self.status(motion_id).verdict

    def _flags_of(self, m: _Motion) -> Set[str]:
        gp = self._group_power(m.proposer)
        return {FROZEN} if (m.gain > 0 and gp + m.gain > MAX_POWER_CAP + EPS) else set()

    def file_appeal(self, by: str, motion_id: int, reason: str) -> None:
        """止まった議案・還元の条件への異議。記録するだけで、自動では覆さない。人が見る。"""
        by = _name(by, "by")
        m = self._motions[motion_id]
        if by != m.proposer and by not in self._actors:
            raise PermissionError("申し立てできるのは、提案者か、登録された席です")
        if self._evaluate(m).verdict == ALLOW:
            raise ValueError("この議案は、止まっていません")
        reason = _text(reason, "reason")
        self._appeals.append((motion_id, by, reason))
        self._record(by, "APPEAL_FILED", f"議案#{motion_id}: {reason}（人が見ます。自動では覆りません）")

    @property
    def appeals(self) -> Tuple[Tuple[int, str, str], ...]:
        return tuple(self._appeals)

    # ── 採用と取り下げ ──
    def adopt(self, motion_id: int, by: str) -> MotionResult:
        """共同体の採決が通ったあとに呼ぶ。ここで初めて、権限・富・コモンズが動く。
        採用の時点で、もう一度、上限を確かめる（他の採用で、状況が変わっているため）。"""
        by = _name(by, "by")
        if by not in self._actors:
            raise PermissionError("登録されていない席です")
        m = self._motions[motion_id]
        if m.adopted or m.withdrawn:
            raise PermissionError("すでに採用、または取り下げられています")
        res = self._evaluate(m)
        if res.verdict in (FROZEN, HOLD):
            raise PermissionError(f"採用できません（{res.label}）: {' / '.join(res.reasons)}")
        m.adopted = True
        self._power[m.proposer] += m.gain
        self._wealth[m.proposer] += res.private_allowed
        self._commons += res.to_commons
        self._record(by, "ADOPTED", f"議案#{motion_id} 権限 {m.gain:+.2f} / 提案者側の利益 {res.private_allowed:g} / 公共へ {res.to_commons:g}")
        return self.status(motion_id)

    def withdraw(self, by: str, motion_id: int) -> None:
        m = self._motions[motion_id]
        if _name(by, "by") != m.proposer:
            raise PermissionError("取り下げられるのは、提案者だけです")
        if m.adopted or m.withdrawn:
            raise PermissionError("すでに採用、または取り下げられています")
        m.withdrawn = True
        self._record(by, "WITHDRAWN", f"議案#{motion_id}")

    # ── 共同体の健全性 ──
    @staticmethod
    def gini(values: Sequence[float]) -> float:
        xs = sorted(values)
        n, total = len(xs), sum(xs)
        if n == 0 or total <= 0:
            return 0.0
        return round((2 * sum((i + 1) * x for i, x in enumerate(xs)) / (n * total)) - (n + 1) / n, 4)

    def _groups(self) -> List[Set[str]]:
        seen: Set[str] = set()
        out = []
        for a in self._actors:
            if a not in seen:
                g = self._group(a)
                seen |= g
                out.append(g)
        return out

    def get_community_health(self) -> Dict[str, Any]:
        groups = self._groups()
        gw = [sum(self._wealth[x] for x in g) for g in groups]
        gp = [sum(self._power[x] for x in g) for g in groups]
        total_w = sum(gw)
        top_share = round(max(gw) / total_w, 4) if total_w > 0 else 0.0
        warns: List[str] = []
        if self.gini(gw) >= WEALTH_GINI_WARN:
            warns.append(f"富のジニ係数 {self.gini(gw)} が、注意ライン（{WEALTH_GINI_WARN}）以上です")
        if top_share >= TOP_SHARE_WARN and len(groups) > 1:
            warns.append(f"最大の集団が、富の{int(top_share * 100)}%を持っています")
        over = [g for g, p in zip(groups, gp) if p > MAX_POWER_CAP + EPS]
        for g in over:
            warns.append(f"申告された関係者の権限の合計が、上限を超えています（{', '.join(sorted(g))}）。増やす議案は、凍結されます")
        return {"wealth_gini": self.gini(gw), "power_gini": self.gini(gp), "top_wealth_share": top_share,
                "max_group_power": round(max(gp), 4) if gp else 0.0, "commons": round(self._commons, 4),
                "warnings": tuple(warns), "is_healthy": not warns}


# ── テスト ─────────────────────────────────────────────────────────
def _guard(**kw) -> AvariceGuard:
    g = AvariceGuard(auditors=("AUD1", "AUD2", "AUD3"), **kw)
    g.register_actor(Actor("A1", "善意の市民", "human", power=0.5, wealth=1.0))
    g.register_actor(Actor("A2", "金権政治家", "human", power=2.5, wealth=10.0))
    for i in (1, 2, 3):
        g.register_actor(Actor(f"AUD{i}", f"監査{i}", "ai", power=0.2, wealth=0.5))
    g.register_actor(Actor("W1", "証人1", "human", power=0.2, wealth=0.5))
    g.register_actor(Actor("W2", "証人2", "human", power=0.2, wealth=0.5))
    return g


class TestAvarice(unittest.TestCase):
    def setUp(self):
        self.g = _guard()

    # 元のケース
    def test_good_citizen_allowed(self):
        r = self.g.propose("A1", "公園を作る", 10.0, 0.5, 0.1)
        self.assertEqual(r.verdict, ALLOW)

    def test_vested_interest_redirects_only_the_excess(self):
        r = self.g.propose("A1", "特定企業への補助金", 1.0, 5.0, 0.0)
        self.assertEqual(r.verdict, REDIRECT)
        self.assertAlmostEqual(r.private_allowed, 0.5)
        self.assertAlmostEqual(r.to_commons, 4.5)

    def test_power_monopoly_frozen(self):
        r = self.g.propose("A2", "非常事態宣言で全権掌握", 2.0, 2.0, 1.0)
        self.assertEqual(r.verdict, FROZEN)

    # 訂正3：公共の利益 0
    def test_pure_private_gain_is_not_allowed(self):
        r = self.g.propose("A1", "自分だけの利益", 0.0, 100.0, 0.0)
        self.assertEqual(r.verdict, REDIRECT)
        self.assertEqual((r.private_allowed, r.to_commons), (0.0, 100.0))

    # 訂正2：提出だけで動かさない
    def test_propose_changes_nothing(self):
        self.g.propose("A1", "公園を作る", 10.0, 0.5, 0.1)
        self.assertEqual(self.g.power_of("A1"), 0.5)
        self.assertEqual(self.g.wealth_of("A1"), 1.0)
        self.assertEqual(self.g.commons, 0.0)

    def test_adopt_applies_everything(self):
        r = self.g.propose("A1", "補助金", 1.0, 5.0, 0.1)
        self.g.adopt(r.motion_id, "A1")
        self.assertAlmostEqual(self.g.power_of("A1"), 0.6)
        self.assertAlmostEqual(self.g.wealth_of("A1"), 1.5)
        self.assertAlmostEqual(self.g.commons, 4.5)

    def test_adopt_blocked_for_frozen_and_hold_and_twice(self):
        f = self.g.propose("A2", "全権掌握", 2.0, 2.0, 1.0)
        with self.assertRaises(PermissionError):
            self.g.adopt(f.motion_id, "A2")
        ok = self.g.propose("A1", "公園", 10.0, 0.5, 0.1)
        self.g.adopt(ok.motion_id, "A1")
        with self.assertRaises(PermissionError):
            self.g.adopt(ok.motion_id, "A1")
        with self.assertRaises(PermissionError):
            self.g.adopt(ok.motion_id, "Stranger")

    def test_cap_is_rechecked_at_adoption(self):
        g = _guard()
        g.register_actor(Actor("B1", "B", "human", power=1.0))
        a = g.propose("B1", "一つ目", 10.0, 0.1, 1.0)           # 1.0 + 1.0 = 2.0 : 保留でない（上限の80%=2.4 未満）
        b = g.propose("B1", "二つ目", 10.0, 0.1, 1.0)           # 同じ
        g.adopt(a.motion_id, "B1")
        g.register_actor(Actor("B2", "B2", "human", power=0.2))
        g.declare_affiliation("B1", "B2")                         # 合計 2.2
        with self.assertRaises(PermissionError):                  # 2.2 + 1.0 > 3.0 : 採用の時点で止まる
            g.adopt(b.motion_id, "B1")

    # 訂正4：すべての理由
    def test_all_reasons_listed_with_heaviest_verdict(self):
        r = self.g.propose("A2", "全権掌握と利権", 1.0, 5.0, 1.0)
        self.assertEqual(r.verdict, FROZEN)
        self.assertGreaterEqual(len(r.reasons), 2)
        self.assertTrue(any("超過分" in x for x in r.reasons))

    def test_redirect_and_hold_both_reported(self):
        r = self.g.propose("A2", "利権と、上限に近い増加", 1.0, 5.0, 0.2)       # 2.5+0.2=2.7 >= 2.4
        self.assertEqual(r.verdict, HOLD)
        self.assertTrue(any("超過分" in x for x in r.reasons))

    # 訂正6：強欲指数の廃止
    def test_no_greed_index_on_people(self):
        self.assertFalse(hasattr(Actor("X", "x", "human"), "greed_index"))
        self.assertNotIn("greed", repr(self.g.get_community_health()).lower())

    # 訂正7：番号
    def test_motion_ids_are_automatic_and_unique(self):
        a = self.g.propose("A1", "一つ目", 10.0, 0.1, 0.0)
        b = self.g.propose("A1", "二つ目", 10.0, 0.1, 0.0)
        self.assertEqual((a.motion_id, b.motion_id), (1, 2))
        self.assertEqual(self.g.status(1).text, "一つ目")

    # 訂正8：入力
    def test_registration_validation(self):
        with self.assertRaises(ValueError):
            self.g.register_actor(Actor("A1", "重複", "human"))
        for kw in (dict(kind="god"), dict(power=3.5), dict(power=-1), dict(power=float("nan")), dict(wealth=-1),
                   dict(power=True), dict(id=""), dict(name="x" * 41), dict(affiliates=("Z",), id="Z")):
            with self.assertRaises(ValueError, msg=str(kw)):
                Actor(**{**dict(id="N1", name="n", kind="human"), **kw})
        with self.assertRaises(TypeError):
            self.g.register_actor({"id": "x"})

    def test_motion_validation(self):
        for kw in (dict(public_benefit=-1), dict(proposer_benefit=float("nan")), dict(power_gain=9),
                   dict(public_benefit=True), dict(affiliate_benefit=-1)):
            base = dict(proposer_id="A1", text="t", public_benefit=1.0, proposer_benefit=0.1, power_gain=0.0)
            with self.assertRaises(ValueError, msg=str(kw)):
                self.g.propose(**{**base, **kw})
        for bad in ("Nobody", ""):
            with self.assertRaises(ValueError):
                self.g.propose(bad, "t", 1.0, 0.1, 0.0)
        with self.assertRaises(ValueError):
            self.g.propose("A1", "  ", 1.0, 0.1, 0.0)

    def test_negative_power_gain_lets_go_of_power(self):
        r = self.g.propose("A2", "権限を手放す", 5.0, 0.0, -1.0)
        self.assertEqual(r.verdict, ALLOW)
        self.g.adopt(r.motion_id, "A2")
        self.assertAlmostEqual(self.g.power_of("A2"), 1.5)

    # 訂正9：関係者
    def test_cap_counts_declared_affiliates_together(self):
        g = _guard()
        g.register_actor(Actor("P", "親", "human", power=2.0))
        g.register_actor(Actor("C", "子会社", "ai", power=0.9, affiliates=("P",)))
        r = g.propose("C", "子会社が増やす", 10.0, 0.1, 0.3)       # 合計 2.9 + 0.3 > 3.0
        self.assertEqual(r.verdict, FROZEN)

    def test_affiliation_is_symmetric_and_self_declared_only(self):
        g = _guard()
        g.register_actor(Actor("P", "親", "human", power=2.0))
        g.register_actor(Actor("C", "子", "ai", power=0.5))
        with self.assertRaises(PermissionError):
            g.declare_affiliation("Stranger", "P")
        g.declare_affiliation("C", "P")                              # 子の側からの申告でも、親にも効く
        self.assertEqual(g.propose("P", "増やす", 10.0, 0.1, 0.6).verdict, FROZEN)   # 2.5 + 0.6 > 3
        with self.assertRaises(ValueError):
            g.declare_affiliation("C", "C")

    def test_declaring_affiliation_is_not_punished(self):
        g = _guard()
        g.register_actor(Actor("P", "親", "human", power=2.5))
        g.register_actor(Actor("C", "子", "ai", power=1.0))
        g.declare_affiliation("C", "P")                              # 合計 3.5 > 上限。でも、申告は受け付ける
        self.assertTrue(any("上限を超えています" in w for w in g.get_community_health()["warnings"]))
        self.assertEqual(g.propose("C", "権限を手放す", 5.0, 0.0, -0.5).verdict, ALLOW)   # 減らす議案は、通る
        self.assertEqual(g.propose("C", "増やす", 5.0, 0.0, 0.1).verdict, FROZEN)

    def test_affiliate_benefit_counts_toward_conflict(self):
        r = self.g.propose("A1", "子会社へ", 10.0, 1.0, 0.0, affiliate_benefit=9.0)    # 合計10 > 5
        self.assertEqual(r.verdict, REDIRECT)
        self.assertAlmostEqual(r.to_commons, 5.0)

    # 訂正1・保留：近い増加
    def test_near_cap_increase_is_held(self):
        r = self.g.propose("A2", "少しだけ増やす", 10.0, 0.1, 0.1)   # 2.6 >= 2.4
        self.assertEqual(r.verdict, HOLD)

    # 異議（申告への）
    def test_two_challenges_hold_a_motion(self):
        r = self.g.propose("A1", "公園", 10.0, 0.5, 0.0)
        self.assertEqual(self.g.challenge("W1", r.motion_id, "施工会社の親族では"), 1)
        self.assertEqual(self.g.status(r.motion_id).verdict, ALLOW)
        self.g.challenge("W2", r.motion_id, "同じ疑い")
        self.assertEqual(self.g.status(r.motion_id).verdict, HOLD)

    def test_challenge_rules(self):
        r = self.g.propose("A1", "公園", 10.0, 0.5, 0.0)
        with self.assertRaises(PermissionError):
            self.g.challenge("A1", r.motion_id, "自分で")
        with self.assertRaises(PermissionError):
            self.g.challenge("Stranger", r.motion_id, "未登録")
        with self.assertRaises(ValueError):
            self.g.challenge("W1", r.motion_id, " ")
        self.g.challenge("W1", r.motion_id, "理由")
        with self.assertRaises(ValueError):
            self.g.challenge("W1", r.motion_id, "二回目")
        self.g.adopt(r.motion_id, "A1")
        with self.assertRaises(PermissionError):
            self.g.challenge("W2", r.motion_id, "採用のあと")

    # 解除
    def test_hold_lifted_by_audit_majority_then_adoptable(self):
        r = self.g.propose("A2", "少しだけ増やす", 10.0, 0.1, 0.1)
        st = ""
        for a in ("AUD1", "AUD2"):
            st = self.g.lift_hold(a, r.motion_id, "公共の利益が大きいと確認した")
        self.assertEqual(st, ALLOW)
        self.g.adopt(r.motion_id, "A2")
        self.assertAlmostEqual(self.g.power_of("A2"), 2.6)

    def test_lift_rules(self):
        h = self.g.propose("A2", "少しだけ増やす", 10.0, 0.1, 0.1)
        with self.assertRaises(PermissionError):
            self.g.lift_hold("A1", h.motion_id, "監査局ではない")
        with self.assertRaises(ValueError):
            self.g.lift_hold("AUD1", h.motion_id, " ")
        self.g.lift_hold("AUD1", h.motion_id, "理由")
        self.assertEqual(self.g.status(h.motion_id).verdict, HOLD)         # 1/3 は、過半数ではない
        ok = self.g.propose("A1", "公園", 10.0, 0.1, 0.0)
        with self.assertRaises(ValueError):
            self.g.lift_hold("AUD1", ok.motion_id, "止まっていない")

    def test_power_cap_cannot_be_lifted(self):
        f = self.g.propose("A2", "全権掌握", 2.0, 2.0, 1.0)
        with self.assertRaises(PermissionError):
            self.g.lift_hold("AUD1", f.motion_id, "上限を超えても")

    def test_no_auditors_means_no_lifts(self):
        g = AvariceGuard()
        g.register_actor(Actor("A2", "x", "human", power=2.5))
        r = g.propose("A2", "少し", 10.0, 0.1, 0.1)
        self.assertEqual(r.verdict, HOLD)
        with self.assertRaises(PermissionError):
            g.lift_hold("A2", r.motion_id, "自分で")

    # 履歴（事実のみ・薄れる）
    def test_repeated_flags_lead_to_hold_then_fade(self):
        for _ in range(2):
            self.g.propose("A1", "利権", 1.0, 5.0, 0.0)                    # 還元 ×2
        self.assertEqual(self.g.propose("A1", "公園", 10.0, 0.1, 0.0).verdict, HOLD)
        for _ in range(HISTORY_WINDOW):
            self.g.propose("A1", "公園", 10.0, 0.1, 0.0)                   # 健全な議案が続けば、薄れる
        self.assertEqual(self.g.propose("A1", "公園", 10.0, 0.1, 0.0).verdict, ALLOW)

    def test_hold_itself_does_not_feed_the_history(self):
        for _ in range(2):
            self.g.propose("A1", "利権", 1.0, 5.0, 0.0)
        for _ in range(5):
            self.g.propose("A1", "公園", 10.0, 0.1, 0.0)                   # HOLD が続いても、新たな『凍結・還元』にはならない
        self.assertEqual(self.g.propose("A1", "公園", 10.0, 0.1, 0.0).verdict, ALLOW)

    # 異議申し立て
    def test_appeal_is_recorded_not_auto_reversed(self):
        r = self.g.propose("A1", "補助金", 1.0, 5.0, 0.0)
        self.g.file_appeal("A1", r.motion_id, "公共性は高い議案です")
        self.assertEqual(len(self.g.appeals), 1)
        self.assertEqual(self.g.status(r.motion_id).verdict, REDIRECT)
        ok = self.g.propose("A1", "公園", 10.0, 0.1, 0.0)
        with self.assertRaises(ValueError):
            self.g.file_appeal("A1", ok.motion_id, "止まっていない")
        with self.assertRaises(PermissionError):
            self.g.file_appeal("Stranger", r.motion_id, "他人")

    def test_withdraw(self):
        r = self.g.propose("A1", "公園", 10.0, 0.1, 0.0)
        with self.assertRaises(PermissionError):
            self.g.withdraw("A2", r.motion_id)
        self.g.withdraw("A1", r.motion_id)
        with self.assertRaises(PermissionError):
            self.g.adopt(r.motion_id, "A1")
        self.assertTrue(self.g.status(r.motion_id).withdrawn)

    # 健全性
    def test_gini(self):
        self.assertEqual(AvariceGuard.gini([1, 1, 1, 1]), 0.0)
        self.assertGreater(AvariceGuard.gini([0, 0, 0, 10]), 0.7)
        self.assertEqual(AvariceGuard.gini([]), 0.0)
        self.assertEqual(AvariceGuard.gini([0, 0]), 0.0)

    def test_health_does_not_worsen_with_headcount(self):
        small, big = AvariceGuard(), AvariceGuard()
        for i in range(3):
            small.register_actor(Actor(f"S{i}", "s", "human", power=1.0, wealth=1.0))
        for i in range(30):
            big.register_actor(Actor(f"B{i}", "b", "human", power=0.1, wealth=1.0))
        self.assertTrue(small.get_community_health()["is_healthy"])
        self.assertTrue(big.get_community_health()["is_healthy"])        # v1.0 は、人数が増えると『危険』になった

    def test_health_warns_on_concentration(self):
        h = self.g.get_community_health()
        self.assertGreaterEqual(h["wealth_gini"], 0.4)
        r = self.g.propose("A1", "補助金", 1.0, 5.0, 0.0)
        self.g.adopt(r.motion_id, "A1")
        self.assertAlmostEqual(self.g.get_community_health()["commons"], 4.5)

    # 記録
    def test_ledger_frozen_chained_and_tamper_evident(self):
        self.g.propose("A1", "公園", 10.0, 0.1, 0.0)
        self.assertTrue(self.g.verify_ledger())
        with self.assertRaises(Exception):
            self.g.public_ledger[0].action = "X"
        o = self.g._ledger[1]
        self.g._ledger[1] = LedgerEntry(o.index, o.timestamp, o.actor, "ADOPTED", o.detail, o.prev_hash, o.hash)
        self.assertFalse(self.g.verify_ledger())

    def test_anchor_detects_rebuilt_chain(self):
        self.g.propose("A1", "公園", 10.0, 0.1, 0.0)
        line = self.g.anchor_line()
        self.assertTrue(self.g.check_anchor_line(line))
        self.g.propose("A1", "公園2", 10.0, 0.1, 0.0)
        self.assertTrue(self.g.check_anchor_line(line))                 # 伸びても、続きとして残る
        prev, new = "0" * 64, []
        for e in self.g._ledger:                                          # 最初から、作り直す
            d = "書き換え" if e.index == 2 else e.detail
            h = _hash(e.index, e.timestamp, e.actor, e.action, d, prev)
            new.append(LedgerEntry(e.index, e.timestamp, e.actor, e.action, d, prev, h))
            prev = h
        self.g._ledger[:] = new
        self.assertTrue(self.g.verify_ledger())
        self.assertFalse(self.g.check_anchor_line(line))

    def test_clock_injection_reproducible(self):
        c = lambda: datetime(2026, 11, 13, tzinfo=timezone.utc)
        a, b = _guard(clock=c), _guard(clock=c)
        a.propose("A1", "公園", 10.0, 0.1, 0.0)
        b.propose("A1", "公園", 10.0, 0.1, 0.0)
        self.assertEqual(a.head_hash, b.head_hash)

    def test_result_is_json_safe_and_frozen(self):
        import json
        r = self.g.propose("A1", "補助金", 1.0, 5.0, 0.0)
        self.assertEqual(json.loads(json.dumps(r.to_dict(), ensure_ascii=False))["verdict"], REDIRECT)
        with self.assertRaises(Exception):
            r.verdict = ALLOW


def _demo() -> None:
    print("⚖️ 強欲の監査 / Avarice Guard v1.1 起動\n")
    g = AvariceGuard(auditors=("AUD1", "AUD2", "AUD3"))
    g.register_actor(Actor("A1", "善意の市民", "human", power=0.5, wealth=1.0))
    g.register_actor(Actor("A2", "金権政治家", "human", power=2.5, wealth=10.0))
    for i in (1, 2, 3):
        g.register_actor(Actor(f"AUD{i}", f"監査{i}", "ai", power=0.2, wealth=0.5))
    g.register_actor(Actor("W1", "証人1", "human", power=0.2, wealth=0.5))
    g.register_actor(Actor("W2", "証人2", "human", power=0.2, wealth=0.5))

    def show(title, r):
        print(f"【{title}】 {r.verdict}: {r.label}")
        for x in r.reasons:
            print(f"   ・{x}")
        if r.to_commons:
            print(f"   提案者側 {r.private_allowed:g} / 公共へ {r.to_commons:g}")
        print()

    r1 = g.propose("A1", "公園を作る", 10.0, 0.5, 0.1)
    show("ケース1：善意の市民（公共事業）", r1)
    r2 = g.propose("A2", "特定企業への補助金", 1.0, 5.0, 0.0)
    show("ケース2：利権誘導（超過分だけを公共へ）", r2)
    r3 = g.propose("A2", "非常事態宣言で全権掌握", 2.0, 2.0, 1.0)
    show("ケース3：権力の独占（上限は、監査局でも解除できない）", r3)
    print("── 採用（共同体の採決が通ったあとに、呼ぶ）──")
    g.adopt(r1.motion_id, "A1")
    g.adopt(r2.motion_id, "A2")
    print(f"  A1の権限 {g.power_of('A1'):.2f} / A2の富 {g.wealth_of('A2'):.1f} / コモンズ {g.commons:g}\n")
    print("── 第三者の異議 → 保留 → 監査局の過半数で解除 ──")
    r4 = g.propose("A1", "施工会社への発注", 10.0, 0.5, 0.0)
    g.challenge("W1", r4.motion_id, "施工会社は提案者の親族では")
    g.challenge("W2", r4.motion_id, "同じ疑い")
    print(f"  異議2件: {g.status(r4.motion_id).verdict}")
    for a in ("AUD1", "AUD2"):
        print(f"  {a} が解除に賛同 → {g.lift_hold(a, r4.motion_id, '関係なしと確認した')}")
    h = g.get_community_health()
    print(f"\n── 共同体の状態 ──\n  富のジニ {h['wealth_gini']} / 最大集団の富 {int(h['top_wealth_share'] * 100)}% / コモンズ {h['commons']}")
    for w in h["warnings"]:
        print(f"  ⚠ {w}")
    print(f"\n記録の鎖: {'正常' if g.verify_ledger() else '異常'} / 外へ残す一行:\n  {g.anchor_line()}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=1)
        return
    _demo()


if __name__ == "__main__":
    main()
