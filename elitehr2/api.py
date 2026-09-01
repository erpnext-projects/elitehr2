import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import getdate,nowdate,today,get_first_day,add_days
from datetime import datetime
# from elitehr2.elitehr2.report.employee_leaves_balances.employee_leaves_balances import get_leave_summary 
from  elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_employee_attendance_handler,set_attendance,get_valid_attendance_site,get_employee_working_days_and_time,get_month_from_and_end_based_on_closing_day
from frappe.utils.file_manager import save_file
import json
from frappe.model.meta import get_meta
from collections import defaultdict

@frappe.whitelist(allow_guest=True)
def login(username, password):

    login_manager = LoginManager()
    login_manager.authenticate(username, password)
    login_manager.post_login()
    

    user = frappe.get_doc("User", frappe.session.user)

    # Always refresh api_key and api_secret on login
    # user.api_key = frappe.generate_hash(length=15)
    # user.api_secret = frappe.generate_hash(length=15)
    # user.save(ignore_permissions=True)
    # api_secret = user.get_password("api_secret")

    if not user.api_key:
        user.api_key = frappe.generate_hash(length=15)
        user.save(ignore_permissions=True)
    api_secret = frappe.generate_hash(length=15)
    user.api_secret = api_secret
    user.save(ignore_permissions=True)
    access_token = f"{user.api_key}:{api_secret}"

    return {
        "access_token": access_token,
        "user": user.name,
        "full_name": user.full_name,
        "role": user.custom_assign_role
    }

@frappe.whitelist()
def refresh_token():
    user = frappe.get_doc("User", frappe.session.user)
    new_secret = frappe.generate_hash(length=15)
    user.api_secret = new_secret
    user.save(ignore_permissions=True)
    access_token = f"{user.api_key}:{new_secret}"
    return {
        "access_token": access_token,
        "message": "Token Updated successfully"
    }

@frappe.whitelist()
def logout():

    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    user_doc.api_key = None
    user_doc.api_secret = None
    user_doc.save(ignore_permissions=True)

    frappe.sessions.clear_sessions(user=user)
    frappe.local.login_manager.logout()
    return {
        "message": "Logged out successfully"
    }



# used in app
@frappe.whitelist()
def get_leave_request_types():
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},
        ["name", "employee_name"],
        as_dict=True
    )
    if not employee:
        frappe.throw(_("No employee linked to this user"))

    leaves = frappe.get_all(
        "Elitehr Employee Leaves Child Table",
        filters={
            "parent": employee.name
        },
        fields=["leave", "leave_name", "days"]
    )

    return {
        "status": "success",
        "data": leaves
    }

@frappe.whitelist()
def get_request_types():
    employee = get_employee_logged_in()

    request_types = frappe.get_all(
            "Elitehr Requests Types",
            filters={"docstatus":1},
            fields=["name","arabic_type_name","english_type_name","code","category"]
        )

    return {
        "status": "success",
        "data": request_types
    }   

@frappe.whitelist()
def get_notifications(is_read=0):
    employee = get_employee_logged_in()

    if is_read not in ("0", "1"):
        frappe.throw(_("Invalid value for is_read, must be 0 or 1"))

    notifications = frappe.get_all(
        "Notification Log",
        filters={
            "for_user": frappe.session.user,
            "read": is_read
        },
        fields=["name","creation","subject","type","read"]
    )

    return {
        "status": "success",
        "data": notifications
    }


