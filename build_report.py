"""Build the two PDFs for the portal (max 2 files, 10 MB each).

    python run_all.py
    python build_report.py --github https://github.com/<you>/CSA08-1921260102-Assignment3

PDF 1 = report with the evidence for Q1-Q7.  PDF 2 = all source code + complete program output.
"""
import argparse
import ast
import datetime
import json
import os
import platform
import textwrap

import matplotlib
import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

import make_figures

ROOT = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument("--github", default="https://github.com/<your-username>/CSA08-1921260102-Assignment3")
parser.add_argument("--name", default="Bala Ashwin R")
parser.add_argument("--reg", default="1921260102")
parser.add_argument("--date", default=datetime.date.today().strftime("%d %B %Y"))
args = parser.parse_args()
PYVER = platform.python_version()

# ------------------------------------------------------------------ fonts and styles
fdir = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
for nm, fn in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
               ("DVM", "DejaVuSansMono.ttf"), ("DVM-B", "DejaVuSansMono-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(nm, os.path.join(fdir, fn)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")
pdfmetrics.registerFontFamily("DVM", normal="DVM", bold="DVM-B", italic="DVM", boldItalic="DVM-B")

BODY = ParagraphStyle("body", fontName="DV", fontSize=8.8, leading=12.2, spaceAfter=4)
H1 = ParagraphStyle("h1", fontName="DV-B", fontSize=14, leading=18, spaceBefore=4, spaceAfter=6,
                    textColor=colors.HexColor("#1f3b63"))
H2 = ParagraphStyle("h2", fontName="DV-B", fontSize=10.2, leading=13, spaceBefore=8, spaceAfter=3,
                    textColor=colors.HexColor("#2c5d8f"))
CAP = ParagraphStyle("cap", fontName="DV-I", fontSize=7.8, leading=10, alignment=TA_CENTER, spaceAfter=6)
MONO = ParagraphStyle("mono", fontName="DVM", fontSize=6.6, leading=7.9, backColor=colors.HexColor("#f4f4f4"),
                      borderPadding=3, spaceAfter=6)
TITLE = ParagraphStyle("title", fontName="DV-B", fontSize=22, leading=28, alignment=TA_CENTER, spaceAfter=10,
                       textColor=colors.HexColor("#1f3b63"))
CENTER = ParagraphStyle("center", parent=BODY, alignment=TA_CENTER, fontSize=10.5, leading=15)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, style=BODY):
    return Paragraph(t, style)


def bullets(items):
    return [Paragraph("•&nbsp;&nbsp;" + t, ParagraphStyle("b", parent=BODY, leftIndent=12, firstLineIndent=-9,
                                                        spaceAfter=2)) for t in items]


def code(text, width=118):
    lines = []
    for ln in text.rstrip("\n").split("\n"):
        lines += textwrap.wrap(ln, width, subsequent_indent="      ", replace_whitespace=False,
                               drop_whitespace=False) or [""]
    return Preformatted("\n".join(lines), MONO)


def table(rows, widths=None, font=7.8):
    cell = ParagraphStyle("cell", fontName="DV", fontSize=font, leading=font + 2.6)
    head = ParagraphStyle("head", parent=cell, fontName="DV-B")
    rows = [[c if not isinstance(c, str) else Paragraph(c, head if i == 0 else cell) for c in row]
            for i, row in enumerate(rows)]
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "DV"), ("FONTNAME", (0, 0), (-1, 0), "DV-B"),
                           ("FONTSIZE", (0, 0), (-1, -1), font), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f2")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    return [t, Spacer(1, 6)]


def img(name, width_cm, caption):
    path = os.path.join(ROOT, "figures", name)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    im = Image(path, width=width_cm * cm, height=width_cm * cm * h / w)
    return [KeepTogether([im, P(caption, CAP)])]


def ft(x):
    if x < 1e-6:
        return f"{x * 1e9:.0f} ns"
    if x < 1e-3:
        return f"{x * 1e6:.1f} µs"
    if x < 1:
        return f"{x * 1e3:.2f} ms"
    return f"{x:.2f} s"


def load(q):
    with open(os.path.join(ROOT, q, "results.json")) as f:
        return json.load(f)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def funcs(path, names):
    src = read(path)
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out.append(ast.get_source_segment(src, node))
    return "\n\n".join(out)


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(1.6 * cm, 1.0 * cm, f"Python Programming - Assignment 3 (CO3) - {args.name} - {args.reg}")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def outputs(path):
    return code(read(path))


