import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register TrueType fonts for Unicode (₹ symbol) support
FONT_PATH = "C:\\Windows\\Fonts\\times.ttf"
FONT_BOLD_PATH = "C:\\Windows\\Fonts\\timesbd.ttf"

if os.path.exists(FONT_PATH) and os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('TimesNewRoman', FONT_PATH))
    pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', FONT_BOLD_PATH))
    TIMES_ROMAN = 'TimesNewRoman'
    TIMES_BOLD = 'TimesNewRoman-Bold'
else:
    TIMES_ROMAN = 'Times-Roman'
    TIMES_BOLD = 'Times-Bold'

def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='MainHeading', fontName=TIMES_BOLD, fontSize=16, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='SecondaryHeading', fontName=TIMES_BOLD, fontSize=14, spaceAfter=10, spaceBefore=15))
    styles.add(ParagraphStyle(name='NormalText', fontName=TIMES_ROMAN, fontSize=12, spaceAfter=5))
    return styles

def generate_reports_summary_pdf(context, response):
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = _get_styles()
    story = []

    story.append(Paragraph("VEHICLE LEDGER — REPORTS & SUMMARY", styles['MainHeading']))
    story.append(Paragraph(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['NormalText']))
    if context.get('from_date') or context.get('to_date'):
        story.append(Paragraph(f"Filters applied — From: {context.get('from_date', 'N/A')} To: {context.get('to_date', 'N/A')}", styles['NormalText']))
    if context.get('vehicle_id') or context.get('driver_id'):
        story.append(Paragraph(f"Filters applied — Vehicle ID: {context.get('vehicle_id', 'All')} Driver ID: {context.get('driver_id', 'All')}", styles['NormalText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Trip Summary", styles['SecondaryHeading']))
    summary_data = [
        ["Total Trips:", str(context['total_trips']), "Total Income:", f"₹ {context['total_income']}"],
        ["Total Overall Expense:", f"₹ {context['total_overall_expense']}", "Final Balance:", f"₹ {context['total_balance']}"],
        ["Expense Ratio (%):", str(context['expense_ratio']), "Profit Margin (%):", str(context['profit_margin'])],
        ["Total KM:", str(context['total_km']), "Avg Mileage:", str(context['avg_mileage'])],
        ["Total Fuel Cost:", f"₹ {context['total_fuel_cost']}", "Fuel Cost/KM:", f"₹ {context['fuel_cost_per_km']}"],
        ["Total Commission:", f"₹ {context['total_commission']}", "", ""]
    ]
    t = Table(summary_data, colWidths=[150, 150, 150, 150])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
    ]))
    story.append(t)
    
    story.append(Paragraph("Detailed Expense Summary", styles['SecondaryHeading']))
    expense_data = [
        ["Diesel Cost:", f"₹ {context['total_diesel_cost']}", "AdBlue Cost:", f"₹ {context['total_adblue_cost']}"],
        ["Loading Charges:", f"₹ {context['total_loading']}", "Unloading Charges:", f"₹ {context['total_unloading']}"],
        ["Driver Salary:", f"₹ {context['total_driver_salary']}", "Cleaner Salary:", f"₹ {context['total_cleaner_salary']}"],
        ["Workshop Expense:", f"₹ {context['total_workshop_expense']}", "RTO Expense:", f"₹ {context['total_rto']}"],
        ["PC Expense:", f"₹ {context['total_pc']}", "Toll Gate Expense:", f"₹ {context['total_toll_gate']}"],
        ["Other Toll Expense:", f"₹ {context['total_other_toll_expense']}", "Other Expenses:", f"₹ {context['total_other_expenses']}"]
    ]
    t2 = Table(expense_data, colWidths=[150, 150, 150, 150])
    t2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
    ]))
    story.append(t2)

    story.append(PageBreak())
    story.append(Paragraph("All Trips", styles['SecondaryHeading']))
    
    # Reports table
    trips_data = [["Trip Ref", "Vehicle", "Date", "Income", "Fuel", "Overall Exp", "Balance"]]
    for row in context['report_rows']:
        trip = row['trip']
        trips_data.append([
            trip.trip_ref_no,
            trip.vehicle.vehicle_number,
            str(trip.entry_date),
            f"₹ {row['income']}",
            f"₹ {row['diesel_cost'] + row['adblue_cost']}",
            f"₹ {row['overall_expense']}",
            f"₹ {row['balance']}"
        ])
    
    t_trips = Table(trips_data, repeatRows=1)
    t_trips.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_trips)
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("OVERALL REPORT TOTAL", styles['SecondaryHeading']))
    
    report_total_data = [
        ["Total Trips:", str(context['total_trips'])],
        ["Total Revenue:", f"₹ {context['total_income']}"],
        ["Total Fuel Cost:", f"₹ {context['total_fuel_cost']}"],
        ["Total Expenses:", f"₹ {context['total_overall_expense']}"],
        ["Total Commission:", f"₹ {context['total_commission']}"],
        ["Total Toll:", f"₹ {context['total_other_toll_expense'] + context['total_toll_gate']}"],
        ["Overall Expense:", f"₹ {context['total_overall_expense']}"],
        ["FINAL BALANCE:", f"₹ {context['total_balance']}"],
    ]
    t_report_total = Table(report_total_data, colWidths=[200, 150])
    t_report_total.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (0, -1), (-1, -1), TIMES_BOLD), # FINAL BALANCE row
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_report_total)

    doc.build(story)


