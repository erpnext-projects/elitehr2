# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict
from datetime import datetime, timedelta,date
from frappe.utils import get_datetime, time_diff_in_seconds, format_datetime, now_datetime, nowtime, get_first_day, get_last_day, add_months, flt, today,add_days,getdate
import calendar
import math

class ElitehrEmployeeCheckin(Document):
    def on_update(self):
        if self.log_type == "Check In":
            get_attendance_penalty(employee = self.employee, date = self.date,status_code="Late",notify=True)
        elif self.log_type == "Check Out":
            get_attendance_penalty(employee = self.employee, date = self.date,status_code="Early Out",notify=True)
        
            
        
        
def get_attendance_penalty(employee, date, status_code=None,notify=False):
    attendace_status = get_employee_attendance(employee, date)

    frappe.log(f"Attendance after save: {attendace_status}")

    if attendace_status and attendace_status.get('status_code') == status_code:
        late_minutes = attendace_status.get("late_minutes", 0)
        early_minutes = attendace_status.get("early_minutes", 0)

        penalty_type = {
            "Late": "lateness",
            "Early Out": "Early Out",
        }.get(status_code)

        if penalty_type is None:
            return

        # get level from lateness
        policy = get_matched_penalty(penalty_type=penalty_type)
        target_policies = []

        if status_code == "Late":
            target_policies = [
                row for row in policy.deduction_levels 
                if row.get("from") <= late_minutes <= row.get("to")
            ]
        elif status_code == "Early Out":
            target_policies = [
                row for row in policy.deduction_levels 
                if row.get("from") <= early_minutes <= row.get("to")
            ]
       
            
        if not target_policies:
            frappe.throw(f"لم يتم العثور على شريحة مطابقة في اللائحة لدقائق : {late_minutes if status_code == 'Late' else early_minutes} من نوع {status_code}. يرجى مراجعة إدارة الموارد البشرية.")
            return


        target_level = target_policies[0]
        frappe.log(f"Matched lateness minutes: {late_minutes} falls in range {target_level.get('from')} - {target_level.get('to')}, action is {target_level.action} with value {target_level.value}")


        # occurrences in the past month
        from_date, to_date = get_month_from_and_end_based_on_closing_day(date)
        if to_date < getdate(date):
            from_date = add_days(to_date, 1)
            to_date = add_months(to_date, 1)

        prior_lateness = get_employee_attendance_handler(
            employee=employee,
            from_date= from_date,
            to_date= to_date
        )
        # frappe.log(f"from: {from_date}, to: {to_date}, prior_lateness: {prior_lateness}")

        specific_prior_count = sum(
            1 for p in prior_lateness 
            if p.get("status_code") == status_code and target_level.get("from",0) <= p.get("late_minutes", 0) <= target_level.get("to",0) and getdate(p.get("date")) < getdate(date)
        )
        
        frappe.log(f"{specific_prior_count} occurrences of lateness in the past month matching the current range")

        # action
        index = min(specific_prior_count, len(target_policies ) - 1)
        target_action = target_policies[index]
        frappe.log(f"Applying action: {target_action.get('from')} - {target_action.get('to')}, action is {target_action.action} with value {target_action.value} , occurrences: {target_action.get('occurrence')} , message: {target_action.get('message')}")
        if notify:
            frappe.msgprint(_(target_action.get("message")))
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": _(target_action.get("message")),
                "for_user": frappe.session.user,
                "type": "Alert",
            }).insert(ignore_permissions=True)

        return target_action.as_dict()



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


def get_employee_working_days_and_time(employee,onlyCurrentDay=False):
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
    if onlyCurrentDay:
        currentDay = getdate(today()).strftime("%A")
        return working_days.get(currentDay) if currentDay in working_days else {}
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


