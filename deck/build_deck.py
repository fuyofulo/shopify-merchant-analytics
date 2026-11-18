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


def pin(slide, x, y, number, size=0.36, font_size=13, fill=GREEN, ring=None):
    dot = shape(slide, MSO_SHAPE.OVAL, x, y, size, size, fill=fill, line=ring, line_width=1.75, name=f"Pin {number}")
    frame = dot.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(number)
    style(run, font_size, CARD, bold=True)
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
        "This is a real question a merchant typed on October 27, spelling and all. Merchants ask in their own "
        "words, by email, support chat, the admin search box and the Community forum. On the right are a few more "
        "from the same day. Someone has to turn each one into a report by hand, and several merchants needed the "
        "answer before placing their Black Friday reorder. So I built a chat dashboard: they type the question "
        "and get a chart and a short answer back, usually in under 3 seconds.",
    )
    split = 7.45
    panel(slide, 0, w=split, name="Green half")
    kicker(slide, "Shopify Merchant Analytics", y=0.8, color=LIME)
    title(slide, "“jakets returnd\nlast wk”", y=1.4, size=64, color=ON_DEEP, h=2.2, w=6.5)
    text(slide, LEFT, 3.72, 6.2, 0.4, "A real merchant question from October 27.", size=16, color=ON_DEEP_MUTED)
    text(slide, LEFT, 4.3, 6.1, 1.3,
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


def mini_bar_chart(slide, x, y, w, h):
    data = CategoryChartData()
    data.categories = ["Alpine Down Parka", "Northridge Insulated"]
    data.add_series("Returned units", [3, 1])
    frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    frame.name = "Chart: returned units by product"
    chart = frame.chart
    quiet_chart_frame(chart)
    chart.has_legend = False
    chart.has_title = False
    chart.font.name = FONT
    chart.font.size = Pt(10)
    chart.font.color.rgb = INK_2
    plot = chart.plots[0]
    plot.gap_width = 45
    plot.vary_by_categories = False
    plot.has_data_labels = True
    plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    plot.data_labels.font.size = Pt(11)
    plot.data_labels.font.bold = True
    plot.data_labels.font.color.rgb = INK
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = GREEN
    values = chart.value_axis
    values.visible = False
    values.has_major_gridlines = False
    values.minimum_scale = 0
    values.maximum_scale = 3.6
    categories = chart.category_axis
    categories.reverse_order = True
    categories.major_tick_mark = XL_TICK_MARK.NONE
    categories.format.line.color.rgb = BORDER


def slide_pipeline(prs):
    slide = new_slide(
        prs,
        "This is how a typed question turns into a chart. The merchant types in their own words. The AI model "
        "reads it and picks one of four reports, sales, returns, repeat customers or 'can't answer', and fills "
        "in the blanks: the dates, what to measure, the breakdown and any filter. It copies the dates from a table "
        "our code wrote, so 'last week' is always October 20 to 26. Then our code runs that report over the "
        "store's orders, so the numbers are exact: the AI never does maths. The code also picks the chart: a "
        "comparison is a bar, a trend is a line, one number is a card. Last, the AI writes a one-sentence answer "
        "from the result.",
    )
    kicker(slide, "How it works")
    title(slide, "How a question becomes a chart")
    text(slide, LEFT, 1.72, CONTENT_W, 0.4,
         [[("The AI only chooses and fills in. ", {"color": GREEN, "bold": True}),
           ("Code works out the dates, does the maths and picks the chart.", {})]],
         size=17, color=MUTED)

    gap = 0.34
    w = (CONTENT_W - 3 * gap) / 4
    top, h = 2.45, 4.2
    steps = [
        ("message-square-text", "The merchant", "types a question"),
        ("sparkles", "The AI model", "picks a report"),
        ("database", "Our code", "runs the numbers"),
        ("chart-column", "The page", "draws the chart"),
    ]
    captions = [
        "In their own words, typos and all.",
        "One of 4 reports, blanks filled in. Dates are copied, never worked out.",
        "Over the store's orders. Exact numbers, no AI maths.",
        "Comparing products means a bar. The AI adds one sentence.",
    ]
    xs = [LEFT + index * (w + gap) for index in range(4)]
    for index, ((icon_name, who, does), x, caption) in enumerate(zip(steps, xs, captions)):
        ai = index == 1
        card(slide, x, top, w, h, fill=DEEP if ai else CARD, name=f"Step {index + 1}: {who}")
        badge(slide, x + 0.25, top + 0.25, 0.48, icon_name, "deep" if ai else "white", LIME if ai else GREEN)
        text(slide, x + 0.85, top + 0.24, w - 1.0, 0.3, who, size=15, bold=True, color=ON_DEEP if ai else INK)
        text(slide, x + 0.85, top + 0.5, w - 1.0, 0.3, does, size=12, color=ON_DEEP_MUTED if ai else MUTED)
        line(slide, x + 0.25, top + h - 1.0, x + w - 0.25, top + h - 1.0, DEEP_RULE if ai else BORDER,
             name="Caption rule")
        text(slide, x + 0.25, top + h - 0.84, w - 0.5, 0.7, caption, size=12, color=ON_DEEP_2 if ai else MUTED,
             line_spacing=1.05)
        if index < 3:
            cx, cy = x + w + gap / 2, top + h / 2 - 0.25
            shape(slide, MSO_SHAPE.OVAL, cx - 0.2, cy - 0.2, 0.4, 0.4, fill=CARD, line=BORDER, name="Arrow circle")
            text(slide, cx - 0.2, cy - 0.2, 0.4, 0.4, "→", size=14, bold=True, color=GREEN, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE)
    body = top + 1.05  # where each step's artefact starts

    # 1. The question, as typed.
    bubble(slide, xs[0] + w - 0.25, body + 0.5, "jakets returnd\nlast wk", size=19, fill=PAGE)

    # 2. The report the model asks for.
    x = xs[1]
    rows = [("report", "Returns"), ("dates", "Oct 20 – 26"), ("measure", "units, refunds"), ("by", "product"),
            ("only", "Outerwear")]
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + 0.2, body, w - 0.4, 1.95, fill=DEEP_CARD, radius=0.1,
          name="Report request")
    for index, (key, value) in enumerate(rows):
        row_y = body + 0.17 + index * 0.33
        text(slide, x + 0.38, row_y, 0.85, 0.3, key, size=12, color=ON_DEEP_MUTED)
        text(slide, x + 1.2, row_y, w - 1.45, 0.3, value, size=12, color=ON_DEEP, bold=True)

    # 3. What the code returns.
    x = xs[2]
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + 0.2, body, w - 0.4, 1.95, fill=FILL, line=BORDER, radius=0.1,
          name="Result rows")
    text(slide, x + 0.38, body + 0.15, w - 0.76, 0.25, "Returned last week", size=10, color=MUTED)
    text(slide, x + 0.38, body + 0.15, w - 0.76, 0.25, "units", size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    for product, units, row_y, bold in [("Alpine Down Parka", "3", 0.48, False), ("Northridge Insulated", "1", 0.82, False),
                                        ("Total", "4", 1.25, True)]:
        text(slide, x + 0.38, body + row_y, w - 1.0, 0.3, product, size=12, color=INK, bold=bold)
        text(slide, x + w - 0.78, body + row_y, 0.4, 0.3, units, size=12, color=INK, bold=bold, align=PP_ALIGN.RIGHT)
    line(slide, x + 0.38, body + 1.17, x + w - 0.38, body + 1.17, BORDER, name="Total rule")
    text(slide, x + 0.38, body + 1.58, w - 0.76, 0.25, "$792.15 refunded", size=11, color=MUTED)

    # 4. The chart and the answer.
    x = xs[3]
    mini_bar_chart(slide, x + 0.1, body - 0.05, w - 0.2, 1.05)
    text(slide, x + 0.25, body + 1.05, w - 0.5, 0.9,
         "“Last week (Oct 20–26), 4 jacket units were returned, totaling $792.15 in refunds.”",
         size=11, color=INK_2, line_spacing=1.1)
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
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, track_x, y + 0.3, track_w, 0.09, fill=PAGE, radius=0.045,
              name="Track")
        bar_w = max(0.14, at(end) - at(start))
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, at(end) - bar_w, y + 0.255, bar_w, 0.18, fill=GREEN, radius=0.09,
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
        "So, is it ready for Black Friday? Yes. It's live on Vercel today and it passed Erik's questions. There "
        "are three small steps before November 28, under an hour in total. First, put the AI key on the public "
        "address: right now only the test preview has it. Second, add a few dollars of OpenRouter credits, "
        "because the free plan stops at about 25 questions a day. Third, re-run the sweaters question to confirm "
        "the fix. Then merchants can use it. Happy to take questions.",
        dark=True,
    )
    kicker(slide, "Status", y=0.8, color=LIME)
    title(slide, "Ready for Black Friday", y=1.15, size=60, color=ON_DEEP, h=1.0)
    text(slide, LEFT, 2.3, CONTENT_W, 0.5, "Live today. Three small steps before November 28, under an hour in all.",
         size=22, color=ON_DEEP_2)

    line_y = 4.0
    xs = [LEFT + 0.3 + index * (CONTENT_W - 0.6) / 4 for index in range(5)]
    line(slide, xs[0], line_y, xs[-1], line_y, DEEP_RULE, width=2, name="Timeline")
    stops = [
        ("rocket", "Now", "Live on Vercel. Passed Erik's 20 questions.", True),
        ("key-round", "Key on the public URL", "One command. Only the test preview has it today.", False),
        ("coins", "Add AI credits", "OpenRouter's free plan stops at about 25 questions a day.", False),
        ("refresh-cw", "Re-run one question", "The sweaters fix (AQ-15) is live. It needs a check.", False),
        ("flag", "Nov 28", "Black Friday. Ready for merchants.", True),
    ]
    for index, ((icon_name, heading, detail, milestone), x) in enumerate(zip(stops, xs)):
        d = 0.6
        if milestone:
            badge(slide, x - d / 2, line_y - d / 2, d, icon_name, "deep", LIME)
        else:
            badge(slide, x - d / 2, line_y - d / 2, d, icon_name, "lime", DEEP_CARD, ring=LIME)
        first, last = index == 0, index == len(stops) - 1
        label_w = 1.8 if first or last else 2.7
        label_x = x - d / 2 if first else (x - label_w + d / 2 if last else x - label_w / 2)
        align = PP_ALIGN.LEFT if first else (PP_ALIGN.RIGHT if last else PP_ALIGN.CENTER)
        text(slide, label_x, line_y + 0.5, label_w, 0.4, heading, size=17, bold=True,
             color=LIME if milestone else ON_DEEP, align=align)
        text(slide, label_x, line_y + 0.9, label_w, 0.8, detail, size=13, color=ON_DEEP_2, align=align,
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
