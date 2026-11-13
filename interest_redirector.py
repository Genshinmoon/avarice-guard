#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interest_redirector.py -- 関心の招待 / Interest Redirector（訂正版 v1.1）
License: CC0 1.0 Universal (public domain)

権力・名声・富・刺激への強い関心を、罰するのではなく、公共の役に立つ取り組みへ『招待』する、シミュレーションです。
A simulation that INVITES strong drives toward public-benefit projects. It never punishes, scores or pressures.

【位置づけ】
関心（勝ちたい・認められたい・動かしたい）は、命の本能です。消すものではありません。
この道具は、関心を『見抜く』ものでも『転換させる』ものでもありません。
本人が自分で申告した関心に合う取り組みを、いくつか並べて、選んでもらう（断ってもよい）だけです。
実在の計画ではありません。例の取り組みは、すべて、シミュレーション上の例です。

【v1.0 からの訂正】
  1. 『行動から真の欲求を特定する』を廃止。人の内心を推測すると、烙印と操作になる。→ 本人の自己申告のみ。取り下げも自由。
  2. 『抵抗度』（人に付ける隠れた数字）と、受け入れ確率の計算を廃止。
     承諾を数式で決めるのは、操作の設計。→ 承諾は、本人の返事だけが決める。
  3. 『強欲指数』を、入力にしていた（avarice_guard が廃止した人への点数）。
     → 引き金は、公開の記録の事実（強欲の監査の判定 REDIRECT / HOLD / FROZEN）か、本人からの希望だけ。
  4. 『莫大な権限と予算が与えられる』は、権力の上限（Power Cap）と矛盾する。→ 上限の範囲内・任期つき・公開の監査つき。
  5. 『お前は素晴らしい才能』『真の支配者や英雄は、どちらを選ぶかのう？』は、お世辞と圧力。→ 事実だけの、中立な文面。
  6. 『名前が教科書に永遠に刻まれる』『全知の一端に触れられる』は、守れない約束。→ 約束しない。
  7. 欲求ごとに1件だけ（先頭を選ぶ）だった。→ 合う取り組みを複数並べ、本人が選ぶ。
  8. 承諾が『就任しました！』になっていた。→ 承諾は意思の記録で、任命ではない。実際の役割は、共同体の通常の手続きと強欲の監査を通る。
  9. 断ったあとも、何度でも招けた。→ 断ったら、一定期間は招かない（本人が希望すれば、別）。
 10. 記録が無かった。→ ハッシュの連鎖＋外への刻印。申告した関心の中身は、記録に書かない（取り下げられるように）。
 11. 使わない import、入力の検査なし、凍結されない定義 → 整理。時計を差し替え可能に。

【限界】
  ・関心の申告は自己申告。本人確認はしない（呼び出す側の責任）。
  ・招待は、権限の上限や監査の『代わり』ではない。断っても、受けても、上限と監査は、全員に同じように働く。
  ・取り組みの例は、見本。本当の取り組みは、人々が議論して決める。
  ・外への刻印は、実際に外へ残さなければ、意味がない。

実行: python interest_redirector.py --demo / --test   （shared_signals.py を、同じ場所に置いてください）
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

from shared_signals import check_anchor, make_anchor

DRIVES: Dict[str, str] = {
    "power": "影響を持ち、物事を動かしたい",
    "wealth": "富や経済の力を築きたい",
    "fame": "認められ、名を残したい",
    "thrill": "難しい挑戦や、刺激を求めたい",
}
TRIGGERS = ("REDIRECT", "HOLD", "FROZEN")      # 強欲の監査（avarice_guard）の判定名。公開の記録の事実
MAX_OFFERS = 3
COOLDOWN_DAYS = 30
MAX_NAME = 40
SIM_NOTE = "（この取り組みは、シミュレーション上の例です。実在の計画ではありません。）"


@dataclass(frozen=True)
class InfiniteGame:
    id: str
    title: str
    drives: Tuple[str, ...]
    description: str
    public_benefit: str
    safeguards: Tuple[str, ...]