# =================================================================== REPORT CONTENT
def cover(story, second=False):
    story += [Spacer(1, 3 * cm), P("PYTHON PROGRAMMING", TITLE),
              P("Assignment 3 - CO3", ParagraphStyle("t2", parent=TITLE, fontSize=16, leading=20)),
              P("Lists, tuples, dictionaries, sets, copying and list comprehension",
                ParagraphStyle("t3", parent=CENTER, fontName="DV-I")), Spacer(1, 1.2 * cm)]
    rows = [["Student name", esc(args.name)], ["Register number", esc(args.reg)],
            ["GitHub repository", esc(args.github)],
            ["Python version", PYVER],
            ["Libraries", f"Programs: standard library only. Report tools: matplotlib {matplotlib.__version__}, "
                          f"reportlab {reportlab.Version}"],
            ["Document", "Source code and complete program output" if second else "Report - evidence for Q1 to Q7"],
            ["Date", esc(args.date)]]
    rows = [[P("<b>%s</b>" % a), P(b)] for a, b in rows]
    t = Table(rows, colWidths=[4.2 * cm, 12.3 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3fa"))]))
    story += [t, Spacer(1, 0.8 * cm)]
    if not second:
        story += [P("<b>Contents.</b> Q1 Lists and slicing (6) · Q2 Tuples, mutability and copying (7) · "
                    "Q3 Dictionaries (7) · Q4 Sets (7) · Q5 List comprehension (6) · Q6 Nested data (7) · "
                    "Q7 Contact merging design (10). Every question follows Design → Implementation → Analysis → "
                    "Evaluation. All numbers in the tables come from the programs in the repository "
                    "(folders Q1 … Q7) run with Python " + PYVER + ".", CENTER),
                  P("Timing note: times are the best of several runs on one computer; they show how the cost "
                    "grows with n and will differ slightly on another machine.", ParagraphStyle(
                        "n", parent=CENTER, fontSize=8.5, textColor=colors.grey))]
    story.append(PageBreak())


def q1(story):
    r = load("Q1")
    story += [P("Q1 - Lists and Slicing: Daily Rainfall Records (K3 - Apply, 6 marks)", H1), P("Implementation", H2),
              P("The year of readings is a Python list of 365 floats; the index is the day number minus one. Weekly totals "
                "use slicing (<font name='DVM'>r[i:i+7]</font>), the extremes use <font name='DVM'>max/min</font> with "
                "<font name='DVM'>index()</font>, and the dry days use <font name='DVM'>enumerate</font>. The 365th day "
                "forms a 53rd, one-day block, so the wettest and driest week are chosen among the 52 full weeks.")]
    story.append(code(funcs("Q1/rainfall.py", {"weekly_totals", "wettest_driest", "max_min_with_positions", "dry_days",
                                               "ma_naive", "ma_running"})))
    story += [P("Output (Q1/rainfall.py, first part)", H2), code("\n".join(read("Q1/output.txt").split("\n")[:22]))]
    story += [P("Design and analysis", H2), P("<b>Pseudocode for the moving average</b>")]
    story.append(code("""FUNCTION moving_average_naive(readings, w = 7)
    result <- empty list
    FOR i FROM 0 TO len(readings) - w
        total <- 0
        FOR j FROM i TO i + w - 1:  total <- total + readings[j]
        APPEND total / w TO result
    RETURN result

FUNCTION moving_average_running(readings, w = 7)
    IF len(readings) < w THEN RETURN empty list
    total <- sum of readings[0 .. w-1]
    result <- [ total / w ]
    FOR i FROM w TO len(readings) - 1
        total <- total + readings[i] - readings[i - w]     (add the newest, remove the oldest)
        APPEND total / w TO result
    RETURN result"""))
    story += bullets([
        "<b>readings[7:14]</b> returns a <i>new</i> list holding the elements at indexes 7 to 13 (the end index is "
        "excluded): days 8 to 14, i.e. the second week - 7 values.",
        "<b>readings[-7:]</b> starts 7 places from the end and runs to the end: the last seven readings (days 359 to 365). "
        "If the list has fewer than 7 values it simply returns all of them, with no error.",
        "<b>readings[::7]</b> takes every 7th element starting at index 0 (days 1, 8, 15, …); for 365 values this "
        "gives 53 values, one sample per week.",
        "<b>Why a list is suitable:</b> readings are ordered by day, are read by position in O(1), can be sliced into weeks, "
        "are mutable (a faulty reading can be corrected with <font name='DVM'>r[i] = x</font>) and a new day is added with "
        "<font name='DVM'>append</font>.",
        "<b>Cost of list operations:</b> <font name='DVM'>append</font> amortised O(1); <font name='DVM'>pop()</font> O(1); "
        "<font name='DVM'>insert(i, x)</font> and <font name='DVM'>pop(i)</font> O(n − i) because later elements shift; "
        "<font name='DVM'>sort</font> O(n log n) (Timsort; O(n) when already sorted)."])
    story += [P("<b>Number of additions (window w = 7, n readings).</b> Naive: there are n − 6 windows and each window needs "
                "6 additions to add 7 numbers, so 6(n − 6) ≈ 6n additions, i.e. O(7n) = O(n) for a fixed window "
                "(in general (w − 1)(n − w + 1)). Running sum: 6 additions for the first window, then for each of the remaining "
                "n − 7 windows one addition and one subtraction, so 6 + 2(n − 7) = 2n − 8. The ratio tends to (w − 1)/2 = 3. "
                "Both counts were also obtained by simulating the loops in the program and match the formulas exactly.")]
    story += table([["n", "Naive additions 6(n−6)", "Running-sum operations 2n−8", "Ratio"]] +
                   [[f"{int(k):,}", f"{v[0]:,}", f"{v[1]:,}", f"{v[0] / v[1]:.2f}"] for k, v in r["adds"].items()],
                   [2.5 * cm, 4.5 * cm, 5.2 * cm, 2.5 * cm])
    story += [P("Experimental investigation", H2)]
    t = r["timing"]
    story += table([["n", "Naive", "Running sum", "Deque (alt.)", "Naive / running (measured)", "Derived ratio"]] +
                   [[f"{d['n']:,}", ft(d["naive"]), ft(d["running"]), ft(d["deque"]),
                     f"{d['naive'] / d['running']:.1f}", "≈ 3.0"] for d in t],
                   [2.2 * cm, 2.4 * cm, 2.6 * cm, 2.6 * cm, 4.2 * cm, 2.6 * cm])
    story += img("q1_timing.png", 10, "Fig. 1 - Both methods grow linearly with n; the running sum is about 3 times faster, "
                                       "as the addition counts predict.")
    story += [P("The measured ratio is close to the derived ratio of 3: the running sum does about a third of the "
                "arithmetic, and both curves are straight lines on the log-log graph (time proportional to n). The "
                "three versions return identical values (checked with <font name='DVM'>math.isclose</font>). Data were "
                "generated with the <font name='DVM'>random</font> module (365, 36,500 and 365,000 readings).")]
    story += [P("<b>Edge-case tests.</b>")] + table([
        ["Input", "Weekly totals", "Max/min", "Moving average (all 3 methods)"],
        ["empty list", "[]", "None (handled)", "[]"],
        ["3 values [1, 2, 3]", "[6.0] (partial week)", "(3.0 at 2), (1.0 at 0)", "[] (list shorter than 7)"],
        ["exactly 7 values of 1.0", "[7.0]", "(1.0 at 0), (1.0 at 0)", "[1.0]"]], [3.8 * cm, 3.6 * cm, 4.2 * cm, 5.0 * cm])
    o = r["ops"][-1]
    story += [P("<b>Design question - a late reading.</b> Finding the right position is cheap "
                "(<font name='DVM'>bisect.bisect_left</font>, O(log n)), but <font name='DVM'>list.insert()</font> must shift "
                "every later element, so it costs O(n − position). Measured for one call on a list of "
                f"{o['n']:,} values: append {ft(o['append'])}, insert at the front {ft(o['insert_front'])}, in the middle "
                f"{ft(o['insert_mid'])}. For a 365-element year this is a few microseconds, so <b>yes, I would still use a "
                "list</b>: it is simple, and late arrivals are rare. If one reading per day is expected, a better design is to "
                "keep a slot per day and assign <font name='DVM'>r[i] = x</font> (O(1)). Only for millions of readings with "
                "frequent out-of-order arrival would I switch to a dictionary keyed by date (O(1) average insert) or a database.")]
    story += table([["n", "append", "pop()", "insert(0)", "insert(middle)", "pop(0)", "sort"]] +
                   [[f"{d['n']:,}", ft(d["append"]), ft(d["pop_end"]), ft(d["insert_front"]), ft(d["insert_mid"]),
                     ft(d["pop_front"]), ft(d["sort"])] for d in r["ops"]], font=7.4)
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>deque(maxlen=7).</b> Each new reading is appended to a <font name='DVM'>collections.deque(maxlen=7)</font>; "
                "when the deque is full the oldest reading drops out automatically. Keeping a running total, "
                "<font name='DVM'>s -= win[0]</font> before appending and <font name='DVM'>s += x</font> after, gives the average of "
                "the last 7 values after every reading (function <font name='DVM'>ma_deque</font> in the repository).")]
    story.append(code(funcs("Q1/rainfall.py", {"ma_deque"})))
    story += table([
        ["Approach", "Time for n days", "Extra space", "Remarks"],
        ["Slicing a list, re-adding (naive)", "O(7n) = O(n), 6(n−6) additions", "O(7) temporary slice each step + O(n) output", "simplest code"],
        ["List with running sum", "O(n), 2n−8 operations", "O(n) output", "fastest here"],
        ["deque(maxlen=7) + running sum", "O(n); push and eviction are O(1)", "O(7) = O(1) for the window (+ O(n) if the averages are stored)",
         "ideal for a stream; no need to keep all readings; slower here by a constant factor (method calls)"],
        ["dict keyed by date", "O(n) to build; O(1) average lookup or late insert", "O(n) with a larger constant (hash table)",
         "no slicing by range; good for missing or late days"]], [4.1 * cm, 4.2 * cm, 4.4 * cm, 4.2 * cm], font=7.2)
    story.append(PageBreak())


