"""Find the video link in text copied from a platform's share button."""
import re

# Share text puts a title before the link; CJK punctuation and full-width brackets often touch it.
_LINK = re.compile(r'https://[^\s<>"\'　-〿＀-￯]+', re.IGNORECASE)


def extract_url(text):
    """Return the first https:// link in pasted text, or the stripped text when there is none."""
    text = (text or '').strip()
    match = _LINK.search(text)
    return match.group(0).rstrip('.,;:!?)]}') if match else text
