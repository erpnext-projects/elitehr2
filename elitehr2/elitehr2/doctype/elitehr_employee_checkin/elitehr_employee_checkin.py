# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict
from datetime import datetime, time
from frappe.utils import get_datetime, time_diff_in_seconds, format_datetime, now_datetime, nowtime, getdate

class ElitehrEmployeeCheckin(Document):
    pass



@frappe.whitelist()
def get_employee_checkin_list(date=None):

    # 📅 لو مفيش تاريخ → النهارده
    if not date:
        date = frappe.utils.nowdate()

    frappe.log(f"date: ${date}")
    # 1. كل الموظفين
    employees = frappe.get_all(
        "Elitehr Employee",
        fields=["name", "employee_name", "department_name","shift"]
    )

    # 2. كل الحضور (في يوم معين مثلاً)
    checkins = frappe.get_all(
        "Elitehr Employee Checkin",
        filters={"date": date},
        fields=["employee", "log_type", "time", "date"],
        order_by="time asc"
    )

    # نحولهم بشكل سهل
    # ونجيب اول دخول واخر خروج
    checkin_map = {}

    for c in checkins:
        key = f"{c.employee}_{c.date}"
        if key not in checkin_map:
            checkin_map[key] = {"in": None, "out": None}

        if c.log_type == "Check In" and not checkin_map[key]["in"]:
            checkin_map[key]["in"] = c.time

        if c.log_type == "Check Out":
            checkin_map[key]["out"] = c.time

    final = []

    # 3. نمشي على كل الموظفين
    today = frappe.utils.nowdate()

    for emp in employees:
        key = f"{emp.name}_{today}"

        record = checkin_map.get(key, {})

        check_in = record.get("in")
        check_out = record.get("out")

         # ⏱️ مدة العمل
        working_hours = ""
        if check_in and check_out:
            # 1. احسب إجمالي الثواني بين الانصراف والحضور
            total_seconds = time_diff_in_seconds(check_out, check_in)
            if total_seconds > 0:
                # 2. الساعات هي قسمة الثواني على 3600
                hours = int(total_seconds // 3600)
                # 3. الدقائق هي باقي قسمة الثواني على 3600 مقسومة على 60
                minutes = int((total_seconds % 3600) // 60)
                working_hours = f"{hours:02d}:{minutes:02d}"




        # حالة
        if not check_in:
            status = _("Absent")
            status_color = "color4"
        else:
            status = _("Present")
            status_color = "color3"


        # late
        if emp.shift == None:
            frappe.throw(f"لم يتم تسجيل وردية للموظف {emp.employee_name}")

        late_minutes = 0
        shift_data = frappe.db.get_value("Elitehr Shifts", emp.shift, ["start_time", "end_time"], as_dict=1)

        frappe.log(f"shift_data: {shift_data}")
        if shift_data == None:
            frappe.throw(f"لا يوجد مواعيد للشيفت {emp.shift}")

        if check_in and shift_data.start_time:
            late_diff = time_diff_in_seconds(check_in,  shift_data.start_time)
            if late_diff > 0:
                late_minutes = int(late_diff // 60)
                status = _("Late ({0}) minutes").format(late_minutes)
                status_color = "color1"
        
        # Early Out
        if check_out and shift_data.end_time:
            # بنطرح وقت الشفت من وقت الانصراف الفعلي
            # لو النتيجة سالبة، يعني انصرف قبل الميعاد
            early_diff = time_diff_in_seconds(shift_data.end_time, check_out)
            if early_diff > 0:
                early_minutes = int(early_diff // 60)
                status = _("Early Out ({0}) minutes").format(early_minutes)
                status_color = "color1"

        final.append({
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "department": emp.department_name,
            "date": today,
            "check_in": check_in or "",
            "check_out": check_out or "",
            "status": status,
            "working_hours": working_hours,
            "late_minutes": late_minutes,
            "status_color": status_color
        })
    # frappe.log(final)
    
    
    return final



@frappe.whitelist()
def set_attendance(logType,employee, date):
    if logType not in ["Check In","Check Out"]:
        frappe.throw("Attendance Log Type Not Valid.")
    current_time = now_datetime()

    new_log = frappe.get_doc({
        "doctype": "Elitehr Employee Checkin",
        "employee": employee,
        "log_type": logType,
        "date": date,
        "time": now_datetime().strftime("%H:%M:%S"), 
    })
    new_log.insert()
    frappe.db.commit()
    return True



@frappe.whitelist()
def set_attendance_by_employee_id(employee_id):
    employees = frappe.get_all("Elitehr Employee", 
        filters={"employee_id": employee_id}, 
        fields=["name", "employee_name"]
    )

    if not employees:
        frappe.throw(_("عذراً، لم يتم العثور على موظف بهذا الرقم: {0}").format(employee_id))

    if len(employees) > 1:
        frappe.throw(_("خطأ: يوجد أكثر من موظف مسجل بنفس الرقم ({0})، يرجى مراجعة شؤون الموظفين").format(employee_id))

    new_log = frappe.get_doc({
        "doctype": "Elitehr Employee Checkin",
        "employee": employees[0].name,
        "log_type": "Check In",
        "date": getdate(),
        "time": now_datetime().strftime("%H:%M:%S"), 
    })
    new_log.insert()
    frappe.db.commit()
    return True


@frappe.whitelist()
def loggedin_manual_attendance():
    user = frappe.session.user
    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},  # أو login_id حسب عندك
        ["name"]
    )
    if not employee:
        frappe.throw(_("بيانات الدخول غير مرتبطة بأي موظف"))

    doc = frappe.get_doc({
        "doctype": "Elitehr Employee Checkin",
        "employee": employee,
        "log_type": "Check In",
        "date": getdate(),
        "time": now_datetime().strftime("%H:%M:%S"), 
    })
    doc.insert()
    return True