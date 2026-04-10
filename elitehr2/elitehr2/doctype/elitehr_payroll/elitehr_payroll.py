# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, add_months, flt, today
# import get_employee_checkin_list
from elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_employee_checkin_list
# elitehr2/elitehr2/doctype/elitehr_employee_checkin/elitehr_employee_checkin.py
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




@frappe.whitelist()
def payrloll(fromDate, toDate):
    result = frappe.get_list(
        "Elitehr Payroll",
        fields=["*"],
        filters=[
            {"creation": ("between", [fromDate, toDate])}
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

    return result



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
def calculate_payroll_for_all_employees():
    active_employees = frappe.get_all("Elitehr Employee", filters={"status": "Active"}, fields=["name", "employee_name", "salary"])
    total_reviewed = len(active_employees)

    # check if any employee has invalid salary
    for emp in active_employees:
        if not emp.salary or emp.salary <= 0:
            frappe.throw(f"Employee {emp.employee_name} has invalid salary.")
    
    already_has_payroll_count = 0
    successfully_processed_count = 0
    current_date = today()
    start_of_month = get_first_day(current_date)
    end_of_month = get_last_day(current_date)

    for emp in active_employees:
        # check if payroll already exists for this employee for the current month
        existing_payroll = frappe.db.exists("Elitehr Payroll", {
            "employee": emp.name,
            "creation": ["between", [start_of_month, end_of_month]]
        })

        if existing_payroll:
            already_has_payroll_count += 1
        else:
            payroll_doc = frappe.new_doc("Elitehr Payroll")
            payroll_doc.employee = emp.name
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

    # payroll_doc = frappe.new_doc("Elitehr Payroll")
    # payroll_doc.employee = emp.name
    # payroll_doc.save()
    # payroll_doc.submit()


@frappe.whitelist()
def attendance_and_departure_summary(employee):
    frappe.log(employee)

    # get shift details and workking dayes
    employee_doc = frappe.get_doc("Elitehr Employee", employee)
    employee_shift = frappe.get_doc("Elitehr Shifts", employee_doc.shift)
    shift_schedule = frappe.get_doc("Elitehr Shift Schedule", employee_shift.shift_schedule)

    frappe.log(employee_doc.shift)
    frappe.log(employee_shift)
    frappe.log(shift_schedule)

    current_date = today()
    start_of_month = get_first_day(current_date)
    end_of_month = get_last_day(current_date)


    res = get_employee_checkin_list(employee=employee, date=current_date)
    frappe.log(res)


@frappe.whitelist()
def update_payroll_status(payroll,status):
    doc = frappe.get_doc("Elitehr Payroll",payroll)
    doc.status = status
    doc.save()
    return True