@frappe.whitelist()
def get_monthly_attendance_matrix(ref_date):

    from_date, to_date = get_month_from_and_end_based_on_closing_day(ref_date)
    frappe.log(f"Generating attendance matrix for date: {ref_date}, from: {from_date}, to: {to_date}")

    rows = get_employee_attendance_handler(
        from_date=from_date,
        to_date=to_date
    ) or []


    result = {}
    for row in rows:
        emp = row.get("employee")

        # إنشاء الموظف مرة واحدة فقط
        if emp not in result:
            result[emp] = {
                "employee": emp,
                "employee_name": row.get("employee_name"),
                "department": row.get("department"),
                "department_name": row.get("department_name"),
                "job_title": row.get("job_title"),
                "days": {},
                "presents": 0,
                "absens": 0,
                "lates": 0,
                "leaves": 0
            }

        date_obj = getdate(row.get("date"))
        day_number = str(date_obj.day)
        day_name_en = date_obj.strftime("%A")

        status = row.get("status_code")
        # عدّ الحالات
        if status == "Present":
            result[emp]["presents"] += 1
        elif status == "Absent":
            result[emp]["absens"] += 1
        elif status == "Late":
            result[emp]["lates"] += 1
        elif status == "Leave":
            result[emp]["leaves"] += 1

        # تخزين حالة اليوم + اسم اليوم بالعربي
        result[emp]["days"][date_obj] = {
            "day_name": day_name_en,
            **row,
        }
    frappe.log(f"Attendance matrix result: {result[emp]["days"]}")
    return list(result.values())


# دالة الاساسية
@frappe.whitelist()
def get_employee_attendance_handler(employee=None,from_date=None,to_date=None):
    
    if from_date is None:
        from_date = today()

    if to_date is None:
        to_date = from_date

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    targetEmployees = []
    if employee is None:
        employees = frappe.get_all(
            "Elitehr Employee",
            filters={"status": "Active"},
            fields=["name", "employee_name", "department","department_name","shift","job_title"]
        )
    else:
        employees = frappe.get_all(
            "Elitehr Employee",
            filters={"name":employee},
            fields=["name", "employee_name", "department", "department_name","shift","job_title"]
        )


    result = []
    for emp in employees:
        working_days = get_employee_working_days_and_time(emp)
        indexDate = from_date
        while indexDate <= to_date:
            weekday = getdate(indexDate).strftime("%A")  # Saturday, Sunday...
            # return weekday
            # check is weekend
            if weekday not in working_days:
                result.append({
                    "employee": emp.name,
                    "employee_name": emp.employee_name,
                    "department": emp.department,
                    "department_name": emp.department_name,
                    "job_title": emp.job_title,
                    "date": indexDate,
                    "check_in": "",
                    "check_out": "",
                    "status": _("Weekend"),
                    "status_code": "Weekend",
                    "working_hours": 0,
                    "working_seconds": 0,
                    "late_minutes": 0,
                    "status_color": ""
                })
                indexDate = add_days(indexDate, 1)
                continue

            # check leave request (holiday)
            if check_employee_leave(emp.name, indexDate):
                result.append({
                    "employee": emp.name,
                    "employee_name": emp.employee_name,
                    "department": emp.department,
                    "department_name": emp.department_name,
                    "job_title": emp.job_title,
                    "date": indexDate,
                    "check_in": "",
                    "check_out": "",
                    "status": _("Leave"),
                    "status_code": "Leave",
                    "working_hours": 0,
                    "working_seconds": 0,
                    "late_minutes": 0,
                    "status_color": ""
                })
                indexDate = add_days(indexDate, 1)
                continue

             # get attendance

            day_result = get_employee_attendance(date=indexDate, employee=emp.name)
            if day_result:
                day_result["department"] = emp.department
                day_result["department_name"] = emp.department_name
                day_result["job_title"] = emp.job_title
                result.append(day_result)
            indexDate = add_days(indexDate, 1)    
    
    # frappe.log(f"get_employee_attendance_handler/ results: {result}")
    return result


def check_employee_leave(employee, date):

    leave = frappe.db.exists(
        "Elitehr Requests",
        {
            "employee": employee,
            "status": "Completed",
            "start_date": ["<=", date],
            "end_date": [">=", date]
        }
    )

    return leave

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
    early_minutes = 0

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
            
            hours = late_minutes // 60
            minutes = late_minutes % 60

            if hours > 0:
                if minutes > 0:
                    status = _("Late {0}h {1}m").format(int(hours), str(int(minutes)).zfill(2))
                else:
                    status = _("Late {0}h").format(int(hours))
            else:
                status = _("Late {0}m").format(int(late_minutes))

            # status = _("Late ({0}) minutes").format(late_minutes)
            status_color = "color1"

    # Early Out
    if check_out and currentDayTime['to_time']:
        early_diff = time_diff_in_seconds(currentDayTime['to_time'], check_out)
        if early_diff > 0:
            early_minutes = int(early_diff // 60)
            statusCode = "Early Out"

            hours = early_minutes // 60
            minutes = early_minutes % 60

            if hours > 0:
                if minutes > 0:
                    status = _("Early Out {0}h {1}m").format(int(hours), str(int(minutes)).zfill(2))
                else:
                    status = _("Early Out {0}h").format(int(hours))
            else:
                status = _("Early Out {0}m").format(int(early_minutes))

            # status = _("Early Out ({0}) minutes").format(early_minutes)
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
        "early_minutes": early_minutes,
        "status_color": status_color
    }


