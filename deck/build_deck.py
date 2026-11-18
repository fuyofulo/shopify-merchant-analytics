"""Builds the six-slide demo deck planned in deck/outline.md.

    pip install -r deck/requirements.txt
    python deck/build_deck.py

Writes deck/shopify-merchant-analytics.pptx. Screenshots come from docs/screenshots/, icons from
deck/icons/ (Lucide, ISC licence), and every number comes from the README's live run of Erik's
acceptance questions.

Look: Shopify's admin palette. Light grey page, white cards, Shopify green for emphasis, deep green
panels behind the product shots, and the bag-logo green as the highlight on dark slides.
"""

from datetime import date
from pathlib import Path

from PIL import ImageFont
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
ICONS = ROOT / "deck" / "icons"
OUT = ROOT / "deck" / "shopify-merchant-analytics.pptx"

# Shopify admin (Polaris) palette.
PAGE = RGBColor(0xF1, 0xF1, 0xF1)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xE3, 0xE3, 0xE3)
FILL = RGBColor(0xF7, 0xF7, 0xF7)
INK = RGBColor(0x1A, 0x1A, 0x1A)
INK_2 = RGBColor(0x30, 0x30, 0x30)
MUTED = RGBColor(0x61, 0x61, 0x61)
GREEN = RGBColor(0x00, 0x80, 0x60)
MINT = RGBColor(0xDF, 0xF3, 0xE8)
BAR_REST = RGBColor(0xD4, 0xD4, 0xD4)

DEEP = RGBColor(0x00, 0x4C, 0x3F)
DEEP_CARD = RGBColor(0x0E, 0x5E, 0x50)
DEEP_RULE = RGBColor(0x2A, 0x70, 0x62)
ON_DEEP = RGBColor(0xFF, 0xFF, 0xFF)
ON_DEEP_2 = RGBColor(0xCF, 0xE6, 0xDC)
ON_DEEP_MUTED = RGBColor(0x8F, 0xBF, 0xAE)
LIME = RGBColor(0x95, 0xBF, 0x47)

SCREEN = RGBColor(0x0D, 0x0D, 0x0D)  # the screenshots' own background
SCREEN_CARD = RGBColor(0x1A, 0x1A, 0x19)
SCREEN_RULE = RGBColor(0x2C, 0x2C, 0x2A)
SCREEN_INK = RGBColor(0xF0, 0xEF, 0xEC)
SCREEN_MUTED = RGBColor(0x89, 0x87, 0x81)

FONT = "Arial"
SLIDE_W, SLIDE_H = 13.333, 7.5
LEFT = 0.7
CONTENT_W = SLIDE_W - 2 * LEFT