def q2(story):
    r = load("Q2")
    story += [P("Q2 - Tuples, Mutability and Copying: City Bus-Stop Map (K4 - Analyse, 7 marks)", H1), P("Implementation", H2),
              P("Stops are <font name='DVM'>(latitude, longitude)</font> tuples used as dictionary keys; the zone grid is created with a "
                "list comprehension; aliasing, shallow copies (<font name='DVM'>copy.copy</font>, slicing) and "
                "<font name='DVM'>copy.deepcopy</font> are demonstrated; tuples are unpacked in a <font name='DVM'>for</font> loop "
                "(<font name='DVM'>for (lat, lon), name in stops.items()</font>).")]
    story += [P("Output (Q2/bus_stops.py)", H2), code("\n".join(read("Q2/output.txt").split("\n")[:36]))]
    story += [P("Design and analysis", H2)]
    story += bullets([
        "<b>Why tuples can be keys but lists cannot.</b> A dictionary stores each key at a position computed from "
        "<font name='DVM'>hash(key)</font>, and the hash must never change while the key is in the table. A tuple of numbers "
        "cannot change, so its hash is fixed. A list can change, so its hash (and equality) would change after insertion and "
        "the entry could no longer be found; Python therefore makes lists unhashable. A tuple that contains a list is also "
        "unhashable. Trying <font name='DVM'>stops[[13.0418, 80.2341]] = ...</font> gives "
        f"<font name='DVM'>TypeError: {esc(r['list_key_error'])}</font>.",
        "<b>Shallow or deep copy.</b> A shallow copy (<font name='DVM'>copy.copy</font>, <font name='DVM'>x[:]</font>) copies only "
        "the outer container; the inner objects are shared. It is enough when the elements are immutable (numbers, strings, "
        "tuples) or when only whole elements are replaced, never modified in place. A deep copy is needed for nested mutable "
        "data, such as a grid of lists, when the copy must be completely independent.",
        "<b>Why a function can change the caller's list.</b> Python passes a reference to the object. The parameter name and the "
        "caller's variable name refer to the same list, so <font name='DVM'>append</font> inside the function changes that one object "
        "(shown in the output: the caller's list gained 'Ravi'). Re-binding the parameter (<font name='DVM'>passengers = []</font>) "
        "would not affect the caller. To protect the caller, pass a copy."])
    story += img("q2_memory.png", 15.5, "Fig. 2 - Memory diagram of [[0]*3]*3 (one shared row) and of the corrected grid "
                                        "(three separate rows).")
    story += [P("<b>Why the bug happens:</b> <font name='DVM'>[0] * cols</font> is evaluated once and "
                "<font name='DVM'>* rows</font> repeats the <i>reference</i> to that single list. The comprehension evaluates "
                "<font name='DVM'>[0] * cols</font> once per row, so each row is a new list.")]
    story += [P("Experimental investigation", H2)]
    m, tm = r["mem"], r["time"]
    story += table([["Test", "Result"],
                    ["Bug shown with is / id()", "bad[0] is bad[1] → True (same id); good[0] is good[1] → False (three ids)"],
                    ["Shallow copy after grid[0][0] = 99", "copy.copy and grid[:] both show 99 (inner row shared); deepcopy unchanged"],
                    ["Replacing a whole row grid[1] = [5,5]", "shallow copy unchanged (outer list was copied)"],
                    [f"sys.getsizeof, {m['n']:,} values", f"list(range(n)): {m['list']:,} B; tuple: {m['tuple']:,} B; "
                                                          f"list built by append: {m['list_appended']:,} B"],
                    ["Creating 1,000,000 values", f"list {ft(tm['create_list'])}; tuple {ft(tm['create_tuple'])}"],
                    ["Indexing 1,000,000 times", f"list {ft(tm['index_list'])}; tuple {ft(tm['index_tuple'])}"]],
                   [5.4 * cm, 11.2 * cm])
    story += [P("<b>Reading the results.</b> <font name='DVM'>getsizeof</font> measures only the container (a block of 8-byte "
                "references), not the integers it points to. A tuple needs exactly that block (8,000,040 bytes); a list built by "
                f"<font name='DVM'>list(range(n))</font> is almost the same (+16 bytes of header), but a list that has grown by "
                f"<font name='DVM'>append</font> keeps spare capacity and is {m['list_appended'] - m['tuple']:,} bytes "
                f"({(m['list_appended'] - m['tuple']) / m['list_appended'] * 100:.1f}%) bigger. Small tuples are 16 bytes smaller "
                "than small lists. Creation and indexing times are practically equal; the differences are within measurement noise, so "
                "the real reasons to choose a tuple are meaning and safety, not speed.")]
    story += [P("<b>A list inside a tuple.</b> For <font name='DVM'>t = ([1, 2], 'route-5')</font>: "
                "<font name='DVM'>t[0].append(3)</font> works; <font name='DVM'>t[0] = [9]</font> raises "
                "<font name='DVM'>TypeError: 'tuple' object does not support item assignment</font>; and "
                "<font name='DVM'>t[0] += [4]</font> raises the same error <i>but the list inside has already been extended</i> "
                "(<font name='DVM'>([1, 2, 3, 4], 'route-5')</font>). Explanation: a tuple is immutable in <i>which objects it holds</i>, "
                "not in the contents of those objects. <font name='DVM'>+=</font> first extends the list in place (list "
                "<font name='DVM'>__iadd__</font>) and only then tries to store the result back into the tuple, which fails.")]
    story += [P("Conclusion", H2),
              P("Use a tuple for a fixed record of a few related values (a coordinate pair, a database row, a function's multiple "
                "return values) and whenever the value must be a dictionary key or set member; use a list for a collection that "
                "grows or changes. Immutability protects against accidental modification through aliases and function calls, makes "
                "the value hashable, and tells the reader that the record is not meant to change. (It protects only the tuple itself; "
                "mutable objects stored inside remain mutable.)")]
    story += [P("Complete the Code (Q2/complete_the_code.py)", H2),
              P("TODO 1 was replaced by <font name='DVM'>good = [[0] * cols for _ in range(rows)]</font>; the rest of the program was not "
                "changed. The output is identical to the expected output."), outputs("Q2/complete_output.txt"),
              P("<b>List as a dictionary key:</b> the last line shows <font name='DVM'>TypeError: unhashable type: 'list'</font>. "
                "Lists define <font name='DVM'>__hash__ = None</font> because their contents (and so any hash computed from them) "
                "can change.")]
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>Dictionary keyed by (row, col) tuples holding only non-empty zones.</b> Boarding a passenger becomes "
                "<font name='DVM'>zones[(r, c)] = zones.get((r, c), 0) + 1</font>; a zone that is not in the dictionary has 0 passengers "
                "(<font name='DVM'>zones.get(key, 0)</font>).")]
    g = r["grid_mem"]
    story += table([["Design", "Access time", "Space", f"Measured ({g['cells']:,} zones, 1,000 boardings)"],
                    ["List of lists", "O(1) average and worst (two index steps)", "O(rows × cols)", f"{g['dense']:,} bytes"],
                    ["Dict keyed by (row, col)", "O(1) average (hash of the tuple)", "O(number of non-empty zones)",
                     f"{g['sparse']:,} bytes for {g['entries']} entries"]], [3.4 * cm, 4.8 * cm, 3.8 * cm, 4.6 * cm])
    story += [P("The dictionary needs about " + f"{g['sparse'] / g['dense'] * 100:.1f}%" + " of the memory when few zones are active. If most zones are non-empty the "
                "dictionary would use <i>more</i> memory per zone (hash table plus tuple keys), so the list of lists is better for "
                "dense grids. Iterating over only the busy zones is O(k) for the dictionary and O(rows × cols) for the list.")]
    story.append(PageBreak())


