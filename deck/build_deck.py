"""Builds the six-slide demo deck planned in deck/outline.md.

    pip install -r deck/requirements.txt
    python deck/build_deck.py

Writes deck/shopify-merchant-analytics.pptx. Screenshots come from docs/screenshots/, and every
number on the slides comes from the README's live run of Erik's acceptance questions.

Look: the app's own light theme for content slides, its dark theme for the opening and closing
slides, product shots in browser windows, and one blue accent.
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
OUT = ROOT / "deck" / "shopify-merchant-analytics.pptx"

# Colours from src/app/globals.css.
PAGE = RGBColor(0xF9, 0xF9, 0xF7)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
WASH = RGBColor(0xEC, 0xEB, 0xE7)
RULE = RGBColor(0xE1, 0xE0, 0xD9)
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK_2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x6F, 0x6D, 0x68)
ACCENT = RGBColor(0x2A, 0x78, 0xD6)
BAR_REST = RGBColor(0xC3, 0xC2, 0xB7)
GOOD = RGBColor(0x1E, 0x7F, 0x4A)

NIGHT = RGBColor(0x0D, 0x0D, 0x0D)  # also the screenshots' background
NIGHT_CARD = RGBColor(0x1A, 0x1A, 0x19)
NIGHT_RULE = RGBColor(0x2C, 0x2C, 0x2A)
NIGHT_INK = RGBColor(0xF0, 0xEF, 0xEC)
NIGHT_INK_2 = RGBColor(0xC3, 0xC2, 0xB7)
NIGHT_MUTED = RGBColor(0x89, 0x87, 0x81)
NIGHT_ACCENT = RGBColor(0x39, 0x87, 0xE5)

FONT = "Arial"
SLIDE_W, SLIDE_H = 13.333, 7.5
LEFT = 0.7
CONTENT_W = SLIDE_W - 2 * LEFT

# Arial metrics, to size chat bubbles to their text. Falls back to an estimate off macOS.
_ARIAL = {False: "/System/Library/Fonts/Supplemental/Arial.ttf", True: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"}


def text_width(text, size, bold=False):
    """Width of one line of Arial text, in inches."""
    try:
        return ImageFont.truetype(_ARIAL[bold], 1000).getlength(text) * size / 1000 / 72
    except OSError:
        return len(text) * size * 0.53 / 72


def wrap(text, size, width, bold=False):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and text_width(trial, size, bold) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


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


def drop_theme_style(item):
    """python-pptx gives shapes the template's style, whose effects some renderers draw as a shadow.
    Every colour here is set explicitly, so the style can go."""
    theme_style = item._element.find(qn("p:style"))
    if theme_style is not None:
        item._element.remove(theme_style)


def soft_shadow(item, alpha=16):
    """A soft drop shadow, for windows and cards that float above the page."""
    sp_pr = item._element.spPr
    for old in sp_pr.findall(qn("a:effectLst")):
        sp_pr.remove(old)
    sp_pr.append(parse_xml(
        f'<a:effectLst {nsdecls("a")}><a:outerShdw blurRad="304800" dist="76200" dir="5400000" algn="t" '
        f'rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="{alpha * 1000}"/></a:srgbClr></a:outerShdw></a:effectLst>'
    ))


def line(slide, x1, y1, x2, y2, color, width=0.75, name=None):
    item = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    item.line.color.rgb = color
    item.line.width = Pt(width)
    drop_theme_style(item)
    if name:
        item.name = name
    return item


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=1.5):
    item = line(slide, x1, y1, x2, y2, color, width, name="Arrow")
    item.line._get_or_add_ln().append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle" w="med" len="med"/>'))
    return item


def pin(slide, x, y, number, fill=ACCENT, size=0.36, font_size=13):
    dot = shape(slide, MSO_SHAPE.OVAL, x, y, size, size, fill=fill, name=f"Pin {number}")
    frame = dot.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(number)
    style(run, font_size, RGBColor(0xFF, 0xFF, 0xFF), bold=True)
    return dot


def chip(slide, x, y, label, fill, color, size=11, name=None):
    """A small rounded label, sized to its text. Returns its width."""
    w = text_width(label, size, bold=True) + 0.32
    h = 0.3
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=fill, radius=h / 2, name=name or f"Chip: {label}")
    text(slide, x, y, w, h, label, size=size, color=color, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, tracking=0.8)
    return w


def bubble(slide, right, y, message, size=17, max_w=4.4, fill=WASH, color=INK, name=None):
    """A chat bubble like the app's question bubble, right-aligned at `right`. Returns its height."""
    pad_x, pad_y = 0.22, 0.13
    lines = wrap(message, size, max_w - 2 * pad_x)
    w = max(text_width(row, size) for row in lines) + 2 * pad_x + 0.1
    h = len(lines) * size * 1.2 / 72 + 2 * pad_y
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, right - w, y, w, h, fill=fill, radius=0.2, name=name or "Question bubble")
    text(slide, right - w + pad_x, y, w - 2 * pad_x + 0.06, h, "\n".join(lines), size=size, color=color,
         anchor=MSO_ANCHOR.MIDDLE)
    return h