# Arial metrics, to size bubbles and rows to their text. Falls back to an estimate off macOS.
_ARIAL = {False: "/System/Library/Fonts/Supplemental/Arial.ttf", True: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"}


def text_width(words, size, bold=False):
    """Width of one line of Arial text, in inches."""
    try:
        return ImageFont.truetype(_ARIAL[bold], 1000).getlength(words) * size / 1000 / 72
    except OSError:
        return len(words) * size * 0.53 / 72


def wrap(words, size, width, bold=False):
    lines, current = [], ""
    for word in words.split():
        trial = f"{current} {word}".strip()
        if current and text_width(trial, size, bold) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    return lines + [current]


# ---------------------------------------------------------------------------------------------
# Drawing helpers


def style(run, size, color, bold=False, italic=False, tracking=0):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    if tracking:
        run._r.get_or_add_rPr().set("spc", str(int(tracking * 100)))


def text(slide, x, y, w, h, paragraphs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=0, line_spacing=None, tracking=0, name=None):
    """paragraphs: a string, or a list of paragraphs; a paragraph is a string or a list of
    (text, options) runs, where options may set size, color, bold, italic and tracking."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    for index, paragraph in enumerate([paragraphs] if isinstance(paragraphs, str) else paragraphs):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line_spacing:
            p.line_spacing = line_spacing
        for content, options in [(paragraph, {})] if isinstance(paragraph, str) else paragraph:
            run = p.add_run()
            run.text = content
            style(run, options.get("size", size), options.get("color", color), options.get("bold", bold),
                  options.get("italic", False), options.get("tracking", tracking))
    return box


def drop_theme_style(item):
    """python-pptx gives shapes the template's style, whose effects some renderers draw as a shadow.
    Every colour here is set explicitly, so the style can go."""
    theme_style = item._element.find(qn("p:style"))
    if theme_style is not None:
        item._element.remove(theme_style)


def shape(slide, kind, x, y, w, h, fill=None, line=None, radius=None, name=None, line_width=0.75):
    item = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius is not None:
        item.adjustments[0] = min(0.5, radius / min(w, h))
    if fill is None:
        item.fill.background()
    else:
        item.fill.solid()
        item.fill.fore_color.rgb = fill
    if line is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = line
        item.line.width = Pt(line_width)
    drop_theme_style(item)
    if name:
        item.name = name
    return item


def shadow(item, alpha=10, blur_pt=10, distance_pt=2):
    """A soft drop shadow, for cards and windows that float above the page."""
    sp_pr = item._element.spPr
    for old in sp_pr.findall(qn("a:effectLst")):
        sp_pr.remove(old)
    sp_pr.append(parse_xml(
        f'<a:effectLst {nsdecls("a")}><a:outerShdw blurRad="{blur_pt * 12700}" dist="{distance_pt * 12700}" '
        f'dir="5400000" algn="t" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="{alpha * 1000}"/>'
        f'</a:srgbClr></a:outerShdw></a:effectLst>'
    ))


def card(slide, x, y, w, h, fill=CARD, name="Card", radius=0.16):
    """A Polaris-style card: white, hairline border, soft shadow."""
    item = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=fill, line=BORDER if fill == CARD else None,
                 radius=radius, name=name)
    shadow(item, alpha=9, blur_pt=8, distance_pt=2)
    return item


def line(slide, x1, y1, x2, y2, color, width=0.75, name=None, dash=False):
    item = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    item.line.color.rgb = color
    item.line.width = Pt(width)
    if dash:
        item.line._get_or_add_ln().append(parse_xml(f'<a:prstDash {nsdecls("a")} val="dash"/>'))
    drop_theme_style(item)
    if name:
        item.name = name
    return item


def icon(slide, name, color, x, y, size):
    picture = slide.shapes.add_picture(str(ICONS / f"{name}-{color}.png"), Inches(x), Inches(y), Inches(size),
                                       Inches(size))
    picture.name = f"Icon: {name}"
    return picture


def badge(slide, x, y, d, icon_name, icon_color, fill, ring=None):
    """An icon in a filled circle."""
    circle = shape(slide, MSO_SHAPE.OVAL, x, y, d, d, fill=fill, line=ring, line_width=1.5, name=f"Badge: {icon_name}")
    inner = d * 0.52
    icon(slide, icon_name, icon_color, x + (d - inner) / 2, y + (d - inner) / 2, inner)
    return circle


def pin(slide, x, y, number, size=0.36, font_size=13, fill=GREEN, ring=None, color=CARD):
    dot = shape(slide, MSO_SHAPE.OVAL, x, y, size, size, fill=fill, line=ring, line_width=1.75, name=f"Pin {number}")
    frame = dot.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(number)
    style(run, font_size, color, bold=True)
    return dot


def bubble(slide, right, y, message, size=17, max_w=4.4, fill=PAGE, color=INK, name=None):
    """A chat bubble like the app's question bubble, right-aligned at `right`. Returns its height."""
    pad_x, pad_y = 0.22, 0.13
    lines = message.split("\n") if "\n" in message else wrap(message, size, max_w - 2 * pad_x)
    w = max(text_width(row, size) for row in lines) + 2 * pad_x + 0.1
    h = len(lines) * size * 1.2 / 72 + 2 * pad_y
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, right - w, y, w, h, fill=fill, radius=0.2, name=name or "Question bubble")
    text(slide, right - w + pad_x, y, w - 2 * pad_x + 0.06, h, "\n".join(lines), size=size, color=color,
         anchor=MSO_ANCHOR.MIDDLE)
    return h


