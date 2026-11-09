"""MSN Messenger & Retro webboard emoticon rendering and external GIF parsing."""

import re
from django.utils.html import escape
from django.utils.safestring import mark_safe

MSN_EMOTICONS = [
    {
        "code": ":)",
        "label": "ยิ้ม",
        "symbol": "😊",
        "svg": (
            '<span class="msn-icon msn-smile" title=":)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="10" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="10" r="1.5" fill="#4A3B00"/>'
            '<path d="M7 14.5 C9 18 15 18 17 14.5" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":D",
        "label": "หัวเราะร่า",
        "symbol": "😀",
        "svg": (
            '<span class="msn-icon msn-laugh" title=":D">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<path d="M7 13 C7 17.5 17 17.5 17 13 Z" fill="#FFFFFF" '
            'stroke="#4A3B00" stroke-width="1.5"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ";)",
        "label": "ขยิบตา",
        "symbol": "😉",
        "svg": (
            '<span class="msn-icon msn-wink" title=";)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<path d="M6.5 10 Q8.5 7.5 10 10" fill="none" stroke="#4A3B00" '
            'stroke-width="1.8" stroke-linecap="round"/>'
            '<circle cx="16" cy="10" r="1.5" fill="#4A3B00"/>'
            '<path d="M8 15 C10 18 15 17.5 16 15" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":-O",
        "label": "อ้าปากค้าง",
        "symbol": "😮",
        "svg": (
            '<span class="msn-icon msn-surprised" title=":-O">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="9" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="9" r="1.5" fill="#4A3B00"/>'
            '<ellipse cx="12" cy="15" rx="3.5" ry="4.5" fill="#800000" '
            'stroke="#4A3B00" stroke-width="1.5"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":P",
        "label": "แลบลิ้น",
        "symbol": "😛",
        "svg": (
            '<span class="msn-icon msn-tongue" title=":P">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<path d="M7 13 H17" stroke="#4A3B00" stroke-width="1.8"/>'
            '<path d="M11 13 C11 17 15 17 15 13 Z" fill="#FF4466" '
            'stroke="#C00020" stroke-width="1.2"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(H)",
        "label": "แว่นกันแดดสุดเท่",
        "symbol": "😎",
        "svg": (
            '<span class="msn-icon msn-cool" title="(H)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<path d="M5 9 Q12 11 19 9" stroke="#111111" stroke-width="2"/>'
            '<ellipse cx="8.5" cy="11.5" rx="3.5" ry="2.5" fill="#111111"/>'
            '<ellipse cx="15.5" cy="11.5" rx="3.5" ry="2.5" fill="#111111"/>'
            '<path d="M9 16 C11 18 13 18 15 16" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":@",
        "label": "โกรธจัดหน้าแดง",
        "symbol": "😡",
        "svg": (
            '<span class="msn-icon msn-angry" title=":@">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FF4B4B" stroke="#B00000" '
            'stroke-width="1.5"/>'
            '<path d="M6 7.5 L10 10" stroke="#330000" stroke-width="2"/>'
            '<path d="M18 7.5 L14 10" stroke="#330000" stroke-width="2"/>'
            '<circle cx="8.5" cy="11" r="1.3" fill="#330000"/>'
            '<circle cx="15.5" cy="11" r="1.3" fill="#330000"/>'
            '<path d="M8 17 C10 14 14 14 16 17" fill="none" '
            'stroke="#330000" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":S",
        "label": "สับสน",
        "symbol": "😵‍💫",
        "svg": (
            '<span class="msn-icon msn-confused" title=":S">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<path d="M7 16 Q10 13 12 16 T17 15" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":$",
        "label": "เขินอายหน้าแดง",
        "symbol": "😳",
        "svg": (
            '<span class="msn-icon msn-blush" title=":$">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<ellipse cx="6" cy="13" rx="2.5" ry="1.5" fill="#FF6B6B"/>'
            '<ellipse cx="18" cy="13" rx="2.5" ry="1.5" fill="#FF6B6B"/>'
            '<circle cx="8" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="9.5" r="1.5" fill="#4A3B00"/>'
            '<path d="M9 16 C11 17.5 13 17.5 15 16" fill="none" '
            'stroke="#4A3B00" stroke-width="1.6" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":(",
        "label": "เศร้า",
        "symbol": "🙁",
        "svg": (
            '<span class="msn-icon msn-sad" title=":(">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="10" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="10" r="1.5" fill="#4A3B00"/>'
            '<path d="M8 16 C10 13.5 14 13.5 16 16" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":'(",
        "label": "ร้องไห้",
        "symbol": "😭",
        "svg": (
            '<span class="msn-icon msn-crying" title=":\'(">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="10" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="10" r="1.5" fill="#4A3B00"/>'
            '<path d="M6.5 12 C6 15 5 18 6.5 20 C8 18 7 15 6.5 12 Z" '
            'fill="#29B6F6"/>'
            '<path d="M8 16 C10 14 14 14 16 16" fill="none" '
            'stroke="#4A3B00" stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": ":|",
        "label": "หน้านิ่ง",
        "symbol": "😐",
        "svg": (
            '<span class="msn-icon msn-straight" title=":|">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="12" r="10" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8" cy="10" r="1.5" fill="#4A3B00"/>'
            '<circle cx="16" cy="10" r="1.5" fill="#4A3B00"/>'
            '<line x1="8" y1="15" x2="16" y2="15" stroke="#4A3B00" '
            'stroke-width="1.8" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(A)",
        "label": "เทวดานางฟ้า",
        "symbol": "😇",
        "svg": (
            '<span class="msn-icon msn-angel" title="(A)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<ellipse cx="12" cy="3" rx="7" ry="2" fill="none" '
            'stroke="#FFC107" stroke-width="1.8"/>'
            '<circle cx="12" cy="13" r="9" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8.5" cy="12" r="1.3" fill="#4A3B00"/>'
            '<circle cx="15.5" cy="12" r="1.3" fill="#4A3B00"/>'
            '<path d="M8.5 16 C10.5 18 13.5 18 15.5 16" fill="none" '
            'stroke="#4A3B00" stroke-width="1.6" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "<:o)",
        "label": "ปาร์ตี้",
        "symbol": "🥳",
        "svg": (
            '<span class="msn-icon msn-party" title="<:o)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<polygon points="7,8 17,2 17,8" fill="#9C27B0" stroke="#6A1B9A" '
            'stroke-width="1.2"/>'
            '<circle cx="12" cy="13" r="9" fill="#FFD000" stroke="#C88E00" '
            'stroke-width="1.5"/>'
            '<circle cx="8.5" cy="12" r="1.3" fill="#4A3B00"/>'
            '<circle cx="15.5" cy="12" r="1.3" fill="#4A3B00"/>'
            '<path d="M8.5 16.5 C10.5 19 13.5 19 15.5 16.5" fill="none" '
            'stroke="#4A3B00" stroke-width="1.6" stroke-linecap="round"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(L)",
        "label": "หัวใจสีแดง",
        "symbol": "❤️",
        "svg": (
            '<span class="msn-icon msn-heart" title="(L)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 '
            "4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 "
            "16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 "
            '21.35z" fill="#E53935" stroke="#B71C1C" stroke-width="1.2"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(U)",
        "label": "อกหัก",
        "symbol": "💔",
        "svg": (
            '<span class="msn-icon msn-broken-heart" title="(U)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 '
            "4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 "
            "16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 "
            '21.35z" fill="#E53935" stroke="#B71C1C" stroke-width="1.2"/>'
            '<path d="M12 4 L9 10 L14 13 L11 18 L13 21" stroke="#FFFFFF" '
            'stroke-width="1.8" fill="none"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(F)",
        "label": "ดอกกุหลาบ",
        "symbol": "🌹",
        "svg": (
            '<span class="msn-icon msn-rose" title="(F)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="12" cy="7" r="5" fill="#D32F2F" stroke="#9A0007" '
            'stroke-width="1.2"/>'
            '<path d="M12 12 V22" stroke="#2E7D32" stroke-width="2.5"/>'
            '<path d="M12 16 Q8 14 7 17" fill="none" stroke="#2E7D32" '
            'stroke-width="2"/>'
            '<path d="M12 18 Q16 16 17 19" fill="none" stroke="#2E7D32" '
            'stroke-width="2"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(M)",
        "label": "MSN Buddy",
        "symbol": "💬",
        "svg": (
            '<span class="msn-icon msn-buddy" title="(M)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<circle cx="8" cy="8" r="4" fill="#00838F"/>'
            '<circle cx="16" cy="10" r="3.5" fill="#F57C00"/>'
            '<path d="M3 20 C3 15 13 15 13 20 Z" fill="#00ACC1"/>'
            '<path d="M11 20 C11 16 21 16 21 20 Z" fill="#FFA726"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(*)",
        "label": "ดาวสีทอง",
        "symbol": "⭐",
        "svg": (
            '<span class="msn-icon msn-star" title="(*)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<polygon points="12,2 15,9 22,9 17,14 19,21 12,17 5,21 7,14 '
            '2,9 9,9" fill="#FFC107" stroke="#FFA000" stroke-width="1.2"/>'
            "</svg></span>"
        ),
    },
    {
        "code": "(S)",
        "label": "พระจันทร์เสี้ยว",
        "symbol": "🌙",
        "svg": (
            '<span class="msn-icon msn-moon" title="(S)">'
            '<svg viewBox="0 0 24 24" width="20" height="20">'
            '<path d="M12 3 C7 3 3 7 3 12 C3 17 7 21 12 21 C14.5 21 16.8 '
            '20 18.5 18.5 C14 18 10.5 14.5 10 10 C9.5 7 10.5 4.5 12 3 Z" '
            'fill="#FFD54F" stroke="#FFB300" stroke-width="1.2"/>'
            "</svg></span>"
        ),
    },
]

IMG_TAG_REGEX = re.compile(
    r"\[img\]\s*(https?://[^\s\"'<>]+?\."
    r"(?:gif|png|jpe?g|webp|bmp)(?:\?[^\s\"'<>]*)?)\s*\[/img\]",
    re.IGNORECASE,
)

BARE_IMG_REGEX = re.compile(
    r"(?<!src=\")(https?://[^\s\"'<>]+?\.(?:gif|png|jpe?g|webp)(?:\?[^\s\"'<>]*)?)",
    re.IGNORECASE,
)


def get_msn_emoticons_list():
    """Return the available list of curated MSN emoticons."""
    return MSN_EMOTICONS


def render_webboard_content(text: str) -> str:
    """Sanitize user text, replace [img] & external GIFs, and parse emoticons."""
    if not text:
        return ""

    escaped = escape(text)

    def _replace_img_tag(match):
        url = match.group(1)
        return (
            '<div class="webboard-embed-box">'
            f'<img src="{url}" alt="external-gif" class="webboard-embed-img" '
            'loading="lazy" referrerpolicy="no-referrer">'
            "</div>"
        )

    processed = IMG_TAG_REGEX.sub(_replace_img_tag, escaped)

    def _replace_bare_img(match):
        url = match.group(1)
        return (
            '<div class="webboard-embed-box">'
            f'<img src="{url}" alt="external-gif" class="webboard-embed-img" '
            'loading="lazy" referrerpolicy="no-referrer">'
            "</div>"
        )

    tokens = re.split(r'(<div class="webboard-embed-box">.*?</div>)', processed)
    for idx, token in enumerate(tokens):
        if not token.startswith('<div class="webboard-embed-box">'):
            tokens[idx] = BARE_IMG_REGEX.sub(_replace_bare_img, token)
    processed = "".join(tokens)

    sorted_emoticons = sorted(
        MSN_EMOTICONS,
        key=lambda item: len(item["code"]),
        reverse=True,
    )

    for emo in sorted_emoticons:
        code_escaped = escape(emo["code"])
        processed = processed.replace(code_escaped, emo["svg"])

    processed = processed.replace("\r\n", "\n").replace("\r", "\n")
    processed = processed.replace("\n", "<br>\n")

    # Input is HTML-escaped before safe SVGs are inserted
    return mark_safe(processed)  # nosec B308, B703