@frappe.whitelist()
def create_leave_request(request_type, subject,start_date, end_date, details):

    """
    إنشاء طلب إجازة للمستخدم الحالي

    المدخلات:
    - from_date : تاريخ البداية
    - to_date : تاريخ النهاية
    - subject : الموضوع
    - notes : السبب / الملاحظات
    - request_type : نوع الإجازة (من Elitehr Requests Types)
    """

    user = frappe.session.user

    if user == "Guest":
        frappe.throw(_("User not logged in"))

    if not request_type:
        frappe.throw(_("Request type is required"))
    
    request_type_exists = frappe.db.exists(
        "Elitehr Leave Policies",
        {
            "name": request_type,
        }
    )

    if not request_type_exists:
        frappe.throw(_("Invalid or unpublished request type"))
    
    if not subject or not str(subject).strip():
        frappe.throw(_("Subject is required"))


    if not start_date:
        frappe.throw(_("From date is required"))

    if not end_date:
        frappe.throw(_("To date is required"))

    if not details or not str(details).strip():
        frappe.throw(_("Details are required"))

    start_date = getdate(start_date)
    end_date = getdate(end_date)
    today = getdate(nowdate())

    if start_date > end_date:
        frappe.throw(_("From date cannot be greater than To date"))

    if start_date < today:
        frappe.throw(_("From date cannot be in the past"))


    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},
        ["name", "employee_name"],
        as_dict=True
    )

    if not employee:
        frappe.throw(_("No employee linked to this user"))

    # return employee
    

    doc = frappe.new_doc("Elitehr Requests")
    doc.status = "New"
    doc.type="LEAVE"
    doc.leave_type = request_type
    doc.employee = employee.name
    doc.start_date = start_date
    doc.end_date = end_date
    doc.subject = subject
    doc.details = details
    doc.insert()

    return {
        "status": "success",
        "message": _("Leave request created successfully"),
        "request_id": doc.name
    }


@frappe.whitelist()
def create_request(**kwargs):
    emp = get_employee_logged_in()

    parameters = kwargs.copy()
    parameters["employee"] = emp.name

    
    attachments_raw = parameters.pop("attachments", None)
    clean_raw = str(attachments_raw).strip()
    attachments_list = []
    
    if attachments_raw:
        try:
            if isinstance(attachments_raw, str):
                attachments_list = json.loads(attachments_raw)
            elif isinstance(attachments_raw, list):
                attachments_list = attachments_raw
        except Exception as e:
            frappe.log_error(str(e), "Error Parsing Attachments")
            pass

 

    try:
        doc = frappe.get_doc({
            "doctype": "Elitehr Requests",
            **parameters
        })

        doc.insert()

        uploaded_files_urls = {}

        if hasattr(frappe.local, "request") and frappe.request.files:
            # return len(frappe.request.files.getlist("attachments"))
            for file_key in frappe.request.files:
                for file in frappe.request.files.getlist(file_key):
                    if file.filename:
                        saved_file = save_file(
                            fname=file.filename,
                            content=file.read(),
                            dt="Elitehr Requests",
                            dn=doc.name,
                            is_private=1
                        )
                        uploaded_files_urls[file.filename] = saved_file.file_url
            
        if doc.type in ["EXPENSE_PURCHASE","EXPENSE_TRAVEL","RESIGNATION"] and attachments_list:
            for att in attachments_list:
                fname = att.get("file_name")
                doc.append("attachments", {
                    "file_name": fname,
                    "attach_type": att.get("attach_type"),
                    "notes": att.get("notes"),
                    # جلب رابط الملف الفعلي الذي تم رفعه باستخدام اسم الملف كمرجع
                    "file": uploaded_files_urls.get(fname) 
                })
            doc.save()

        doc.reload()


    except frappe.ValidationError as e:
        frappe.local.response.http_status_code = 417
        return {
            "status": "error",
            # "error_code": 1003,
            "message": str(e)
        }

    return {
        "status": "success",
        "message": _("Request created successfully"),
        "data": doc.as_dict()
    }


