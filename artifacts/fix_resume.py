"""Fix issues in the resume PDF:

1. Reposition + resize the profile photo so it stays within page margins
   and preserves its natural aspect ratio (was extending close to the
   right edge and rendering distorted in some viewers).
2. Add a `codeforces.com/profile/chakrala_s` line to the contact section.
3. Add clickable hyperlink annotations for LinkedIn and Codeforces that
   redirect to the URLs provided by the user.
"""

import fitz
from PIL import Image
import io

LINKEDIN_URL = "https://www.linkedin.com/in/sairam-chakrala-a18509276/"
CODEFORCES_URL = "https://codeforces.com/profile/chakrala_s"

SRC = "Chakrala_Sairam_Resume_Final.pdf"
DST = "Chakrala_Sairam_Resume_Final_FIXED.pdf"

doc = fitz.open(SRC)
page = doc[0]

# 1) Fix the photo: cover the original placement and re-insert at a clean
#    position that respects the page right margin and preserves aspect.
imgs = page.get_images(full=True)
xref = imgs[0][0]
pix = fitz.Pixmap(doc, xref)
img_w, img_h = pix.width, pix.height

# Original placement was Rect(512, 27.95, 594.5, 132.95) - too close to
# the page edge (page is 612 wide). Move it inward so it lives entirely
# within the right column's safe area.
new_right = 575.0
new_top = 28.0
target_h = 110.0
target_w = target_h * img_w / img_h  # preserve aspect ratio
new_left = new_right - target_w
new_bottom = new_top + target_h
new_rect = fitz.Rect(new_left, new_top, new_right, new_bottom)
print(f"Original image rect: {page.get_image_rects(xref)}")
print(f"New image rect: {new_rect}")

# Cover the original image area with a white rectangle (slightly padded so
# any visible remnants are wiped clean).
cover_rect = fitz.Rect(500, 24, 600, 138)
page.draw_rect(cover_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True, width=0)

# Re-insert the image with the proper aspect ratio.
img_bytes = pix.tobytes("png")
page.insert_image(new_rect, stream=img_bytes, keep_proportion=True, overlay=True)

# 2) Add the Codeforces contact text right under the existing contact line.
#    Existing contact line baseline origin: (35.1, 100.75) at size 8.5.
#    "Bengaluru, India" sits at y origin ~112.46.
#    We shift "Bengaluru, India" down a touch and inject a new line for
#    the Codeforces handle. Easier: place Codeforces on the same row as
#    LinkedIn (after some padding) since there is plenty of horizontal room.

# Place Codeforces text immediately to the right of the LinkedIn text on
# the contact line. LinkedIn ends at x ~= 320.76. Add some padding and a
# bullet separator.
contact_y = 100.75  # baseline used by the contact line
sep_x = 325.0
cf_text = "  ·  codeforces.com/profile/chakrala_s"
# Draw with the same font/size/color as the rest of the contact line.
contact_color = (85 / 255, 85 / 255, 85 / 255)  # 0x555555 ~= 5592405
# Use Helvetica as a built-in fallback (Carlito isn't bundled). It blends
# well at 8.5pt and avoids needing an external font file.
cf_x = sep_x
cf_origin = fitz.Point(cf_x, contact_y)
page.insert_text(
    cf_origin,
    cf_text,
    fontname="helv",
    fontsize=8.5,
    color=contact_color,
    overlay=True,
)

# Compute a bounding rect for the inserted Codeforces text portion only
# (excluding the leading separator) for the link annotation.
just_cf = "codeforces.com/profile/chakrala_s"
# Width of the leading separator part (in helv 8.5)
sep_part = "  ·  "
sep_w = fitz.get_text_length(sep_part, fontname="helv", fontsize=8.5)
cf_w = fitz.get_text_length(just_cf, fontname="helv", fontsize=8.5)
cf_rect = fitz.Rect(
    cf_x + sep_w,
    contact_y - 7.5,  # ascent
    cf_x + sep_w + cf_w,
    contact_y + 2.0,  # descent
)
print(f"Codeforces link rect: {cf_rect}")

# 3) Hyperlink annotations.
# LinkedIn link rect (from page.search_for)
linkedin_rect = fitz.Rect(208.695556640625, 92.65799713134766,
                          320.75958251953125, 103.02799987792969)
page.insert_link({
    "kind": fitz.LINK_URI,
    "from": linkedin_rect,
    "uri": LINKEDIN_URL,
})
page.insert_link({
    "kind": fitz.LINK_URI,
    "from": cf_rect,
    "uri": CODEFORCES_URL,
})

# Optional: underline both links subtly so they're visually identifiable
# as clickable. Use the same gray as the surrounding text.
def underline(rect):
    y = rect.y1 - 0.5
    page.draw_line(fitz.Point(rect.x0, y), fitz.Point(rect.x1, y),
                   color=contact_color, width=0.4)

underline(linkedin_rect)
underline(cf_rect)

doc.save(DST, garbage=4, deflate=True, clean=True)
print(f"Saved {DST}")