def q3(story):
    r = load("Q3")
    story += [P("Q3 - Dictionaries: Farmer Helpline Complaint Analysis (K4 - Analyse, 7 marks)", H1), P("Implementation", H2),
              P("Text is lower-cased and split with a regular expression so that 'Seeds,' and 'seeds' are the same word; common words "
                "are removed with a set of stop words; counts are stored in a dictionary with <font name='DVM'>get()</font> and, "
                "alternatively, <font name='DVM'>setdefault()</font>; complaints are grouped with "
                "<font name='DVM'>setdefault(key, []).append(...)</font>; the top k use "
                "<font name='DVM'>sorted(..., key=lambda p: (-p[1], p[0]))</font>.")]
    story.append(code(funcs("Q3/complaints.py", {"words_of", "freq_get", "freq_setdefault", "freq_listcount", "freq_counter",
                                                 "top_k", "group_by"})))
    story += [P("Output (Q3/complaints.py, first part)", H2), code("\n".join(read("Q3/output.txt").split("\n")[:20]))]
    story += [P("Design and analysis", H2)]
    story += bullets([
        "<b>How a dictionary finds a key.</b> Python computes <font name='DVM'>hash(key)</font>, uses it to choose a slot in an internal "
        "array, and compares the stored key (first by identity or hash, then by <font name='DVM'>==</font>); if the slot holds a different key it "
        "probes the next slot. The table is resized so that it is never more than about two-thirds full, so the expected number of "
        "probes is a small constant. The cost therefore does not depend on how many keys there are: O(1) on average (O(n) only in the "
        "worst case where all keys collide).",
        "<b>Dictionary versus list.count().</b> The dictionary reads each word once, so n words cost O(n). With "
        "<font name='DVM'>list.count(w)</font> for every distinct word, each call scans all n words: d distinct words cost O(n·d).",
        "<b>Order of keys (Python 3.7+).</b> A dictionary keeps keys in insertion order (this is guaranteed by the language). Updating the "
        "value of an existing key does not move it. The order of first appearance is not the order of frequency, so sorting is needed for "
        "the top-k report.",
        "<b>Views.</b> <font name='DVM'>keys()</font>, <font name='DVM'>values()</font> and <font name='DVM'>items()</font> return view "
        "objects that are <i>live</i> (they show later changes - demonstrated in the program: after adding 'c' the earlier keys view "
        "contains it), do not copy the data, support iteration, <font name='DVM'>len</font> and <font name='DVM'>in</font>; "
        "keys and items views behave like sets. They cannot be indexed; use <font name='DVM'>list(d.items())</font> for that."])
    story += [P("Experimental investigation", H2)]
    story += table([["Complaints", "Words", "dict + get()", "setdefault()", "Counter", "list.count()", "list.count / dict"]] +
                   [[f"{d['n']:,}", f"{d['words']:,}", ft(d["dict_get"]), ft(d["setdefault"]), ft(d["counter"]),
                     ft(d["list_count"]), f"{d['list_count'] / d['dict_get']:.1f}×"] for d in r["timing"]],
                   [2.2 * cm, 2.1 * cm, 2.4 * cm, 2.4 * cm, 2.2 * cm, 2.6 * cm, 2.7 * cm])
    story += img("q3_timing.png", 10, "Fig. 3 - Word counting for 1,000, 10,000 and 100,000 generated complaints.")
    story += [P("All four methods returned identical dictionaries (asserted in the program). The dictionary loop and "
                "<font name='DVM'>Counter</font> have the same O(n) growth and almost the same speed (Counter's advantage is shorter code "
                "and <font name='DVM'>most_common</font>). <font name='DVM'>list.count()</font> is also linear <i>here</i> only because "
                "the vocabulary is fixed at d ≈ 100 words; its cost is n × d, so it falls further behind as the vocabulary grows "
                "(real complaint text has thousands of distinct words). It is competitive at this size because "
                "<font name='DVM'>count</font> runs in C.")]
    story += [P("<b>Edge-case tests.</b>")] + table([
        ["Input", "Result"],
        ["empty text ''", "{} and top-k = [] (no error)"],
        ["no complaints at all", "{}"],
        ["'Seeds SEEDS seeds'", "{'seeds': 3} (case ignored)"],
        ["'price, price. price!'", "{'price': 3} (punctuation ignored)"],
        ["only stop words", "{}"]], [5.2 * cm, 11.4 * cm])
    story += [P("Engineering decision", H2),
              P("For 100,000 complaints a day I would deploy <b>collections.Counter</b> (or the equivalent dictionary loop), after "
                "normalising the text. It is O(n) in time and O(d) in space, reads the data once (so it also works on a stream), is "
                f"short and well tested, and processed 100,000 complaints in {ft(r['timing'][-1]['counter'])} here. "
                "<font name='DVM'>list.count()</font> costs O(n·d) and would become impractical with a realistic vocabulary: with "
                "750,000 words and 20,000 distinct words it needs about 1.5 × 10<super>10</super> comparisons. "
                "For the report, <font name='DVM'>Counter.most_common(k)</font> (heap-based, O(d log k)) avoids sorting the whole "
                "vocabulary.")]
    story += [P("Complete the Code (Q3/complete_the_code.py)", H2),
              P("TODO 1 uses <font name='DVM'>counts[word] = counts.get(word, 0) + 1</font> for every word not in the stop set; TODO 2 sorts "
                "the items with <font name='DVM'>key=lambda pair: (-pair[1], pair[0])</font> and slices the first k."),
              code(funcs("Q3/complete_the_code.py", {"frequencies", "top"})), outputs("Q3/complete_output.txt"),
              P("<b>Why 'price' comes before 'received'.</b> Both occur twice, so the first part of the sort key, the negative count, is equal "
                "(−2). The second part, the word, breaks the tie alphabetically, and 'price' &lt; 'received' because 'p' comes before "
                "'r'. 'seeds' (3) comes first because −3 is smaller than −2.")]
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>list.count() for every distinct word, or Counter.</b> With a list: build <font name='DVM'>words</font>, then "
                "<font name='DVM'>{w: words.count(w) for w in set(words)}</font>. With Counter: "
                "<font name='DVM'>Counter(words)</font>.")]
    story += table([["Method", "Time (n words, d distinct)", "Extra space", "Measured at 100,000 complaints"],
                    ["dictionary loop with get()", "O(n) average", "O(d)", ft(r["timing"][-1]["dict_get"])],
                    ["Counter", "O(n) average", "O(d)", ft(r["timing"][-1]["counter"])],
                    ["list.count() per distinct word", "O(n·d)", "O(n) for the word list + O(d)", ft(r["timing"][-1]["list_count"])]],
                   [4.4 * cm, 4.2 * cm, 4.2 * cm, 3.8 * cm])
    story.append(PageBreak())