def get_valid_attendance_site(employee,lat, long):
    # 0.000009
    # try converting lat and long to float
    try:
        lat = float(lat)
        long = float(long)
    except ValueError:
        frappe.throw(_("Invalid latitude or longitude"))

    employee_doc = frappe.get_doc("Elitehr Employee", employee)
    sites = employee_doc.fingerprint_sites
    
    distances = []
    for site in sites:
        site_doc = frappe.get_doc("Elitehr Fingerprint Sites", site.site_name)
        site_lat = float(site_doc.latitude)
        site_long = float(site_doc.longitude)
        allowed_range = float(site_doc.allowed_range or 0)

        is_valid, distance = verify_geofence(lat, long, site_lat, site_long, allowed_range)
        distances.append(f"Site: {site_doc.site_name}, Distance: {distance} meters, Valid: {is_valid}")

        if is_valid:
            return [True,site_doc,distance]

    # if end and not site found
    return [False, None, distances]


# used in get_valid_attendance_site
def verify_geofence(user_lat, user_lon, office_lat, office_lon, allowed_radius):
    # تحويل الدرجات إلى راديان
    user_lat, user_lon, office_lat, office_lon = map(math.radians, [user_lat, user_lon, office_lat, office_lon])

    # فرق الإحداثيات
    dlat = office_lat - user_lat
    dlon = office_lon - user_lon

    # حساب المسافة باستخدام صيغة هافيرسين
    a = math.sin(dlat / 2)**2 + math.cos(user_lat) * math.cos(office_lat) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # نصف قطر الأرض بالكيلومترات
    r = 6371000
    distance = c * r  # المسافة بالمتر
    distance = round(distance, 2)
    if distance <= allowed_radius:
        return True, distance
    else:
        return False, distance


# دالة الاساسية
@frappe.whitelist()
def set_attendance(logType,employee,latitude,Longitude,device_name,device_id):
    date = today()
    working_days = get_employee_working_days_and_time(employee)
    currentDay =   getdate(date).strftime("%A")
    
    if currentDay not in working_days:
        frappe.throw(_("No attendance outside working days"))

    if logType not in ["Check In","Check Out"]:
        frappe.throw("Attendance Log Type Not Valid.")
    current_time = now_datetime()

    #check if there's already a logType for today
    existing_log = frappe.db.exists(
        "Elitehr Employee Checkin",
        {
            "employee": employee,
            "date": date,
            "log_type": logType
        }    )
    if existing_log:
        frappe.throw(_("You have already done {0} for today").format(logType))

    new_log = frappe.get_doc({
        "doctype": "Elitehr Employee Checkin",
        "employee": employee,
        "log_type": logType,
        "date": date,
        "time": now_datetime().strftime("%H:%M:%S"), 
        "latitude": latitude,
        "longitude": Longitude,
        "device_name": device_name,
        "device_id": device_id
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

    set_attendance("Check In",employees[0].name,"","","","")

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

    set_attendance("Check In",employee,"","","","")
    return True



@frappe.whitelist()
def get_matched_penalty(penalty_type):
    docs = frappe.get_all(
        "Elitehr Deduction Rules",
        filters={
            "type": penalty_type,
            "active": 1
        },
        limit=1
    )
    if not docs:
        frappe.throw(_("No active lateness deduction rules found. Please contact HR Manager. for {penalty_type}").format(penalty_type=penalty_type))
    
    return frappe.get_doc("Elitehr Deduction Rules", docs[0].name)


@frappe.whitelist()
def get_month_from_and_end_based_on_closing_day(ref_date=None):

    closing_day = int(
        frappe.db.get_single_value("Elitehr Company", "cutoff_day") or 30
    )
    frappe.log(f"Company cutoff_day: {closing_day}")

    ref_date = getdate(ref_date) if ref_date else getdate()
    
    previous_month = add_months(ref_date, -1)

    from_date = date(
        previous_month.year,
        previous_month.month,
        closing_day + 1
    )

    to_date = date(
        ref_date.year,
        ref_date.month,
        closing_day
    )

    return from_date, to_date