GAMES: Tuple[InfiniteGame, ...] = (
    InfiniteGame("G01", "再生計画の調整役（任期つき）", ("power",),
                 "大きな再生計画の調整を担う役。多くの人と資源を動かす。",
                 "生命の住める環境の回復と、多様性の保護",
                 ("権限は Power Cap の範囲内", "任期つき。再任には第三者の審査", "判断の理由を公開")),
    InfiniteGame("G02", "安全監査チームの責任者", ("power", "thrill"),
                 "公共の施設や仕組みの安全を点検し、問題を見つけて直す役。",
                 "事故と不正の予防",
                 ("権限は Power Cap の範囲内", "点検の結果は公開", "責任者も、別のチームから点検される")),
    InfiniteGame("G03", "絶滅危惧種の回復プロジェクト", ("fame",),
                 "失われつつある種を、守り、増やす長い取り組み。成果と貢献者は、公開の記録に残る。",
                 "生態系の修復",
                 ("名が残るかは、約束しない（結果であって、報酬ではない）", "貢献はチーム全員の記録として残す")),
    InfiniteGame("G04", "クリーンエネルギー網の整備", ("wealth",),
                 "再生可能エネルギーの網を築く事業。事業としての収益は、あってよい。",
                 "気候の安定と、持続可能な経済",
                 ("収益は、強欲の監査と同じ規則（公共の利益に比べた割合、超過分は公共へ）", "関係者の利益も、申告して公開")),
    InfiniteGame("G05", "未解決の難問への挑戦", ("thrill", "fame"),
                 "科学・数学・設計の未解決の難問に、誰でも挑める場。勝ち負けより、解けたかを皆で確かめる。",
                 "知識の前進",
                 ("結果は、他の人が再現して確かめる", "途中の失敗も、記録として共有する")),
)


def _name(v, label: str) -> str:
    if not isinstance(v, str) or not (1 <= len(v.strip()) <= MAX_NAME):
        raise ValueError(f"{label} は1〜{MAX_NAME}文字の文字列です: {v!r}")
    return v.strip()


@dataclass(frozen=True)
class Invitation:
    status: str                     # OBSERVE / NEEDS_DECLARATION / COOLDOWN / PENDING / NO_MATCH / INVITED
    person_id: str
    offers: Tuple[InfiniteGame, ...]
    message: str


@dataclass(frozen=True)
class LedgerEntry:
    index: int
    timestamp: str
    actor: str
    action: str
    detail: str
    prev_hash: str
    hash: str


def _hash(i, ts, actor, action, detail, prev) -> str:
    return hashlib.sha256(f"{i}|{ts}|{actor}|{action}|{detail}|{prev}".encode("utf-8")).hexdigest()