def q4(story):
    r = load("Q4")
    story += [P("Q4 - Sets: Elective Registration Clash Detection (K4 - Analyse, 7 marks)", H1), P("Implementation", H2),
              P("Register numbers of each elective are stored in a set, which removes duplicate registrations automatically. Union "
                "(<font name='DVM'>|</font>), intersection (<font name='DVM'>&amp;</font>), difference (<font name='DVM'>-</font>) and symmetric "
                "difference (<font name='DVM'>^</font>) give the reports, which are printed with <font name='DVM'>sorted()</font> "
                "because a set has no order.")]
    story.append(code(funcs("Q4/electives.py", {"report"})))
    story += [P("Output (Q4/electives.py, first part)", H2), code("\n".join(read("Q4/output.txt").split("\n")[:27]))]
    story += [P("Design and analysis", H2)]
    story += img("q4_venn.png", 15, "Fig. 4 - Venn diagrams of the six results (shaded = result). A = AI elective, B = IoT elective, "
                                    "U = all students.")
    story += bullets([
        "<b>Why sets remove duplicates.</b> A set is a hash table of unique elements. Adding an element that is already present "
        "(same hash and equal value) finds the existing entry, so no second entry is made.",
        "<b>Why x in s is faster for a set.</b> A set computes the hash and looks at one slot: O(1) on average. A list compares x with "
        "elements one by one: O(n). For the last element of 1,000,000 numbers the set was about "
        f"{r['membership'][-1]['list'] / r['membership'][-1]['set']:,.0f} times faster in the measurement below.",
        "<b>Lists cannot be in sets, tuples can.</b> Set elements must be hashable. A list is mutable and unhashable "
        "(<font name='DVM'>TypeError: unhashable type: 'list'</font>, shown in the edge-case test); a tuple of hashable values is "
        "immutable and hashable (<font name='DVM'>{(1, 2), (1, 2), (3, 4)}</font> keeps two elements)."])
    story += [P("Experimental investigation", H2)]
    story += table([["n register numbers", "x in list (last element)", "x in set", "Speed-up"]] +
                   [[f"{d['n']:,}", ft(d["list"]), ft(d["set"]), f"{d['list'] / d['set']:,.0f}×"] for d in r["membership"]],
                   [4 * cm, 4.4 * cm, 3.6 * cm, 3.6 * cm])
    story += table([["n (each list)", "Nested loops", "Sort + walk", "Set &"]] +
                   [[f"{d['n']:,}", ft(d["nested"]), ft(d["sorted"]), ft(d["set"])] for d in r["common"]],
                   [4 * cm, 4.2 * cm, 4.2 * cm, 4.2 * cm])
    story += img("q4_timing.png", 15, "Fig. 5 - Left: membership test (list grows linearly, set stays flat). Right: common students: "
                                      "nested loops grow with n², the other two with about n.")
    story += [P("List lookup time grows 10 times for every 10 times more data (O(n)); set lookup stays almost constant (O(1)). "
                f"For nested loops, doubling n multiplies the time by about 4 ({ft(r['common'][1]['nested'])} → {ft(r['common'][2]['nested'])} → "
                f"{ft(r['common'][3]['nested'])} for n = 1,000, 2,000, 4,000): O(n²). "
                "The results of all three methods were checked to be identical. Hand-verified small case "
                "(A = {1,2,3}, B = {3,4}, U = {1…5}): A∩B = {3}, A−B = {1,2}, B−A = {4}, A∆B = {1,2,4}, A∪B = {1,2,3,4}, "
                "U−(A∪B) = {5}; the program output matches all six (see source output). Other tests: both electives empty "
                "(no clash, all 10 students in 'neither'), identical electives (all students clash, none in 'exactly one').")]
    story += [P("Conclusion", H2),
              P("Convert a list to a set before processing when you need many membership tests, duplicate removal or set algebra such as "
                "clash detection. The conversion loses <b>duplicates</b> (how many times a value occurred), <b>order</b> (the "
                "position of elements) and requires every element to be hashable. If counts are needed use "
                "<font name='DVM'>Counter</font>; if order matters use <font name='DVM'>dict.fromkeys(items)</font>.")]
    story += [P("Complete the Code (Q4/complete_the_code.py)", H2),
              code(read("Q4/complete_the_code.py").split("# TODO 1")[1].split("print(")[0].replace(
                  ": Use set operators to find: students in both electives, students in exactly\n# one, and students in neither\n", "# TODO 1: Use set operators ...\n")),
              outputs("Q4/complete_output.txt"),
              P("The program also contains TODO 1 rewritten with the methods <font name='DVM'>intersection</font>, "
                "<font name='DVM'>symmetric_difference</font>, <font name='DVM'>difference</font> and <font name='DVM'>union</font>; the last "
                "output line confirms <font name='DVM'>True True True</font> (identical results).")]
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>Lists with nested loops, or sorted lists walked together.</b> Nested loops compare every pair. For the sorted walk both lists "
                "are sorted, then two indexes move forward: advance the smaller one, record equal values.")]
    story.append(code(funcs("Q4/electives.py", {"common_nested", "common_sorted_walk"})))
    story += table([["Approach", "Time (lists of n and m)", "Extra space"],
                    ["nested loops", "O(n·m)", "O(1) besides the result"],
                    ["sort both lists and walk", "O(n log n + m log m)", "O(n + m) for sorted copies (O(1) if sorted in place)"],
                    ["sets and &amp;", "O(n + m) average (build both sets, then iterate the smaller)", "O(n + m) for the two sets"]],
                   [4.2 * cm, 6.4 * cm, 6 * cm])
    story.append(PageBreak())


def q5_text(r):
    last = r["timing"][-1]
    ranked = sorted([("the plain for loop", last["loop"]), ("the list comprehensions", last["comp"]),
                     ("map/filter with lambda", last["mapfilter"])], key=lambda p: p[1])
    return ("<b>No, a list comprehension is not always the best choice.</b> At 1,000,000 readings the order from fastest to slowest was "
            + ", ".join(f"{n} ({ft(t)})" for n, t in ranked) + ". ")


