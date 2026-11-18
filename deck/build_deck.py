"""Builds the six-slide demo deck planned in deck/outline.md.

    pip install python-pptx
    python deck/build_deck.py

Writes deck/shopify-merchant-analytics.pptx. Screenshots come from docs/screenshots/,
and every number on the slides is from the README's live run.
"""

from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
OUT = ROOT / "deck" / "shopify-merchant-analytics.pptx"

# The app's dark theme, from src/app/globals.css, so the screenshots sit flush on the slides.
BG = RGBColor(0x0D, 0x0D, 0x0D)
SURFACE = RGBColor(0x1A, 0x1A, 0x19)
HAIRLINE = RGBColor(0x38, 0x38, 0x35)
INK = RGBColor(0xF0, 0xEF, 0xEC)
INK_2 = RGBColor(0xC3, 0xC2, 0xB7)
MUTED = RGBColor(0x89, 0x87, 0x81)
ACCENT = RGBColor(0x39, 0x87, 0xE5)
BAR_REST = RGBColor(0x5C, 0x5B, 0x57)
FONT = "Arial"

LEFT = 0.6  # slide margin, inches
WIDTH = 13.333 - 2 * LEFT


def style_run(run, size, color=INK, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic


def add_text(slide, x, y, w, h, paragraphs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, space_after=0, name=None):
    """paragraphs: a string, or a list of paragraphs; each paragraph is a string or a list of
    (text, {size, color, bold, italic}) runs."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    for index, paragraph in enumerate(paragraphs):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        runs = [(paragraph, {})] if isinstance(paragraph, str) else paragraph
        for text, options in runs:
            run = p.add_run()
            run.text = text
            style_run(run, options.get("size", size), options.get("color", color), options.get("bold", bold),
                      options.get("italic", False))
    return box


def add_card(slide, x, y, w, h, fill=SURFACE, name=None):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    card.adjustments[0] = min(0.12, 0.16 / min(w, h))
    card.fill.solid()
    card.fill.fore_color.rgb = fill
    card.line.color.rgb = HAIRLINE
    card.line.width = Pt(0.75)
    card.shadow.inherit = False
    if name:
        card.name = name
    return card


def add_number(slide, x, y, number, size=0.42):
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(size), Inches(size))
    dot.fill.solid()
    dot.fill.fore_color.rgb = ACCENT
    dot.line.fill.background()
    dot.shadow.inherit = False
    dot.name = f"Step {number}"
    frame = dot.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(number)
    style_run(run, 15, RGBColor(0xFF, 0xFF, 0xFF), bold=True)
    return dot


def add_picture(slide, path, x, y, w, name):
    picture = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))
    picture.name = name
    return picture


def new_slide(prs, title, notes, title_size=36):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # "Title Only", so each slide has a real title
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG
    heading = slide.shapes.title
    heading.left, heading.top, heading.width, heading.height = Inches(LEFT), Inches(0.5), Inches(WIDTH), Inches(0.8)
    frame = heading.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.TOP
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = title
    style_run(run, title_size, INK, bold=True)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


# ---------------------------------------------------------------------------------------------
# 1. The problem and the fix


def slide_problem(prs):
    slide = new_slide(
        prs,
        "Merchants ask in their own words",
        "Merchants send us questions like these every day: by email, in support chat, in the admin search box "
        "and on the Community forum. These four are real, from the requests logged on October 27. Most are simple, "
        "but someone has to build each report by hand, and several merchants needed the answer before placing "
        "their Black Friday reorder. So I built a chat dashboard. The merchant types the question in their own "
        "words and gets a chart and a short answer back in a few seconds.",
    )
    add_text(slide, LEFT, 1.45, 8, 0.4, "Real requests, spelling and all", size=14, color=MUTED)

    quotes = [
        ("jakets returnd last wk", "Admin search"),
        ("best seller since summer?", "Admin search"),
        ("are repeat customers growing or not", "Support chat"),
        ("sales been weird lately, can you show me whats going on", "Support chat"),
    ]
    card_w, card_h, gap = 3.75, 1.55, 0.3
    for index, (quote, source) in enumerate(quotes):
        x = LEFT + (index % 2) * (card_w + gap)
        y = 2.0 + (index // 2) * (card_h + gap)
        add_card(slide, x, y, card_w, card_h, name=f"Request {index + 1}")
        add_text(slide, x + 0.3, y + 0.25, card_w - 0.6, 0.85, [[(f"“{quote}”", {"italic": True})]], size=17)
        add_text(slide, x + 0.3, y + card_h - 0.48, card_w - 0.6, 0.3, source, size=12, color=MUTED)

    right = LEFT + 2 * card_w + gap + 0.6
    add_text(slide, right, 1.85, 13.333 - LEFT - right, 1.45, "30", size=80, color=ACCENT, bold=True)
    add_text(
        slide, right, 3.4, 13.333 - LEFT - right, 1.5,
        "merchant report requests from October 27, by email, support chat, admin search and the Community forum.",
        size=16, color=INK_2,
    )
    add_text(
        slide, right, 4.75, 13.333 - LEFT - right, 1.0,
        "Several needed the answer before their Black Friday reorder.", size=16, color=INK_2,
    )

    add_text(
        slide, LEFT, 6.05, WIDTH, 0.8,
        [[("The fix: ", {"color": ACCENT, "bold": True}),
          ("a chat dashboard. Type the question, get a chart and a short answer in a few seconds.", {})]],
        size=20,
    )


# ---------------------------------------------------------------------------------------------
# 2. The interface


def slide_interface(prs):
    slide = new_slide(
        prs,
        "Type a question. Get a chart and a short answer.",
        "Here's what the merchant sees. They type 'which jackets came back the most last week'. While it works, "
        "grey steps say what it's doing, then fold away. The chart shows the exact dates it used, October 20 to 26, "
        "and underneath is a short answer: 4 jacket units came back, $792.15 refunded, mostly the Alpine Down Parka. "
        "I'll show this live in a moment.",
    )
    callouts = [
        ("Ask in your own words", "“which jackets came back the most last week”"),
        ("See what it's doing", "Grey steps while it works, folded into “Show steps (3)” once the chart lands"),
        ("Check the dates", "The exact range sits under the chart title: Oct 20–26, 2025"),
        ("Read the answer", "One to three plain sentences: 4 units back, $792.15 refunded"),
    ]
    y = 1.75
    for index, (heading, detail) in enumerate(callouts, start=1):
        add_number(slide, LEFT, y, index)
        add_text(slide, LEFT + 0.65, y - 0.02, 3.65, 0.4, heading, size=18, bold=True)
        add_text(slide, LEFT + 0.65, y + 0.4, 3.65, 0.8, detail, size=14, color=INK_2)
        y += 1.3

    shot_w = 7.6
    add_picture(slide, SHOTS / "jacket-returns-tooltip.png", 13.333 - LEFT - shot_w, 1.75, shot_w,
                "Screenshot: jacket returns last week")
    add_text(
        slide, 13.333 - LEFT - shot_w + 0.15, 1.75 + shot_w * 740 / 1520 + 0.15, shot_w - 0.3, 0.4,
        "The live dashboard answering “which jackets came back the most last week”.",
        size=12, color=MUTED,
    )


# ---------------------------------------------------------------------------------------------
# 3. The pipeline


def slide_pipeline(prs):
    slide = new_slide(
        prs,
        "How a question becomes a chart",
        "This is how a typed question turns into a chart. First, the AI model reads the question and picks one of "
        "four reports: sales, returns, repeat customers, or 'can't answer'. It fills in the dates, the breakdown and "
        "any filter, like Outerwear. Then our own code runs that report over the store's orders. The AI never adds "
        "numbers up and never works out dates, so the numbers are always exact. The code also picks the chart: one "
        "number is a card, a trend over time is a line, a comparison is a bar. Last, the AI writes a short answer "
        "from the result.",
    )
    steps = [
        ("You", "Type the question", "“jakets returnd last wk”"),
        ("The AI model", "Picks one of four reports and fills in the details", "Returns report\nOct 20–26\nOuterwear, by product"),
        ("Our code", "Runs the numbers on the store's orders", "4 units back\n$792.15 refunded"),
        ("The page", "Draws the chart. The AI adds a short answer.", "A bar chart, because it compares products"),
    ]
    card_w, gap, y, card_h = 2.7, 0.443, 1.75, 3.75
    for index, (who, what, example) in enumerate(steps):
        x = LEFT + index * (card_w + gap)
        add_card(slide, x, y, card_w, card_h, name=f"Pipeline step {index + 1}")
        add_number(slide, x + 0.3, y + 0.3, index + 1)
        add_text(slide, x + 0.85, y + 0.33, card_w - 1.0, 0.4, who.upper(), size=12, color=MUTED, bold=True)
        add_text(slide, x + 0.3, y + 0.95, card_w - 0.6, 1.1, what, size=18, bold=True)
        example_box = add_card(slide, x + 0.3, y + 2.15, card_w - 0.6, 1.3, fill=BG, name=f"Example {index + 1}")
        example_box.line.color.rgb = HAIRLINE
        add_text(slide, x + 0.45, y + 2.27, card_w - 0.9, 1.1, example.split("\n"), size=14, color=INK_2,
                 anchor=MSO_ANCHOR.TOP)
        if index < len(steps) - 1:
            arrow = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x + card_w + gap / 2 - 0.1),
                                           Inches(y + card_h / 2 - 0.17), Inches(0.2), Inches(0.34))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = MUTED
            arrow.line.fill.background()
            arrow.shadow.inherit = False
            arrow.name = f"Arrow {index + 1}"

    add_text(
        slide, LEFT, 5.85, WIDTH, 1.0,
        [[("The AI never does maths or works out dates. ", {"bold": True}),
          ("Code does both, and code picks the chart shape, so the same question always gets the same numbers "
           "and the same chart.", {"color": INK_2})]],
        size=18,
    )


# ---------------------------------------------------------------------------------------------
# 4. What it answers, vague dates, speed


def slide_questions(prs):
    slide = new_slide(
        prs,
        "Vague questions get exact dates, in seconds",
        "It answers three kinds of questions: sales and best sellers, returns and why they came back, and repeat "
        "customers. Merchants rarely give exact dates, so the code turns vague words into exact ranges. 'Last week' "
        "is Monday to Sunday, October 20 to 26. 'Lately' is the last 30 full days. With no date at all it uses all "
        "the data, and the range always shows under the chart title. Ask about ad spend or stock and it says that "
        "isn't in the data instead of making up a chart. And it's quick: most charts appear in under 3 seconds.",
    )
    add_text(slide, LEFT, 1.55, 5.6, 0.4, "It answers", size=14, color=MUTED)
    x = LEFT
    for label, width in [("Sales and best sellers", 2.0), ("Returns and why", 1.55), ("Repeat customers", 1.65)]:
        pill = add_card(slide, x, 1.95, width, 0.45, name=f"Report: {label}")
        pill.adjustments[0] = 0.5
        add_text(slide, x, 1.95, width, 0.45, label, size=13, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += width + 0.1

    add_text(slide, LEFT, 2.75, 5.6, 0.4, "Vague words become exact dates", size=14, color=MUTED)
    rows = [
        ("“last week”", "Oct 20–26"),
        ("“lately”, “recently”", "Sep 27 – Oct 26"),
        ("“since Labor Day”", "Sep 1 – Oct 26"),
        ("no date at all", "all data, May 6 – Oct 27"),
    ]
    add_card(slide, LEFT, 3.15, 5.65, 2.2, name="Date examples")
    for index, (said, dates) in enumerate(rows):
        y = 3.35 + index * 0.47
        add_text(slide, LEFT + 0.3, y, 2.2, 0.4, said, size=15, color=INK_2)
        add_text(slide, LEFT + 2.55, y, 2.95, 0.4, [[("→  ", {"color": MUTED}), (dates, {"bold": True})]], size=15)

    add_text(
        slide, LEFT, 5.6, 5.65, 0.9,
        [[("Ad spend or stock levels? ", {"bold": True}),
          ("It says the data doesn't have them and draws no chart.", {"color": INK_2})]],
        size=15,
    )

    shot_w = 6.3
    shot_x = 13.333 - LEFT - shot_w
    add_picture(slide, SHOTS / "weekly-revenue.png", shot_x, 1.55, shot_w, "Screenshot: weekly revenue, recently")
    shot_bottom = 1.55 + shot_w * 908 / 1536
    add_text(slide, shot_x + 0.15, shot_bottom + 0.1, shot_w - 0.3, 0.35,
             "“revenue by wk recently”: a trend over time, so a line.", size=12, color=MUTED)
    add_text(
        slide, shot_x + 0.15, shot_bottom + 0.55, shot_w - 0.3, 1.0,
        [[("Under 3 seconds", {"color": ACCENT, "bold": True, "size": 28})],
         [("from Ask to chart, for 17 of Erik's 18 chart questions", {"color": INK_2})]],
        size=15,
    )


# ---------------------------------------------------------------------------------------------
# 5. Results


FIRST_CHART_SECONDS = {  # README live run; AQ-07 and AQ-20 rightly draw no chart
    1: 2.04, 2: 2.99, 3: 4.63, 4: 2.31, 5: 2.92, 6: 2.33, 8: 2.69, 9: 1.67, 10: 2.73,
    11: 2.31, 12: 2.15, 13: 2.64, 14: 2.84, 15: 1.65, 16: 2.18, 17: 1.75, 18: 2.63, 19: 2.46,
}


def quiet_chart_frame(chart):
    """No fill or border on the chart and plot area, so the chart sits on the slide background."""
    no_fill = f'<c:spPr {nsdecls("c", "a")}><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
    chart._chartSpace.find(qn("c:chart")).addnext(parse_xml(no_fill))
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    plot_area.append(parse_xml(no_fill))


def slide_results(prs):
    slide = new_slide(
        prs,
        "Erik's 20 questions: all three pass marks met",
        "Erik gave us 20 acceptance questions and three pass marks. We ran all 20 on the live preview, each in a "
        "fresh chat. 19 picked the right report, and the bar is 18. Nothing crashed. Every chart appeared in under "
        "5 seconds. The slowest, AQ-03, took 5.26 seconds at first, because the chart waited for the loading steps. "
        "We changed that and it's now 4.63. The one miss was 'which sweaters sell best': it charted every product "
        "instead of only knitwear. The prompt now says where sweaters belong, and we'll re-run it to confirm.",
    )
    stats = [
        ("19 of 20", "picked the right report", "Pass mark: 18"),
        ("0", "crashes", "Pass mark: 0"),
        ("4.63 s", "slowest time to first chart", "Pass mark: under 5 s"),
    ]
    card_w = (WIDTH - 2 * 0.3) / 3
    for index, (value, label, mark) in enumerate(stats):
        x = LEFT + index * (card_w + 0.3)
        add_card(slide, x, 1.6, card_w, 1.5, name=f"Pass mark {index + 1}")
        add_text(slide, x + 0.3, 1.72, card_w - 0.6, 0.75, value, size=36, bold=True, color=ACCENT)
        add_text(slide, x + 0.3, 2.42, card_w - 0.6, 0.35, label, size=15)
        add_text(slide, x + 0.3, 2.72, card_w - 0.6, 0.3, mark, size=12, color=MUTED)

    data = CategoryChartData()
    data.categories = [str(number) for number in FIRST_CHART_SECONDS]
    data.add_series("Seconds to first chart", list(FIRST_CHART_SECONDS.values()), number_format="0.00")
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(LEFT - 0.1), Inches(3.35), Inches(8.3),
                                   Inches(3.6), data)
    frame.name = "Chart: seconds to first chart"
    chart = frame.chart
    quiet_chart_frame(chart)
    chart.has_legend = False
    chart.font.name = FONT
    chart.font.size = Pt(11)
    chart.font.color.rgb = MUTED
    chart.has_title = True
    title = chart.chart_title.text_frame
    title.text = "Seconds from Ask to chart, by question (the top line is the 5 s pass mark)"
    style_run(title.paragraphs[0].runs[0], 13, INK_2)

    plot = chart.plots[0]
    plot.gap_width = 60
    plot.vary_by_categories = False
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = BAR_REST
    slowest = list(FIRST_CHART_SECONDS).index(3)
    point = series.points[slowest]
    point.format.fill.solid()
    point.format.fill.fore_color.rgb = ACCENT
    label = point.data_label
    label.has_text_frame = True
    label.text_frame.text = "4.63 s"
    style_run(label.text_frame.paragraphs[0].runs[0], 11, INK, bold=True)
    label.position = XL_LABEL_POSITION.INSIDE_END

    values = chart.value_axis
    values.minimum_scale = 0
    values.maximum_scale = 5
    values.major_unit = 1
    values.major_tick_mark = XL_TICK_MARK.NONE
    values.has_major_gridlines = True
    values.major_gridlines.format.line.color.rgb = HAIRLINE
    values.major_gridlines.format.line.width = Pt(0.75)
    values.format.line.fill.background()
    values.tick_labels.number_format = '0" s"'
    values.tick_labels.number_format_is_linked = False

    categories = chart.category_axis
    categories.format.line.color.rgb = HAIRLINE
    categories.major_tick_mark = XL_TICK_MARK.NONE
    categories.has_title = True
    categories.axis_title.text_frame.text = "Erik's question number (AQ-07 and AQ-20 rightly draw no chart)"
    style_run(categories.axis_title.text_frame.paragraphs[0].runs[0], 11, MUTED)

    notes_x = LEFT + 8.5
    notes = [
        ("AQ-03 got faster. ", "It took 5.26 s at first, because the chart waited for the loading steps. Now it doesn't."),
        ("One miss: AQ-15. ", "“which sweaters sell best” charted every product, not just knitwear. "
                               "The fix is live, re-run pending."),
        ("Checked, not assumed. ", "Every number matched the order data."),
    ]
    y = 3.55
    for bold, rest in notes:
        add_text(slide, notes_x, y, 13.333 - LEFT - notes_x, 1.1, [[(bold, {"bold": True}), (rest, {"color": INK_2})]],
                 size=14)
        y += 1.15


# ---------------------------------------------------------------------------------------------
# 6. Status


def slide_status(prs):
    slide = new_slide(
        prs,
        "Ready for Black Friday, November 28",
        "So, is it ready for Black Friday? Yes. It's live on Vercel and it passed Erik's questions. There are three "
        "small things to do before November 28, under an hour in total. First, put the AI key on the public "
        "address; right now only the test preview has it. Second, add a few dollars of OpenRouter credits, because "
        "the free plan stops at about 25 questions a day. Third, re-run the sweaters question to confirm the fix. "
        "Then merchants can use it. Happy to take questions.",
    )
    add_card(slide, LEFT, 1.75, 5.2, 3.45, name="Live now")
    add_text(slide, LEFT + 0.4, 2.05, 4.4, 0.9, "Live now", size=40, bold=True, color=ACCENT)
    add_text(
        slide, LEFT + 0.4, 3.05, 4.4, 2.4,
        ["Running on Vercel.", "Passed all three of Erik's pass marks.", "Every number checked against the order data."],
        size=17, color=INK_2, space_after=10,
    )

    right = LEFT + 5.2 + 0.6
    add_text(slide, right, 1.75, 13.333 - LEFT - right, 0.5, "Before Nov 28: three small steps, under an hour",
             size=18, bold=True)
    todo = [
        ("Put the AI key on the public URL", "One command. Today only the test preview has it."),
        ("Add OpenRouter credits", "The free plan stops at about 25 questions a day."),
        ("Re-run the sweaters question", "The fix is live. It just needs checking."),
    ]
    y = 2.5
    for index, (heading, detail) in enumerate(todo, start=1):
        add_number(slide, right, y, index)
        add_text(slide, right + 0.65, y - 0.02, 13.333 - LEFT - right - 0.65, 0.4, heading, size=17, bold=True)
        add_text(slide, right + 0.65, y + 0.38, 13.333 - LEFT - right - 0.65, 0.4, detail, size=14, color=INK_2)
        y += 1.05

    add_text(slide, LEFT, 6.1, WIDTH, 0.6,
             [[("Then it's ready for merchants. ", {"bold": True}), ("Questions?", {"color": ACCENT, "bold": True})]],
             size=22)


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