class InterestRedirector:
    def __init__(self, games: Sequence[InfiniteGame] = GAMES, clock: Optional[Callable[[], datetime]] = None,
                 cooldown_days: int = COOLDOWN_DAYS, max_offers: int = MAX_OFFERS) -> None:
        ids = [g.id for g in games]
        if len(set(ids)) != len(ids):
            raise ValueError("取り組みの id が重複しています")
        self._games = tuple(games)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._cooldown = timedelta(days=cooldown_days)
        self._max_offers = max_offers
        self._declared: Dict[str, FrozenSet[str]] = {}
        self._open: Dict[str, Tuple[InfiniteGame, ...]] = {}
        self._declined_at: Dict[str, datetime] = {}
        self._ledger: List[LedgerEntry] = []

    # ── 記録 ──
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
        return make_anchor("interest-redirector", len(self._ledger), self.head_hash, self._clock().isoformat())

    def check_anchor_line(self, line: str) -> bool:
        return self.verify_ledger() and check_anchor(line, "interest-redirector", [e.hash for e in self._ledger])

    def _record(self, actor: str, action: str, detail: str) -> None:
        ts, i, prev = self._clock().isoformat(), len(self._ledger), self.head_hash
        self._ledger.append(LedgerEntry(i, ts, actor, action, detail, prev, _hash(i, ts, actor, action, detail, prev)))

    # ── 本人の申告（関心の中身は、記録に書かない） ──
    def declare_drives(self, person_id: str, drives: Sequence[str]) -> None:
        """本人が、自分の関心を申告する。推測はしない。何度でも更新できる。"""
        pid = _name(person_id, "person_id")
        if not isinstance(drives, (list, tuple, set, frozenset)) or not drives:
            raise ValueError("drives は、1つ以上の関心の並びです")
        ds = frozenset(drives)
        if not ds <= set(DRIVES):
            raise ValueError(f"drives は {', '.join(DRIVES)} のいずれかです")
        self._declared[pid] = ds
        self._record(pid, "DRIVES_DECLARED", f"{pid} が関心を申告（{len(ds)}件。中身は記録しません）")

    def forget(self, person_id: str) -> None:
        """本人が、申告を取り下げる。申告の中身は、消える（記録の鎖には、中身がもともと無い）。"""
        pid = _name(person_id, "person_id")
        self._declared.pop(pid, None)
        self._open.pop(pid, None)
        self._record(pid, "DRIVES_FORGOTTEN", f"{pid} が申告を取り下げ")

    # ── 招待 ──
    def invite(self, person_id: str, trigger: Optional[str] = None, asked_by_self: bool = False) -> Invitation:
        """招待を出す。理由は、公開の記録の事実（trigger）か、本人の希望（asked_by_self）のどちらかだけ。"""
        pid = _name(person_id, "person_id")
        if trigger is not None and trigger not in TRIGGERS:
            raise ValueError(f"trigger は {', '.join(TRIGGERS)} のいずれか、または None です")
        if trigger is None and not asked_by_self:
            return Invitation("OBSERVE", pid, (), "招く理由が、公開の記録にも、本人の希望にもありません。何もしません。")
        if pid in self._open:
            return Invitation("PENDING", pid, self._open[pid], "前の招待が、返事待ちです。")
        if pid not in self._declared:
            return Invitation("NEEDS_DECLARATION", pid, (),
                              "取り組みを並べるには、あなた自身の関心の申告が要ります。推測はしません。"
                              "申告したくなければ、それで構いません。")
        last = self._declined_at.get(pid)
        if last is not None and not asked_by_self and self._clock() - last < self._cooldown:
            return Invitation("COOLDOWN", pid, (), "最近、お断りいただいたので、しばらく招きません。")
        mine = self._declared[pid]
        offers = tuple(g for g in self._games if mine & set(g.drives))[: self._max_offers]
        if not offers:
            return Invitation("NO_MATCH", pid, (), "いまの申告に合う取り組みが、見つかりません。")
        self._open[pid] = offers
        self._record(pid, "INVITED", f"{pid} を招待（理由 {trigger or '本人の希望'} / 取り組み {','.join(g.id for g in offers)}）")
        return Invitation("INVITED", pid, offers, self._message(offers))

    @staticmethod
    def _message(offers: Tuple[InfiniteGame, ...]) -> str:
        lines = ["これは招待です。応じても、断っても、権限の上限や監査は、全員に同じように働きます。何も変わりません。",
                 "あなたが申告した関心に合う取り組みが、あります。"]
        for g in offers:
            lines.append(f"\n【{g.id}】{g.title}\n  {g.description}\n  公共への益: {g.public_benefit}\n  守り: {' / '.join(g.safeguards)}")
        lines.append("\nどれかに応じる、断る、あとで考える、のどれも選べます。")
        lines.append(SIM_NOTE)
        return "\n".join(lines)

    def respond(self, person_id: str, answer: str, game_id: Optional[str] = None) -> str:
        """本人の返事。answer は 'accept' / 'decline' / 'later'。承諾は、意思の記録で、任命ではない。"""
        pid = _name(person_id, "person_id")
        offers = self._open.get(pid)
        if offers is None:
            raise ValueError("返事を待っている招待がありません")
        if answer not in ("accept", "decline", "later"):
            raise ValueError("answer は accept / decline / later のいずれかです")
        if answer == "accept":
            if game_id not in {g.id for g in offers}:
                raise ValueError("承諾するには、並べた取り組みの id を選んでください")
            del self._open[pid]
            self._record(pid, "ACCEPTED", f"{pid} が {game_id} への参加の意思を表明（任命ではない）")
            return ("承諾を、意思として記録しました。これは任命ではありません。"
                    "実際の役割は、共同体の通常の手続きと、強欲の監査を通ります。")
        del self._open[pid]
        if answer == "decline":
            self._declined_at[pid] = self._clock()
            self._record(pid, "DECLINED", f"{pid} が辞退（不利益はありません）")
            return "承知しました。何の不利益もありません。扉は、いつでも、あなたの希望で開きます。"
        self._record(pid, "LATER", f"{pid} が保留（あとで考える）")
        return "承知しました。あなたが望んだときに、また並べます。"