def browser(slide, x, y, w, h, url="shopify-merchant-analytics.vercel.app"):
    """A dark browser window to hold the app's screenshots. Returns the top of its content area."""
    window = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=NIGHT, line=NIGHT_RULE, radius=0.14,
                   name="Browser window")
    soft_shadow(window, alpha=22)
    bar = 0.42
    for index in range(3):
        shape(slide, MSO_SHAPE.OVAL, x + 0.2 + index * 0.2, y + bar / 2 - 0.055, 0.11, 0.11, fill=NIGHT_RULE,
              name="Window dot")
    url_w = min(3.6, w - 2.0)
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + (w - url_w) / 2, y + 0.09, url_w, 0.25, fill=NIGHT_CARD,
          radius=0.125, name="Address bar")
    text(slide, x + (w - url_w) / 2, y + 0.09, url_w, 0.25, url, size=10, color=NIGHT_MUTED, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    line(slide, x, y + bar, x + w, y + bar, NIGHT_RULE, name="Window bar edge")
    return y + bar


def picture(slide, path, x, y, w, name):
    item = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    item.name = name
    return item


def new_slide(prs, notes, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # "Title Only": every slide keeps a real title
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NIGHT if dark else PAGE
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def title(slide, words, y=0.55, size=38, color=INK, h=0.8, w=CONTENT_W, x=LEFT):
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


def footer(slide, number):
    text(slide, LEFT, 7.0, 6, 0.25, "Shopify Merchant Analytics", size=10, color=MUTED)
    text(slide, SLIDE_W - LEFT - 1, 7.0, 1, 0.25, f"{number} / 6", size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def quiet_chart_frame(chart):
    """No fill or border on the chart or plot area, so the chart sits straight on the slide."""
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
        dark=True,
    )
    text(slide, LEFT, 0.8, 7, 0.3, "SHOPIFY MERCHANT ANALYTICS", size=12, color=NIGHT_ACCENT, bold=True, tracking=2)
    title(slide, "“jakets returnd\nlast wk”", y=1.45, size=64, color=NIGHT_INK, h=2.2, w=7.2)
    text(slide, LEFT, 3.75, 6.6, 0.4, "A real merchant question from October 27.", size=16, color=NIGHT_MUTED)
    text(
        slide, LEFT, 4.35, 6.6, 1.4,
        "Merchants ask in their own words. Before Black Friday they need the answer in seconds, not a report "
        "request.",
        size=22, color=NIGHT_INK_2, line_spacing=1.1,
    )
    text(
        slide, LEFT, 5.95, 7.2, 0.8,
        ["Now they ask the dashboard,", [("and get a chart back in under 3 seconds.", {"color": NIGHT_ACCENT, "bold": True})]],
        size=20, color=NIGHT_INK,
    )

    requests = [
        ("best seller since summer?", "Admin search"),
        ("are repeat customers growing or not", "Support chat"),
        ("sales been weird lately, can you show me whats going on", "Support chat"),
        ("how do i see which coats got returned most over the last couple weeks? need it before i reorder",
         "Shopify Community"),
    ]
    right, y = SLIDE_W - LEFT, 0.8
    for index, (message, source) in enumerate(requests):
        h = bubble(slide, right, y, message, size=16, max_w=4.4, fill=NIGHT_CARD, color=NIGHT_INK,
                   name=f"Request {index + 1}")
        text(slide, right - 3, y + h + 0.07, 3, 0.25, source, size=11, color=NIGHT_MUTED, align=PP_ALIGN.RIGHT)
        y += h + 0.6
    text(slide, right - 4.4, 6.25, 4.4, 0.4,
         [[("30", {"bold": True, "color": NIGHT_INK}), (" report requests logged on Oct 27", {})]],
         size=14, color=NIGHT_MUTED, align=PP_ALIGN.RIGHT)


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
    title(slide, "Type a question.\nGet a chart and\nan answer.", size=36, h=1.9, w=4.2)

    features = [
        ("Steps while it works", "Grey steps say what it's doing, then fold into “Show steps (3)”."),
        ("The exact dates", "Every chart shows the range it used, so “last week” is never a guess."),
        ("A short answer", "One to three sentences, with numbers straight from the data."),
    ]
    y = 3.0
    for index, (heading, detail) in enumerate(features, start=1):
        pin(slide, LEFT, y, index)
        text(slide, LEFT + 0.55, y - 0.01, 3.6, 0.35, heading, size=17, bold=True)
        text(slide, LEFT + 0.55, y + 0.36, 3.6, 0.8, detail, size=14, color=INK_2, line_spacing=1.1)
        y += 1.25

    win_x = 5.3
    win_w = SLIDE_W - LEFT - win_x
    pad = 0.25
    shot_w = win_w - 2 * pad
    shot_h = shot_w * 740 / 1520
    bubble_size = 13
    win_h = 0.42 + 0.2 + (bubble_size * 1.2 / 72 + 0.26) + 0.12 + shot_h + 0.15
    win_y = (SLIDE_H - win_h) / 2 - 0.05
    top = browser(slide, win_x, win_y, win_w, win_h)
    bubble_h = bubble(slide, win_x + win_w - pad - 0.1, top + 0.2, "which jackets came back the most last week",
                      size=bubble_size, fill=NIGHT_CARD, color=NIGHT_INK)
    shot_y = top + 0.2 + bubble_h + 0.12
    picture(slide, SHOTS / "jacket-returns-tooltip.png", win_x + pad, shot_y, shot_w, "Screenshot: jacket returns")

    # Pins on the window's left edge, level with each feature (y in the 740 px tall screenshot).
    scale = shot_w / 1520
    for number, py in enumerate([37, 166, 650], start=1):
        pin(slide, win_x - 0.15, shot_y + py * scale - 0.15, number, size=0.3, font_size=12)
    footer(slide, 2)


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
    series.format.fill.fore_color.rgb = ACCENT
    values = chart.value_axis
    values.visible = False
    values.has_major_gridlines = False
    values.minimum_scale = 0
    values.maximum_scale = 3.6
    categories = chart.category_axis
    categories.reverse_order = True
    categories.major_tick_mark = XL_TICK_MARK.NONE
    categories.format.line.color.rgb = RULE


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
    title(slide, "How a question becomes a chart")
    text(slide, LEFT, 1.4, CONTENT_W, 0.4,
         [[("The AI only chooses and fills in. ", {"color": ACCENT, "bold": True}),
           ("Code works out the dates, does the maths and picks the chart.", {})]],
         size=18, color=INK_2)

    top = 2.3
    stages = [  # x, width, who, chip fill, chip text
        (LEFT, 2.0, "MERCHANT", WASH, INK_2),
        (3.25, 2.95, "AI MODEL", ACCENT, CARD),
        (6.75, 2.6, "OUR CODE", INK, CARD),
        (9.9, SLIDE_W - LEFT - 9.9, "THE PAGE", INK, CARD),
    ]
    for x, w, who, fill, color in stages:
        chip(slide, x, top, who, fill, color, name=f"Who: {who}")
    body, card_h = top + 0.5, 2.15
    for (x, w, *_), (next_x, *_) in zip(stages, stages[1:]):
        arrow(slide, x + w + 0.1, body + card_h / 2, next_x - 0.1, body + card_h / 2)

    # 1. The question, as typed.
    x, w = stages[0][:2]
    bubble(slide, x + w, body + card_h / 2 - 0.3, "jakets returnd last wk", size=17, max_w=w, fill=WASH, color=INK)

    # 2. The report the model asks for.
    x, w = stages[1][:2]
    card = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, body, w, card_h, fill=NIGHT, radius=0.12,
                 name="Report request")
    soft_shadow(card, alpha=14)
    rows = [("report", "Returns"), ("dates", "Oct 20 – 26"), ("measure", "units, refunds"),
            ("by", "product"), ("only", "Outerwear")]
    for index, (key, value) in enumerate(rows):
        row_y = body + 0.24 + index * 0.35
        text(slide, x + 0.25, row_y, 0.95, 0.3, key, size=13, color=NIGHT_MUTED)
        text(slide, x + 1.2, row_y, w - 1.4, 0.3, value, size=13, color=NIGHT_INK, bold=True)

    # 3. What the code returns.
    x, w = stages[2][:2]
    card = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, body, w, card_h, fill=CARD, line=RULE, radius=0.12,
                 name="Result rows")
    soft_shadow(card, alpha=8)
    text(slide, x + 0.25, body + 0.22, w - 0.5, 0.3, "Returned last week", size=11, color=MUTED)
    text(slide, x + 0.25, body + 0.22, w - 0.5, 0.3, "units", size=11, color=MUTED, align=PP_ALIGN.RIGHT)
    rows = [("Alpine Down Parka", "3", 0.6, False), ("Northridge Insulated", "1", 0.97, False), ("Total", "4", 1.45, True)]
    for product, units, row_y, bold in rows:
        text(slide, x + 0.25, body + row_y, w - 0.9, 0.3, product, size=13, color=INK, bold=bold)
        text(slide, x + w - 0.65, body + row_y, 0.4, 0.3, units, size=13, color=INK, bold=bold, align=PP_ALIGN.RIGHT)
    line(slide, x + 0.25, body + 1.35, x + w - 0.25, body + 1.35, RULE, name="Total rule")
    text(slide, x + 0.25, body + 1.78, w - 0.5, 0.3, "$792.15 refunded", size=12, color=INK_2)

    # 4. The chart and the answer.
    x, w = stages[3][:2]
    card = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, body, w, card_h, fill=CARD, line=RULE, radius=0.12,
                 name="Chart and answer")
    soft_shadow(card, alpha=8)
    mini_bar_chart(slide, x + 0.1, body + 0.1, w - 0.2, 1.05)
    text(slide, x + 0.25, body + 1.22, w - 0.5, 0.85,
         "“Last week (Oct 20–26), 4 jacket units were returned, totaling $792.15 in refunds.”",
         size=11, color=INK_2, line_spacing=1.1)

    captions = [
        "Typed in their own words, typos and all.",
        "Picks 1 of 4 reports and fills in the blanks. Dates are copied from a table code wrote.",
        "Runs the report over the orders. Exact numbers, no AI maths.",
        "Code picks the chart: comparing products means a bar. The AI writes one sentence.",
    ]
    for (x, w, *_), caption in zip(stages, captions):
        text(slide, x, body + card_h + 0.25, w, 0.9, caption, size=13, color=INK_2, line_spacing=1.1)
    footer(slide, 3)


