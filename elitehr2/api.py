import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import getdate,nowdate
from elitehr2.elitehr2.report.employee_leaves_balances.employee_leaves_balances import get_leave_summary 


@frappe.whitelist(allow_guest=True)
def login(username, password):

	login_manager = LoginManager()
	login_manager.authenticate(username, password)
	login_manager.post_login()

	user = frappe.get_doc("User", frappe.session.user)

	# Always refresh api_key and api_secret on login
	user.api_key = frappe.generate_hash(length=15)
	user.api_secret = frappe.generate_hash(length=15)
	user.save(ignore_permissions=True)

	api_secret = user.get_password("api_secret")

	access_token = f"{user.api_key}:{api_secret}"

	return {
		"access_token": access_token,
		"user": user.name,
		"full_name": user.full_name
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
	data = frappe.get_all(
		"Elitehr Requests Types",
		filters={
			"docstatus": "1",
			"category": "أجازة"
		},
		fields=[
			"name",
			"arabic_type_name"
		],
		order_by="name asc"
	)

	return {
		"status": "success",
		"data": data
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
		"Elitehr Requests Types",
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
	doc.type = request_type
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
	
	final_result = []
	for i in get_leave_summary([employee]):
		# emploayee, emploayee_name,  leave_name, days, used_days , percentage
		final_result.append({
			"employee": i[0],	
			"employee_name": i[1],
			"leave_name": i[2],
			"days": i[3],
			"used_days" : i[4],
			"percentage" : i[5],

		})
	return final_result