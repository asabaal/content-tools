#!/usr/bin/env python3
"""Generate a fillable Self Employment Income Report PDF with AcroForm fields.

2-page landscape layout:
  Page 1: Title, Section 1, Section 2, Section 4 (Income rows + Expenses rows 1-11)
  Page 2: Section 4 continued (Expenses rows 12-21, Net Totals), Section 3 (Signature)
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor
from reportlab.pdfgen.canvas import Canvas

OUTPUT = "/home/asabaal/Downloads/self_employment_form_fillable.pdf"
PAGE_W, PAGE_H = landscape(letter)

LEFT_MARGIN = 0.5 * inch
RIGHT_MARGIN = 0.5 * inch
TOP_MARGIN = 0.5 * inch
BOTTOM_MARGIN = 0.4 * inch
FIELD_HEIGHT = 16
LABEL_SIZE = 9
HEADER_SIZE = 9
TITLE_SIZE = 14
SECTION_SIZE = 11

COL_LABEL_W = 2.4 * inch
COL_MONTH_W = (PAGE_W - LEFT_MARGIN - RIGHT_MARGIN - COL_LABEL_W) / 3
ROW_H = 18

LIGHT_GREY = HexColor("#f0f0f0")
HEADER_BG = HexColor("#d9e2f3")
SECTION_BG = HexColor("#b4c6e7")


def draw_text(c, text, x, y, font="Helvetica", size=LABEL_SIZE, color=black):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, text)


def draw_field(c, name, x, y, w, h=FIELD_HEIGHT, tooltip=""):
    c.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x,
        y=y,
        width=w,
        height=h,
        borderWidth=0.5,
        borderColor=HexColor("#999999"),
        fillColor=HexColor("#ffffff"),
        textColor=black,
        fontSize=9,
        fieldFlags="",
    )


def draw_cell_box(c, x, y, w, h, fill_color=None):
    if fill_color:
        c.setFillColor(fill_color)
        c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#cccccc"))
    c.setLineWidth(0.5)
    c.rect(x, y, w, h, stroke=1, fill=0)


MONTHS = ["January 2026", "February 2026", "March 2026"]
MONTH_PREFIXES = ["jan", "feb", "mar"]

INCOME_ROWS = [
    ("Gross receipts and/or sales", "gross_sales"),
    ("Other income", "other_income"),
]

EXPENSE_ROWS = [
    ("Wages and commissions", "wages"),
    ("Employee benefits", "employee_benefits"),
    ("Travel", "travel"),
    ("Vehicle", "vehicle"),
    ("Rent or lease", "rent_lease"),
    ("Repairs and maintenance", "repairs"),
    ("Telephone and utilities", "telephone"),
    ("Materials and supplies", "materials"),
    ("Freight", "freight"),
    ("Legal and professional fees", "legal_fees"),
    ("Advertising", "advertising"),
    ("Taxes (not income tax)", "taxes"),
    ("Insurance", "insurance"),
    ("Capital purchases", "capital_purchases"),
    ("Loan principal payments", "loan_payments"),
    ("Depreciation", "depreciation"),
    ("Depletion", "depletion"),
    ("Amortization", "amortization"),
    ("Other expenses 1", "other_expenses_1"),
    ("Other expenses 2", "other_expenses_2"),
    ("Other expenses 3", "other_expenses_3"),
]

EXPENSE_PAGE_BREAK = 11  # rows 0-10 on page 1, rows 11-20 on page 2


def draw_table_header(c, y):
    table_left = LEFT_MARGIN
    draw_cell_box(c, table_left, y - ROW_H, COL_LABEL_W, ROW_H, fill_color=HEADER_BG)
    draw_text(c, "Category", table_left + 4, y - ROW_H + 4, font="Helvetica-Bold", size=HEADER_SIZE)
    for i, month in enumerate(MONTHS):
        col_x = table_left + COL_LABEL_W + i * COL_MONTH_W
        draw_cell_box(c, col_x, y - ROW_H, COL_MONTH_W, ROW_H, fill_color=HEADER_BG)
        tw = c.stringWidth(month, "Helvetica-Bold", HEADER_SIZE)
        draw_text(c, month, col_x + (COL_MONTH_W - tw) / 2, y - ROW_H + 4,
                  font="Helvetica-Bold", size=HEADER_SIZE)
    return y - ROW_H


def draw_section_header(c, text, y):
    table_left = LEFT_MARGIN
    table_w = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
    draw_cell_box(c, table_left, y - ROW_H, table_w, ROW_H, fill_color=SECTION_BG)
    draw_text(c, text, table_left + 4, y - ROW_H + 4, font="Helvetica-Bold", size=LABEL_SIZE)
    return y - ROW_H


def draw_data_row(c, label, field_key, y):
    table_left = LEFT_MARGIN
    draw_cell_box(c, table_left, y - ROW_H, COL_LABEL_W, ROW_H)
    draw_text(c, "  " + label, table_left + 2, y - ROW_H + 4, size=8)
    for i in range(3):
        col_x = table_left + COL_LABEL_W + i * COL_MONTH_W
        draw_cell_box(c, col_x, y - ROW_H, COL_MONTH_W, ROW_H, fill_color=LIGHT_GREY)
        field_name = f"s4_{MONTH_PREFIXES[i]}_{field_key}"
        tooltip = f"{label} - {MONTHS[i]}"
        draw_field(c, field_name,
                   col_x + 2, y - ROW_H + 1,
                   COL_MONTH_W - 4, FIELD_HEIGHT, tooltip)
    return y - ROW_H


def draw_totals_row(c, y):
    table_left = LEFT_MARGIN
    table_w = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
    draw_cell_box(c, table_left, y - ROW_H, COL_LABEL_W, ROW_H, fill_color=HEADER_BG)
    draw_text(c, "  Net Total (Income - Expenses)", table_left + 2, y - ROW_H + 4,
              font="Helvetica-Bold", size=8)
    for i in range(3):
        col_x = table_left + COL_LABEL_W + i * COL_MONTH_W
        draw_cell_box(c, col_x, y - ROW_H, COL_MONTH_W, ROW_H, fill_color=HEADER_BG)
        field_name = f"s4_{MONTH_PREFIXES[i]}_net_total"
        tooltip = f"Net Total - {MONTHS[i]}"
        draw_field(c, field_name,
                   col_x + 2, y - ROW_H + 1,
                   COL_MONTH_W - 4, FIELD_HEIGHT, tooltip)
    return y - ROW_H


def build_page1(c):
    y = PAGE_H - TOP_MARGIN

    draw_text(c, "Self Employment Income Report \u2013 January to March 2026",
              LEFT_MARGIN, y, size=TITLE_SIZE, font="Helvetica-Bold")
    y -= 16
    draw_text(c, "Providing actual income and expenses for January February March 2026",
              LEFT_MARGIN, y, size=9, color=HexColor("#555555"))
    y -= 26

    draw_text(c, "SECTION 1 \u2013 Personal Information",
              LEFT_MARGIN, y, size=SECTION_SIZE, font="Helvetica-Bold")
    y -= 20

    label_w = 1.1 * inch
    field_w = 2.5 * inch
    col2_left = LEFT_MARGIN + 4.2 * inch

    draw_text(c, "Name:", LEFT_MARGIN, y + 4)
    draw_field(c, "s1_name", LEFT_MARGIN + label_w, y, field_w, FIELD_HEIGHT, "Full Name")
    draw_text(c, "Case Number:", col2_left, y + 4)
    draw_field(c, "s1_case_number", col2_left + 1.1 * inch, y, 2.0 * inch, FIELD_HEIGHT, "Case Number")
    y -= 26

    draw_text(c, "SECTION 2 \u2013 Business Information",
              LEFT_MARGIN, y, size=SECTION_SIZE, font="Helvetica-Bold")
    y -= 20

    draw_text(c, "Business Name:", LEFT_MARGIN, y + 4)
    draw_field(c, "s2_business_name", LEFT_MARGIN + label_w, y, field_w, FIELD_HEIGHT, "Business Name")
    draw_text(c, "Business Type:", col2_left, y + 4)
    draw_field(c, "s2_business_type", col2_left + 1.1 * inch, y, 2.0 * inch, FIELD_HEIGHT, "Business Type")
    y -= 22

    draw_text(c, "Start Date:", LEFT_MARGIN, y + 4)
    draw_field(c, "s2_start_date", LEFT_MARGIN + label_w, y, field_w, FIELD_HEIGHT, "Start Date (MM/DD/YYYY)")
    draw_text(c, "Percent Owned:", col2_left, y + 4)
    draw_field(c, "s2_percent_owned", col2_left + 1.1 * inch, y, 2.0 * inch, FIELD_HEIGHT, "Percent Owned (%)")
    y -= 26

    draw_text(c, "SECTION 4 \u2013 Income and Expenses",
              LEFT_MARGIN, y, size=SECTION_SIZE, font="Helvetica-Bold")
    y -= 8

    y = draw_table_header(c, y)
    y = draw_section_header(c, "Income", y)
    for label, key in INCOME_ROWS:
        y = draw_data_row(c, label, key, y)

    y = draw_section_header(c, "Expenses", y)
    for label, key in EXPENSE_ROWS[:EXPENSE_PAGE_BREAK]:
        y = draw_data_row(c, label, key, y)

    return y


def build_page2(c):
    y = PAGE_H - TOP_MARGIN

    draw_text(c, "Self Employment Income Report \u2013 January to March 2026 (continued)",
              LEFT_MARGIN, y, size=12, font="Helvetica-Bold")
    y -= 8

    y = draw_table_header(c, y)
    y = draw_section_header(c, "Expenses (continued)", y)
    for label, key in EXPENSE_ROWS[EXPENSE_PAGE_BREAK:]:
        y = draw_data_row(c, label, key, y)

    y = draw_totals_row(c, y)
    y -= 24

    draw_text(c, "SECTION 3 \u2013 Signature",
              LEFT_MARGIN, y, size=SECTION_SIZE, font="Helvetica-Bold")
    y -= 22

    draw_text(c, "Typed Name:", LEFT_MARGIN, y + 4)
    draw_field(c, "s3_typed_name", LEFT_MARGIN + 1.1 * inch, y, 3.0 * inch, FIELD_HEIGHT, "Typed Name")
    draw_text(c, "Date:", LEFT_MARGIN + 5.0 * inch, y + 4)
    draw_field(c, "s3_signature_date", LEFT_MARGIN + 5.5 * inch, y, 2.0 * inch, FIELD_HEIGHT, "Date (MM/DD/YYYY)")

    return y


def build_pdf():
    c = Canvas(OUTPUT, pagesize=landscape(letter))
    c.setTitle("Self Employment Income Report - January to March 2026")

    build_page1(c)
    c.showPage()
    build_page2(c)
    c.save()
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