def browser(slide, x, y, w, h, url="shopify-merchant-analytics.vercel.app"):
    """A browser window to hold the app's screenshots. Returns the top of its content area."""
    window = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=SCREEN, line=SCREEN_RULE, radius=0.14,
                   name="Browser window")
    shadow(window, alpha=35, blur_pt=24, distance_pt=8)
    bar = 0.42
    for index in range(3):
        shape(slide, MSO_SHAPE.OVAL, x + 0.2 + index * 0.2, y + bar / 2 - 0.055, 0.11, 0.11, fill=SCREEN_RULE,
              name="Window dot")
    url_w = min(3.6, w - 2.0)
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + (w - url_w) / 2, y + 0.09, url_w, 0.25, fill=SCREEN_CARD,
          radius=0.125, name="Address bar")
    text(slide, x + (w - url_w) / 2, y + 0.09, url_w, 0.25, url, size=10, color=SCREEN_MUTED, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    line(slide, x, y + bar, x + w, y + bar, SCREEN_RULE, name="Window bar edge")
    return y + bar


def picture(slide, path, x, y, w, name):
    item = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    item.name = name
    return item


def to_back(item):
    """Moves a shape behind everything else on the slide, title included."""
    tree = item._element.getparent()
    tree.remove(item._element)
    tree.insert(2, item._element)  # after the group's own nvGrpSpPr and grpSpPr
    return item


def panel(slide, x, w=None, name="Green panel"):
    """A full-height deep green block from x (to the right edge unless w is given), behind everything."""
    return to_back(shape(slide, MSO_SHAPE.RECTANGLE, x, 0, w or SLIDE_W - x, SLIDE_H, fill=DEEP, name=name))


def new_slide(prs, notes, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # "Title Only": every slide keeps a real title
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = DEEP if dark else PAGE
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def kicker(slide, words, y=0.6, color=GREEN, x=LEFT):
    text(slide, x, y, 6, 0.3, words.upper(), size=12, color=color, bold=True, tracking=1.8)


def title(slide, words, y=0.92, size=36, color=INK, h=0.75, w=CONTENT_W, x=LEFT):
    heading = slide.shapes.title
    heading.left, heading.top, heading.width, heading.height = Inches(x), Inches(y), Inches(w), Inches(h)
    frame = heading.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.TOP
    for index, row in enumerate(words.split("\n")):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 0.95
        run = p.add_run()
        run.text = row
        style(run, size, color, bold=True, tracking=-size / 30)
    return heading


def footer(slide, number, number_on_panel=False):
    text(slide, LEFT, 7.02, 5, 0.25, "Shopify Merchant Analytics", size=10, color=MUTED)
    text(slide, SLIDE_W - LEFT - 1, 7.02, 1, 0.25, f"{number} / 6", size=10,
         color=ON_DEEP_MUTED if number_on_panel else MUTED, align=PP_ALIGN.RIGHT)


def quiet_chart_frame(chart):
    """No fill or border on the chart or plot area, so the chart sits straight on its card."""
    no_fill = f'<c:spPr {nsdecls("c", "a")}><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
    chart_el = chart._chartSpace.find(qn("c:chart"))
    chart_el.addnext(parse_xml(no_fill))
    chart_el.find(qn("c:plotArea")).append(parse_xml(no_fill))


# ---------------------------------------------------------------------------------------------
# 1. The problem


def slide_problem(prs):
    slide = new_slide(
        prs,
        "This is a real question a merchant sent us on October 27. Merchants ask in their own "
        "words, by email, support chat, the admin search box and the Community forum. On the right are a few more "
        "from the same day. Someone has to turn each one into a report by hand, and several merchants needed the "
        "answer before placing their Black Friday reorder. So I built a chat dashboard: they type the question "
        "and get a chart and a short answer back, usually in under 3 seconds.",
    )
    split = 7.45
    panel(slide, 0, w=split, name="Green half")
    kicker(slide, "Shopify Merchant Analytics", y=0.8, color=LIME)
    title(slide, "“Which jackets came\nback as returns\nlast week?”", y=1.35, size=48, color=ON_DEEP, h=2.3, w=6.6)
    text(slide, LEFT, 3.8, 6.2, 0.4, "A real merchant question from October 27.", size=16, color=ON_DEEP_MUTED)
    text(slide, LEFT, 4.38, 6.1, 1.3,
         "Merchants ask in their own words. Before Black Friday they need the answer in seconds, not a report "
         "request.", size=20, color=ON_DEEP_2, line_spacing=1.1)
    text(slide, LEFT, 5.95, 6.4, 0.8,
         ["Now they ask the dashboard,", [("and get a chart back in under 3 seconds.", {"color": LIME, "bold": True})]],
         size=20, color=ON_DEEP)

    # An inbox of the day's requests, as a Shopify admin card.
    x, w, y = split + 0.55, SLIDE_W - split - 0.55 - 0.55, 0.8
    requests = [
        ("search", "best seller since summer?", "Admin search"),
        ("messages-square", "sales been weird lately, can you show me whats going on", "Support chat"),
        ("mail", "…before we place our BFCM reorder with our supplier we need to know which parkas and puffers "
                 "had the most returns…", "Email"),
        ("users", "how do i see which coats got returned most over the last couple weeks? need it before i reorder",
         "Shopify Community"),
    ]
    message_w = w - 0.95
    rows = [(name, wrap(message, 13, message_w), source) for name, message, source in requests]
    heights = [len(lines) * 13 * 1.2 / 72 + 0.62 for _, lines, _ in rows]
    inbox_h = 0.95 + sum(heights) + 0.1
    card(slide, x, y, w, inbox_h, name="Report requests")
    text(slide, x + 0.3, y + 0.25, 3, 0.3, "Report requests", size=15, bold=True)
    text(slide, x + 0.3, y + 0.53, 3, 0.25, "October 27, 2025", size=11, color=MUTED)
    pill_label = "30 that day"
    pill_w = text_width(pill_label, 11, bold=True) + 0.32
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + w - 0.3 - pill_w, y + 0.3, pill_w, 0.3, fill=MINT, radius=0.15,
          name="Count pill")
    text(slide, x + w - 0.3 - pill_w, y + 0.3, pill_w, 0.3, pill_label, size=11, bold=True, color=GREEN,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    row_y = y + 0.95
    for (name, lines, source), h in zip(rows, heights):
        line(slide, x, row_y, x + w, row_y, BORDER, name="Row rule")
        badge(slide, x + 0.28, row_y + 0.22, 0.4, name, "green", MINT)
        text(slide, x + 0.85, row_y + 0.2, message_w, h - 0.5, "\n".join(lines), size=13, color=INK)
        text(slide, x + 0.85, row_y + h - 0.4, message_w, 0.25, source, size=11, color=MUTED)
        row_y += h


# ---------------------------------------------------------------------------------------------
# 2. The interface


def slide_interface(prs):
    slide = new_slide(
        prs,
        "Here's what the merchant sees. They type 'which jackets came back the most last week'. While it works, "
        "grey steps say what it's doing, then fold away once the chart lands. The chart shows the exact dates it "
        "used, October 20 to 26, and underneath is a short answer: 4 jacket units came back, $792.15 refunded, "
        "mostly the Alpine Down Parka. I'll show this live in a moment.",
    )
    split = 5.15
    panel(slide, split)
    kicker(slide, "The interface")
    title(slide, "Type a question.\nGet a chart and\nan answer.", size=34, h=1.7, w=4.3)

    features = [
        ("Steps while it works", "Grey steps say what it's doing, then fold into “Show steps (3)”."),
        ("The exact dates", "Every chart shows the range it used, so “last week” is never a guess."),
        ("A short answer", "One to three sentences, with numbers straight from the data."),
    ]
    y = 3.1
    for index, (heading, detail) in enumerate(features, start=1):
        pin(slide, LEFT, y, index)
        text(slide, LEFT + 0.55, y - 0.01, split - LEFT - 0.95, 0.35, heading, size=17, bold=True)
        text(slide, LEFT + 0.55, y + 0.36, split - LEFT - 0.95, 0.8, detail, size=14, color=MUTED, line_spacing=1.1)
        y += 1.22

    win_x = split + 0.5
    win_w = SLIDE_W - 0.5 - win_x
    pad = 0.25
    shot_w = win_w - 2 * pad
    shot_h = shot_w * 740 / 1520
    bubble_size = 13
    win_h = 0.42 + 0.2 + (bubble_size * 1.2 / 72 + 0.26) + 0.12 + shot_h + 0.15
    win_y = (SLIDE_H - win_h) / 2
    top = browser(slide, win_x, win_y, win_w, win_h)
    bubble_h = bubble(slide, win_x + win_w - pad - 0.1, top + 0.2, "which jackets came back the most last week",
                      size=bubble_size, fill=SCREEN_CARD, color=SCREEN_INK)
    shot_y = top + 0.2 + bubble_h + 0.12
    picture(slide, SHOTS / "jacket-returns-tooltip.png", win_x + pad, shot_y, shot_w, "Screenshot: jacket returns")

    # Pins on the window's left edge, level with each feature (y in the 740 px tall screenshot).
    scale = shot_w / 1520
    for number, py in enumerate([37, 166, 650], start=1):
        pin(slide, win_x - 0.17, shot_y + py * scale - 0.17, number, size=0.34, font_size=12, ring=CARD)
    footer(slide, 2, number_on_panel=True)


# ---------------------------------------------------------------------------------------------
# 3. How a question becomes a chart


def flow(slide, points, color=INK_2, width=1.25, name="Flow"):
    """An arrow along a path of (x, y) points in inches, bending at right angles."""
    local = [(round(x * 1000), round(y * 1000)) for x, y in points]  # thousandths of an inch
    builder = slide.shapes.build_freeform(*local[0], scale=Inches(1) / 1000)
    builder.add_line_segments(local[1:], close=False)
    item = builder.convert_to_shape()
    item.name = name
    item.fill.background()
    item.line.color.rgb = color
    item.line.width = Pt(width)
    outline = item.line._get_or_add_ln()
    outline.append(parse_xml(f'<a:round {nsdecls("a")}/>'))
    outline.append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle" w="med" len="med"/>'))
    drop_theme_style(item)
    return item


def step_node(slide, x, y, w, h, number, heading, ai=False):
    """One numbered step of the pipeline diagram. Returns the top of its body."""
    item = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=DEEP if ai else CARD,
                 line=None if ai else BORDER, radius=0.12, name=f"Step {number}: {heading}")
    shadow(item, alpha=14 if ai else 8, blur_pt=8, distance_pt=2)
    pin(slide, x + 0.16, y + 0.15, number, size=0.27, font_size=10, fill=LIME if ai else GREEN,
        color=DEEP if ai else CARD)
    text(slide, x + 0.52, y + 0.15, w - 0.6, 0.27, heading, size=12, bold=True, color=ON_DEEP if ai else INK,
         anchor=MSO_ANCHOR.MIDDLE)
    return y + 0.52


def pairs(slide, x, y, w, rows, key_w, key_color, value_color, value_align=PP_ALIGN.LEFT, size=10.5, pitch=0.19):
    for index, (key, value) in enumerate(rows):
        row_y = y + index * pitch
        text(slide, x, row_y, key_w, pitch, key, size=size, color=key_color)
        text(slide, x + key_w, row_y, w - key_w, pitch, value, size=size, color=value_color, bold=True,
             align=value_align)


def slide_pipeline(prs):
    slide = new_slide(
        prs,
        "This is how a typed question becomes a chart. Read it as six steps across three lanes: the merchant at "
        "the top, the AI model in the green lane, and our code at the bottom. One, the merchant asks in their own "
        "words. Two, before the AI sees anything, our code has already worked out what phrases like 'last week' "
        "mean: October 20 to 26. Three, the AI picks one of four reports, sales, returns, repeat customers or "
        "'can't answer', and fills in the blanks, copying the dates from that table. Four, our code runs the "
        "report over the store's orders, so the numbers are exact, and picks the chart shape: comparing products "
        "means a bar. That goes straight to the page. Five, the AI reads the result and writes one sentence. Six, "
        "the merchant sees the chart and the answer. The AI never does the maths or draws the chart.",
    )
    kicker(slide, "How it works")
    title(slide, "How a question becomes a chart")
    text(slide, LEFT, 1.72, CONTENT_W, 0.4,
         [[("The AI only chooses and writes. ", {"color": GREEN, "bold": True}),
           ("Code works out the dates, does the maths and picks the chart.", {})]],
         size=17, color=MUTED)

    lane_h = 1.45
    tops = [2.3 + index * lane_h for index in range(3)]
    merchant, ai, code = 0, 1, 2
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, LEFT, tops[ai] + 0.04, CONTENT_W, lane_h - 0.08, fill=MINT, radius=0.16,
          name="AI lane")
    lanes = [("message-square-text", "Merchant", "asks, then reads"),
             ("sparkles", "AI model", "only chooses and writes"),
             ("database", "Our code", "dates, maths and the chart")]
    for index, (icon_name, who, role) in enumerate(lanes):
        cy = tops[index] + lane_h / 2
        is_ai = index == ai
        badge(slide, LEFT + 0.2, cy - 0.27, 0.46, icon_name, "lime" if is_ai else "white", DEEP if is_ai else GREEN)
        text(slide, LEFT + 0.78, cy - 0.3, 1.2, 0.28, who, size=14, bold=True, color=DEEP if is_ai else INK)
        text(slide, LEFT + 0.78, cy - 0.01, 1.15, 0.45, role, size=10.5, color=GREEN if is_ai else MUTED)

    gap, x0 = 0.45, 2.75
    w = (SLIDE_W - LEFT - 0.15 - x0 - 3 * gap) / 4
    col = [x0 + index * (w + gap) for index in range(4)]
    h = 1.16
    ny = [top + (lane_h - h) / 2 for top in tops]
    cy = [y + h / 2 for y in ny]
    pad = 0.18

    body = step_node(slide, col[0], ny[merchant], w, h, 1, "Asks a question")
    text(slide, col[0] + pad, body, w - 2 * pad, 0.55, "“which jackets came back the most last week”",
         size=11, color=INK_2, line_spacing=1.05)

    body = step_node(slide, col[0], ny[code], w, h, 2, "Works out dates")
    pairs(slide, col[0] + pad, body, w - 2 * pad,
          [("last week", "Oct 20–26"), ("lately", "Sep 27–Oct 26")], key_w=0.74, key_color=MUTED, value_color=INK)
    text(slide, col[0] + pad, body + 0.41, w - 2 * pad, 0.19, "a table the AI copies from", size=10.5, color=MUTED)

    body = step_node(slide, col[1], ny[ai], w, h, 3, "Picks a report", ai=True)
    pairs(slide, col[1] + pad, body, w - 2 * pad, [("report", "Returns"), ("dates", "Oct 20–26"), ("only", "Outerwear")],
          key_w=0.65, key_color=ON_DEEP_MUTED, value_color=ON_DEEP)

    body = step_node(slide, col[2], ny[code], w, h, 4, "Runs the report")
    pairs(slide, col[2] + pad, body, w - 2 * pad, [("Alpine Down Parka", "3"), ("Northridge Insulated", "1")],
          key_w=w - 2 * pad - 0.3, key_color=INK_2, value_color=INK, value_align=PP_ALIGN.RIGHT)
    text(slide, col[2] + pad, body + 0.41, w - 2 * pad, 0.19, "4 units, $792.15 refunded", size=10.5, color=MUTED)

    body = step_node(slide, col[2], ny[ai], w, h, 5, "Writes the answer", ai=True)
    text(slide, col[2] + pad, body, w - 2 * pad, 0.55,
         "4 jacket units were returned, $792.15 refunded.", size=10.5, color=ON_DEEP_2,
         line_spacing=1.05)

    body = step_node(slide, col[3], ny[merchant], w, h, 6, "Sees the chart")
    bar_room = w - 2 * pad - 0.25
    for index, (product, units) in enumerate([("Alpine Down Parka", 3), ("Northridge Insulated", 1)]):
        row_y = body - 0.04 + index * 0.31
        text(slide, col[3] + pad, row_y, w - 2 * pad, 0.17, product, size=9.5, color=INK_2)
        bar_w = bar_room * units / 3
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, col[3] + pad, row_y + 0.2, bar_w, 0.08, fill=GREEN, radius=0.03,
              name=f"Bar: {product}")
        text(slide, col[3] + pad + bar_w + 0.07, row_y + 0.16, 0.25, 0.16, str(units), size=9.5, bold=True, color=INK,
             anchor=MSO_ANCHOR.MIDDLE)

    right = [x + w for x in col]
    mid = [x + w / 2 for x in col]
    bend = [x + w + gap / 2 for x in col]
    flow(slide, [(right[0], cy[merchant]), (bend[0], cy[merchant]), (bend[0], cy[ai]), (col[1], cy[ai])],
         name="Question to the AI")
    flow(slide, [(right[0], cy[code]), (bend[0], cy[code]), (bend[0], cy[ai]), (col[1], cy[ai])],
         name="Date table to the AI")
    flow(slide, [(right[1], cy[ai]), (bend[1], cy[ai]), (bend[1], cy[code]), (col[2], cy[code])],
         name="Report request to the code")
    flow(slide, [(mid[2], ny[code]), (mid[2], ny[ai] + h)], name="Result to the AI")
    flow(slide, [(right[2], cy[ai]), (bend[2], cy[ai]), (bend[2], cy[merchant]), (col[3], cy[merchant])],
         name="Answer to the page")
    flow(slide, [(right[2], cy[code]), (mid[3], cy[code]), (mid[3], ny[merchant] + h)], name="Chart to the page")
    text(slide, right[2] + 0.12, cy[code] - 0.27, 1.5, 0.2, "chart + numbers", size=10, color=MUTED)
    footer(slide, 3)