@frappe.whitelist()
def get_expense_attach_types():
    emp = get_employee_logged_in()

    meta = get_meta("Elitehr Requests")
    table_field = meta.get_field("attachments")

    if not table_field:
        return {"status": "error", "message": "Child table not found"}
    
    child_meta = get_meta(table_field.options)

    attach_type_field = child_meta.get_field("attach_type")
    if not attach_type_field:
        return {"status": "error", "message": "Field not found"}

    options = attach_type_field.options.split('\n')
    clean_options = [{"name": opt,"title": _(opt)} for opt in options if opt.strip()]
    
    return {
        "status": "success",
        "data": clean_options
    }


@frappe.whitelist()
def get_employee_requests(only_leave_requests=False):

    user = frappe.session.user
    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},
        ["name", "employee_name"],
        as_dict=True
    )

    if not employee:
        frappe.throw(_("No employee linked to this user"))

    filters = {"employee": employee.name}
    
    if only_leave_requests:
        filters["type"] = "LEAVE"
        fields=[
                "name",
                "type",
                "request_type_name",
                "leave_type",
                "leave_type_name",
                "start_date",
                "end_date",
                "total_days",
                "subject",
                "details",
                "status",
                "creation",
            ]
    else:
        filters["type"] = ["!=", "LEAVE"]
        fields = ["*"]

    data = frappe.get_all(
        "Elitehr Requests",
        filters=filters,
        fields=fields,
        order_by="name asc"
    )
    
    if not data:
        return {"status": "success", "data": []}
    
    request_names = [row.name for row in data]
    all_files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Elitehr Requests",
            "attached_to_name": ("in", request_names) 
        },
        fields=["attached_to_name", "file_name", "file_url"]
    )

    files_map = defaultdict(list)
    for f in all_files:
        files_map[f.attached_to_name].append({
            "file_name": f.file_name,
            "file_url": f.file_url
        })
        
    result = []
    for row in data:
        row_dict = dict(row)
        row_dict["id"] = row.name
        row_dict["files"] = files_map.get(row.name, [])
        
        if only_leave_requests:
            row_dict["status"] = _(row.status)
            row_dict["history"] = get_request_status_history(row.name)
        result.append(row_dict)
        
    return {
        "status": "success",
        "data": result
    }


def get_request_status_history(docname):

    users = frappe.get_all("User", fields=["name", "full_name"])
    user_map = {u.name: u.full_name for u in users}

    history = []

    # creation event (اختياري هنا أو في الدالة الرئيسية)
    doc = frappe.get_doc("Elitehr Requests", docname)

    history.append({
        "action": "created",
        "status": _("New"),
        "by": user_map.get(doc.owner, doc.owner),
        "date": doc.creation
    })

    # status changes
    versions = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": "Elitehr Requests",
            "docname": docname
        },
        fields=["data", "creation", "owner"],
        order_by="creation asc"
    )

    for v in versions:
        data = frappe.parse_json(v.data)

        for change in data.get("changed", []):
            if change[0] == "status":
                history.append({
                    "action": "status_changed",
                    "from": change[1],
                    "to": change[2],
                    "by": user_map.get(v.owner, v.owner),
                    "date": v.creation
                })

    return history


@frappe.whitelist()
def get_requests_field_options(fieldname):
    emp = get_employee_logged_in()

    meta = frappe.get_meta("Elitehr Requests")
    field = meta.get_field(fieldname)

    if not field:
        return {
            "status": "error",
            "message": "Field not found"
        }

    options = []

    if field.fieldtype == "Select" and field.options:
        options = [{"name": opt, "title": opt} for opt in field.options.split("\n")]

    elif field.fieldtype == "Link" and field.options:

        if field.options == "Elitehr Fingerprint Sites":
            records = frappe.get_all(field.options, fields=["name","site_name"], filters={"name":["!=",emp.department]})
            options = [{"name": r.name, "title": r.site_name} for r in records]

        elif field.options == "Elitehr Branches":
            records = frappe.get_all(field.options, fields=["name","branch_name"], filters={"name":["!=",emp.branche]})
            options = [{"name": r.name, "title": r.branch_name} for r in records]

    return {
        "status" : "success",
        "options": options
    }


