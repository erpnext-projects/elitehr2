import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import getdate,nowdate,today,get_first_day
from datetime import datetime
# from elitehr2.elitehr2.report.employee_leaves_balances.employee_leaves_balances import get_leave_summary 
from  elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_employee_attendance_handler,set_attendance,get_valid_attendance_site,get_employee_working_days_and_time
from frappe.utils.file_manager import save_file
import json
from frappe.model.meta import get_meta

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

    result = []

    if only_leave_requests:
        filters["type"] = "LEAVE"
    
        data = frappe.get_all(
            "Elitehr Requests",
            filters=filters,
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
            ],
            order_by="name asc"
        )

        for row in data:

            files = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Elitehr Requests",
                    "attached_to_name": row.name
                },
                fields=["file_name", "file_url"]
            )

            result.append({
                "id": row.name,
                "type": row.type,
                "type_name": row.request_type_name,
                "leave_type": row.leave_type,
                "leave_type_name": row.leave_type_name,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "total_days": row.total_days,
                "subject": row.subject,
                "details": row.details,
                "status": _(row.status),
                "creation": row.creation,
                "files": files,
                "history": get_request_status_history(row.name)
            })
    else:
        filters["type"] = ["!=", "LEAVE"]
        data = frappe.get_all(
            "Elitehr Requests",
            filters=filters,
            fields=["*"],
            order_by="name asc"
        )
        
        for row in data:
            row_dict = dict(row)
            files = frappe.get_all(
                    "File",
                    filters={
                        "attached_to_doctype": "Elitehr Requests",
                        "attached_to_name": row.name
                    },
                    fields=["file_name", "file_url"]
                )
            row_dict["files"] = files
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
def get_employees_leave_summary(employees=None):

    data = []

    if not employees:
        employees = frappe.get_all("Elitehr Employee", pluck="name")

    for emp_name in employees or []:
        emp = frappe.get_doc("Elitehr Employee", emp_name)

        for l in emp.table_leaves:
            used_days = frappe.db.sql("""
                SELECT SUM(total_days)
                FROM `tabElitehr Requests`
                WHERE employee=%s
                AND leave_type=%s
                AND status="Completed"
                
            """, (emp.name, l.leave))[0][0] or 0

            total_days = float(l.days or 0)
            percentage = (used_days / total_days * 100) if total_days else 0

            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "leave_name": l.leave_name or l.leave,
                "days": l.days,
                "used_days": used_days,
                "percentage": round(percentage, 1),
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

    result = []

    for task in tasks:
        tags = frappe.get_all(
            "Tag Link",
            filters={
                "document_type": "Elitehr Tasks",
                "document_name": task.name
            },
            pluck="tag"
        )

        assigns = frappe.get_all(
            "ToDo",
            filters={
                "reference_type": "Elitehr Tasks",
                "reference_name": task.name,
                "status": ["!=", "Cancelled"]
            },
            fields=["allocated_to"]
        )

        assigns_data = [
            {
                "email": assign.allocated_to,
                "name": frappe.db.get_value(
                    "User",
                    assign.allocated_to,
                    "full_name"
                )
            }
            for assign in assigns
        ]

        result.append({
            "name": task.name,
            "title": task.task_title,
            "description": task.task_description,
            "priority": _(task.priority),
            "due_date": task.due_date,
            "status": _(task.status),
            "tags": tags,
            "assigns": assigns_data
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
        "current_month_salary": 0
    }
    # attendance_dayes
    # from start of month to today 
    attendance = get_employee_attendance_handler(employee=emp.name, from_date=get_first_day(today()),to_date=today())
    # filter by status
    attendance = [a for a in attendance if a['status_code'] in ("Present", "Late", "Early Out")]
    attendance_dayes = len(attendance)
    final_result["attendance_dayes"] = attendance_dayes

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
        "status": "Completed",
        "device_id": phone_id
    })

    # check if request for this device is already created and pending
    pending_request = frappe.db.exists("Elitehr Requests", {
        "employee": emp.name,
        "status": ["!=", "Completed"],
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
        ["name", "employee_name","branche","department"],
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
    