# ---------------------------------------------------------------------------------------------
# 4. Vague dates, what it answers, speed


def slide_questions(prs):
    slide = new_slide(
        prs,
        "Merchants rarely give exact dates, so the code turns vague words into exact ranges before the AI sees "
        "the question. Each bar is the range a phrase becomes. 'Last week' is Monday to Sunday, October 20 to 26. "
        "'Lately' and 'recently' are the last 30 full days. With no date at all it uses all the data, and the range "
        "always shows under the chart title. On the right is 'revenue by wk recently'. It answers three kinds of "
        "question, says plainly when something like ad spend isn't in the data, and the median time from pressing "
        "Ask to seeing the chart was 2.4 seconds.",
    )
    split = 7.7
    panel(slide, split)
    kicker(slide, "Vague questions")
    title(slide, "Vague words, exact dates", w=split - LEFT - 0.3)

    # The date ranges, on a timeline card.
    cx, cy, cw, ch = LEFT, 1.85, split - LEFT - 0.45, 3.2
    card(slide, cx, cy, cw, ch, name="Date ranges")
    first, last = date(2025, 5, 1), date(2025, 10, 31)
    track_x, track_w = cx + 2.15, cw - 2.15 - 0.3

    def at(day):
        return track_x + track_w * (day - first).days / (last - first).days

    rows = [
        ("“last week”", date(2025, 10, 20), date(2025, 10, 26), "Oct 20–26"),
        ("“lately”", date(2025, 9, 27), date(2025, 10, 26), "Sep 27 – Oct 26"),
        ("“since Labor Day”", date(2025, 9, 1), date(2025, 10, 26), "Sep 1 – Oct 26"),
        ("“since summer”", date(2025, 6, 1), date(2025, 10, 26), "Jun 1 – Oct 26"),
        ("no date at all", date(2025, 5, 6), date(2025, 10, 27), "all data: May 6 – Oct 27"),
    ]
    first_row, row_gap = cy + 0.2, 0.53
    months_y = first_row + len(rows) * row_gap + 0.05
    for month in range(5, 11):
        day = date(2025, month, 1)
        line(slide, at(day), first_row + 0.15, at(day), months_y, BORDER, width=0.5, name="Month line")
        text(slide, at(day) + 0.04, months_y + 0.02, 0.6, 0.25, day.strftime("%b"), size=10, color=MUTED)
    for index, (phrase, start, end, label) in enumerate(rows):
        y = first_row + index * row_gap
        text(slide, cx + 0.3, y + 0.2, 1.85, 0.3, phrase, size=14, color=INK, bold=True)
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, track_x, y + 0.27, track_w, 0.14, fill=PAGE, radius=0.07,
              name="Track")
        bar_w = max(0.14, at(end) - at(start))
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, at(end) - bar_w, y + 0.27, bar_w, 0.14, fill=GREEN, radius=0.07,
              name=f"Range: {label}")
        text(slide, at(end) - 2.6, y + 0.02, 2.6, 0.22, label, size=10, color=INK_2, bold=True, align=PP_ALIGN.RIGHT)

    # Three facts, as small cards.
    facts = [
        ("zap", "2.4 s", "median from Ask to chart, over Erik's 18 chart questions"),
        ("layers", "3", "reports: sales and best sellers, returns and why, repeat customers"),
        ("ban", "0", "made-up charts. Ad spend or stock gets “not in the data”"),
    ]
    fw = (cw - 2 * 0.2) / 3
    for index, (icon_name, big, small) in enumerate(facts):
        fx = cx + index * (fw + 0.2)
        card(slide, fx, 5.3, fw, 1.45, name=f"Fact: {big}")
        badge(slide, fx + 0.2, 5.48, 0.42, icon_name, "green", MINT)
        text(slide, fx + 0.72, 5.5, fw - 0.85, 0.4, big, size=20, bold=True, color=INK, tracking=-0.4)
        text(slide, fx + 0.2, 6.0, fw - 0.4, 0.7, small, size=10.5, color=MUTED, line_spacing=1.05)

    # The weekly revenue chart for "recently", on the green panel.
    win_x = split + 0.45
    win_w = SLIDE_W - 0.45 - win_x
    shot_w = win_w - 0.3
    shot_h = shot_w * 908 / 1536
    win_h = 0.42 + 0.15 + shot_h + 0.15
    win_y = 1.75
    top = browser(slide, win_x, win_y, win_w, win_h)
    picture(slide, SHOTS / "weekly-revenue.png", win_x + 0.15, top + 0.15, shot_w, "Screenshot: weekly revenue")
    text(slide, win_x, win_y + win_h + 0.3, win_w, 0.8,
         [[("“revenue by wk recently”", {"bold": True, "color": ON_DEEP})],
          "→ Sep 27 – Oct 26, the last 30 full days. A trend over time, so a line."],
         size=14, color=ON_DEEP_2, line_spacing=1.15)
    footer(slide, 4, number_on_panel=True)