def q5(story):
    r = load("Q5")
    story += [P("Q5 - List Comprehension: Cleaning Sensor Readings (K3 - Apply, 6 marks)", H1), P("Implementation", H2),
              P("Three versions clean the readings (valid range −50 °C to 50 °C), convert to Fahrenheit (F = C × 9/5 + 32) and "
                "list the alarm minutes (valid readings outside 2-8 °C) with <font name='DVM'>enumerate()</font>.")]
    story.append(code(funcs("Q5/sensors.py", {"clean_loop", "clean_comp", "clean_mapfilter"})))
    story += [P("Output (Q5/sensors.py, first part)", H2), code("\n".join(read("Q5/output.txt").split("\n")[:26]))]
    story += [P("Design and analysis", H2)]
    story += bullets([
        "<b>General form:</b> <font name='DVM'>[expression for item in iterable if condition]</font>. For example "
        "<font name='DVM'>[c * 9/5 + 32 for c in readings if -50 &lt;= c &lt;= 50]</font>.",
        "<b>When a comprehension is harder to read than a loop:</b> when it has several nested loops or conditions, a long expression, "
        "or needs several results or side effects (printing, updating counters) in one pass - then a loop with clear names is easier to read and "
        "debug.",
        "<b>Dictionary comprehension:</b> <font name='DVM'>{minute: c for minute, c in enumerate(readings) if -50 &lt;= c &lt;= 50}</font> "
        "(minute → valid reading). <b>Set comprehension:</b> <font name='DVM'>{round(c) for c in valid}</font> (distinct whole-degree values).",
        "<b>List comprehension versus generator expression:</b> square brackets build the whole list in memory at once; round brackets "
        "create a generator that produces one value at a time when asked, so it uses almost no memory, but it can be used only once, "
        "cannot be indexed and has no <font name='DVM'>len</font>."])
    story += [P("Experimental investigation", H2)]
    story += table([["Readings", "for + append", "list comprehensions", "map / filter + lambda"]] +
                   [[f"{d['n']:,}", ft(d["loop"]), ft(d["comp"]), ft(d["mapfilter"])] for d in r["timing"]],
                   [3.5 * cm, 4 * cm, 4.6 * cm, 4.5 * cm])
    story += img("q5_timing.png", 10, "Fig. 6 - Time for the three versions (log scale); results are identical in every run.")
    m = r["mem"]
    story += [P(f"<b>Memory (1,000,000 readings, {m['items']:,} valid):</b> list comprehension "
                f"<font name='DVM'>sys.getsizeof</font> = {m['list']:,} bytes; generator expression = {m['gen']} bytes (independent of n). "
                f"Summing the valid readings took {ft(r['sum']['list'])} with a list and {ft(r['sum']['gen'])} with a generator.")]
    story += [P("<b>Tests.</b> The three versions return identical lists for the sample, for all-valid readings (no alarms), for "
                "all-invalid readings (empty results) and for an empty list; this is asserted in the program and in the timing runs.")]
    story += [P("Conclusion", H2),
              P(q5_text(r) + "A plain loop can win because it produces the Celsius list, the Fahrenheit list and the alarms in <i>one pass</i> over the data, "
                "while the comprehension version makes three separate passes; the lambda-based <font name='DVM'>map/filter</font> pays for a Python function "
                "call for every element. Comprehensions are usually a little faster than an append loop doing the <i>same</i> work and are "
                "short and clear for one simple transformation, but a loop is better when several results are built together, when there are side "
                "effects, or when the logic is complicated. When the result is only consumed once (a sum, a count, a "
                f"loop), a generator expression avoids storing {m['list'] / 1e6:.1f} MB.")]
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>Generator expression.</b> <font name='DVM'>sum(c for c in readings if -50 &lt;= c &lt;= 50)</font> gives the total without "
                "building the list of valid readings. The elements are produced one at a time and consumed immediately by "
                "<font name='DVM'>sum</font>.")]
    story += table([["Approach", "Time", "Memory", "Measured (1,000,000 readings)"],
                    ["list comprehension (then sum)", "O(n)", "O(n) for the list", f"{ft(r['sum']['list'])}, {m['list']:,} bytes"],
                    ["generator expression", "O(n)", "O(1)", f"{ft(r['sum']['gen'])}, {m['gen']} bytes"]],
                   [4.6 * cm, 2.2 * cm, 3.6 * cm, 6.2 * cm])
    story += [P("Both examine every reading once (O(n)); the generator trades a small per-item overhead for constant memory, so the "
                "times are almost equal while the memory differs by a factor of about "
                f"{m['list'] // max(m['gen'], 1):,}.")]
    story.append(PageBreak())


