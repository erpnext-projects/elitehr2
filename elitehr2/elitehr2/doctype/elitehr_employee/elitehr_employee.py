# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
from elitehr2.install import allow_only_specific_module 
from frappe.utils import get_first_day, get_last_day, add_months, flt, today

class ElitehrEmployee(Document):
    def on_update(self):
        # 1. تحديث صلاحيات الموظف نفسه (إن وجد له حساب)
        if self.login_data:
            sync_user_permissions(self.login_data)

        # 2. تحديث صلاحيات المدير الجديد (مثل: خالد)
        if self.manager:
            manager_user = frappe.db.get_value("Elitehr Employee", self.manager, "login_data")
            if manager_user:
                sync_user_permissions(manager_user)

        # 3. تحديث صلاحيات المدير القديم (إذا تم تغيير المدير)
        if not self.is_new():
            previous_doc = self.get_doc_before_save()
            if previous_doc and previous_doc.manager and previous_doc.manager != self.manager:
                old_manager_user = frappe.db.get_value("Elitehr Employee", previous_doc.manager, "login_data")
                if old_manager_user:
                    sync_user_permissions(old_manager_user)
                    
    def before_save(self):
        if not self.department and self.fingerprint_sites:
            self.department = self.fingerprint_sites[0].site_name

        # Total Allowances
        total_allowances = 0
        for allowance in self.allowances:
            if allowance.type == "Constant number":
                total_allowances += allowance.amount
            elif allowance.type == "Percentage":
                total_allowances += (allowance.amount / 100) * self.salary

        
        # Total Deductions
        total_deductions = 0
        for deduction in self.deductions:
            if deduction.type == "Constant number":
               total_deductions += deduction.amount
            elif deduction.type == "Percentage":
                total_deductions += (deduction.amount / 100) * self.salary
        
        self.net_salary = (self.salary + total_allowances) - total_deductions



    # used
    # def onload(self):
    #     for l in self.table_leaves:
    #         res = leaveUsed(self.name, l.leave, l.days)
    #         l.used = res['used_days']
    #         l.precent = res['percentage']

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

    

# def leaveUsed(employee, leave, daysAllowed=0):
#     requests = frappe.get_all("Elitehr Requests", filters={"employee": employee,"leave_type": leave,"status":"Completed"}, fields=["type","name", "total_days","status"])
#     used_days = sum(int(r.total_days) for r in requests)
#     percentage = (used_days / int(daysAllowed)) * 100 if daysAllowed else 0
#     return {
#         "used_days": used_days,
#         "percentage": percentage
#     }


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
        "custom_assign_role": "Employee",
        "new_password": "Welcome@123",
        "language": "ar"
    })
    
    user_doc.append("roles", {
        "role": "Elite HR Employee"
    })
    user_doc.append("roles", {
        "role": "Raven User"
    })
    
    user_doc.insert()
    emp.login_data = user_doc.name
    emp.save()
    
    
    
    # Allow Modules
    allow_only_specific_module(email, "Elitehr2")
    # allow_only_specific_module(email, "Core")


    frappe.msgprint(_("تم اضافة صلاحية موظف"))
    frappe.msgprint(_("تم ارسالة رسالة لتغيير كلمة المرور"))
    frappe.msgprint(_("تم اضافة الموظف بنجاح"))
    return {
        "login_data": user_doc.name,
        "modified": emp.modified
    }

def update_user_roles(doc, method=None):
    """Hook يُستدعى عند حفظ شاشة User"""
    sync_user_permissions(doc.name)
    