# ---------------------------------------------------------------------------------------------
# 5. Results


FIRST_CHART_SECONDS = {  # README live run; AQ-07 and AQ-20 rightly draw no chart
    1: 2.04, 2: 2.99, 3: 4.63, 4: 2.31, 5: 2.92, 6: 2.33, 8: 2.69, 9: 1.67, 10: 2.73,
    11: 2.31, 12: 2.15, 13: 2.64, 14: 2.84, 15: 1.65, 16: 2.18, 17: 1.75, 18: 2.63, 19: 2.46,
}


def threshold_as_line(chart, color, label):
    """Turns the chart's second series into a dashed line drawn over the bars, on the same axes."""
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    bar_chart = plot_area.find(qn("c:barChart"))
    series = bar_chart.findall(qn("c:ser"))[1]
    bar_chart.remove(series)
    for tag in ("c:invertIfNegative", "c:spPr", "c:dLbls"):
        for old in series.findall(qn(tag)):
            series.remove(old)
    series.find(qn("c:tx")).addnext(parse_xml(
        f'<c:spPr {nsdecls("c", "a")}><a:ln w="19050" cap="rnd"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:prstDash val="dash"/></a:ln></c:spPr>'
    ))
    series.find(qn("c:spPr")).addnext(parse_xml(f'<c:marker {nsdecls("c")}><c:symbol val="none"/></c:marker>'))
    series.find(qn("c:marker")).addnext(parse_xml(
        f'<c:dLbls {nsdecls("c", "a")}><c:dLbl><c:idx val="{len(FIRST_CHART_SECONDS) - 1}"/><c:tx><c:rich><a:bodyPr/>'
        f'<a:lstStyle/><a:p><a:r><a:rPr sz="1100" b="1"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="{FONT}"/></a:rPr><a:t>{label}</a:t></a:r></a:p></c:rich></c:tx><c:dLblPos val="t"/>'
        f'<c:showLegendKey val="0"/><c:showVal val="1"/><c:showCatName val="0"/><c:showSerName val="0"/>'
        f'<c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbl><c:showLegendKey val="0"/><c:showVal val="0"/>'
        f'<c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbls>'
    ))
    series.append(parse_xml(f'<c:smooth {nsdecls("c")} val="0"/>'))
    line_chart = parse_xml(f'<c:lineChart {nsdecls("c")}><c:grouping val="standard"/><c:varyColors val="0"/></c:lineChart>')
    line_chart.append(series)
    line_chart.append(parse_xml(f'<c:marker {nsdecls("c")} val="1"/>'))
    for ax_id in bar_chart.findall(qn("c:axId")):
        line_chart.append(parse_xml(f'<c:axId {nsdecls("c")} val="{ax_id.get("val")}"/>'))
    bar_chart.addnext(line_chart)


