import re
import difflib
from typing import List, Optional, Tuple, Dict, Any

def is_symbol_only(text: str) -> bool:
    """Check if the keyword consists only of punctuation/symbols (e.g. '.', '..', '!', '#')."""
    if not text:
        return False
    return all(not ch.isalnum() for ch in text.strip())

def normalize_text(text: str) -> str:
    """Normalizes text by removing non-alphanumeric punctuation and lowercasing."""
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def match_symbol_trailing(comment: str, symbol: str) -> bool:
    """
    Check if a comment ends with a specific symbol/punctuation sequence.
    Tolerates minor differences:
    - If symbol is '..', also accepts single '.' or '...' (missing or extra dot)
    - Tolerates trailing emojis and spaces
    """
    comment = str(comment).strip()
    symbol = str(symbol).strip()
    if not comment or not symbol:
        return False
    
    # Direct match
    if comment.endswith(symbol):
        return True

    # Trailing dots tolerance: if symbol consists of dots ('.' or '..')
    if set(symbol) == {'.'}:
        if re.search(r'\.+[\s\U00010000-\U0010ffff]*$', comment):
            return True

    # Regex trailing non-word sequence matching symbol
    m = re.search(r'([^\w\s]+)[\s\U00010000-\U0010ffff]*$', comment)
    if m:
        trailing = m.group(1).strip()
        if trailing == symbol or symbol in trailing:
            return True

    return False

def match_ending_hint(comment: str, ending_hint: str) -> bool:
    """
    Checks if a review comment ends with the specified hint/suffix (case-insensitive).
    Tolerates:
    - ALL CAPS vs lowercase
    - Missing dot (e.g. user typed '.' instead of '..' or vice-versa)
    - Missing 1 alphabet at the end (e.g. '#ARCEU' instead of '#ARCEUS' or 'bonu' instead of 'bonus')
    - Trailing emojis, spaces, and punctuation (e.g. '.. 😊', '.. 👍')
    """
    if not ending_hint or not ending_hint.strip():
        return True

    clean_comment = str(comment).strip().lower()
    clean_hint = ending_hint.strip().lower()

    # 1. Direct match at end
    if clean_comment.endswith(clean_hint):
        return True

    # 2. Dot-based tolerance (if hint is '..' or '...', also accepts single '.' or '...')
    if set(clean_hint) == {'.'}:
        if re.search(r'\.+[\s\U00010000-\U0010ffff]*$', clean_comment):
            return True

    # 3. Check tail (last 35 chars) for hint followed only by emojis, whitespace or punctuation
    tail = clean_comment[-max(35, len(clean_hint) + 15):]
    idx = tail.rfind(clean_hint)
    if idx != -1:
        after_hint = tail[idx + len(clean_hint):].strip()
        if not after_hint or all(not ch.isalnum() for ch in after_hint):
            return True

    # 4. Strip trailing emojis/non-ascii and check
    stripped_tail = re.sub(r'[^\w\s\.\!\#\?]+$', '', clean_comment).strip()
    if stripped_tail.endswith(clean_hint):
        return True

    # 5. Missing 1 alphabet at the end of the last word (e.g. '#ARCEU' instead of '#ARCEUS' or 'bonu' instead of 'bonus')
    last_tokens = [t for t in tail.split() if t.strip()]
    if last_tokens:
        last_token = last_tokens[-1]
        token_clean = re.sub(r'^[^\w]+|[^\w]+$', '', last_token)
        hint_clean = re.sub(r'^[^\w]+|[^\w]+$', '', clean_hint)
        if token_clean and hint_clean:
            if len(hint_clean) >= 3 and hint_clean.startswith(token_clean) and len(hint_clean) - len(token_clean) == 1:
                return True
            if len(token_clean) >= 3 and len(hint_clean) >= 3:
                ratio = difflib.SequenceMatcher(None, hint_clean, token_clean).ratio()
                if ratio >= 0.80:
                    return True

    return False

