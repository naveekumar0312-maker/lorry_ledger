import io
from datetime import datetime
# pyrefly: ignore [missing-import]
from docx import Document
# pyrefly: ignore [missing-import]
from docx.shared import Pt, Inches
# pyrefly: ignore [missing-import]
from docx.enum.text import WD_ALIGN_PARAGRAPH
# pyrefly: ignore [missing-import]
from docx.enum.section import WD_ORIENT
# pyrefly: ignore [missing-import]
from docx.oxml.ns import qn

def _setup_document(landscape_mode=False):
    document = Document()
    style = document.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    
    if landscape_mode:
        section = document.sections[-1]
        new_width, new_height = section.page_height, section.page_width
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = new_width
        section.page_height = new_height
        
    return document

def _add_heading(document, text, level=1):
    heading = document.add_heading(text, level=level)
    for run in heading.runs:
        run.font.name = 'Times New Roman'
        run.font.size = Pt(16) if level == 1 else Pt(14)
        run.font.bold = True
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT

def _create_styled_table(document, rows, cols):
    table = document.add_table(rows=rows, cols=cols)
    table.style = 'Table Grid'
    return table

def generate_reports_summary_word(context, response):
    document = _setup_document(landscape_mode=True)
    _add_heading(document, "VEHICLE LEDGER — REPORTS & SUMMARY", level=1)
    
    p = document.add_paragraph(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if context.get('from_date') or context.get('to_date'):
        p2 = document.add_paragraph(f"Filters applied — From: {context.get('from_date', 'N/A')} To: {context.get('to_date', 'N/A')}")
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if context.get('vehicle_id') or context.get('driver_id'):
        p3 = document.add_paragraph(f"Filters applied — Vehicle ID: {context.get('vehicle_id', 'All')} Driver ID: {context.get('driver_id', 'All')}")
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    _add_heading(document, "Trip Summary", level=2)
    t = _create_styled_table(document, 6, 4)
    summary_data = [
        ["Total Trips:", str(context['total_trips']), "Total Income:", f"₹ {context['total_income']}"],
        ["Total Overall Expense:", f"₹ {context['total_overall_expense']}", "Final Balance:", f"₹ {context['total_balance']}"],
        ["Expense Ratio (%):", str(context['expense_ratio']), "Profit Margin (%):", str(context['profit_margin'])],
        ["Total KM:", str(context['total_km']), "Avg Mileage:", str(context['avg_mileage'])],
        ["Total Fuel Cost:", f"₹ {context['total_fuel_cost']}", "Fuel Cost/KM:", f"₹ {context['fuel_cost_per_km']}"],
        ["Total Commission:", f"₹ {context['total_commission']}", "", ""]
    ]
    for r_idx, row_data in enumerate(summary_data):
        for c_idx, cell_value in enumerate(row_data):
            cell = t.rows[r_idx].cells[c_idx]
            cell.text = cell_value
            if c_idx in [0, 2]:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        
    _add_heading(document, "Detailed Expense Summary", level=2)
    t2 = _create_styled_table(document, 6, 4)
    expense_data = [
        ["Diesel Cost:", f"₹ {context['total_diesel_cost']}", "AdBlue Cost:", f"₹ {context['total_adblue_cost']}"],
        ["Loading Charges:", f"₹ {context['total_loading']}", "Unloading Charges:", f"₹ {context['total_unloading']}"],
        ["Driver Salary:", f"₹ {context['total_driver_salary']}", "Cleaner Salary:", f"₹ {context['total_cleaner_salary']}"],
        ["Workshop Expense:", f"₹ {context['total_workshop_expense']}", "RTO Expense:", f"₹ {context['total_rto']}"],
        ["PC Expense:", f"₹ {context['total_pc']}", "Toll Gate Expense:", f"₹ {context['total_toll_gate']}"],
        ["Other Toll Expense:", f"₹ {context['total_other_toll_expense']}", "Other Expenses:", f"₹ {context['total_other_expenses']}"]
    ]
    for r_idx, row_data in enumerate(expense_data):
        for c_idx, cell_value in enumerate(row_data):
            cell = t2.rows[r_idx].cells[c_idx]
            cell.text = cell_value
            if c_idx in [0, 2]:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        
    document.add_page_break()
    _add_heading(document, "All Trips", level=2)
    t_trips = _create_styled_table(document, 1, 7)
    hdr_cells = t_trips.rows[0].cells
    headers = ["Trip Ref", "Vehicle", "Date", "Income", "Fuel", "Overall Exp", "Balance"]
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            for run in p.runs:
                run.font.bold = True
                
    for row in context['report_rows']:
        trip = row['trip']
        row_cells = t_trips.add_row().cells
        row_cells[0].text = trip.trip_ref_no
        row_cells[1].text = trip.vehicle.vehicle_number
        row_cells[2].text = str(trip.entry_date)
        row_cells[3].text = f"₹ {row['income']}"
        row_cells[4].text = f"₹ {row['diesel_cost'] + row['adblue_cost']}"
        row_cells[5].text = f"₹ {row['overall_expense']}"
        row_cells[6].text = f"₹ {row['balance']}"

    document.add_paragraph("")
    _add_heading(document, "OVERALL REPORT TOTAL", level=2)
    t_report_total = _create_styled_table(document, 0, 2)
    report_total_data = [
        ("Total Trips:", str(context['total_trips'])),
        ("Total Revenue:", f"₹ {context['total_income']}"),
        ("Total Fuel Cost:", f"₹ {context['total_fuel_cost']}"),
        ("Total Expenses:", f"₹ {context['total_overall_expense']}"),
        ("Total Commission:", f"₹ {context['total_commission']}"),
        ("Total Toll:", f"₹ {context['total_other_toll_expense'] + context['total_toll_gate']}"),
        ("Overall Expense:", f"₹ {context['total_overall_expense']}"),
        ("FINAL BALANCE:", f"₹ {context['total_balance']}"),
    ]
    for label, val in report_total_data:
        row_cells = t_report_total.add_row().cells
        row_cells[0].text = label
        row_cells[1].text = val
        for p in row_cells[0].paragraphs:
            for run in p.runs:
                run.font.bold = True
        if label == "FINAL BALANCE:":
            for p in row_cells[1].paragraphs:
                for run in p.runs:
                    run.font.bold = True

    document.save(response)


def generate_trip_voucher_word(context, response):
    trip = context['trip']
    document = _setup_document(landscape_mode=False)
    _add_heading(document, "TRIP LEDGER VOUCHER", level=1)
    p = document.add_paragraph(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    _add_heading(document, "1. BASIC TRIP INFORMATION", level=2)
    t = _create_styled_table(document, 0, 4)
    basic_data = [
        ["Trip Reference:", trip.trip_ref_no, "Entry Date:", str(trip.entry_date)],
        ["From - To:", f"{trip.period_from} to {trip.period_to}", "Vehicle:", trip.vehicle.vehicle_number],
        ["Primary Driver:", trip.primary_driver.full_name, "Secondary Driver:", trip.secondary_driver.full_name if trip.secondary_driver else "N/A"]
    ]
    if hasattr(trip, 'km_detail') and trip.km_detail:
        basic_data.append(["Start KM:", str(trip.km_detail.start_km or 0), "End KM:", str(trip.km_detail.end_km or 0)])
        basic_data.append(["Total KM:", str(trip.km_detail.total_km or 0), "", ""])
        
    for row_data in basic_data:
        row_cells = t.add_row().cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = val
            if c_idx in [0, 2]:
                for p in row_cells[c_idx].paragraphs:
                    for run in p.runs:
                        run.font.bold = True
                        
    _add_heading(document, "2. LOAD & REVENUE DETAILS", level=2)
    entries = trip.load_revenue_entries.all()
    if entries:
        t_rev = _create_styled_table(document, 1, 7)
        headers = ["Date", "Route/Place", "Ton", "Income", "Commission", "Loading", "Unloading"]
        for i, h in enumerate(headers):
            t_rev.rows[0].cells[i].text = h
            for paragraph in t_rev.rows[0].cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    
        for entry in entries:
            route = f"{entry.from_location or ''} to {entry.to_location or ''}".strip()
            if route == "to":
                route = entry.load_place or "Load"
            row_cells = t_rev.add_row().cells
            row_cells[0].text = str(entry.date)
            row_cells[1].text = route
            row_cells[2].text = str(entry.ton or 0)
            row_cells[3].text = f"₹ {entry.income_amount or 0}"
            row_cells[4].text = f"₹ {entry.commission_amount or 0}"
            row_cells[5].text = f"₹ {entry.loading_charges or 0}"
            row_cells[6].text = f"₹ {entry.unloading_charges or 0}"
            
        t_rev_total = _create_styled_table(document, 3, 4)
        rev_total_data = [
            ["Total Ton:", str(context['total_ton']), "Total Income:", f"₹ {context['overall_income']}"],
            ["Total Commission:", f"₹ {context['commission_total']}", "Total Loading:", f"₹ {context['loading_charges']}"],
            ["Total Unloading:", f"₹ {context['unloading_charges']}", "", ""]
        ]
        for r_idx, row_data in enumerate(rev_total_data):
            for c_idx, val in enumerate(row_data):
                t_rev_total.rows[r_idx].cells[c_idx].text = val
                if c_idx in [0, 2]:
                    for p in t_rev_total.rows[r_idx].cells[c_idx].paragraphs:
                        for run in p.runs:
                            run.font.bold = True
    else:
        document.add_paragraph("No records available.")

    _add_heading(document, "3. FUEL / DIESEL DETAILS", level=2)
    fuels = trip.fuel_entries.all()
    if fuels:
        t_fuel = _create_styled_table(document, 1, 6)
        headers = ["Type", "Date", "Station", "Qty (L)", "Rate", "Total"]
        for i, h in enumerate(headers):
            t_fuel.rows[0].cells[i].text = h
            for paragraph in t_fuel.rows[0].cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
        for entry in fuels:
            row_cells = t_fuel.add_row().cells
            row_cells[0].text = entry.fuel_type
            row_cells[1].text = str(entry.fuel_date)
            row_cells[2].text = entry.station_name or ""
            row_cells[3].text = str(entry.quantity)
            row_cells[4].text = f"₹ {entry.rate}"
            row_cells[5].text = f"₹ {entry.total_cost}"
    else:
        document.add_paragraph("No records available.")
        
    _add_heading(document, "4. FUEL / VEHICLE PERFORMANCE", level=2)
    t_perf = _create_styled_table(document, 0, 4)
    perf_data = [
        ["Diesel Consumption:", f"{context['total_diesel_quantity']} L", "Diesel Cost:", f"₹ {context['diesel_cost']}"],
    ]
    if context.get('total_adblue_quantity') and context['total_adblue_quantity'] > 0:
        perf_data.append(["AdBlue Consumption:", f"{context['total_adblue_quantity']} L", "AdBlue Cost:", f"₹ {context['adblue_cost']}"])
        
    if context.get('total_km') and context['total_km'] > 0:
        perf_data.append(["Total Distance:", f"{context['total_km']} KM", "Mileage:", f"{context['mileage']} KM/L"])
    else:
        perf_data.append(["Mileage:", f"{context['mileage']} KM/L", "", ""])
        
    for row_data in perf_data:
        row_cells = t_perf.add_row().cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = val
            if c_idx in [0, 2]:
                for p in row_cells[c_idx].paragraphs:
                    for run in p.runs:
                        run.font.bold = True

    _add_heading(document, "5. EXPENSE ENTRIES", level=2)
    expenses = trip.expense_entries.all()
    if expenses:
        t_exp = _create_styled_table(document, 1, 4)
        headers = ["Date", "Expense Name", "Payment", "Amount"]
        for i, h in enumerate(headers):
            t_exp.rows[0].cells[i].text = h
            for p in t_exp.rows[0].cells[i].paragraphs:
                for run in p.runs:
                    run.font.bold = True
        for ex in expenses:
            row_cells = t_exp.add_row().cells
            row_cells[0].text = str(ex.expense_date or "")
            row_cells[1].text = ex.expense_name
            row_cells[2].text = ex.payment_method or ""
            row_cells[3].text = f"₹ {ex.amount}"
            
        t_exp_total = _create_styled_table(document, 1, 2)
        t_exp_total.rows[0].cells[0].text = "TOTAL SECTION 4 EXPENSES:"
        t_exp_total.rows[0].cells[1].text = f"₹ {context['other_expenses']}"
        for p in t_exp_total.rows[0].cells[0].paragraphs:
            for run in p.runs:
                run.font.bold = True
    else:
        document.add_paragraph("No records available.")

    _add_heading(document, "6. RTO / PC ENTRIES", level=2)
    rtos = trip.rto_pc_entries.all()
    if rtos:
        t_rto = _create_styled_table(document, 1, 5)
        headers = ["Type", "Place", "Onward", "Return", "Total"]
        for i, h in enumerate(headers):
            t_rto.rows[0].cells[i].text = h
            for p in t_rto.rows[0].cells[i].paragraphs:
                for run in p.runs:
                    run.font.bold = True
        for rto in rtos:
            row_cells = t_rto.add_row().cells
            row_cells[0].text = rto.expense_type
            row_cells[1].text = rto.place
            row_cells[2].text = f"₹ {rto.onward_amount or 0}"
            row_cells[3].text = f"₹ {rto.return_amount or 0}"
            row_cells[4].text = f"₹ {rto.total_amount or 0}"
            
        t_rto_total = _create_styled_table(document, 2, 4)
        rto_total_data = [
            ["Total RTO Only:", f"₹ {context['rto_expense']}", "Total PC Only:", f"₹ {context['pc_expense']}"],
            ["RTO + PC TOTAL:", f"₹ {context['rto_pc_total']}", "", ""]
        ]
        for r_idx, row_data in enumerate(rto_total_data):
            for c_idx, val in enumerate(row_data):
                t_rto_total.rows[r_idx].cells[c_idx].text = val
                if c_idx in [0, 2]:
                    for p in t_rto_total.rows[r_idx].cells[c_idx].paragraphs:
                        for run in p.runs:
                            run.font.bold = True
    else:
        document.add_paragraph("No records available.")

    _add_heading(document, "7. OTHER TOLL EXPENSES", level=2)
    tolls = trip.other_toll_expenses.all()
    if tolls:
        t_toll = _create_styled_table(document, 1, 3)
        headers = ["Date", "Toll Name", "Amount"]
        for i, h in enumerate(headers):
            t_toll.rows[0].cells[i].text = h
            for p in t_toll.rows[0].cells[i].paragraphs:
                for run in p.runs:
                    run.font.bold = True
        for toll in tolls:
            row_cells = t_toll.add_row().cells
            row_cells[0].text = str(toll.toll_date or "")
            row_cells[1].text = toll.toll_name
            row_cells[2].text = f"₹ {toll.amount or 0}"
            
        t_toll_total = _create_styled_table(document, 1, 2)
        t_toll_total.rows[0].cells[0].text = "TOTAL OTHER TOLL EXPENSES:"
        t_toll_total.rows[0].cells[1].text = f"₹ {context['other_toll_expense']}"
        for p in t_toll_total.rows[0].cells[0].paragraphs:
            for run in p.runs:
                run.font.bold = True
    else:
        document.add_paragraph("No records available.")
        
    _add_heading(document, "8. MANUAL ACCOUNTING EXPENSES", level=2)
    t_man = _create_styled_table(document, 0, 4)
    man_data = [
        ["Cleaner Salary:", f"₹ {trip.cleaner_salary or 0}", "Workshop Expense:", f"₹ {trip.workshop_expense or 0}"],
        ["Toll Gate Expense:", f"₹ {trip.toll_gate_expense or 0}", "Driver Salary:", f"₹ {context['driver_salary'] or 0}"]
    ]
    for row_data in man_data:
        row_cells = t_man.add_row().cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = val
            if c_idx in [0, 2]:
                for p in row_cells[c_idx].paragraphs:
                    for run in p.runs:
                        run.font.bold = True
                        
    t_man_total = _create_styled_table(document, 1, 2)
    t_man_total.rows[0].cells[0].text = "DRIVER SALARY & ACCOUNTING TOTAL:"
    t_man_total.rows[0].cells[1].text = f"₹ {context['accounting_total']}"
    for p in t_man_total.rows[0].cells[0].paragraphs:
        for run in p.runs:
            run.font.bold = True

    _add_heading(document, "9. FINAL ACCOUNTING / OVERALL TOTAL", level=2)
    t_acc = _create_styled_table(document, 0, 2)
    total_toll = context['other_toll_expense'] + (trip.toll_gate_expense or 0)
    acc_data = [
        ("Total Revenue:", f"₹ {context['overall_income']}"),
        ("Total Fuel Cost:", f"₹ {context['total_fuel_cost']}"),
    ]
    if context.get('adblue_cost') and context['adblue_cost'] > 0:
        acc_data.append(("Total AdBlue Cost:", f"₹ {context['adblue_cost']}"))
        
    acc_data.extend([
        ("Total Commission:", f"₹ {context['commission_total']}"),
        ("Total Loading Charges:", f"₹ {context['loading_charges']}"),
        ("Total Unloading Charges:", f"₹ {context['unloading_charges']}"),
        ("Total Toll:", f"₹ {total_toll}"),
        ("Driver Salary:", f"₹ {context['driver_salary']}"),
        ("Overall Expense:", f"₹ {context['overall_expense']}"),
        ("FINAL BALANCE:", f"₹ {context['final_balance']}")
    ])
    
    for label, val in acc_data:
        row_cells = t_acc.add_row().cells
        row_cells[0].text = label
        row_cells[1].text = val
        for p in row_cells[0].paragraphs:
            for run in p.runs:
                run.font.bold = True
        if label == "FINAL BALANCE:":
            for p in row_cells[1].paragraphs:
                for run in p.runs:
                    run.font.bold = True
                
    document.save(response)
