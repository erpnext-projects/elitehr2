# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
from elitehr2.install import allow_only_specific_module 
from frappe.utils import get_first_day, get_last_day, add_months, flt, today

class ElitehrEmployee(Document):
    def before_save(self):
        if not self.department and self.fingerprint_sites:
            self.department = self.fingerprint_sites[0].site_name


    # used
    def onload(self):
        for l in self.table_leaves:
            res = leaveUsed(self.name, l.leave, l.days)
            l.used = res['used_days']
            l.precent = res['percentage']

    def before_insert(self):
        self.set("table_leaves", [])
        records = frappe.get_all(
            "Elitehr Leave Policies",
            fields=["name","ar_name", "normal_days", "gender"],
        )
        frappe.log(records)
        for r in records:
            self.append("table_leaves", {
                "leave": r.name,
                "leave_name": r.ar_name,
                "days": r.normal_days
            })
        frappe.msgprint('تم اضافة الاجازات', alert=True)

    def validate(self):
        seen = set()
        for leave in self.table_leaves:  
            if leave.leave_name in seen:
                frappe.throw(f"تم إضافة هذه الإجازة مسبقًا: {leave.leave_name}")
            seen.add(leave.leave_name)

    

def leaveUsed(employee, leave, daysAllowed=0):
    requests = frappe.get_all("Elitehr Leaves", filters={"employee": employee,"type": leave,"status":"مكتمل"}, fields=["type","name", "days","status"])
    used_days = sum(int(r.days) for r in requests)
    percentage = (used_days / int(daysAllowed)) * 100 if daysAllowed else 0
    return {
        "used_days": used_days,
        "percentage": percentage
    }


@frappe.whitelist()
def createLoginData(name):
    emp = frappe.get_doc("Elitehr Employee", name)
    if emp.email == None:
        frappe.throw(_("Please add the employee's email address."))

    email = emp.email.strip().lower()
    existing_user = frappe.db.exists("User", email)
    if existing_user:
        frappe.throw(_("Login details already exist"))

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": emp.employee_name,
        "enabled": 1,
        "custom_assign_role": "System Manager",
        "new_password": "Welcome@123",
        "language": "ar"
    })
    
    user_doc.insert()
    emp.login_data = user_doc.name
    emp.save()
    
    # Allow Modules
    allow_only_specific_module(email, "Elitehr2")
    # allow_only_specific_module(email, "Core")


    frappe.msgprint(_("تم اضافة صلاحية System Manager"))
    frappe.msgprint(_("تم ارسالة رسالة لتغيير كلمة المرور"))
    frappe.msgprint(_("تم اضافة الموظف بنجاح"))
    return {
        "login_data": user_doc.name,
        "modified": emp.modified
    }


# used in hook in use core doctye
def update_user_roles(doc, method=None):  
    if doc.get("custom_assign_role"):
        doc.set("roles", [])
        if doc.custom_assign_role == "System Manager":
            doc.append("roles", {
                "role": "Elite HR Admin"
            })

# @frappe.whitelist()
# def test(doc):
#     # هذه الدالة الآن خارج الكلاس لتسهيل استدعائها من الـ Action
#     # doc = frappe.get_doc("Elitehr Employee", docname)

# 	if isinstance(doc, str):
#         doc_data = json.loads(doc)
#     else:
#         doc_data = doc

# 	docname = doc_data.get("name")

# 	doc = frappe.get_doc("Elitehr Employee", docname)

#     frappe.msgprint(f'Test function called for {doc.name}', alert=True)

# @frappe.whitelist()
# def test(doc):
# 	data = json.loads(doc) if isinstance(doc, str) else doc
# 	docname = data.get("name")
# 	doc = frappe.get_doc("Elitehr Employee", docname)
# 	# frappe.msgprint(f'Test function called for {doc.table_leaves}', alert=True)

# 	list_leaves_ids = []
# 	for leave in doc.table_leaves:
# 		list_leaves_ids.append(leave.leave)

# 	frappe.log(list_leaves_ids)

    

@frappe.whitelist()
def get_employee_growth_stats():
    # 1. تحديد التواريخ تلقائياً
    current_date = today()
    curr_start = get_first_day(current_date)
    curr_end = get_last_day(current_date)

    last_month_date = add_months(current_date, -1)
    prev_start = get_first_day(last_month_date)
    prev_end = get_last_day(last_month_date)

    def get_employee_count_by_period(start, end):
        payroll_list = frappe.get_list("Elitehr Employee", 
            filters=[
                {"date_of_appointment": ["between", [start, end]]},
                {"status": "Active"}
                ],
            fields=["employee"] 
        )
        return len(payroll_list)

    def get_total_active_employees():
        return frappe.db.count("Elitehr Employee", filters={"status": "Active"})

    current_count = get_employee_count_by_period(curr_start, curr_end)
    previous_count = get_employee_count_by_period(prev_start, prev_end)

    # 4. حساب الفرق (كم موظف زاد أو نقص)
    diff_value = current_count - previous_count

    # تنسيق النص ليظهر مثل: +12 أو -5
    diff_text = f"{'+' if diff_value >= 0 else ''}{diff_value}"

    return {
        "total": get_total_active_employees(), # إجمالي الموظفين الكلي
        "current_month_count": current_count,   # عدد الموظفين في مسير هذا الشهر
        "diff_text": diff_text,                # الفرق الرقمي (+12 موظف)
        "is_increase": diff_value >= 0,
        "month_name": frappe.utils.get_datetime(current_date).strftime("%B")
    }