def calculate_comment_similarity(review: str, target: str) -> float:
    """
    Calculates similarity between a posted review and a target comment.
    Returns a score between 0.0 and 1.0 based on:
    1. Direct containment (1.0)
    2. Word overlap / token coverage (with typo tolerance)
    3. Sequence alignment / sliding window
    """
    r_clean = re.sub(r'[^\w\s]', ' ', review.lower()).strip()
    t_clean = re.sub(r'[^\w\s]', ' ', target.lower()).strip()
    if not t_clean or not r_clean:
        return 0.0

    # 1. Direct containment
    if t_clean in r_clean or r_clean in t_clean:
        return 1.0

    words_t = [w for w in t_clean.split() if w]
    words_r = [w for w in r_clean.split() if w]
    if not words_t or not words_r:
        return 0.0

    # 2. Word overlap / token coverage (with fuzzy typo tolerance)
    matched_words = 0
    for tw in words_t:
        if any(difflib.SequenceMatcher(None, tw, rw).ratio() >= 0.80 for rw in words_r):
            matched_words += 1
    word_ratio = matched_words / len(words_t)

    # 3. Sequence ratio: best sliding window
    seq_ratio = 0.0
    if len(words_r) >= len(words_t):
        for i in range(len(words_r) - len(words_t) + 1):
            sub = " ".join(words_r[i:i+len(words_t)])
            ratio = difflib.SequenceMatcher(None, t_clean, sub).ratio()
            if ratio > seq_ratio:
                seq_ratio = ratio
    else:
        seq_ratio = difflib.SequenceMatcher(None, t_clean, r_clean).ratio()

    return seq_ratio

def match_single_keyword(comment: str, keyword: str, exact_word: bool = False, is_app_mode: bool = False, min_comment_ratio: float = 0.70) -> bool:
    """
    Matches a single keyword or comment against review comment.
    In APP mode (or when exact_word is True), enforces exact comment matching.
    Tolerates:
    - ALL CAPS vs lowercase (e.g. 'FAST PAYMENT' == 'fast payment')
    - Missing punctuation/dots (e.g. 'fast payment.' matches 'fast payment')
    - Minor 1-letter typo in the exact sentence (SequenceMatcher >= 0.88)
    - Rejects different reviews that merely share unordered words (e.g. Smith vs Nisha)
    """
    comment_str = str(comment).strip().rstrip(',')
    keyword_str = str(keyword).strip().rstrip(',')
    if not comment_str or not keyword_str:
        return False

    # Symbol-only check (e.g., '.', '..', '!')
    if is_symbol_only(keyword_str):
        return match_symbol_trailing(comment_str, keyword_str)

    comment_lower = comment_str.lower()
    keyword_lower = keyword_str.lower()

    # 1. Exact case-insensitive direct match
    if keyword_lower == comment_lower:
        return True

    # 2. Punctuation & space normalized exact equality (same comment, small/capital & punctuation no difference)
    c_norm = " ".join(normalize_text(comment_lower).split())
    k_norm = " ".join(normalize_text(keyword_lower).split())

    if c_norm and k_norm and c_norm == k_norm:
        return True

    words_k = k_norm.split()
    words_c = c_norm.split()

    # 3. For multi-word comments:
    if len(words_k) >= 2:
        if exact_word or is_app_mode:
            # For App mode or when Exact Match is checked:
            # MUST be the exact target comment!
            # 1) Full normalized exact match or sentence containment
            if c_norm == k_norm or k_norm in c_norm:
                return True

            # 1b) Truncated review tolerance (e.g. Google Play truncates long reviews at ~500 chars)
            if (len(words_c) >= 10 and k_norm.startswith(c_norm)) or (len(words_k) >= 10 and c_norm.startswith(k_norm)):
                return True

            # 2) Consecutive word-by-word match (Every single word of target must match consecutively)
            if len(words_k) <= len(words_c):
                k_len = len(words_k)
                for i in range(len(words_c) - k_len + 1):
                    window = words_c[i : i + k_len]
                    all_match = True
                    for tw, cw in zip(words_k, window):
                        if tw == cw:
                            continue
                        if len(tw) >= 3 and len(cw) >= 3 and (tw.startswith(cw) or cw.startswith(tw) or difflib.SequenceMatcher(None, tw, cw).ratio() >= 0.88):
                            continue
                        all_match = False
                        break
                    if all_match:
                        return True

            # 3) Minor 1-letter typo tolerance across the full sentence
            seq_sim = difflib.SequenceMatcher(None, k_norm, c_norm).ratio()
            return seq_sim >= 0.88

        # When Exact Match is unchecked in Map mode: requires phrase containment or sequence match >= 70%
        return k_norm in c_norm or calculate_comment_similarity(comment_str, keyword_str) >= min_comment_ratio

    # 4. Single-word keyword matching
    if len(words_k) == 1:
        kw = words_k[0]
        pattern = r'(?<!\w)' + re.escape(kw) + r'(?!\w)'
        if re.search(pattern, comment_lower) is not None:
            return True
        # Typo or prefix tolerance for single word (e.g. #ARCEU for #ARCEUS)
        for cw in words_c:
            if len(cw) >= 3 and len(kw) >= 3:
                if kw.startswith(cw) or cw.startswith(kw) or difflib.SequenceMatcher(None, kw, cw).ratio() >= 0.82:
                    return True
        if not (exact_word or is_app_mode):
            return kw in words_c or k_norm in c_norm
        return False