# get_leave_summary

@frappe.whitelist()
def get_employee_leave_summary():

    user = frappe.session.user

    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},
        ["name", "employee_name"],
        as_dict=True
    )

    if not employee:
        frappe.throw(_("No employee linked to this user"))
    
    return get_employees_leave_summary(employees=[employee.name])



@frappe.whitelist()
def get_employees_leave_summary(employees=None, year=None):

    data = []
    
    if not year:
        year = getdate(nowdate()).year
    else:
        year = int(year)
    
    roles = frappe.get_roles()
    if "Elite HR Employee" in roles and "Elite HR Admin" not in roles:
            employee = frappe.db.get_value(
                "Elitehr Employee",
                {"login_data": frappe.session.user},
                "name"
            )
            employees = [employee]
            
    if not employees:
        employees = frappe.get_all("Elitehr Employee", pluck="name")
    if not employees:
        return data
    
    if isinstance(employees, str):
        employees = [employees]
        
    
    employees_data = frappe.get_all(
        "Elitehr Employee",
        filters={"name": ("in", employees)},
        fields=["name", "employee_name"]
    )
    employee_map = {
        emp.name: emp.employee_name
        for emp in employees_data
    }
    
    start_date = f"{year}-01-01 00:00:00"
    end_date = f"{year}-12-31 23:59:59"
    
    leave_rows = frappe.get_all(
        "Elitehr Employee Leaves Child Table",
        filters={
            "parent": ("in", employees),
            "parenttype": "Elitehr Employee",
            "creation": ["between", [start_date, end_date]]
        },
        fields=[
            "parent",
            "leave",
            "leave_name",
            "days"
        ]
    )

    used_rows = frappe.db.sql("""
        SELECT
            employee,
            leave_type,
            SUM(total_days) AS used_days
        FROM `tabElitehr Requests`
        WHERE
            type='LEAVE'
            AND status='Approved'
            AND employee IN %(employees)s
            AND YEAR(creation) = %(year)s
        GROUP BY
            employee,
            leave_type
    """, { "employees":tuple(employees), "year": year }, as_dict=True)

    used_map = {
        (row.employee, row.leave_type): float(row.used_days or 0)
        for row in used_rows
    }

    for leave in leave_rows:

        total_days = float(leave.days or 0)
        used_days = used_map.get(
            (leave.parent, leave.leave),
            0
        )

        percentage = (
            used_days / total_days * 100
            if total_days else 0
        )

        data.append({
            "employee": leave.parent,
            "employee_name": employee_map.get(leave.parent),
            "leave_name": leave.leave_name or leave.leave,
            "days": leave.days,
            "used_days": used_days,
            "percentage": round(percentage, 1),
            "avilable": int(leave.days) - int(used_days)
        })

    return data


@frappe.whitelist()
def get_employee_attendance_by_date(date):
    emp = get_employee_logged_in()
    # from_date = datetime.strptime(str(date), "%d-%m-%Y").date()
    
    res = get_employee_attendance_handler(employee=emp.name,from_date=getdate(date))
    # from_date
    return res



