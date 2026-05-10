"""Fix issues in the resume PDF:

1. Reposition + resize the profile photo so it stays within page margins
   and preserves its natural aspect ratio.
2. Rewrite the contact line so every item (phone, email, LinkedIn,
   Codeforces) shares the same font, size, color and baseline alignment.
3. Use the requested display text:
       linkedin/sairam-chakrala
       codeforces/chakrala_s
4. Attach clickable URI annotations to the LinkedIn and Codeforces text.
   No borders/underlines - the links are visually identical to the rest
   of the contact line.
"""

import fitz

LINKEDIN_URL = "https://www.linkedin.com/in/sairam-chakrala-a18509276/"
CODEFORCES_URL = "https://codeforces.com/profile/chakrala_s"

CARLITO_PATH = "/tmp/Carlito-Regular.ttf"
SRC = "Chakrala_Sairam_Resume_Final.pdf"
DST = "Chakrala_Sairam_Resume_Final_FIXED.pdf"

doc = fitz.open(SRC)
page = doc[0]

# ---------------------------------------------------------------------------
# 1) Profile photo: cover original placement and re-insert preserving aspect.
# ---------------------------------------------------------------------------
imgs = page.get_images(full=True)
img_xref = imgs[0][0]
pix = fitz.Pixmap(doc, img_xref)
img_w, img_h = pix.width, pix.height

new_right = 575.0
new_top = 28.0
target_h = 110.0
target_w = target_h * img_w / img_h
new_left = new_right - target_w
new_bottom = new_top + target_h
new_rect = fitz.Rect(new_left, new_top, new_right, new_bottom)
print(f"Original image rect: {page.get_image_rects(img_xref)}")
print(f"New image rect: {new_rect}")

cover_photo = fitz.Rect(500, 24, 600, 138)
page.draw_rect(cover_photo, color=(1, 1, 1), fill=(1, 1, 1),
               overlay=True, width=0)

img_bytes = pix.tobytes("png")
page.insert_image(new_rect, stream=img_bytes,
                  keep_proportion=True, overlay=True)

# ---------------------------------------------------------------------------
# 2) Rewrite the contact line.
#
# The original line was rendered in Carlito-Regular 8.5pt at baseline
# y=100.75, color #555555, starting at x=35.1 and ending around x=320.76:
#
#     +91-8019150941    sairamchakrala1@gmail.com    linkedin.com/in/sairam-chakrala
#
# We rewrite it as four equally-styled items separated by the same
# 4-space spacing the original used:
#
#     +91-8019150941    sairamchakrala1@gmail.com    linkedin/sairam-chakrala    codeforces/chakrala_s
#
# Bundling Carlito-Regular keeps it visually identical to the email text
# the user pointed to as the reference style.
# ---------------------------------------------------------------------------

# Cover the existing contact line. Bbox from the original PDF was
# (35.1, 92.66) -> (320.76, 103.03). Pad slightly but stop well before
# the relocated profile photo (which starts at ~x=489.5) so we don't
# punch a white stripe through it.
cover_contact = fitz.Rect(34.5, 92.0, 485.0, 103.6)
page.draw_rect(cover_contact, color=(1, 1, 1), fill=(1, 1, 1),
               overlay=True, width=0)

contact_color = (85 / 255, 85 / 255, 85 / 255)  # 0x555555
contact_baseline_y = 100.75
contact_x = 35.1
font_size = 8.5
fontfile = CARLITO_PATH
fontname = "carlito"

# Register the font on the page so insert_text can refer to it by alias.
page.insert_font(fontname=fontname, fontfile=fontfile)
carlito_font = fitz.Font(fontfile=fontfile)

phone = "+91-8019150941"
email = "sairamchakrala1@gmail.com"
linkedin_text = "linkedin/sairam-chakrala"
codeforces_text = "codeforces/chakrala_s"
sep = "    "  # four spaces, matching the original line


def text_width(s: str) -> float:
    return carlito_font.text_length(s, fontsize=font_size)


# Lay out each segment and remember its x-range so we can attach link
# annotations precisely to the LinkedIn and Codeforces portions.
segments = [phone, sep, email, sep, linkedin_text, sep, codeforces_text]
positions = []
cursor = contact_x
for seg in segments:
    w = text_width(seg)
    positions.append((seg, cursor, w))
    cursor += w

line_text = "".join(segments)
page.insert_text(
    fitz.Point(contact_x, contact_baseline_y),
    line_text,
    fontname=fontname,
    fontfile=fontfile,
    fontsize=font_size,
    color=contact_color,
    overlay=True,
)

linkedin_seg = next(p for p in positions if p[0] == linkedin_text)
codeforces_seg = next(p for p in positions if p[0] == codeforces_text)

# Bbox heights mirror the original contact line (ascent/descent from the
# original span: 92.66 -> 103.03, baseline at 100.75).
y0 = 92.66
y1 = 103.03
linkedin_rect = fitz.Rect(linkedin_seg[1], y0,
                          linkedin_seg[1] + linkedin_seg[2], y1)
codeforces_rect = fitz.Rect(codeforces_seg[1], y0,
                            codeforces_seg[1] + codeforces_seg[2], y1)
print("LinkedIn rect:  ", linkedin_rect)
print("Codeforces rect:", codeforces_rect)

# ---------------------------------------------------------------------------
# 3) Hyperlink annotations (no borders).
# ---------------------------------------------------------------------------
page.insert_link({
    "kind": fitz.LINK_URI,
    "from": linkedin_rect,
    "uri": LINKEDIN_URL,
})
page.insert_link({
    "kind": fitz.LINK_URI,
    "from": codeforces_rect,
    "uri": CODEFORCES_URL,
})

for entry in page.annot_xrefs():
    xref = entry[0]
    try:
        doc.xref_set_key(xref, "Border", "[0 0 0]")
        doc.xref_set_key(xref, "BS", "<< /W 0 /S /S >>")
        doc.xref_set_key(xref, "H", "/N")
    except Exception as e:
        print("border tweak skipped:", e)

doc.save(DST, garbage=4, deflate=True, clean=True)
print(f"Saved {DST}")
