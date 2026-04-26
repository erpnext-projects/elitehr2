# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, add_months, flt, today,add_days, format_datetime
from elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_employee_attendance_handler 
import calendar
from datetime import datetime

class ElitehrPayroll(Document):
    def before_save(self):
        employee = frappe.get_doc("Elitehr Employee", self.employee)
        self.allowances = employee.allowances
        self.deductions = employee.deductions
        
        # Total Allowances
        self.total_allowances = 0
        self.set("allowances", [])
        for allowance in employee.allowances:
            self.append("allowances", {
                "name1": allowance.name1,
                "type": allowance.type,
                "amount": allowance.amount
            })
            if allowance.type == "Constant number":
                self.total_allowances += allowance.amount
            elif allowance.type == "Percentage":
                self.total_allowances += (allowance.amount / 100) * employee.salary

        # Total Deductions
        self.total_deductions = 0
        self.set("deductions", [])
        for deduction in employee.deductions:
            self.append("deductions", {
                "name1": deduction.name1,
                "type": deduction.type,
                "amount": deduction.amount
            })
            if deduction.type == "Constant number":
                self.total_deductions += deduction.amount
            elif deduction.type == "Percentage":
                self.total_deductions += (deduction.amount / 100) * employee.salary


        # Salary correction
        sallaryAddition = 0
        sallaryDeduction = 0
        for correction in self.salary_correction:
            if correction.type == "Addition (+)":
                sallaryAddition += correction.amount
            elif correction.type == "Deduction (-)":
                sallaryDeduction += correction.amount

        # update salary dedction and allowance total
        self.total_deductions += sallaryDeduction
        self.total_allowances += sallaryAddition

        # Net Salary
        self.net_salary = (employee.salary + self.total_allowances) - (self.total_deductions)

        # Attendance
        attendance = get_employee_attendance_handler(employee= self.employee,from_date= get_first_day(self.date),to_date=get_last_day(self.date))
        self.set("attendance_table", [])
        for day in attendance:
            self.append("attendance_table", {
                "date": day.get("date"),
                "check_in": day.get("check_in"),
                "check_out": day.get("check_out"),
                "status": day.get("status"),
                "status_code": day.get("status_code"),
                "status_color": day.get("status_color"),
                "working_hours": day.get("working_hours"),
                "working_seconds": day.get("working_seconds"),
                "late_minutes": day.get("late_minutes", 0)
            })

        # Requests
        # employee , creation , ATTENDANCE_EDIT
        # modification_type modification_date original_attendance_time required_attendance_time
        self.set("processing_requests", [])
        requests = frappe.get_all(
            "Elitehr Requests",
            fields=["*"],
            filters={
                "employee": self.employee,
                "request_type_code": "ATTENDANCE_EDIT"
            }
            )
        for r in requests:
            frappe.log(r) # name creation modification_type check in check out
            self.append("processing_requests", {
                "request": r.name,
                "request_name": r.request_type_name,
                "date_of_application": format_datetime(r.creation),
                "modification_type": r.modification_type,
                "modification_date": r.modification_date,
                "check_in": r.check_in,
                "check_out": r.check_out,
                "status": r.status,
            })


    
@frappe.whitelist()
def payrloll(fromDate, toDate):
    result = frappe.get_list(
        "Elitehr Payroll",
        fields=["*"],
        filters=[
            {"date": ("between", [fromDate, toDate])}
        ]
    )

    for row in result:
        row["allowances"] = frappe.get_all(
            "Elitehr Employee Allowances",
            filters={"parent": row.name},
            fields=["*"] 
        )
        row["deductions"] = frappe.get_all(
            "Elitehr Employee Deductions",
            filters={"parent": row.name},
            fields=["*"]
        )
        row["salary_correction"] = frappe.get_all(
            "Elitehr Salary Corrections",
            filters={"parent": row.name},
            fields=["*"]
        )
        row["attedndace"] = frappe.get_all(
            "Elitehr Payroll Attendance",
            filters={"parent": row.name},
            fields=["*"]
        )

    active_employees = frappe.db.count("Elitehr Employee")

    return {
        "data": result,
        "active_employee": active_employees
    }