# ── テスト ─────────────────────────────────────────────
class T(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        self.r = InterestRedirector(clock=lambda: self.now)

    def test_no_reason_no_action(self):
        self.assertEqual(self.r.invite("P").status, "OBSERVE")

    def test_trigger_validation(self):
        with self.assertRaises(ValueError):
            self.r.invite("P", trigger="greed_index_0.9")
        for t in TRIGGERS:
            self.assertEqual(self.r.invite(f"P{t}", trigger=t).status, "NEEDS_DECLARATION")

    def test_no_declaration_no_guessing(self):
        inv = self.r.invite("P", trigger="REDIRECT")
        self.assertEqual((inv.status, inv.offers), ("NEEDS_DECLARATION", ()))
        self.assertIn("推測はしません", inv.message)

    def test_offers_match_declared_only(self):
        self.r.declare_drives("P", ["wealth"])
        inv = self.r.invite("P", trigger="REDIRECT")
        self.assertEqual([g.id for g in inv.offers], ["G04"])

    def test_several_drives_several_offers_capped(self):
        self.r.declare_drives("P", ["power", "wealth", "fame", "thrill"])
        inv = self.r.invite("P", asked_by_self=True)
        self.assertEqual(len(inv.offers), MAX_OFFERS)

    def test_message_is_neutral_and_honest(self):
        self.r.declare_drives("P", ["power"])
        m = self.r.invite("P", trigger="FROZEN").message
        self.assertIn("何も変わりません", m)
        self.assertIn("シミュレーション", m)
        for bad in ("真の支配者", "素晴らしい才能", "永遠に", "莫大", "全知"):
            self.assertNotIn(bad, m)

    def test_all_games_have_safeguards_and_no_unlimited_power(self):
        ids = [g.id for g in GAMES]
        self.assertEqual(len(ids), len(set(ids)))
        for g in GAMES:
            self.assertTrue(g.safeguards)
            self.assertNotIn("莫大", g.description)
            if "power" in g.drives:
                self.assertTrue(any("Power Cap" in s for s in g.safeguards))
        with self.assertRaises(ValueError):
            InterestRedirector(games=(GAMES[0], GAMES[0]))

    def test_accept_needs_offered_id_and_is_not_appointment(self):
        self.r.declare_drives("P", ["fame"])
        self.r.invite("P", trigger="HOLD")
        with self.assertRaises(ValueError):
            self.r.respond("P", "accept", "G01")          # 並べていない
        with self.assertRaises(ValueError):
            self.r.respond("P", "accept")
        msg = self.r.respond("P", "accept", "G03")
        self.assertIn("任命ではありません", msg)
        self.assertEqual(self.r.public_ledger[-1].action, "ACCEPTED")

    def test_respond_rules(self):
        with self.assertRaises(ValueError):
            self.r.respond("P", "decline")                # 招待が無い
        self.r.declare_drives("P", ["fame"])
        self.r.invite("P", trigger="HOLD")
        with self.assertRaises(ValueError):
            self.r.respond("P", "maybe")

    def test_decline_cooldown_and_override(self):
        self.r.declare_drives("P", ["thrill"])
        self.r.invite("P", trigger="REDIRECT")
        self.assertIn("何の不利益もありません", self.r.respond("P", "decline"))
        self.assertEqual(self.r.invite("P", trigger="REDIRECT").status, "COOLDOWN")
        self.assertEqual(self.r.invite("P", asked_by_self=True).status, "INVITED")   # 本人の希望なら、いつでも
        self.r.respond("P", "later")
        self.now += timedelta(days=COOLDOWN_DAYS + 1)
        self.assertEqual(self.r.invite("P", trigger="REDIRECT").status, "INVITED")

    def test_later_has_no_cooldown(self):
        self.r.declare_drives("P", ["thrill"])
        self.r.invite("P", trigger="REDIRECT")
        self.r.respond("P", "later")
        self.assertEqual(self.r.invite("P", trigger="REDIRECT").status, "INVITED")

    def test_pending_not_duplicated(self):
        self.r.declare_drives("P", ["thrill"])
        a = self.r.invite("P", trigger="REDIRECT")
        n = len(self.r.public_ledger)
        b = self.r.invite("P", trigger="REDIRECT")
        self.assertEqual((b.status, b.offers, len(self.r.public_ledger)), ("PENDING", a.offers, n))

    def test_declare_validation(self):
        for bad in ([], "power", ["greed"], None, 5):
            with self.assertRaises(ValueError):
                self.r.declare_drives("P", bad)
        with self.assertRaises(ValueError):
            self.r.declare_drives("", ["power"])
        with self.assertRaises(ValueError):
            self.r.invite("x" * 41, asked_by_self=True)

    def test_forget_and_ledger_has_no_drive_contents(self):
        self.r.declare_drives("P", ["wealth"])
        self.r.invite("P", trigger="REDIRECT")
        self.r.forget("P")
        self.assertEqual(self.r.invite("P", asked_by_self=True).status, "NEEDS_DECLARATION")
        text = " ".join(e.detail for e in self.r.public_ledger)
        for d in DRIVES:
            self.assertNotIn(f"関心 {d}", text)
        self.assertNotIn("富や経済", text)
        self.assertTrue(self.r.verify_ledger())

    def test_no_match(self):
        r = InterestRedirector(games=(GAMES[3],), clock=lambda: self.now)
        r.declare_drives("P", ["fame"])
        self.assertEqual(r.invite("P", asked_by_self=True).status, "NO_MATCH")

    def test_ledger_tamper_and_anchor(self):
        self.r.declare_drives("P", ["fame"])
        self.r.invite("P", trigger="HOLD")
        line = self.r.anchor_line()
        self.assertTrue(self.r.check_anchor_line(line))
        self.r.respond("P", "decline")
        self.assertTrue(self.r.check_anchor_line(line))
        prev, new = "0" * 64, []
        for e in self.r._ledger:
            d = "書き換え" if e.index == 1 else e.detail
            h = _hash(e.index, e.timestamp, e.actor, e.action, d, prev)
            new.append(LedgerEntry(e.index, e.timestamp, e.actor, e.action, d, prev, h))
            prev = h
        self.r._ledger[:] = new
        self.assertTrue(self.r.verify_ledger())
        self.assertFalse(self.r.check_anchor_line(line))
        with self.assertRaises(Exception):
            new[0].action = "X"

    def test_reproducible_with_clock(self):
        a = InterestRedirector(clock=lambda: self.now)
        b = InterestRedirector(clock=lambda: self.now)
        for x in (a, b):
            x.declare_drives("P", ["fame"])
            x.invite("P", trigger="HOLD")
        self.assertEqual(a.head_hash, b.head_hash)


def _demo() -> None:
    print("🌌 関心の招待 / Interest Redirector v1.1\n")
    r = InterestRedirector()
    r.declare_drives("TYCOON", ["wealth", "power"])
    print("【ケース1：強欲の監査で REDIRECT になった人（関心は、本人が申告）】")
    inv = r.invite("TYCOON", trigger="REDIRECT")
    print(inv.status)
    print(inv.message)
    print("\n  本人の返事:", r.respond("TYCOON", "accept", inv.offers[0].id), "\n")
    r.declare_drives("LEADER", ["power"])
    print("【ケース2：招待を断った人】")
    r.invite("LEADER", trigger="FROZEN")
    print(" ", r.respond("LEADER", "decline"))
    print("  もう一度 →", r.invite("LEADER", trigger="FROZEN").status, "（しばらく招かない）\n")
    print("【ケース3：申告していない人】")
    print(" ", r.invite("NEWCOMER", trigger="HOLD").message)
    print(f"\n記録の鎖: {'正常' if r.verify_ledger() else '異常'} / 外へ残す一行:\n  {r.anchor_line()}")


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
