# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json

class ElitehrEmployee(Document):
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
        "custom_assign_role": "System Manager"
    })
    user_doc.insert()
    emp.login_data = user_doc.name
    emp.save()

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

    