@frappe.whitelist()
def get_employee_tasks():
    emp = get_employee_logged_in()
    frappe.local.lang = "en"

    tasks = frappe.get_all(
        "Elitehr Tasks",
        filters={ "responsable": emp.name },
        fields=["name", "task_title", "task_description", "priority", "due_date","status"]
    )
    if not tasks:
        return []
    
    task_names = [task.name for task in tasks]
    
    tags_data = frappe.get_all(
        "Tag Link",
        filters={
            "document_type": "Elitehr Tasks",
            "document_name": ("in", task_names)
        },
        fields=["document_name", "tag"]
    )
    tags_map = defaultdict(list)
    for t in tags_data:
        tags_map[t.document_name].append(t.tag)
        
    assigns_data = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Elitehr Tasks",
            "reference_name": ("in", task_names),
            "status": ["!=", "Cancelled"]
        },
        fields=["reference_name", "allocated_to"]
    )
    
    user_emails = list(set([a.allocated_to for a in assigns_data if a.allocated_to]))
    user_map = {}
    if user_emails:
        users = frappe.get_all(
            "User",
            filters={"name": ("in", user_emails)},
            fields=["name", "full_name"]
        )
        # إنشاء قاموس: الإيميل -> الاسم الكامل
        user_map = {u.name: u.full_name for u in users}

    # ربط الإسنادات والأسماء بالمهمة الخاصة بها
    assigns_map = defaultdict(list)
    for a in assigns_data:
        assigns_map[a.reference_name].append({
            "email": a.allocated_to,
            "name": user_map.get(a.allocated_to)
        })
    result = []
    
    for task in tasks:
        result.append({
            "name": task.name,
            "title": task.task_title,
            "description": task.task_description,
            "priority": _(task.priority),
            "due_date": task.due_date,
            "status": _(task.status),
            "tags": tags_map.get(task.name, []),
            "assigns": assigns_map.get(task.name, [])
        })
        
    return result

@frappe.whitelist()
def update_task_status(task_name, status):
    emp = get_employee_logged_in()

    task = frappe.get_doc("Elitehr Tasks", task_name)
    # check if status in field select options
    status_options = frappe.get_meta("Elitehr Tasks").get_field("status").options
    if status not in status_options.split("\n"):
        frappe.throw(_("Invalid status, must be one of: {0}").format(status_options.replace("\n", ", ")))
    task.status = status
    task.save()

    return {
        "status": "success",
        "message": _("Task status updated successfully")
    }

@frappe.whitelist()
def get_mobile_home_statistics():
    emp = get_employee_logged_in()

    final_result = {
        "attendance_dayes": 0,
        "leaves_balance": 0,
        "pending_requests": 0,
        "current_month_salary": 0,
        "late_minutes": 0
    }
    # attendance_dayes
    # from start of month to today 
    attendance = get_employee_attendance_handler(employee=emp.name, from_date=get_first_day(today()),to_date=today())
    # filter by status
    attendance = [a for a in attendance if a['status_code'] in ("Present", "Late", "Early Out")]
    attendance_dayes = len(attendance)
    final_result["attendance_dayes"] = attendance_dayes
    
    # late minutes
    late_attendance = [a for a in attendance if a['status_code'] in ("Late")]
    late_minutes = sum( int(a["late_minutes"])  for a in late_attendance)
    final_result["late_minutes"] = late_minutes
    

    # leaves
    leaves = get_employee_leave_summary()
    leaves_balance = sum( int(leave['days'])  - int(leave['used_days'])  for leave in leaves)
    final_result["leaves_balance"] = leaves_balance

    # pending requests by status not Completed
    pending_requests = frappe.db.count("Elitehr Requests", filters={"employee": emp.name, "status": ["!=", "Completed"]})
    
    final_result["pending_requests"] = pending_requests

    # salary of current month
    current_month_salary = frappe.db.get_value("Elitehr Payroll", 
        filters={
            "employee": emp.name,
            "date": ["between", (get_first_day(today()), today())]
            },
        fieldname="net_salary") or 0
    final_result["current_month_salary"] = current_month_salary

    return final_result
    



