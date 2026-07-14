---
name: Arabic rendering in matplotlib & reportlab PDFs
description: Why Arabic shows as disconnected letters or boxes in generated charts/PDFs, and the font requirement that fixes it.
---

Rendering Arabic in generated images (matplotlib PNGs) and PDFs (reportlab) requires TWO independent things:

1. **Reshaping + bidi**: raw Arabic strings render as isolated, left-to-right letters. Must run text through `arabic-reshaper` then `python-bidi` (a single `ar()` helper does this) before drawing.
2. **A font that contains the Arabic Presentation Forms-B Unicode block (U+FE70–U+FEFF)**: reshaping produces presentation-form glyphs, so a font missing that block renders them as empty boxes (□) even though the shaping is correct.

**Why:** Many popular Arabic webfonts (Tajawal, Cairo) ship glyphs for the base Arabic block but NOT all Presentation Forms-B codepoints (e.g. U+FE8D, U+FEAD were missing in Tajawal). Amiri contains the full block (verified 0 missing glyphs) and works for both matplotlib and reportlab.

**How to apply:** Bundle Amiri (Regular + Bold) under `assets/fonts/`. For matplotlib, load via `FontProperties` and use its `.get_name()` for the family. For reportlab, register as a named font. To verify a candidate font covers the needed glyphs, check each reshaped codepoint against the font's cmap before trusting it. Test the final PNG/PDF under `-W error::UserWarning` — missing-glyph warnings become errors and catch the problem early.