# ---------------------------------------------------------------------------------------------
# 4. Vague dates, what it answers, speed


def slide_questions(prs):
    slide = new_slide(
        prs,
        "Merchants rarely give exact dates, so the code turns vague words into exact ranges before the AI sees "
        "the question. Each bar here is the range a phrase becomes. 'Last week' is Monday to Sunday, October 20 to "
        "26. 'Lately' and 'recently' are the last 30 full days. With no date at all it uses all the data, and the "
        "range always shows under the chart title. On the right is 'revenue by wk recently'. It answers three "
        "kinds of question, says plainly when something like ad spend isn't in the data, and the median time "
        "from pressing Ask to seeing the chart was 2.4 seconds.",
    )
    title(slide, "Vague words become exact dates")

    first, last = date(2025, 5, 1), date(2025, 10, 31)
    track_x, track_w = LEFT + 2.3, 4.4

    def at(day):
        return track_x + track_w * (day - first).days / (last - first).days

    rows = [
        ("“last week”", date(2025, 10, 20), date(2025, 10, 26), "Oct 20–26"),
        ("“lately”", date(2025, 9, 27), date(2025, 10, 26), "Sep 27 – Oct 26"),
        ("“since Labor Day”", date(2025, 9, 1), date(2025, 10, 26), "Sep 1 – Oct 26"),
        ("“since summer”", date(2025, 6, 1), date(2025, 10, 26), "Jun 1 – Oct 26"),
        ("no date at all", date(2025, 5, 6), date(2025, 10, 27), "all data: May 6 – Oct 27"),
    ]
    first_row, row_gap = 1.75, 0.66
    months_y = first_row + len(rows) * row_gap
    for month in range(5, 11):
        day = date(2025, month, 1)
        line(slide, at(day), first_row + 0.2, at(day), months_y, RULE, width=0.5, name="Month line")
        text(slide, at(day) + 0.05, months_y + 0.03, 0.6, 0.25, day.strftime("%b"), size=10, color=MUTED)
    for index, (phrase, start, end, label) in enumerate(rows):
        y = first_row + index * row_gap
        text(slide, LEFT, y + 0.22, 2.25, 0.35, phrase, size=16, color=INK, bold=True)
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, track_x, y + 0.33, track_w, 0.1, fill=WASH, radius=0.05,
              name="Track")
        bar_w = max(0.14, at(end) - at(start))
        shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, at(end) - bar_w, y + 0.28, bar_w, 0.2, fill=ACCENT, radius=0.1,
              name=f"Range: {label}")
        text(slide, at(end) - 2.6, y + 0.02, 2.6, 0.25, label, size=11, color=INK_2, bold=True, align=PP_ALIGN.RIGHT)

    # The weekly revenue chart for "recently", in a browser window.
    win_x = 7.75
    win_w = SLIDE_W - LEFT - win_x
    shot_w = win_w - 0.3
    shot_h = shot_w * 908 / 1536
    win_h = 0.42 + 0.15 + shot_h + 0.15
    top = browser(slide, win_x, 1.6, win_w, win_h)
    picture(slide, SHOTS / "weekly-revenue.png", win_x + 0.15, top + 0.15, shot_w, "Screenshot: weekly revenue")
    text(slide, win_x, 1.6 + win_h + 0.12, win_w, 0.3,
         "“revenue by wk recently” → Sep 27 – Oct 26. A trend, so a line.", size=12, color=MUTED)

    # Three facts along the bottom.
    facts = [
        ("2.4 s", "median time from Ask to chart, over Erik's 18 chart questions"),
        ("3 reports", "sales and best sellers, returns and why, repeat customers"),
        ("No made-up charts", "ad spend or stock gets a plain “not in the data”"),
    ]
    col_w = (CONTENT_W - 2 * 0.4) / 3
    line(slide, LEFT, 5.7, SLIDE_W - LEFT, 5.7, RULE, name="Facts rule")
    for index, (big, small) in enumerate(facts):
        x = LEFT + index * (col_w + 0.4)
        text(slide, x, 5.88, col_w, 0.5, big, size=24, bold=True, color=ACCENT if index == 0 else INK, tracking=-0.5)
        text(slide, x, 6.35, col_w, 0.5, small, size=13, color=INK_2)
    footer(slide, 4)


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
        "under 5 seconds, the dashed line. The blue bar is AQ-03: it took 5.26 seconds at first, because the chart "
        "waited for the loading steps. We changed that and it's now 4.63. The one miss was 'which sweaters sell "
        "best': it charted every product instead of only knitwear. The prompt now says where sweaters belong, and "
        "we'll re-run it to confirm.",
    )
    title(slide, "Erik's 20 questions: every pass mark met")

    stats = [("19/20", "picked the right report", "needs 18"), ("0", "crashes", "needs 0"),
             ("4.63 s", "slowest time to chart", "needs under 5 s")]
    col_w = (CONTENT_W - 2 * 0.5) / 3
    for index, (value, label, mark) in enumerate(stats):
        x = LEFT + index * (col_w + 0.5)
        if index:
            line(slide, x - 0.25, 1.6, x - 0.25, 3.05, RULE, name="Stat divider")
        text(slide, x, 1.45, col_w, 0.9, value, size=48, bold=True, color=ACCENT, tracking=-1.5)
        text(slide, x, 2.35, col_w, 0.35, label, size=16, color=INK)
        chip_w = chip(slide, x, 2.78, "PASS", GOOD, CARD, size=10, name=f"Pass {index + 1}")
        text(slide, x + chip_w + 0.12, 2.78, col_w - chip_w, 0.3, mark, size=13, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

    data = CategoryChartData()
    data.categories = [str(number) for number in FIRST_CHART_SECONDS]
    data.add_series("Seconds to first chart", list(FIRST_CHART_SECONDS.values()), number_format="0.00")
    data.add_series("Pass mark", [5.0] * len(FIRST_CHART_SECONDS), number_format="0.0")
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(LEFT - 0.1), Inches(3.4), Inches(8.4),
                                   Inches(3.5), data)
    frame.name = "Chart: seconds to first chart"
    chart = frame.chart
    quiet_chart_frame(chart)
    chart.has_legend = False
    chart.font.name = FONT
    chart.font.size = Pt(11)
    chart.font.color.rgb = MUTED
    chart.has_title = True
    chart_title = chart.chart_title.text_frame
    chart_title.text = "Seconds from Ask to chart, by question"
    style(chart_title.paragraphs[0].runs[0], 13, INK, bold=True)

    plot = chart.plots[0]
    plot.gap_width = 55
    plot.vary_by_categories = False
    bars = plot.series[0]
    bars.format.fill.solid()
    bars.format.fill.fore_color.rgb = BAR_REST
    slowest = bars.points[list(FIRST_CHART_SECONDS).index(3)]
    slowest.format.fill.solid()
    slowest.format.fill.fore_color.rgb = ACCENT

    values = chart.value_axis
    values.minimum_scale = 0
    values.maximum_scale = 6
    values.major_unit = 1
    values.has_major_gridlines = True
    values.major_gridlines.format.line.color.rgb = RULE
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
    style(categories.axis_title.text_frame.paragraphs[0].runs[0], 11, MUTED)
    threshold_as_line(chart, "0B0B0B", "5 s pass mark")

    notes_x = LEFT + 8.75
    notes_w = SLIDE_W - LEFT - notes_x
    notes = [
        ("AQ-03: 5.26 s → 4.63 s", "The blue bar. The chart no longer waits for the loading steps."),
        ("One miss: AQ-15", "“which sweaters sell best” charted every product. Fixed, re-run pending."),
        ("Checked, not assumed", "Every number matched the order data."),
    ]
    y = 3.55
    for heading, detail in notes:
        text(slide, notes_x, y, notes_w, 0.35, heading, size=16, bold=True)
        text(slide, notes_x, y + 0.36, notes_w, 0.7, detail, size=13, color=INK_2, line_spacing=1.1)
        y += 1.15
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
    text(slide, LEFT, 0.8, 7, 0.3, "STATUS", size=12, color=NIGHT_ACCENT, bold=True, tracking=2)
    title(slide, "Ready for Black Friday", y=1.2, size=60, color=NIGHT_INK, h=1.0)
    text(slide, LEFT, 2.35, CONTENT_W, 0.5, "Live today. Three small steps before November 28, under an hour in all.",
         size=22, color=NIGHT_INK_2)

    line_y = 3.95
    xs = [LEFT + 0.18 + index * (CONTENT_W - 0.36) / 4 for index in range(5)]
    line(slide, xs[0], line_y, xs[-1], line_y, NIGHT_RULE, width=2, name="Timeline")
    stops = [
        ("Now", "Live on Vercel. Passed Erik's 20 questions.", None),
        ("Key on the public URL", "One command. Only the test preview has it today.", 1),
        ("Add OpenRouter credits", "The free plan stops at about 25 questions a day.", 2),
        ("Re-run one question", "The sweaters fix (AQ-15) is live. It needs a check.", 3),
        ("Nov 28", "Black Friday. Ready for merchants.", None),
    ]
    for index, ((heading, detail, number), x) in enumerate(zip(stops, xs)):
        size = 0.36
        if number is None:
            shape(slide, MSO_SHAPE.OVAL, x - size / 2, line_y - size / 2, size, size, fill=NIGHT_ACCENT,
                  name=f"Milestone: {heading}")
        else:
            dot = pin(slide, x - size / 2, line_y - size / 2, number, fill=NIGHT_CARD, size=size)
            dot.line.color.rgb = NIGHT_ACCENT
            dot.line.width = Pt(1.5)
        first, last = index == 0, index == len(stops) - 1
        label_w = 1.7 if first or last else 2.6
        label_x = x - size / 2 if first else (x - label_w + size / 2 if last else x - label_w / 2)
        align = PP_ALIGN.LEFT if first else (PP_ALIGN.RIGHT if last else PP_ALIGN.CENTER)
        milestone = number is None
        text(slide, label_x, line_y + 0.42, label_w, 0.4, heading, size=20 if milestone else 16, bold=True,
             color=NIGHT_ACCENT if milestone else NIGHT_INK, align=align)
        text(slide, label_x, line_y + (0.85 if milestone else 0.8), label_w, 0.8, detail, size=13,
             color=NIGHT_INK_2, align=align, line_spacing=1.1)

    text(slide, LEFT, 6.25, 6, 0.6, "Questions?", size=32, bold=True, color=NIGHT_ACCENT, tracking=-1)


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