@frappe.whitelist()
def get_monthly_comparison_stats(field = "net_salary"):
    # 1. تحديد تواريخ الشهر الحالي تلقائياً
    current_date = today()
    curr_start = get_first_day(current_date)
    curr_end = get_last_day(current_date)

    # 2. تحديد تواريخ الشهر الماضي تلقائياً
    last_month_date = add_months(current_date, -1)
    prev_start = get_first_day(last_month_date)
    prev_end = get_last_day(last_month_date)

    # 3. دالة جلب الإجمالي من قاعدة البيانات
    def get_total_salaries_by_month(start, end):
        payroll_list = frappe.get_list("Elitehr Payroll", 
            filters={"creation": ["between", [start, end]]},
            fields=[field]
        )
        return sum(flt(d[field]) for d in payroll_list)

    def get_total_salaries():
        payroll_list = frappe.get_list("Elitehr Payroll", fields=[field])
        return sum(flt(d[field]) for d in payroll_list)

    current_total = get_total_salaries_by_month(curr_start, curr_end)
    previous_total = get_total_salaries_by_month(prev_start, prev_end)

    # 4. حساب نسبة التغير
    diff_percent = 0
    if previous_total > 0:
        diff_percent = ((current_total - previous_total) / previous_total) * 100
    elif current_total > 0:
        diff_percent = 100

    return {
        "total": get_total_salaries(),
        "diff_text": f"{'+' if diff_percent >= 0 else ''}{round(diff_percent, 1)}%",
        "is_increase": diff_percent >= 0,
        "month_name": frappe.utils.get_datetime(current_date).strftime("%B") # اسم الشهر الحالي
    }
    

@frappe.whitelist()
def calculate_payroll_for_all_employees(date):
    start_of_month = get_first_day(date)
    end_of_month = get_last_day(date)

    if date > today():
        frappe.throw("لا يمكن اختيار تاريخ في المستقبل")
    
    if date != end_of_month:
        frappe.throw("لا يمكن تقفيل الشهر قبل نهايته")

    active_employees = frappe.get_all("Elitehr Employee", filters={"status": "Active"}, fields=["name", "employee_name", "salary"])
    total_reviewed = len(active_employees)

    # check if any employee has invalid salary
    for emp in active_employees:
        if not emp.salary or emp.salary <= 0:
            frappe.throw(f"Employee {emp.employee_name} has invalid salary.")
    
    already_has_payroll_count = 0
    successfully_processed_count = 0
    

    for emp in active_employees:
        # check if payroll already exists for this employee for the current month
        existing_payroll = frappe.db.exists("Elitehr Payroll", {
            "employee": emp.name,
            "date": ["between", [start_of_month, end_of_month]]
        })

        if existing_payroll:
            already_has_payroll_count += 1
        else:
            payroll_doc = frappe.new_doc("Elitehr Payroll")
            payroll_doc.employee = emp.name
            payroll_doc.date = date
            payroll_doc.save()
            successfully_processed_count += 1
    
    msg = f"""
        <b>تمت عملية المعالجة بنجاح:</b><br>
        <ul>
            <li>تم مراجعة <b>{total_reviewed}</b> موظف.</li>
            <li><b>{already_has_payroll_count}</b> موظفين لديهم راتب لهذا الشهر بالفعل.</li>
            <li>تم حساب الراتب لـ <b>{successfully_processed_count}</b> موظف بنجاح.</li>
        </ul>
    """

    frappe.msgprint(msg,title="نتائج احتساب الرواتب")
    return True



@frappe.whitelist()
def update_payroll_status(payroll,status):
    doc = frappe.get_doc("Elitehr Payroll",payroll)
    doc.status = status
    doc.save()
    return True



