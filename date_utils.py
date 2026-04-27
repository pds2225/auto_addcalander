import re
from calendar import monthrange


def normalize_date_ranges(text: str) -> str:
    normalized = text

    # YYYY-MM-DD ~ DD  -> YYYY-MM-DD ~ YYYY-MM-DD
    def repl_short(match):
        year = int(match.group(1))
        month = int(match.group(2))
        start_day = int(match.group(3))
        end_day = int(match.group(4))
        last_day = monthrange(year, month)[1]
        end_day = max(1, min(end_day, last_day))
        return f"{year:04d}-{month:02d}-{start_day:02d}~{year:04d}-{month:02d}-{end_day:02d}"

    # Match only when the end number is NOT followed by a date separator (- . /)
    # Prevents "2026-05-28 ~ 06-02" from being misread as end_day=06
    normalized = re.sub(
        r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})\s*[~∼]\s*(\d{1,2})(?![-./\d])",
        repl_short,
        normalized,
    )

    return normalized