def generate_trip_voucher_pdf(context, response):
    trip = context['trip']
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = _get_styles()
    story = []

    story.append(Paragraph("TRIP LEDGER VOUCHER", styles['MainHeading']))
    story.append(Paragraph(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['NormalText']))
    
    # Basic info
    story.append(Paragraph("1. BASIC TRIP INFORMATION", styles['SecondaryHeading']))
    basic_data = [
        ["Trip Reference:", trip.trip_ref_no, "Entry Date:", str(trip.entry_date)],
        ["From - To:", f"{trip.period_from} to {trip.period_to}", "Vehicle:", trip.vehicle.vehicle_number],
        ["Primary Driver:", trip.primary_driver.full_name, "Secondary Driver:", trip.secondary_driver.full_name if trip.secondary_driver else "N/A"]
    ]
    if hasattr(trip, 'km_detail') and trip.km_detail:
        basic_data.append(["Start KM:", str(trip.km_detail.start_km or 0), "End KM:", str(trip.km_detail.end_km or 0)])
        basic_data.append(["Total KM:", str(trip.km_detail.total_km or 0), "", ""])
        
    t = Table(basic_data, colWidths=[100, 150, 100, 150])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
    ]))
    story.append(t)

    # Load & Revenue
    story.append(Paragraph("2. LOAD & REVENUE DETAILS", styles['SecondaryHeading']))
    rev_data = [["Date", "Route/Place", "Ton", "Income", "Commission", "Loading", "Unloading"]]
    entries = trip.load_revenue_entries.all()
    if entries:
        for entry in entries:
            route = f"{entry.from_location or ''} to {entry.to_location or ''}".strip()
            if route == "to":
                route = entry.load_place or "Load"
            rev_data.append([
                str(entry.date),
                route, 
                str(entry.ton or 0), 
                f"₹ {entry.income_amount or 0}", 
                f"₹ {entry.commission_amount or 0}", 
                f"₹ {entry.loading_charges or 0}", 
                f"₹ {entry.unloading_charges or 0}"
            ])
        t_rev = Table(rev_data)
        t_rev.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_rev)

        story.append(Spacer(1, 5))
        t_rev_total = Table([
            ["Total Ton:", str(context['total_ton']), "Total Income:", f"₹ {context['overall_income']}"],
            ["Total Commission:", f"₹ {context['commission_total']}", "Total Loading:", f"₹ {context['loading_charges']}"],
            ["Total Unloading:", f"₹ {context['unloading_charges']}", "", ""]
        ], colWidths=[120, 100, 120, 100])
        t_rev_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
            ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_rev_total)
    else:
        story.append(Paragraph("No records available.", styles['NormalText']))

    # Fuel Details
    story.append(Paragraph("3. FUEL / DIESEL DETAILS", styles['SecondaryHeading']))
    fuel_data = [["Type", "Date", "Station", "Qty (L)", "Rate", "Total"]]
    fuels = trip.fuel_entries.all()
    if fuels:
        for entry in fuels:
            fuel_data.append([
                entry.fuel_type, 
                str(entry.fuel_date), 
                entry.station_name or "", 
                str(entry.quantity), 
                f"₹ {entry.rate}", 
                f"₹ {entry.total_cost}"
            ])
        t_fuel = Table(fuel_data)
        t_fuel.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_fuel)
    else:
        story.append(Paragraph("No records available.", styles['NormalText']))

    # Vehicle Performance
    story.append(Paragraph("4. FUEL / VEHICLE PERFORMANCE", styles['SecondaryHeading']))
    perf_data = [
        ["Diesel Consumption:", f"{context['total_diesel_quantity']} L", "Diesel Cost:", f"₹ {context['diesel_cost']}"],
    ]
    if context.get('total_adblue_quantity') and context['total_adblue_quantity'] > 0:
        perf_data.append(["AdBlue Consumption:", f"{context['total_adblue_quantity']} L", "AdBlue Cost:", f"₹ {context['adblue_cost']}"])
        
    if context.get('total_km') and context['total_km'] > 0:
        perf_data.append(["Total Distance:", f"{context['total_km']} KM", "Mileage:", f"{context['mileage']} KM/L"])
    else:
        perf_data.append(["Mileage:", f"{context['mileage']} KM/L", "", ""])
        
    t_perf = Table(perf_data, colWidths=[150, 100, 150, 100])
    t_perf.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
    ]))
    story.append(t_perf)

    # Section 4 Expenses
    story.append(Paragraph("5. EXPENSE ENTRIES", styles['SecondaryHeading']))
    exp_data = [["Date", "Expense Name", "Payment", "Amount"]]
    expenses = trip.expense_entries.all()
    if expenses:
        for ex in expenses:
            exp_data.append([
                str(ex.expense_date or ""),
                ex.expense_name,
                ex.payment_method or "",
                f"₹ {ex.amount}"
            ])
        t_exp = Table(exp_data)
        t_exp.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_exp)
        
        story.append(Spacer(1, 5))
        t_exp_total = Table([["TOTAL SECTION 4 EXPENSES:", f"₹ {context['other_expenses']}"]], colWidths=[200, 150])
        t_exp_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_exp_total)
    else:
        story.append(Paragraph("No records available.", styles['NormalText']))

    # RTO / PC
    story.append(Paragraph("6. RTO / PC ENTRIES", styles['SecondaryHeading']))
    rto_data = [["Type", "Place", "Onward", "Return", "Total"]]
    rtos = trip.rto_pc_entries.all()
    if rtos:
        for rto in rtos:
            rto_data.append([
                rto.expense_type,
                rto.place,
                f"₹ {rto.onward_amount or 0}",
                f"₹ {rto.return_amount or 0}",
                f"₹ {rto.total_amount or 0}"
            ])
        t_rto = Table(rto_data)
        t_rto.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_rto)
        
        story.append(Spacer(1, 5))
        t_rto_total = Table([
            ["Total RTO Only:", f"₹ {context['rto_expense']}", "Total PC Only:", f"₹ {context['pc_expense']}"],
            ["RTO + PC TOTAL:", f"₹ {context['rto_pc_total']}", "", ""]
        ], colWidths=[120, 100, 120, 100])
        t_rto_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
            ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_rto_total)
    else:
        story.append(Paragraph("No records available.", styles['NormalText']))

    # Other Toll Expense
    story.append(Paragraph("7. OTHER TOLL EXPENSES", styles['SecondaryHeading']))
    toll_data = [["Date", "Toll Name", "Amount"]]
    tolls = trip.other_toll_expenses.all()
    if tolls:
        for toll in tolls:
            toll_data.append([
                str(toll.toll_date or ""),
                toll.toll_name,
                f"₹ {toll.amount or 0}"
            ])
        t_toll = Table(toll_data)
        t_toll.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 0), TIMES_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_toll)
        
        story.append(Spacer(1, 5))
        t_toll_total = Table([["TOTAL OTHER TOLL EXPENSES:", f"₹ {context['other_toll_expense']}"]], colWidths=[200, 150])
        t_toll_total.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), TIMES_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_toll_total)
    else:
        story.append(Paragraph("No records available.", styles['NormalText']))

    # Manual Accounting & Salary
    story.append(Paragraph("8. MANUAL ACCOUNTING EXPENSES", styles['SecondaryHeading']))
    man_data = [
        ["Cleaner Salary:", f"₹ {trip.cleaner_salary or 0}", "Workshop Expense:", f"₹ {trip.workshop_expense or 0}"],
        ["Toll Gate Expense:", f"₹ {trip.toll_gate_expense or 0}", "Driver Salary:", f"₹ {context['driver_salary'] or 0}"]
    ]
    t_man = Table(man_data, colWidths=[150, 100, 150, 100])
    t_man.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (2, 0), (2, -1), TIMES_BOLD),
    ]))
    story.append(t_man)

    story.append(Spacer(1, 5))
    t_man_total = Table([["DRIVER SALARY & ACCOUNTING TOTAL:", f"₹ {context['accounting_total']}"]], colWidths=[250, 150])
    t_man_total.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_man_total)

    # Final Accounting
    story.append(Paragraph("9. FINAL ACCOUNTING / OVERALL TOTAL", styles['SecondaryHeading']))
    
    # Calculate toll total from other tolls and toll gate 
    total_toll = context['other_toll_expense'] + (trip.toll_gate_expense or 0)
    
    acc_data = [
        ["Total Revenue:", f"₹ {context['overall_income']}"],
        ["Total Fuel Cost:", f"₹ {context['total_fuel_cost']}"],
    ]
    if context.get('adblue_cost') and context['adblue_cost'] > 0:
        acc_data.append(["Total AdBlue Cost:", f"₹ {context['adblue_cost']}"])
        
    acc_data.extend([
        ["Total Commission:", f"₹ {context['commission_total']}"],
        ["Total Loading Charges:", f"₹ {context['loading_charges']}"],
        ["Total Unloading Charges:", f"₹ {context['unloading_charges']}"],
        ["Total Toll:", f"₹ {total_toll}"],
        ["Driver Salary:", f"₹ {context['driver_salary']}"],
        ["Overall Expense:", f"₹ {context['overall_expense']}"],
        ["FINAL BALANCE:", f"₹ {context['final_balance']}"]
    ])
    
    t_acc = Table(acc_data, colWidths=[200, 150])
    t_acc.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), TIMES_ROMAN),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (0, -1), TIMES_BOLD),
        ('FONTNAME', (0, -1), (-1, -1), TIMES_BOLD), # FINAL BALANCE row
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_acc)

    doc.build(story)