@frappe.whitelist()
def get_deductions_summary(from_date, to_date):
    rows = frappe.db.sql("""
        SELECT 
            d.name1,
            d.type,
            d.amount,
            p.basic_salary
        FROM `tabElitehr Employee Deductions` d
        INNER JOIN `tabElitehr Payroll` p 
            ON d.parent = p.name
        WHERE 
            p.date BETWEEN %s AND %s
    """, (from_date, to_date), as_dict=True)
    
    # frappe.log("rows")
    # for r in rows:
    #     frappe.log(r)

    grouped = {}
    total = 0
    for r in rows:
        if r.type == "Percentage":
            amount = (r.amount / 100) * (r.basic_salary or 0)
        else:  # Constant number
            amount = r.amount or 0

        if r.name1 not in grouped:
            grouped[r.name1] = 0

        grouped[r.name1] += amount
        total += amount

    # frappe.log("grouped")
    # frappe.log(grouped)

    # 👇 تحويل لـ list + حساب النسبة
    result = []
    for name, value in grouped.items():
        result.append({
            "type": name,
            "amount": round(value, 2),
            "percentage": round((value / total * 100), 2) if total else 0
        })

    return {
        "total": round(total, 2),
        "data": result
    }




@frappe.whitelist()
def get_monthly_payroll_trend(year=None):
    

    if not year:
        year = datetime.now().year

    rows = frappe.db.sql("""
        SELECT 
            MONTH(p.date) as month,
            SUM(p.net_salary) as net_salary,
            SUM(p.basic_salary) as total_salary,
            SUM(p.total_allowances) as total_allowances,
            SUM(p.total_deductions) as total_deductions
        FROM `tabElitehr Payroll` p
        WHERE YEAR(p.date) = %s
        GROUP BY MONTH(p.date)
    """, (year,), as_dict=True)

    # frappe.log("get_monthly_payroll_trend")
    # frappe.log(rows)

    # نحول ل map
    data_map = {r.month: r for r in rows}

    months = []
    salaries = []
    allowances = []
    deductions = []
    net = []

    for m in range(1, 13):
        row = data_map.get(m, {})
        months.append(m)
        net.append(row.get("net_salary", 0) or 0)
        salaries.append(row.get("total_salary", 0) or 0)
        allowances.append(row.get("total_allowances", 0) or 0)
        deductions.append(row.get("total_deductions", 0) or 0)
    

    return {
        "months": months,
        "salaries": salaries,
        "allowances": allowances,
        "deductions": deductions,
        "net": net
    }



@frappe.whitelist()
def get_salary_distribution(from_date, to_date):
    rows = frappe.db.sql("""
        SELECT net_salary
        FROM `tabElitehr Payroll` p
        WHERE 
            p.date BETWEEN %s AND %s
    """, (from_date, to_date) , as_dict=True)

    ranges = {
        "0 - 3,000": 0,
        "3,000 - 5,000": 0,
        "5,000 - 8,000": 0,
        "8,000 - 12,000": 0,
        "12,000 - 15,000": 0,
        "15,000+": 0
    }

    for r in rows:
        salary = r.net_salary or 0

        if salary <= 3000:
            ranges["0 - 3,000"] += 1
        elif salary <= 5000:
            ranges["3,000 - 5,000"] += 1
        elif salary <= 8000:
            ranges["5,000 - 8,000"] += 1
        elif salary <= 12000:
            ranges["8,000 - 12,000"] += 1
        elif salary <= 15000:
            ranges["12,000 - 15,000"] += 1
        else:
            ranges["15,000+"] += 1

    return ranges




@frappe.whitelist()
def get_top_employees_leaves(limit=10):
    rows = frappe.db.sql("""
        SELECT 
            r.employee,
            r.employee_name,
            e.job_title,
            SUM(total_days) as total_days
        FROM `tabElitehr Requests` r
        LEFT JOIN `tabElitehr Employee` e ON r.employee = e.name
        where r.request_type_code in ('LEAVE_ANNUAL','LEAVE_EMERGENCY','LEAVE_SICK')
        GROUP BY r.employee
        ORDER BY total_days DESC
        LIMIT %s
    """, (limit,), as_dict=True)
    # frappe.log("get_top_employees_leaves")
    # frappe.log(rows)
    return rows


@frappe.whitelist()
def get_leaves_summary():
    rows = frappe.db.sql(f"""
        SELECT 
            request_type_name as leave_type,
            SUM(total_days) as total_days
        FROM `tabElitehr Requests`
        WHERE request_type_code IN ('LEAVE_ANNUAL','LEAVE_EMERGENCY','LEAVE_SICK','LEAVE_MATERNITY')
        GROUP BY request_type_name
        ORDER BY total_days DESC
    """, as_dict=True)

    return rows