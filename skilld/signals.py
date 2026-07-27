"""Heuristic pre-filter: score messages for 'teaching moment' signals.

The LLM does the real distillation; these signals decide whether a project is
worth an LLM call at all, and annotate high-value messages so the model
pays attention to them.

Signal hierarchy (strongest first):
  1. correction  — "no, not like that"; the agent did it wrong, the fix is stated
  2. frustration — the clearest evidence of pain
  3. repetition  — same instruction across sessions (computed at corpus level)
  4. preference  — explicit "always/never" style statements
"""

import re

CORRECTION = re.compile(
    r"(hay[ıi]r|yanl[ıi][şs]|olmad[ıi]|olmam[ıi][şs]|demi[şs]tim|d[üu]zelt|"
    r"\bdeğil\b|kullanma|yapma\b|anlam[ıi]yorsun|s[öo]yledim|"
    r"\bno[,.]|not like that|that'?s wrong|i said|instead of|don'?t use)",
    re.I,
)
FRUSTRATION = re.compile(
    r"(ulan|geri zekal[ıi]|neden (hala|h[âa]l[âa])|ka[çc] kere|yine mi|"
    r"\bwhy (do you keep|can'?t you)|again\?|hala|h[âa]l[âa] daha)",
    re.I,
)
PREFERENCE = re.compile(
    r"(her zaman|asla|hi[çc]bir zaman|bundan sonra|hep b[öo]yle|olmal[ıi]|"
    r"laz[ıi]m|gerek(iyor)?\b|olsun\b|\balways\b|\bnever\b|from now on|"
    r"make sure|must\b)",
    re.I,
)


def score(text: str) -> int:
    """0 = no signal, higher = stronger teaching moment."""
    s = 0
    if CORRECTION.search(text):
        s += 3
    if FRUSTRATION.search(text):
        s += 2
    if PREFERENCE.search(text):
        s += 1
    return s


def tag(text: str) -> str:
    """Inline marker prepended to high-signal messages in the LLM corpus."""
    n = score(text)
    if n >= 3:
        return "[CORRECTION] "
    if n == 2:
        return "[FRUSTRATION] "
    if n == 1:
        return "[PREFERENCE] "
    return ""


def worth_distilling(messages, min_signals: int = 3) -> bool:
    """A project earns an LLM call if it has enough teaching signal."""
    return sum(1 for _, m in messages if score(m) > 0) >= min_signals