def q6(story):
    r = load("Q6")
    story += [P("Q6 - Nested Data: A Railway Timetable (K4 - Analyse, 7 marks)", H1), P("Implementation", H2),
              P("<font name='DVM'>timetable[train_no]</font> is a dictionary with the keys <font name='DVM'>'name'</font>, "
                "<font name='DVM'>'stops'</font> (a list of <font name='DVM'>(station, arrival, departure)</font> tuples) and "
                "<font name='DVM'>'days'</font> (a set). Five sample trains are used (illustrative data, not the official timetable).")]
    story.append(code(funcs("Q6/railway.py", {"print_timetable", "trains_at_scan", "build_index", "trains_at_indexed"})))
    story += [P("Output (Q6/railway.py, first part)", H2), code("\n".join(read("Q6/output.txt").split("\n")[:62]))]
    story += [P("Design and analysis", H2)]
    story += img("q6_nested.png", 15.5, "Fig. 7 - The nested structure and the expression for the departure time of the third station.")
    story += bullets([
        "<b>Expression:</b> <font name='DVM'>timetable[12001]['stops'][2][2]</font> → <font name='DVM'>'10:35'</font>: the train's "
        "dictionary, its list of stops, the third stop (index 2), the departure field of the tuple (index 2).",
        "<b>Why each type.</b> <i>Dictionary</i> for the train record and for train numbers: a unique key, fast O(1) lookup, named fields. "
        "<i>List</i> for the stops: the order of stations along the route matters. <i>Tuple</i> for one stop: a fixed record of three "
        "values that should not change and needs no name. <i>Set</i> for the running days: only membership matters ('Fri' in days), "
        "no duplicates, no order.",
        "<b>Work for one station query (no index).</b> Every train and every stop of it may be examined: with T trains and about S stops "
        "per train that is O(T·S) = O(N), where N is the total number of stops, then sorting the k matching trains costs O(k log k).",
        "<b>Index design:</b> a dictionary <font name='DVM'>station → list of train numbers</font>, built once in O(N) by "
        "<font name='DVM'>setdefault(station, []).append(train_no)</font>. A query then looks at only the k trains that stop there: "
        "O(1) lookup + O(k·S) to read their stop lists (S is small) + O(k log k) to sort."])
    story += [P("Experimental investigation", H2)]
    story += table([["Trains", "Total stops", "Nested scan / query", "Flat list / query", "With index / query", "Speed-up vs nested",
                     "Index build", "Extra memory"]] +
                   [[f"{d['trains']:,}", f"{d['stops']:,}", ft(d["scan"]), ft(d["flat"]), ft(d["indexed"]),
                     f"{d['scan'] / d['indexed']:.1f}×", ft(d["build"]), f"{d['index_bytes'] / 1024:,.0f} KiB"] for d in r["timing"]],
                   [1.5 * cm, 1.9 * cm, 2.4 * cm, 2.2 * cm, 2.3 * cm, 2.1 * cm, 2.0 * cm, 2.2 * cm], font=7)
    story += img("q6_timing.png", 15, "Fig. 8 - Average time per station query (200 random queries) and memory used by the index.")
    story += [P("Without the index the time per query grows 10 times for every 10 times more trains (O(N)), as derived. With the index the "
                "growth is also linear in this experiment, because each station is served by a fixed fraction of the trains (12 stops "
                "per train out of 300 stations, so about 4% of trains stop at a given station); the index removes the work for the other "
                f"96% of the trains and is {min(d['scan'] / d['indexed'] for d in r['timing']):.0f} to {max(d['scan'] / d['indexed'] for d in r['timing']):.0f} times faster. The index is built once (a few ms) and uses memory proportional to the "
                "number of stops. Tests: unknown station → empty list; a train that does not run on the requested day is not "
                "listed (12003 is absent for Katpadi on Sunday); an invalid day → empty list; answers of all methods agree on "
                "50 random queries per size. Note: sorting uses the 'HH:MM' text, so an overnight stop such as 01:40 sorts as early morning; "
                "a real system would add a day offset.")]
    story += [P("Conclusion", H2),
              P("An index makes each query faster because the work of finding which trains stop at a station is done once, in advance, and "
                "stored in a dictionary; each query then jumps straight to those trains instead of examining every stop. The trade-off is "
                "<b>extra memory</b> (one entry per stop) and <b>extra work to keep the index up to date</b> whenever a train is added, removed "
                "or its stops change; it pays off when queries are much more frequent than timetable changes, as at an enquiry counter.")]
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>One flat list of tuples scanned for every query.</b> "
                "<font name='DVM'>flat = [(train, station, arrival, departure, days), ...]</font>; a query scans every tuple and keeps those with the "
                "right station and a day in <font name='DVM'>days</font> (function <font name='DVM'>trains_at_flat</font>).")]
    story.append(code(funcs("Q6/railway.py", {"flat_list", "trains_at_flat"})))
    story += table([["Design", "Time per query", "Space"],
                    ["flat list of tuples, scanned", "O(total stops N), always the whole list", "O(N) tuples; train data repeated on every row"],
                    ["nested dicts, no index", "O(N) worst case, but trains not running that day are skipped without reading stops",
                     "O(T + N): one record per train + the stop tuples"],
                    ["nested dicts + station index", "O(k) trains at the station (plus O(k log k) sort)", "O(T + N) + O(N) for the index"]],
                   [4.4 * cm, 6.3 * cm, 5.9 * cm])
    flat_slower = all(d["flat"] > d["scan"] for d in r["timing"])
    story += [P(("In the measurements the flat list was a little slower than the nested scan at every size (it cannot skip a train that does "
                 "not run on the day)" if flat_slower else "In the measurements the flat list and the nested scan took similar time (both are O(N))")
                + f" and both were {min(d['scan'] / d['indexed'] for d in r['timing']):.0f} to "
                  f"{max(d['flat'] / d['indexed'] for d in r['timing']):.0f} times slower than the indexed design.")]
    story.append(PageBreak())


