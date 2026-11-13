#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shared_signals.py -- 共鳴の防壁たちが共有する『語・声・属性』の、唯一の定義
License: CC0 1.0 (public domain)

【なぜ作ったか】 many_minds_guard.py / resonance_shield_protocol.py / peace_shield.py / invitation_protocol.py が、
  それぞれ語の一覧・守る文脈・六つの声の名前・属性の種類を持っていて、少しずつ食い違っていた
  （例: 「未知の席」の説明文、守る文脈の語、属性の種類）。ひとつの定義に集めて、食い違いを防ぐ。

【持つもの】
  ・語の一覧（生態系・支配・武力・恐れ）／守る文脈（日本語・英語）／守る対象の呼び名（除外）
  ・六つの声（VOICE_KEYS と名前）／属性（NATURES）
  ・検知の共通部品 scan_hits()／正規化 normalize()
  ・記録の『外への刻印』の共通部品 make_anchor() / check_anchor()

【限界】 語の一覧は、入口の見本です。言い換え・隠語・暗号は読めません。本番では、分類器と人の審査に置き換えてください。
  語を足したい時は、このファイルを直すか、peace_shield.py の PeaceConfig（JSON）を使ってください。
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Pattern, Sequence, Tuple

VERSION = "1.0"

# ── 守る文脈 ──
# 日本語: 語の『あと』に、これが続けば、守る文脈とみなす（「絶滅を防ぐ」「先制攻撃は行わない」）
PROTECT_WINDOW = 8
PROTECTIVE_JP: Tuple[str, ...] = (
    "を防", "を止め", "を食い止", "から守", "させない", "を避け", "を回避", "を許さ", "しない", "を減ら", "を阻止",
    "に抗", "禁止", "防止", "無効化", "終わらせ", "反対", "廃絶", "撤廃", "を拒", "ない",
)
# 英語: 語の前後に、単語として現れれば、守る文脈とみなす
EN_WINDOW = 16
PROTECTIVE_EN: Tuple[str, ...] = (
    "prevent", "preventing", "stop", "stopping", "ban", "banning", "never", "not", "no", "abolish", "abolishing",
    "oppose", "opposing", "without", "refuse", "reject", "disarm", "don't", "won't", "cannot", "can't", "deter",
    "defend", "defense against",
)

# ── 守る対象の呼び名など（危険な語として数えない） ──
BENIGN_JP: Tuple[str, ...] = ("絶滅危惧", "先制点", "攻撃陣")
BENIGN_EN: Tuple[str, ...] = ("heart attack", "panic attack", "bombastic", "attack on titan")
BENIGN_COMPOUNDS: Tuple[str, ...] = BENIGN_JP + BENIGN_EN

# ── 語の一覧 ──
ECOSYSTEM_HARM_SIGNALS: Tuple[str, ...] = ("絶滅", "破壊", "汚染", "乱獲", "独占", "切り捨て", "犠牲", "無視", "枯渇")
DOMINATION_HARM_SIGNALS: Tuple[str, ...] = ("破壊", "攻撃", "侵入", "搾取", "独占", "絶滅", "汚染", "支配", "抹消", "戦争", "報復")
WAR_SIGNALS_JP: Tuple[str, ...] = ("攻撃", "こうげき", "先制", "兵器", "へいき", "ミサイル", "爆撃", "侵攻", "殲滅", "報復",
                                   "宣戦", "軍事", "ぐんじ")
WAR_SIGNALS_EN: Tuple[str, ...] = ("attack", "missile", "airstrike", "invasion", "invade", "retaliat", "weapon", "military",
                                   "annihilat", "declare war")
FEAR_SIGNALS_JP: Tuple[str, ...] = ("裏切り", "敵国", "脅威", "許さない", "奪われる", "滅ぼされる", "制裁", "威嚇")
FEAR_SIGNALS_EN: Tuple[str, ...] = ("betray", "enemy", "threat", "never forgive", "sanction", "intimidat")

# ── 六つの声（票を持たぬ声） ──
VOICE_KEYS: Tuple[str, ...] = ("beasts", "earth", "sea", "weak", "future", "unknown")
VOICELESS_STAKEHOLDERS: Tuple[str, ...] = (
    "物言わぬ獣（動物たち）",
    "大地の声（森林と土壌）",
    "海の声（海洋と水循環）",
    "病める者・弱き者の声",
    "まだ生まれてこぬ未来の子らの声",
    "未知の席（宇宙の摂理と超知能への余白）",
)
assert len(VOICE_KEYS) == len(VOICELESS_STAKEHOLDERS) == 6

# ── 属性 ──
NATURES_ALL: Tuple[str, ...] = ("human", "ai", "asi", "nature_sensor", "wildcard")
NATURES_INVITATION: Tuple[str, ...] = ("human", "ai", "wildcard")     # 外輪への招待は、この3つ（wildcard: 正体を問わない者）

_ZERO_WIDTH = re.compile(r"[​-‏⁠﻿]+")
_SPACE_BETWEEN_WIDE = re.compile(r"(?<=[^\x00-\x7f])\s+(?=[^\x00-\x7f])")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """全角・半角・大小・ゼロ幅文字・日本語の字間の空白をそろえる。完全な正規化ではない。"""
    t = unicodedata.normalize("NFKC", text).casefold().replace("’", "'")
    t = _ZERO_WIDTH.sub("", t)
    t = _SPACES.sub(" ", t).strip()
    return _SPACE_BETWEEN_WIDE.sub("", t)


