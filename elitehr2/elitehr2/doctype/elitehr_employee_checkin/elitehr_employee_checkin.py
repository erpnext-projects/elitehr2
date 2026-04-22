# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict
from datetime import datetime, timedelta
from frappe.utils import get_datetime, time_diff_in_seconds, format_datetime, now_datetime, nowtime, get_first_day, get_last_day, add_months, flt, today,add_days,getdate
import calendar

class ElitehrEmployeeCheckin(Document):
    pass





@frappe.whitelist()
def get_employee_checkin_list_old(date=None,employee=None):

    has_date = True if date else False

    # 📅 لو مفيش تاريخ → النهارده
    if not date:
        date = frappe.utils.nowdate()

    frappe.log(f"date: ${date}")


    # 1. كل الموظفين
    if employee:
        employees = frappe.get_all(
            "Elitehr Employee",
            filters={"name":employee},
            fields=["name", "employee_name", "department_name","shift"]
        )
    else:
        employees = frappe.get_all(
            "Elitehr Employee",
            fields=["name", "employee_name", "department_name","shift"]
        )

    shifts = frappe.get_all("Elitehr Shifts", fields=["name", "start_time", "end_time"])
    shift_map = {s.name: s for s in shifts}

    # 2. كل الحضور (في يوم معين مثلاً)
    if employee:
        if not has_date:
            # لو مفيش تاريخ -> هنجيب آخر 10 حركات بس (الأحدث)
            checkins = frappe.get_all(
                "Elitehr Employee Checkin",
                filters={"employee": employee},
                fields=["employee", "log_type", "time", "date"],
                order_by="time desc",
                limit_page_length=10
            )    
            checkins.reverse() # بنعكسهم عشان يبقوا من الأقدم للأحدث
        else:
            # لو فيه تاريخ للموظف -> هنجيب حركات اليوم ده بس
            checkins = frappe.get_all(
                "Elitehr Employee Checkin",
                filters={"employee": employee, "date": date},
                fields=["employee", "log_type", "time", "date"],
                order_by="time asc"
            )

    else:
        # لو مش باعت موظف -> هنجيب اليوم كله لكل الموظفين
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

    # frappe.log("checkin_map")
    # frappe.log(checkin_map)

    # 3. سجل حضور واحد لكل موظف
    # today = frappe.utils.nowdate()
    rows_to_process = []
    if employee and not has_date:
        # لو بنجيب آخر 10 بصمات لموظف، هنمشي على التواريخ اللي جت في البصمات فعلاً
        for key, record in checkin_map.items():
            emp_id, current_date = key.split('_')
            rows_to_process.append((emp_id, current_date, record))
    else:
        # لو بنجيب يوم معين، هنمشي على كل الموظفين في اليوم المحدد
        for emp in employees:
            key = f"{emp.name}_{date}"
            record = checkin_map.get(key, {})
            rows_to_process.append((emp.name, date, record))

    # 6. معالجة الحسابات (شاملة وموحدة لكل الحالات)
    for emp_id, target_date, record in rows_to_process:
        emp = next((e for e in employees if e.name == emp_id), None)
        if not emp:
            continue

        check_in = record.get("in")
        check_out = record.get("out")

         # ⏱️ مدة العمل
        working_hours = ""
        working_seconds = 0
        if check_in and check_out:
            # 1. احسب إجمالي الثواني بين الانصراف والحضور
            total_seconds = time_diff_in_seconds(check_out, check_in)
            if total_seconds > 0:
                working_seconds = total_seconds
                # 2. الساعات هي قسمة الثواني على 3600
                hours = int(total_seconds // 3600)
                # 3. الدقائق هي باقي قسمة الثواني على 3600 مقسومة على 60
                minutes = int((total_seconds % 3600) // 60)
                working_hours = f"{hours:02d}:{minutes:02d}"




        # حالة
        if not check_in:
            statusCode = "Absent"
            status = _("Absent")
            status_color = "color4"
        else:
            statusCode = "Present"
            status = _("Present")
            status_color = "color3"


        # late
        if emp.shift == None:
            frappe.throw(f"لم يتم تسجيل وردية للموظف {emp.employee_name}")

        late_minutes = 0
        shift_data = shift_map.get(emp.shift)

        # frappe.log(f"shift_data: {shift_data}")
        if not shift_data:
            frappe.throw(f"لا يوجد مواعيد للشيفت {emp.shift}")

        if check_in and shift_data.start_time:
            late_diff = time_diff_in_seconds(check_in,  shift_data.start_time)
            if late_diff > 0:
                late_minutes = int(late_diff // 60)
                statusCode = "Late"
                status = _("Late ({0}) minutes").format(late_minutes)
                status_color = "color1"
        
        # Early Out
        if check_out and shift_data.end_time:
            # بنطرح وقت الشفت من وقت الانصراف الفعلي
            # لو النتيجة سالبة، يعني انصرف قبل الميعاد
            early_diff = time_diff_in_seconds(shift_data.end_time, check_out)
            if early_diff > 0:
                early_minutes = int(early_diff // 60)
                statusCode = "Early Out"
                status = _("Early Out ({0}) minutes").format(early_minutes)
                status_color = "color1"

        final.append({
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "department": emp.department_name,
            "date": target_date,
            "check_in": check_in or "",
            "check_out": check_out or "",
            "status": status,
            "status_code": statusCode,
            "working_hours": working_hours,
            "working_seconds": working_seconds,
            "late_minutes": late_minutes,
            "status_color": status_color
        })

    return final


def get_employee_working_days_and_time(employee):
    employee_doc = frappe.get_doc("Elitehr Employee", employee)

    # get shift details and workking dayes
    if not employee_doc.shift:
        frappe.throw(_("Shift not found for employee {0}").format(employee_doc.employee_name)) 

    employee_shift = frappe.get_doc("Elitehr Shifts", employee_doc.shift)

    if not employee_shift.shift_schedule:
        frappe.throw(_("Shift schedule not found for employee {0}").format(employee_doc.employee_name)) 
    
    shift_schedule = frappe.get_doc("Elitehr Shift Schedule", employee_shift.shift_schedule)
    

    working_days = {}
    for d in shift_schedule.days:
        working_days[d.day] = {
            "from_time": d.get("from"),
            "to_time": d.get("to"),
            "break": d.get("break")
        }
    return working_days


@frappe.whitelist()
def get_year_monthes_employees():
    year = datetime.today().year
    employees = frappe.get_all(
            "Elitehr Employee",
            fields=["name", "employee_name", "department_name","shift"]
        )

    months = {}
    current_month = datetime.today().month
    
    for m in range(1, current_month + 1):
        present = 0
        late = 0
        absent = 0
        # build a date inside that month (safe)
        sample_date = f"{year}-{m:02d}-01"
        for emp in employees:
            data = get_employee_attendance_handler(emp.name,get_first_day(sample_date),get_last_day(sample_date))
            if not data:
                continue
            for row in data:
                status = row.get("status_code")
                if status == "Absent":
                    absent+=1
                elif status == "Present":
                    present += 1
                elif status == "Late":
                    late += 1
        months[m] = {
            "month": m,
            "present": present,
            "late": late,
            "absent": absent
        }
    # frappe.log(months)
    return [months[m] for m in months]


# الدالة الاساسية
@frappe.whitelist()
def get_employee_attendance_handler(employee=None,from_date=None,to_date=None):
    
    if from_date is None:
        from_date = today()

    if to_date is None:
        to_date = from_date

    targetEmployees = []
    if employee is None:
        employees = frappe.get_all(
            "Elitehr Employee",
            fields=["name", "employee_name", "department","department_name","shift"]
        )
    else:
        employees = frappe.get_all(
            "Elitehr Employee",
            filters={"name":employee},
            fields=["name", "employee_name", "department", "department_name","shift"]
        )


    result = []
    for emp in employees:
        working_days = get_employee_working_days_and_time(emp)
        indexDate = from_date
        while indexDate <= to_date:
            weekday = getdate(indexDate).strftime("%A")  # Saturday, Sunday...
            if weekday not in working_days:
                indexDate = add_days(indexDate, 1)
                continue

            day_result = get_employee_attendance(date=indexDate, employee=emp.name)
            if day_result:
                day_result["department"] = emp.department
                day_result["department_name"] = emp.department_name
                result.append(day_result)
            indexDate = add_days(indexDate, 1)    
    
    # frappe.log(f"get_employee_attendance_handler/ results: {result}")
    return result


def get_employee_attendance(employee, date):

    if not employee or not date:
        frappe.throw("لازم تحدد الموظف والتاريخ")

    # ✅ بيانات الموظف
    emp = frappe.get_doc("Elitehr Employee", employee)

    working_days_and_time = get_employee_working_days_and_time(employee)

    # ✅ بصمات اليوم
    checkins = frappe.get_all(
        "Elitehr Employee Checkin",
        filters={
            "employee": employee,
            "date": date
        },
        fields=["log_type", "time"],
        order_by="time asc"
    )

    check_in = None
    check_out = None

    for c in checkins:
        if c.log_type == "Check In" and not check_in:
            check_in = c.time
        elif c.log_type == "Check Out":
            check_out = c.time

    # Working Hours
    working_seconds = 0
    working_hours = ""

    if check_in and check_out:
        total_seconds = time_diff_in_seconds(check_out, check_in)
        if total_seconds > 0:
            working_seconds = total_seconds
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            working_hours = f"{hours:02d}:{minutes:02d}"

    # Status
    statusCode = "Absent"
    status = _("Absent")
    status_color = "color4"
    late_minutes = 0

    if check_in:
        statusCode = "Present"
        status = _("Present")
        status_color = "color3"

    # Late
    currentDay =   getdate(date).strftime("%A")
    currentDayTime = working_days_and_time.get(currentDay)
    if check_in and currentDayTime['from_time']:
        late_diff = time_diff_in_seconds(check_in, currentDayTime['from_time'])
        if late_diff > 0:
            late_minutes = int(late_diff // 60)
            statusCode = "Late"
            status = _("Late ({0}) minutes").format(late_minutes)
            status_color = "color1"

    # Early Out
    if check_out and currentDayTime['to_time']:
        early_diff = time_diff_in_seconds(currentDayTime['to_time'], check_out)
        if early_diff > 0:
            early_minutes = int(early_diff // 60)
            statusCode = "Early Out"
            status = _("Early Out ({0}) minutes").format(early_minutes)
            status_color = "color1"

    return {
        "employee": emp.name,
        "employee_name": emp.employee_name,
        "date": date,
        "check_in": check_in or "",
        "check_out": check_out or "",
        "status": status,
        "status_code": statusCode,
        "working_hours": working_hours,
        "working_seconds": working_seconds,
        "late_minutes": late_minutes,
        "status_color": status_color
    }

@frappe.whitelist()
def set_attendance(logType,employee, date = today()):
    date = today()
    working_days = get_employee_working_days_and_time(employee)
    currentDay =   getdate(date).strftime("%A")
    
    if currentDay not in working_days:
        frappe.throw(_("No attendance outside working days"))

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