@frappe.whitelist()
def set_employee_attendance(attendace_type,lat,long,phone_name,phone_id):
    emp = get_employee_logged_in()
    now = datetime.now()
    date = now.date()
    time = now.time()

    # check phone_id in employee Requests and its Completed
    allowed_devices = frappe.db.exists("Elitehr Requests", {
        "employee": emp.name,
        "status": "Approved",
        "device_id": phone_id
    })

    # check if request for this device is already created and pending
    pending_request = frappe.db.exists("Elitehr Requests", {
        "employee": emp.name,
        "status": ["!=", "Approved"],
        "device_id": phone_id,
        "type": "ADD_AUTHORIZED_DEVICE"
    })

    if pending_request:
        # frappe.throw(_("Device not authorized for attendance, And There's a request for this device, waiting for approval"))
        frappe.local.response.http_status_code = 417
        return{
            "status": "error",
            "error_code": 1001,
            "message": _("Device not authorized for attendance, And There's a request for this device, waiting for approval")
        }

    if not allowed_devices:
        # frappe.throw(_("Device not authorized for attendance"))
        frappe.local.response.http_status_code = 417
        return{
            "status": "error",
            "error_code": 1002,
            "message": _("Device not authorized for attendance")
        }

    try:
        set_attendance(attendace_type,emp.name, lat, long, phone_name, phone_id)
        return {"status": "success",}

    except frappe.ValidationError as e:
        frappe.local.response.http_status_code = 417
        return {
            "status": "error",
            "error_code": 1003,
            "message": str(e)
        }





@frappe.whitelist()
def create_authorized_device_request(phone_id, phone_name, subject, details):
    emp = get_employee_logged_in()

    # check if there's already a pending request for this device
    existing_request = frappe.db.exists("Elitehr Requests", {
        "employee": emp.name,
        "type": "ADD_AUTHORIZED_DEVICE",
        "device_id": phone_id
    })

    if existing_request:
        frappe.throw(_("There's already a request for this device"))

    doc = frappe.new_doc("Elitehr Requests")
    doc.status = "New"
    doc.type="ADD_AUTHORIZED_DEVICE"
    doc.employee = emp.name
    doc.subject = subject
    doc.details = details
    doc.device_id = phone_id
    doc.device_name = phone_name
    doc.insert()

    return {
        "status": "success",
        "message": _("Device authorization request created successfully"),
        "request_id": doc.name,
        "request_status": doc.status
    }


@frappe.whitelist()
def check_attendance_status(lat, long):
    # try converting lat and long to float
    try:
        lat = float(lat)
        long = float(long)
    except ValueError:
        frappe.throw(_("Invalid latitude or longitude"))


    emp = get_employee_logged_in()
    is_valid, site_doc, distance = get_valid_attendance_site(emp.name,lat, long)

    if is_valid:
        return {
            "allowed_area": True,
            "site": site_doc.site_name,
            "distance": distance,
            "work_schedule": get_employee_working_days_and_time(emp.name,onlyCurrentDay=True),
            "attendance_status": get_employee_attendance_handler(employee=emp.name)
        }
    else:
        # respose code error code 400 with message
        return {
            "allowed_area": False,
            "distance": distance
        }
    





def get_employee_logged_in(): 
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Elitehr Employee",
        {"login_data": user},
        ["name", "employee_name","branche","department","login_data"],
        as_dict=True
    )

    if not employee:
        frappe.throw(_("No employee linked to this user"))

    frappe.local.lang = "ar"
    return employee


@frappe.whitelist()
def profile():
    emp = get_employee_logged_in()
    emp_doc = frappe.get_doc("Elitehr Employee", emp.name)
    data = emp_doc.as_dict()
    data["mobile_home_statistics"] = get_mobile_home_statistics()
    return data

@frappe.whitelist()
def employee_salary(only_current_month=False):
    emp = get_employee_logged_in()
    filters = {
        "employee": emp.name
    }

    
    if only_current_month:
        filters["date"] = ["between", (get_first_day(today()), today())]

    salary = frappe.get_all(
        "Elitehr Payroll",
        filters=filters,
        fields=["name"]
    )  

    final_result = []
    for s in salary:
        doc = frappe.get_doc("Elitehr Payroll", s.name)
        final_result.append(doc)


    return final_result


@frappe.whitelist()
def leave_policies_rules():
    # get single doc of leave policies rules

    meta = frappe.get_meta("Elitehr Leave Policies Rules")

    html_field = meta.get_field("html_itrd")

    return {
        "html": html_field.options
    }