def q7(story):
    r = load("Q7")
    story += [P("Q7 - Design a Contact-Merging Program from First Principles (K5 - Evaluate, 10 marks)", H1)]
    story += [P("Stage 1 - Interpret the problem (2 marks)", H2)]
    story += bullets([
        "<b>Input:</b> contacts from two phones and a SIM card; each record has a name (any spelling), zero or more phone numbers "
        "(any format) and zero or more e-mail addresses. <b>Output:</b> a list in which every person appears once, with all their "
        "numbers (normalised) and e-mail addresses and one display name.",
        "<b>Rule for 'same person':</b> two records are the same person if they share at least one normalised phone number; this is "
        "transitive (if A shares a number with B and B shares one with C, all three are one person). A record with no number is matched by "
        "e-mail address (case-insensitive). The <i>name is not used</i> to decide: the same person is written many ways and different "
        "people share names.",
        "<b>Data structures:</b> list of dictionaries for input and output; a dictionary <font name='DVM'>owner</font> (normalised number → group id) for "
        "O(1) matching; a dictionary <font name='DVM'>groups</font> (id → record); <i>sets</i> inside each record for names, numbers and e-mails so that "
        "duplicates vanish.",
        "<b>Measurable requirements:</b> R1 every normalised number appears in exactly one output person. R2 no number is lost "
        "(set of output numbers = set of normalised input numbers). R3 the formats '+91 98400 12345', '9840012345', '098400-12345', "
        "'91 9840012345' give the same key. R4 two different people with the same name stay separate unless they share a number. "
        f"R5 100,000 contacts are merged in under 5 s (measured {ft(r['dict_timing'][1]['dict'])}). R6 empty input and records with missing "
        "fields do not crash."])
    story += [P("Stage 2 - Design (3 marks)", H2), P("<b>Normalisation.</b> Number: keep only digits; remove a leading 00; if 12 digits start "
                "with 91 drop the 91; if 11 digits start with 0 drop the 0; accept if at least 6 digits remain. Name: lower-case, keep letters, "
                "drop titles (dr, mr, mrs, ms, prof, …), join with single spaces. E-mail: strip and lower-case.")]
    story.append(code("""FUNCTION merge(contacts)
    owner  <- empty dictionary          // key (normalised number or "mail:"+email) -> group id
    groups <- empty dictionary          // group id -> {names, numbers, emails, keys}  (all sets)
    FOR EACH contact c IN contacts
        keys <- { normalise_number(x) FOR x IN c.numbers, if valid }
        IF keys is empty THEN keys <- { "mail:" + normalise_email(e) FOR e IN c.emails }
        hit  <- { owner[k] FOR k IN keys IF k IN owner }          // groups already known for these keys
        IF hit is empty THEN g <- new empty group
        ELSE
            g <- the largest group in hit
            FOR EACH other group h IN hit, h != g           // c links two earlier groups: join them
                add all sets of h to g;  FOR k IN h.keys: owner[k] <- g;  delete h
        add normalise_name(c.name), c's normalised numbers and e-mails TO g's sets
        add keys TO g.keys;  FOR k IN keys: owner[k] <- g
    RETURN groups, each with its longest normalised name as display name, numbers and e-mails sorted"""))
    story += [P("Stage 3 - Implement and measure (3 marks)", H2)]
    story.append(code(funcs("Q7/contacts.py", {"norm_number", "norm_name", "keys_of", "merge_dict"})))
    story += [P("<b>Hand-verified test.</b> Nine records were written by hand: three records for Ravi Kumar (formats '+91 98400 12345', "
                "'9840012345' + '98400 99999', '098400-12345', e-mails 'Ravi@Mail.com' and 'ravi@mail.com'), two for Asha (same number in two "
                "formats), a different 'Ravi' with 9876543210, two records with no number sharing one e-mail in different letter cases, and an "
                "empty record. The correct answer by hand is 5 people; the program gives exactly 5 and the same result as the pairwise method. "
                "Another test shows that a record holding two numbers joins two earlier groups into one person.")]
    story.append(code("\n".join(read("Q7/output.txt").split("\n")[:25])))
    pt = r["pair_timing"]
    story += table([["Test", "Result"],
                    ["Duplicates in different formats", "merged into one person (R3)"],
                    ["Missing fields (no number / no name / empty)", "merged by e-mail, or kept as separate records, no crash (R6)"],
                    ["Empty input", "[]"],
                    ["Two numbers in one record bridging two groups", "one person"],
                    ["100,000 contacts: numbers lost / repeated", f"lost: {not r['checks']['no_number_lost']}, repeated: {not r['checks']['no_number_repeated']} (R1, R2 met)"]],
                   [7 * cm, 9.6 * cm])
    story += table([["Contacts n", "People found", "Time (dictionary design)"]] +
                   [[f"{d['n']:,}", f"{d['people']:,}", ft(d["dict"])] for d in r["dict_timing"]], [4 * cm, 4 * cm, 5 * cm])
    story += [P("Stage 4 - Defend the design (2 marks)", H2)]
    story += bullets([
        "<b>Dictionary versus comparing every pair.</b> Comparing every pair needs n(n − 1)/2 comparisons, O(n²), which is "
        f"{100_000 * 99_999 // 2:,} comparisons for 100,000 contacts. The dictionary finds the earlier owner of a number in O(1) average, so each contact "
        "is handled once: O(n) in total (see the measurements below).",
        "<b>Two different people with the same name.</b> The name is never used as a key, so 'Ravi' (9876543210) and 'Ravi Kumar' (9840012345) "
        "stay separate; they merge only if they share a normalised number. The output keeps their numbers, so the user can tell them apart.",
        "<b>A remaining limitation.</b> Matching depends on shared numbers or e-mails. The same person with a different number on each phone and no "
        "common number or e-mail is shown twice (a missed merge), and two people who really share a number (a family landline, an office "
        "board) are wrongly merged. A fuller solution would add name similarity as a <i>suggestion</i> for the user to confirm."])
    story += [P("Alternative concept and complexity analysis", H2),
              P("<b>Compare every pair of contacts.</b> For each pair (i, j) test whether the key sets intersect and join the two records with a "
                "union-find structure (function <font name='DVM'>merge_pairwise</font>).")]
    story.append(code(funcs("Q7/contacts.py", {"merge_pairwise"})))
    story += table([["Contacts n", "Pairwise (measured)", "Dictionary (measured)", "Ratio"]] +
                   [[f"{d['n']:,}", ft(d["pairwise"]), ft(d["dict"]), f"{d['pairwise'] / d['dict']:.0f}×"] for d in pt] +
                   [["100,000", f"≈ {r['extrapolated_pairwise_100k'] / 60:.1f} min (extrapolated from n = 4,000 by (n/4000)²)",
                     ft(r["dict_timing"][1]["dict"]) + " (measured)", f"≈ {r['extrapolated_pairwise_100k'] / r['dict_timing'][1]['dict']:.0f}×"]],
                   [3 * cm, 7 * cm, 4 * cm, 2.6 * cm], font=7.4)
    story += img("q7_timing.png", 10, "Fig. 9 - Pairwise comparison grows with n² (steeper line); the dictionary grows with n.")
    story += table([["Approach", "Time", "Space (n contacts)"],
                    ["every pair + union-find", f"O(n²) comparisons (time ×{pt[3]['pairwise'] / pt[2]['pairwise']:.1f} when n doubles: {ft(pt[2]['pairwise'])} → {ft(pt[3]['pairwise'])} from n = 2,000 to 4,000)", "O(n) for the keys and parents"],
                    ["dictionary keyed by normalised number", "O(n) on average (each contact does a constant number of lookups)",
                     "O(n) for the dictionaries and sets"]], [4.4 * cm, 8.4 * cm, 3.8 * cm], font=7.4)
    story += [P("The 100,000-contact pairwise figure is an extrapolation, clearly marked; it was not run because it needs about "
                "5 × 10<super>9</super> comparisons. The dictionary run was measured. At every size where both were measured the "
                "two methods produced identical groups.")]


def build_report(path):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.5 * cm,
                            bottomMargin=1.7 * cm, title="Python Programming - Assignment 3 (CO3) - Report",
                            author=args.name)
    story = []
    cover(story)
    for fn in (q1, q2, q3, q4, q5, q6, q7):
        fn(story)
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


def build_code(path):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.5 * cm,
                            bottomMargin=1.7 * cm, title="Python Programming - Assignment 3 (CO3) - Source code",
                            author=args.name)
    story = []
    cover(story, second=True)
    story += [P("How to run", H1), P("Repository folders: Q1 … Q7, one folder per task. From the repository root:"),
              code("python run_all.py\npython build_report.py --github <repository URL>\n\n"
                   "# or one program at a time, for example\ncd Q3\npython complete_the_code.py\npython complaints.py"),
              P("Only the Python standard library is needed to run the programs (Python " + PYVER + "); "
                "<font name='DVM'>requirements.txt</font> lists matplotlib and reportlab, which are used only to draw the graphs and build the PDFs. "
                "Results of each task: see the 'Output' and measurement tables in the report; each program prints the complete evidence "
                "and checks its own results with <font name='DVM'>assert</font>."), PageBreak()]
    files = [("Q1", "rainfall.py", "output.txt"), ("Q2", "complete_the_code.py", "complete_output.txt"),
             ("Q2", "bus_stops.py", "output.txt"), ("Q3", "complete_the_code.py", "complete_output.txt"),
             ("Q3", "complaints.py", "output.txt"), ("Q4", "complete_the_code.py", "complete_output.txt"),
             ("Q4", "electives.py", "output.txt"), ("Q5", "sensors.py", "output.txt"), ("Q6", "railway.py", "output.txt"),
             ("Q7", "contacts.py", "output.txt")]
    for folder, py, out in files:
        story += [P(f"{folder}/{py}", H1), code(read(f"{folder}/{py}"), 120), P(f"Output of {folder}/{py}", H2),
                  code(read(f"{folder}/{out}"), 120), PageBreak()]
    doc.build(story[:-1], onFirstPage=page_number, onLaterPages=page_number)


if __name__ == "__main__":
    make_figures.make_all()
    out = os.path.join(ROOT, "submission")
    os.makedirs(out, exist_ok=True)
    build_report(os.path.join(out, "File1_Report_Q1-Q7.pdf"))
    build_code(os.path.join(out, "File2_Source_Code_and_Output.pdf"))
    for f in sorted(os.listdir(out)):
        print(f, round(os.path.getsize(os.path.join(out, f)) / 1024 / 1024, 2), "MB")