def slide_results(prs):
    slide = new_slide(
        prs,
        "Erik gave us 20 acceptance questions and three pass marks. We ran all 20 on the live preview, each in a "
        "fresh chat. 19 picked the right report, and the bar is 18. Nothing crashed. And every chart appeared in "
        "under 5 seconds, the dashed line. The green bar is AQ-03: it took 5.26 seconds at first, because the chart "
        "waited for the loading steps. We changed that and it's now 4.63. The one miss was 'which sweaters sell "
        "best': it charted every product instead of only knitwear. The prompt now says where sweaters belong, and "
        "we'll re-run it to confirm.",
    )
    kicker(slide, "Acceptance test")
    title(slide, "Erik's 20 questions: every pass mark met")

    stats = [("19/20", "picked the right report", "Pass mark: 18"), ("0", "crashes", "Pass mark: 0"),
             ("4.63 s", "slowest time to chart", "Pass mark: under 5 s")]
    sw = (CONTENT_W - 2 * 0.3) / 3
    for index, (value, label, mark) in enumerate(stats):
        sx = LEFT + index * (sw + 0.3)
        card(slide, sx, 1.9, sw, 1.45, name=f"Pass mark {index + 1}")
        text(slide, sx + 0.3, 2.02, sw - 1.1, 0.75, value, size=40, bold=True, color=INK, tracking=-1.2)
        text(slide, sx + 0.3, 2.72, sw - 0.6, 0.3, label, size=14, color=INK_2)
        text(slide, sx + 0.3, 3.0, sw - 0.6, 0.25, mark, size=11, color=MUTED)
        badge(slide, sx + sw - 0.8, 2.12, 0.5, "circle-check", "green", MINT)

    cx, cy, cw, ch = LEFT, 3.6, 8.55, 3.25
    card(slide, cx, cy, cw, ch, name="Chart card")
    data = CategoryChartData()
    data.categories = [str(number) for number in FIRST_CHART_SECONDS]
    data.add_series("Seconds to first chart", list(FIRST_CHART_SECONDS.values()), number_format="0.00")
    data.add_series("Pass mark", [5.0] * len(FIRST_CHART_SECONDS), number_format="0.0")
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(cx + 0.15), Inches(cy + 0.12),
                                   Inches(cw - 0.3), Inches(ch - 0.22), data)
    frame.name = "Chart: seconds to first chart"
    chart = frame.chart
    quiet_chart_frame(chart)
    chart.has_legend = False
    chart.font.name = FONT
    chart.font.size = Pt(10)
    chart.font.color.rgb = MUTED
    chart.has_title = True
    chart_title = chart.chart_title.text_frame
    chart_title.text = "Seconds from Ask to chart, by question"
    style(chart_title.paragraphs[0].runs[0], 12, INK, bold=True)

    plot = chart.plots[0]
    plot.gap_width = 55
    plot.vary_by_categories = False
    bars = plot.series[0]
    bars.format.fill.solid()
    bars.format.fill.fore_color.rgb = BAR_REST
    slowest = bars.points[list(FIRST_CHART_SECONDS).index(3)]
    slowest.format.fill.solid()
    slowest.format.fill.fore_color.rgb = GREEN

    values = chart.value_axis
    values.minimum_scale = 0
    values.maximum_scale = 6
    values.major_unit = 1
    values.has_major_gridlines = True
    values.major_gridlines.format.line.color.rgb = BORDER
    values.major_gridlines.format.line.width = Pt(0.5)
    values.format.line.fill.background()
    values.major_tick_mark = XL_TICK_MARK.NONE
    values.tick_labels.number_format = '0" s"'
    values.tick_labels.number_format_is_linked = False
    categories = chart.category_axis
    categories.format.line.color.rgb = BAR_REST
    categories.major_tick_mark = XL_TICK_MARK.NONE
    categories.has_title = True
    categories.axis_title.text_frame.text = "Erik's question number (AQ-07 and AQ-20 rightly draw no chart)"
    style(categories.axis_title.text_frame.paragraphs[0].runs[0], 10, MUTED)
    threshold_as_line(chart, "1A1A1A", "Pass mark")

    nx = cx + cw + 0.35
    nw = SLIDE_W - LEFT - nx
    notes = [
        ("zap", "AQ-03: 5.26 s → 4.63 s", "The green bar. The chart no longer waits for the loading steps."),
        ("refresh-cw", "One miss: AQ-15", "Sweaters showed every product. Fixed; re-run pending."),
        ("circle-check", "Checked, not assumed", "Every number matched the order data."),
    ]
    y = 3.7
    for icon_name, heading, detail in notes:
        badge(slide, nx, y, 0.38, icon_name, "green", MINT)
        text(slide, nx + 0.52, y + 0.03, nw - 0.52, 0.3, heading, size=14, bold=True)
        text(slide, nx + 0.52, y + 0.34, nw - 0.52, 0.7, detail, size=12, color=MUTED, line_spacing=1.1)
        y += 1.08
    footer(slide, 5)


