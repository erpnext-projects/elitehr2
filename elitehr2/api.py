import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import getdate,nowdate,today,get_first_day
from datetime import datetime
# from elitehr2.elitehr2.report.employee_leaves_balances.employee_leaves_balances import get_leave_summary 
from  elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_employee_attendance_handler


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
def get_employee_leave_requests():

	user = frappe.session.user
	employee = frappe.db.get_value(
		"Elitehr Employee",
		{"login_data": user},
		["name", "employee_name"],
		as_dict=True
	)

	if not employee:
		frappe.throw(_("No employee linked to this user"))

	data = frappe.get_all(
		"Elitehr Requests",
		filters={
			"employee": employee.name
		},
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

	result = []

	for row in data:
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
			"history": get_request_status_history(row.name)
		})

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
	

def get_employee_logged_in(): 
	user = frappe.session.user

	employee = frappe.db.get_value(
		"Elitehr Employee",
		{"login_data": user},
		["name", "employee_name"],
		as_dict=True
	)

	if not employee:
		frappe.throw(_("No employee linked to this user"))
	return employee