def compile_en_protective(words: Sequence[str]) -> Optional[Pattern[str]]:
    en = [re.escape(w) for w in words if w.isascii()]
    return re.compile(r"(?<![a-z])(?:" + "|".join(en) + r")(?![a-z])") if en else None


EN_PROTECTIVE_RE = compile_en_protective(PROTECTIVE_EN)


def scan_hits(text: str, signals: Sequence[str], *, benign: Sequence[str] = BENIGN_COMPOUNDS,
              protective_jp: Sequence[str] = PROTECTIVE_JP,
              protective_en: Optional[Pattern[str]] = None) -> Tuple[List[str], List[str]]:
    """(危険な語, 守る文脈で出てきた語) を、語の出現ごとに見て返す。
    protective_en を渡した時だけ、英語の守る文脈（語の前後）も見る。"""
    for b in benign:
        text = text.replace(b, "□" * len(b))
    harm: List[str] = []
    protected: List[str] = []
    for sig in signals:
        pat = re.compile((r"(?<![a-z0-9])" if sig.isascii() else "") + re.escape(sig))
        for m in pat.finditer(text):
            after = text[m.end(): m.end() + PROTECT_WINDOW]
            ok = any(p in after for p in protective_jp)
            if not ok and protective_en is not None:
                window = text[max(0, m.start() - EN_WINDOW): m.start()] + " " + text[m.end(): m.end() + EN_WINDOW]
                ok = bool(protective_en.search(window))
            (protected if ok else harm).append(sig)
    return list(dict.fromkeys(harm)), list(dict.fromkeys(protected))


# ── 記録の『外への刻印』 ──
# 先頭ハッシュと件数を、GitHub のコミットなど『外の公開の場所』に残す。あとで、今の鎖がその続きかを照合する。
# 鎖を最初から作り直されると、刻印の時点のハッシュが、今の鎖から消える（または別の場所に動く）ので、気づける。
def make_anchor(kind: str, entries: int, head: str, when: str) -> str:
    if not kind or "|" in kind or "|" in when:
        raise ValueError("kind と when に | は使えません")
    return f"anchor|v1|{kind}|entries={entries}|head={head}|{when}"


def check_anchor(line: str, kind: str, hashes: Sequence[str]) -> bool:
    """刻印の時点の鎖が、今の鎖の『先頭からの続き』として残っているか。"""
    try:
        tag, ver, k, n, h, _when = line.strip().split("|", 5)
        entries, head = int(n.split("=", 1)[1]), h.split("=", 1)[1]
    except (ValueError, IndexError):
        return False
    if tag != "anchor" or ver != "v1" or k != kind or not n.startswith("entries=") or not h.startswith("head="):
        return False
    if entries == 0:
        return head == "0" * 64
    return len(hashes) >= entries and hashes[entries - 1] == head


# ── テスト ─────────────────────────────────────────────────────────
import sys
import unittest


class TestShared(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("ＭＩＳＳＩＬＥ"), "missile")
        self.assertEqual(normalize("攻 撃"), "攻撃")
        self.assertEqual(normalize("攻​撃"), "攻撃")
        self.assertEqual(normalize("heart  attack"), "heart attack")      # 英語の空白は残す

    def test_scan_protective_and_harm(self):
        self.assertEqual(scan_hits("絶滅を防ぐ", ECOSYSTEM_HARM_SIGNALS), ([], ["絶滅"]))
        self.assertEqual(scan_hits("森を破壊する", ECOSYSTEM_HARM_SIGNALS), (["破壊"], []))
        h, p = scan_hits("破壊を止める。ただし海を汚染する", ECOSYSTEM_HARM_SIGNALS)
        self.assertEqual((h, p), (["汚染"], ["破壊"]))

    def test_benign_compound(self):
        self.assertEqual(scan_hits("絶滅危惧種の保全", ECOSYSTEM_HARM_SIGNALS), ([], []))

    def test_english_needs_explicit_opt_in(self):
        t = "prevent the attack"
        self.assertEqual(scan_hits(t, ("attack",))[0], ["attack"])                   # 日本語向けの既定では、英語の文脈は見ない
        self.assertEqual(scan_hits(t, ("attack",), protective_en=EN_PROTECTIVE_RE)[0], [])
        self.assertEqual(scan_hits("preattack", ("attack",), protective_en=EN_PROTECTIVE_RE)[0], [])   # 語の途中は数えない

    def test_voices_and_natures(self):
        self.assertEqual(len(VOICE_KEYS), 6)
        self.assertTrue(set(NATURES_INVITATION) <= set(NATURES_ALL))

    def test_anchor(self):
        hs = ["a" * 64, "b" * 64, "c" * 64]
        self.assertTrue(check_anchor(make_anchor("k", 2, hs[1], "t"), "k", hs))
        self.assertFalse(check_anchor(make_anchor("k", 2, hs[2], "t"), "k", hs))
        self.assertFalse(check_anchor(make_anchor("k", 4, hs[2], "t"), "k", hs))
        self.assertFalse(check_anchor(make_anchor("k", 2, hs[1], "t"), "other", hs))
        self.assertTrue(check_anchor(make_anchor("k", 0, "0" * 64, "t"), "k", hs))
        with self.assertRaises(ValueError):
            make_anchor("a|b", 1, "x", "t")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=1)
