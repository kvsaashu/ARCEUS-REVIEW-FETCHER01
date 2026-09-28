import re
import difflib

def match_exact_comment(comment: str, target: str) -> bool:
    c_str = str(comment).strip()
    t_str = str(target).strip()
    if not c_str or not t_str:
        return False

    # 1. Direct case-insensitive substring match
    if t_str.lower() in c_str.lower():
        return True

    # 2. Punctuation & space normalized exact substring match
    c_norm = re.sub(r'[^\w\s]', ' ', c_str.lower())
    c_norm = " ".join(c_norm.split())
    
    t_norm = re.sub(r'[^\w\s]', ' ', t_str.lower())
    t_norm = " ".join(t_norm.split())

    if t_norm and t_norm in c_norm:
        return True

    # 3. Word-by-word consecutive match where EVERY SINGLE WORD of target MUST be present
    words_t = t_norm.split()
    words_c = c_norm.split()
    if not words_t or not words_c:
        return False

    if len(words_t) > len(words_c):
        return False

    k_len = len(words_t)
    for i in range(len(words_c) - k_len + 1):
        window = words_c[i : i + k_len]
        all_match = True
        for tw, cw in zip(words_t, window):
            if tw == cw:
                continue
            # Allow minor missing ending character (e.g. 'massag' instead of 'massage')
            if len(tw) >= 3 and len(cw) >= 3 and (tw.startswith(cw) or cw.startswith(tw) or difflib.SequenceMatcher(None, tw, cw).ratio() >= 0.88):
                continue
            all_match = False
            break
        if all_match:
            return True

    return False

# Unit tests
test_cases = [
    # (review, target, expected, desc)
    ("amazing app and instant payment", "AMAZING APP AND INSTANT PAYMENT", True, "Upper vs lower case"),
    ("Really good service and smooth experience", "really good service and smooth experience", True, "Exact case insensitive"),
    ("Really good service and smooth experience", "Really good service and experience", False, "Missing 1 word (smooth) -> NO COUNT"),
    ("Aroma oils and gentle touch felt amazing at aroma Swedish massage spa.", "Aroma oils and gentle touch felt amazing at aroma Swedish massage spa.", True, "Full target match"),
    ("Aroma oils and gentle touch felt amazing at aroma Swedish massage spa.", "Aroma oils and gentle touch felt amazing", False, "Partial comment -> NO COUNT"),
    ("Great game! Fast response.. 😊", "great game fast response", True, "Punctuation & emoji normalized"),
    ("I love antigravity #1", "i love antigravity #1", True, "With symbol #1"),
]

all_passed = True
for r, t, exp, desc in test_cases:
    actual = match_exact_comment(r, t)
    status = "PASS" if actual == exp else "FAIL"
    if actual != exp:
        all_passed = False
    print(f"[{status}] {desc} | Expected: {exp}, Got: {actual}")

print("\nALL PASSED:", all_passed)