def extract_keyword_list(keyword_text: str) -> List[str]:
    """
    Intelligently extracts individual comments from user input.
    Handles:
    - Multi-line paragraphs separated by blank lines (\n\n)
    - Single-line comments
    - Trailing commas (., or ,)
    """
    if not keyword_text or not keyword_text.strip():
        return []

    # If comments are separated by blank lines (\n\n), treat each block as a comment
    if "\n\n" in keyword_text or "\r\n\r\n" in keyword_text:
        raw_blocks = re.split(r'(?:\r?\n\s*){2,}', keyword_text)
        items = []
        for b in raw_blocks:
            b_clean = " ".join(b.split()).strip()
            if b_clean:
                b_clean = b_clean.rstrip(',').strip()
                if b_clean:
                    items.append(b_clean)
        if items:
            return items

    # Otherwise split by single lines
    items = []
    for line in keyword_text.splitlines():
        line_clean = line.strip().rstrip(',').strip()
        if line_clean:
            items.append(line_clean)
    return items

def match_keywords(comment: str, keyword_text: str, exact_word: bool = False, is_app_mode: bool = False) -> Tuple[bool, List[str]]:
    """
    Matches multiple target comments or keywords.
    Each comment can be on its own line, or separated by 1-2 blank lines.
    In App mode (or exact_word=True), strictly requires exact comment matching.
    Returns (is_matched, list_of_matched_keywords).
    """
    if not keyword_text or not keyword_text.strip():
        # If no keywords specified, match all
        return True, []

    keywords = extract_keyword_list(keyword_text)
    if not keywords:
        return True, []

    matched = []
    for kw in keywords:
        if match_single_keyword(comment, kw, exact_word=exact_word, is_app_mode=is_app_mode):
            matched.append(kw)

    return (len(matched) > 0), matched

def match_member_name(reviewer_name: str, members_list_text: str) -> bool:
    """
    Check if the reviewer's name matches any member name in the list.
    Tolerates:
    - ALL CAPS vs lowercase
    - Missing middle names / initials
    - Minor spelling differences (similarity ratio >= 0.75)
    """
    if not members_list_text or not members_list_text.strip():
        return True

    members = [m.strip().lower() for m in members_list_text.splitlines() if m.strip()]
    if not members:
        return True

    name_clean = reviewer_name.strip().lower()
    name_words = [w for w in re.sub(r'[^\w\s]', '', name_clean).split() if len(w) >= 2]

    for m in members:
        # Direct substring
        if m in name_clean or name_clean in m:
            return True

        # First name / primary token match (e.g. 'Aditya' in 'Aditya Raj')
        m_words = [w for w in re.sub(r'[^\w\s]', '', m).split() if len(w) >= 2]
        if m_words and name_words:
            # If both have matching first word
            if m_words[0] == name_words[0]:
                return True
            # Fuzzy match of full name
            ratio = difflib.SequenceMatcher(None, m, name_clean).ratio()
            if ratio >= 0.75:
                return True

    return False

def highlight_matches(text: str, matched_keywords: List[str]) -> str:
    """
    Wraps matched keywords with <mark class="kw-highlight"> for frontend display.
    """
    if not matched_keywords or not text:
        return text

    highlighted = text
    for kw in matched_keywords:
        if not is_symbol_only(kw):
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f'<mark class="kw-highlight">{m.group(0)}</mark>', highlighted)
        else:
            # Trailing symbol highlight
            if highlighted.endswith(kw):
                pos = highlighted.rfind(kw)
                highlighted = highlighted[:pos] + f'<mark class="kw-highlight">{kw}</mark>'
    return highlighted