# ---------------------------------------------------------------------------------------------
# 6. Status


def slide_status(prs):
    slide = new_slide(
        prs,
        "So, is it ready for Black Friday? Yes. It's live today at shopify-merchant-analytics.vercel.app, with the "
        "AI key in place, and it passed Erik's questions. One step is left before November 28: add $10 of "
        "OpenRouter credits. The free plan stops at about 25 questions a day; with credits it's about 500. The "
        "sweaters fix from the last slide gets re-run as soon as the daily limit allows. Happy to take questions.",
        dark=True,
    )
    kicker(slide, "Status", y=0.8, color=LIME)
    title(slide, "Ready for Black Friday", y=1.15, size=60, color=ON_DEEP, h=1.0)
    text(slide, LEFT, 2.3, CONTENT_W, 0.5,
         [[("Live now at ", {}), ("shopify-merchant-analytics.vercel.app", {"bold": True, "color": ON_DEEP})]],
         size=22, color=ON_DEEP_2)

    line_y = 4.0
    xs = [LEFT + 0.3, SLIDE_W / 2, SLIDE_W - LEFT - 0.3]
    line(slide, xs[0], line_y, xs[-1], line_y, DEEP_RULE, width=2, name="Timeline")
    stops = [
        ("rocket", "Now", "Public URL live, with the AI key. Passed Erik's 20 questions.", True),
        ("coins", "Add AI credits", "The free plan allows about 25 questions a day. $10 of OpenRouter credits "
                                    "raises that to about 500.", False),
        ("flag", "Nov 28", "Black Friday. Ready for merchants.", True),
    ]
    for index, ((icon_name, heading, detail, milestone), x) in enumerate(zip(stops, xs)):
        d = 0.6
        if milestone:
            badge(slide, x - d / 2, line_y - d / 2, d, icon_name, "deep", LIME)
        else:
            badge(slide, x - d / 2, line_y - d / 2, d, icon_name, "lime", DEEP_CARD, ring=LIME)
        first, last = index == 0, index == len(stops) - 1
        label_w = 3.0 if first or last else 3.6
        label_x = x - d / 2 if first else (x - label_w + d / 2 if last else x - label_w / 2)
        align = PP_ALIGN.LEFT if first else (PP_ALIGN.RIGHT if last else PP_ALIGN.CENTER)
        text(slide, label_x, line_y + 0.5, label_w, 0.4, heading, size=18, bold=True,
             color=LIME if milestone else ON_DEEP, align=align)
        text(slide, label_x, line_y + 0.92, label_w, 0.8, detail, size=14, color=ON_DEEP_2, align=align,
             line_spacing=1.1)

    text(slide, LEFT, 6.25, 6, 0.6, "Questions?", size=32, bold=True, color=LIME, tracking=-1)


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)  # 16:9, 13.333 x 7.5 in
    prs.core_properties.title = "Shopify Merchant Analytics"
    for build in (slide_problem, slide_interface, slide_pipeline, slide_questions, slide_results, slide_status):
        build(prs)
    prs.save(OUT)
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