@frappe.whitelist()
def mark_notifications_as_read():
    emp = get_employee_logged_in()

    notifications = frappe.get_all(
        "Notification Log",
        filters={
            "for_user": frappe.session.user,
            "read": 0
        },
        pluck="name"
    )

    for notification in notifications:
        frappe.db.set_value(
            "Notification Log",
            notification,
            "read",
            1,
            update_modified=False
        )
        
    frappe.db.commit()

    return {
        "status": "success",
        "total_marked": len(notifications),
        "message": _("Notifications marked as read")
    }
    


@frappe.whitelist()
def user_fcm(device_name,device_token,device_type):

    if device_type not in ["ios", "android"]:
        return {
            "success": False,
            "message": _("Invalid device type must ios or android")
        }

    emp = get_employee_logged_in()

    user_device = frappe.get_all("User Device",filters={"user":emp.login_data},fields=["name"])

    try:
        if user_device:
            # update existing device
            doc = frappe.get_doc("User Device", user_device[0].name)
            doc.device_name = device_name
            doc.device_token = device_token
            doc.device_type = device_type
            doc.is_active = True
            doc.save(ignore_permissions=True)
        else:
            # create new device
            doc = frappe.get_doc({
                "doctype": "User Device",
                "user": emp.login_data,
                "device_name": device_name,
                "device_token": device_token,
                "device_type": device_type,
                "is_active": True
            })
            doc.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        return{
            "success": False,
            "message": str(e)
        }

    return {
        "success": True,
        "device": doc.name
    }


# admin


def get_manager_team_members(manager_name):
    return frappe.get_all(
        "Elitehr Employee",
        filters={"manager": manager_name, "status": "Active"},
        fields=["name", "employee_name", "department", "department_name", "job_title","login_data"]
    )


@frappe.whitelist()
def get_manager_team_attendance_summary():
    manager = get_employee_logged_in()
    team_members = get_manager_team_members(manager.name)
    team_count = len(team_members)

    employee_names = [t.name for t in team_members]
    employee_phones = frappe.get_all(
        "Elitehr Employee",
        filters={"name": ["in", employee_names]},
        fields=["name", "phone_number"]
    )
    phone_map = {
        employee.name: employee.phone_number or ""
        for employee in employee_phones
    }
    
    attendance_records = []
    for t in team_members:
        attendance = get_employee_attendance_handler(
            employee=t.name,
            from_date=today(),
            to_date=today()
        )
        for record in attendance:
            record["phone_number"] = phone_map.get(t.name, "")
            
        attendance_records.append(attendance)


    return {
        "status": "success",
        "team_count": team_count,
        "data": attendance_records
    }

@frappe.whitelist()
def get_manager_team_week_attendance_summary():
    manager = get_employee_logged_in()
    team_members = get_manager_team_members(manager.name)
    
    from_date = add_days(today(), -6)
    to_date = today()

    grouped_by_date = defaultdict(list)


    for t in team_members:
        records = get_employee_attendance_handler(employee = t.name,from_date=from_date, to_date=to_date)
        for record in records:
            grouped_by_date[record["date"]].append(record)

    # data = [
    #     {
    #         "date": date,
    #     }
    #     for date, employees in sorted(grouped_by_date.items())
    # ]
    return {
        "status": "success",
        "data": grouped_by_date
    }
    # return {
    #     "status": "success",
    #     "data": [
    #         {date: employees}
    #         for date, employees in grouped_by_date.items()
    #     ]
    # }


@frappe.whitelist()
def get_manager_team_requests():
    manager = get_employee_logged_in()
    members = get_manager_team_members(manager.name)

    member_names = [m.get("name") for m in members]

    if not member_names:
        return {"status": "success", "data": []}

    requests = frappe.get_all(
        "Elitehr Requests",
        filters={
            "employee": ["in", member_names]
        },
        fields=["*"],
        order_by="creation desc"
    )

    return {"status": "success", "data": requests}