def sync_user_permissions(user_id):
    """دالة موحدة لإعادة بناء الصلاحيات لأي مستخدم بشكل نظيف وصحيح"""
    if not user_id or not frappe.db.exists("User", user_id):
        return

    # 1. التحقق من أن المستخدم يمتلك دور Elite HR Employee
    user_roles = frappe.get_roles(user_id)
    if "Elite HR Employee" not in user_roles:
        # حذف جميع الصلاحيات في حال سحب الدور منه
        old_perms = frappe.get_all(
            "User Permission",
            filters={"user": user_id, "allow": "Elitehr Employee"},
            pluck="name"
        )
        for perm in old_perms:
            frappe.delete_doc("User Permission", perm, ignore_permissions=True)
        return

    # 2. جلب سجل الموظف المرتبط بهذا المستخدم
    emp = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user_id},
        ["name"],
        as_dict=True
    )
    if not emp:
        return

    # 3. تجميع قائمة الموظفين المسموح برؤيتهم: (الموظف نفسه + كل المرؤوسين المباشرين له)
    subordinates = frappe.get_all(
        "Elitehr Employee",
        filters={"manager": emp.name},
        pluck="name"
    )
    
    allowed_employees = set([emp.name] + subordinates)

    # 4. جلب الصلاحيات الحالية المسجلة في قاعدة البيانات لهذا المستخدم
    existing_perms = frappe.get_all(
        "User Permission",
        filters={"user": user_id, "allow": "Elitehr Employee"},
        fields=["name", "for_value"]
    )
    existing_map = {p.for_value: p.name for p in existing_perms}

    # 5. إضافة الصلاحيات الناقصة (مع جعل apply_to_all_doctypes = 1)
    for emp_name in allowed_employees:
        if emp_name not in existing_map:
            frappe.get_doc({
                "doctype": "User Permission",
                "user": user_id,
                "allow": "Elitehr Employee",
                "for_value": emp_name,
                "apply_to_all_doctypes": 1  # أساسي لرؤية كافة المستندات (الإجازات، الحضور...)
            }).insert(ignore_permissions=True)

    # 6. حذف الصلاحيات الزائدة (لموظفين لم يعودوا تابعين له)
    for emp_name, perm_name in existing_map.items():
        if emp_name not in allowed_employees:
            frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)

# used in hook in use core doctye
def update_user_roles_old(doc, method=None):  
    #  التحقق مما إذا كان المستخدم يمتلك دور Elite HR Employee
    is_employee = any(row.role == "Elite HR Employee" for row in doc.roles)
    
    # إذا لم يكن يمتلك الدور، نقوم بحذف كل صلاحيات النظام المتعلقة به نظافةً للقاعدة
    if not is_employee:
        frappe.db.delete("User Permission", {
            "user": doc.name,
            "allow": "Elitehr Employee"
        })
        return

    # جلب الموظف المرتبط بالمستخدم
    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": doc.name},
        fieldname=["name","manager"],
        as_dict=True
    )

    if not employee:
        return
    
    # has manager
    manager_user = None
    if employee.manager:
        
        manager_user = frappe.db.get_value("Elitehr Employee", employee.manager, "login_data")
        if manager_user:
            # check لو الصلاحية موجودة مسبقاً عشان ميعملش خطأ
            if not frappe.db.exists("User Permission", {
                "user": manager_user,
                "allow": "Elitehr Employee",
                "for_value": employee.name
            }):
                frappe.get_doc({
                    "doctype": "User Permission",
                    "user": manager_user,
                    "allow": "Elitehr Employee",
                    "for_value": employee.name,
                    "apply_to_all_doctypes": 0 
                }).insert(ignore_permissions=True)
    # تنظيف: حذف الصلاحيات من أي مدير سابق
    valid_users = [doc.name]
    if manager_user:
        valid_users.append(manager_user)
    other_manager_perms = frappe.get_all(
        "User Permission",
        filters={
            "allow": "Elitehr Employee",
            "for_value": employee.name,
            "user": ["not in", valid_users]
        },
        pluck="name"
    )
    for perm_name in other_manager_perms:
        frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)

    #  تكوين قائمة القيم المسموحة (الموظف نفسه + المرؤوسين التابعين له)
    allowed_values = [employee.name]
    subordinates = frappe.get_all(
        "Elitehr Employee", 
        filters={"manager": employee.name}, 
        pluck="name"
    )
    allowed_values.extend(subordinates)

    # جلب الصلاحيات الحالية الموجودة في قاعدة البيانات لهذا المستخدم
    existing_permissions = frappe.get_all(
        "User Permission",
        filters={"user": doc.name, "allow": "Elitehr Employee"},
        fields=["name", "for_value"]
    )
    
    # تحويلها إلى قاموس (Dictionary) لتسهيل المقارنة
    existing_map = {p.for_value: p.name for p in existing_permissions}

    # إضافة الصلاحيات الجديدة التي لم تكن موجودة
    for val in allowed_values:
        if val not in existing_map:
            frappe.get_doc({
                "doctype": "User Permission",
                "user": doc.name,
                "allow": "Elitehr Employee",
                "for_value": val,
                "apply_to_all_doctypes": 1
            }).insert(ignore_permissions=True)

    # حذف الصلاحيات القديمة لموظفين لم يعودوا تابعين له أو تم إلغاؤهم
    for val, perm_name in existing_map.items():
        if val not in allowed_values:
            frappe.delete_doc("User Permission", perm_name, ignore_permissions=True)
            
            
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