@frappe.whitelist()
def get_requests_responsible_for_user():

    emp = get_employee_logged_in()

    request_names = frappe.get_all(
        "Elitehr Requests",
        filters=[
            ["Elitehr Request Approvals", "responsible_id", "=", emp.name],
            # ["Elitehr Request Approvals", "status", "=", "Pending"]
        ],
        pluck="name",
        distinct=True
    )

    if not request_names:
        return {"success": True, "data": []}


    result = []

    for name in request_names:
        doc = frappe.get_cached_doc("Elitehr Requests", name)
        result.append(doc.as_dict())

    return {"success": True, "data": result}


@frappe.whitelist()
def update_request_approval_status(request_name, new_status):
    emp = get_employee_logged_in()

    if new_status not in ["Approved", "Rejected"]:
        return {"success": False, "message": "Invalid status, It must Approved or Rejected"}

    if not frappe.db.exists("Elitehr Requests", request_name):
        return {"success": False, "message": "هذا الطلب غير موجود."}
    
    doc = frappe.get_doc("Elitehr Requests", request_name)
    is_updated = False
    for level in doc.levels:
        if level.responsible_id == emp.name:
            level.status = new_status
            level.approved_by = frappe.session.user
            is_updated = True
            break
    if is_updated:
        doc.save()
        frappe.db.commit()
        return {
            "success": True, 
            "message": _("تم تحديث حالة الطلب إلى {0} بنجاح.").format(new_status)
        }
    else:
        return {
            "success": False, 
            "message": _("Error not updated request.")
        }


@frappe.whitelist()
def get_team_activity():
    manager = get_employee_logged_in()
    members = get_manager_team_members(manager.name)


    result = get_requests_updates(employees=members)
    
    return {
        "success": True,
        "data": {
            "team": [m.get("employee_name") for m in members if m.get("employee_name")],
            "activity": result
        }
        }


def get_requests_updates(limit=500,employees=None):
    if not employees:
        return []
    
    requests = frappe.get_all(
        "Elitehr Requests",
        filters={
            "employee": ["in", [e.get("name") for e in employees]]
        },
        fields=["name","employee","employee_name","request_type_name","creation"]
    )
    
    if not requests:
        return []
    
    requests_map = {
        r["name"]: r
        for r in requests
    }
    
    versions = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": "Elitehr Requests",
            "docname": ["in", list(requests_map.keys())]
        },
        fields=[
            "owner",
            "creation",
            "docname",
            "data"
        ],
        order_by="creation desc",
        limit=limit
    )

    activities = []
    for request in requests:
        activities.append({
            "type": "request_created",
            "employee_name": request["employee_name"],
            "request_name": request["name"],
            "request_type": request["request_type_name"],
            "date":  request["creation"]
        })
        
    for version in versions:
        data = json.loads(version.data or "{}")
        
        request = requests_map.get(version.docname)
        if not request:
            continue
        
        employee_name = request["employee_name"]
        request_title = request["request_type_name"]

        
        for field, old_value, new_value in data.get("changed", []):

            if field != "status":
                continue
            
            activities.append({
                "type": "request_status_changed",
                "employee_name": employee_name,
                "request_name": version.docname,
                "request_type": request_title,
                "status": new_value,
                "date": version.creation
            })

    activities.sort(
        key=lambda x: x["date"],
        reverse=True
    )
    return activities


@frappe.whitelist()
def get_employee_month_attendance(employee_id,date):
    emp = get_employee_logged_in()

    from_date, to_date = get_month_from_and_end_based_on_closing_day(date)
    res = get_employee_attendance_handler(employee=employee_id,from_date= from_date,to_date=to_date)
    # from_date
    
    return {
            "success": True,
            "data": res
        }