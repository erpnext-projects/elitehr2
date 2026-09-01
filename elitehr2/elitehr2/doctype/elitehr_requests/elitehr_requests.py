# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe import _
from frappe.utils import date_diff,today
from datetime import datetime

class ElitehrRequests(Document):
    def validate(self):
        if self.status == "Completed":
            frappe.throw("غير مسموح بتعديل الطلب بعد اكتماله")
        
        if self.start_date and self.end_date:
            self.total_days = date_diff(self.end_date, self.start_date) + 1

    def before_save(self):
        self.getRequestLevels()
        self.checkRequestStatusFromLevel()
        # self.checkAllLevelsApproved()

        # check if request is add authorized device and its first one
        r = frappe.get_all("Elitehr Requests", filters={"employee": self.employee, "type": "ADD_AUTHORIZED_DEVICE"}, fields=["name"])
        if self.type == "ADD_AUTHORIZED_DEVICE" and len(r) == 0:
            self.status = "Approved" 


        


    def getRequestLevels(self):
        # Check if all levels have been approved
        emptyLevelStatus = list(filter(lambda l: l.status is None, self.levels))
        # if all is empty
        if len(emptyLevelStatus)  == len(self.levels):
            workflow = frappe.get_last_doc(
                'Elitehr Approval Workflow',
                filters={'active': '1', "request_type": self.type}
            ) if frappe.db.exists('Elitehr Approval Workflow', {'active': '1', "request_type": self.type}) else None
            
            if workflow is None:
                frappe.throw(_("No active approval workflow found for request type: {0}. Please contact the HR department.").format(self.type))
            
            department = frappe.get_doc("Elitehr Employee",self.employee)
            departmentId = department.department
            departmentName = department.department_name
            departmentManager = frappe.get_doc("Elitehr Fingerprint Sites",departmentId).manager
            if departmentManager is None:
                frappe.throw(f"لم يتم العثور علي مدير الفرع {departmentName}")

            manager = frappe.get_doc("Elitehr Employee",departmentManager)

            directSupervisor = frappe.get_doc('Elitehr Employee', self.employee).manager

            self.levels = []
            for level in workflow.levels:
                approvedType = level.approved_type
                responsible = None
                responsibleId = None

                if approvedType == "Specific Employee":
                    responsible = frappe.get_doc('Elitehr Employee', level.employee).employee_name
                    responsibleId = level.employee
                elif approvedType == "Department Manager":
                    responsible = manager.employee_name
                    responsibleId = manager.name
                elif approvedType == "Direct Supervisor":
                    if not directSupervisor:
                        frappe.throw(_("The request cannot be Save. Please go to the employee's file and select (Manager) from the (Employee Data) tab."))
                    directSupervisor = frappe.get_doc('Elitehr Employee', directSupervisor)
                    responsible = directSupervisor.employee_name
                    responsibleId = directSupervisor.name
                
                # frappe.log(approvedType)

                self.append('levels', {
                        'approved_type': approvedType,
                        "responsible": responsible,
                        "responsible_id": responsibleId
                })
                frappe.log(self.levels)

    # def checkAllLevelsApproved(self):
    #     # Check if all levels have been approved
    #     if self.levels and all(l.status is not None for l in self.levels):
    #         self.status = self.levels[-1].status
    def checkRequestStatusFromLevel(self):
        if any(l.status == "Rejected" for l in self.levels):
            self.status = "Rejected"
        elif all(l.status == "Approved" for l in self.levels):
            self.status = "Approved"
        else:
            self.status = "New"


@frappe.whitelist()
def get_requests_list(request_type):
    filters={"request_type_code": request_type}
    
    if "Elite HR Employee" in frappe.get_roles():
        employee = frappe.db.get_value(
            "Elitehr Employee",
            {"login_data": frappe.session.user},
            "name"
        )
        if not employee:
            return []
        
        subordinates = frappe.get_all(
            "Elitehr Employee", 
            filters={"manager": employee}, 
            pluck="name"
        )
        
        allowed_employees = [employee] + subordinates
        filters["employee"] = ["in", allowed_employees]
        
            
    requests = frappe.get_all(
        "Elitehr Requests",
        filters=filters,
        fields=["*"]
    )
    return requests


@frappe.whitelist()
def update_approval(docname, status,level_name,approved_by):
    doc = frappe.get_doc("Elitehr Requests", docname)
    for row in doc.levels:
        if row.name == level_name:
            row.status = status
            row.action_date = frappe.utils.now()
            row.approved_by = approved_by
            doc.status = status
            doc.save() 
            frappe.db.commit()
            break

@frappe.whitelist()
def request_for_review(docname):
    doc = frappe.get_doc("Elitehr Requests", docname)
    for row in doc.levels:
        row.status = None
    doc.status = "Request for review"
    doc.save() 
    frappe.db.commit()



@frappe.whitelist()
def get_requests_approval_report():

    total_requests = frappe.db.count("Elitehr Requests")

    if not total_requests:
        return {
            "status": "success",
            "data": {
                "request_status": [],
                "summary": {
                    "total_requests": 0,
                    "approval_rate": 0,
                    "avg_processing_days": 0,
                    "pending_requests": 0
                }
            }
        }
        

    # الحالات الأساسية
    completed_count = frappe.db.count(
        "Elitehr Requests",
        filters={"status": "Completed"}
    )
    

    rejected_count = frappe.db.count(
        "Elitehr Requests",
        filters={"status": "Rejected"}
    )

    pending_count = frappe.db.count(
        "Elitehr Requests",
        filters={"status": ["not in", ["Completed", "Rejected"]]}
    )

    approval_rate = round((completed_count / total_requests) * 100, 1)


    # متوسط وقت المعالجة (من الإنشاء إلى آخر تعديل)
    avg_processing = frappe.db.sql("""
        SELECT AVG(DATEDIFF(modified, creation))
        FROM `tabElitehr Requests`
        WHERE status IN ('Approve', 'Rejected')
    """)[0][0] or 0

    avg_processing = round(float(avg_processing), 1)

    # frappe.log(f"""
    #     completed_count: {completed_count}
    #     rejected_count: {rejected_count}
    #     pending_count: {pending_count}
    #     approval_rate: {approval_rate}
    #     avg_processing: {avg_processing}
    # """)

    # تفاصيل حالة الطلبات
    request_status = [
        {
            "title": "تمت الموافقة",
            "count": completed_count,
            "percentage": round((completed_count / total_requests) * 100, 1),
            "bg": ""
        },
        {
            "title": "مرفوض",
            "count": rejected_count,
            "percentage": round((rejected_count / total_requests) * 100, 1),
            "bg": "red"
        },
        {
            "title": "قيد الانتظار",
            "count": pending_count,
            "percentage": round((pending_count / total_requests) * 100, 1),
            "bg": "#e67e22"
        }
    ]

    return {
        "status": "success",
        "data": {
            "request_status": request_status,
            "summary": {
                "total_requests": total_requests,
                "completed_count": completed_count,
                "pending_requests": pending_count,
                "approval_rate": approval_rate,
                "avg_processing_days": avg_processing,
            }
        }
    }


import frappe
from frappe import _


@frappe.whitelist()
def get_requests_by_type_report():
    data = frappe.db.sql("""
        SELECT
            request_type_name,
            COUNT(name) as total
        FROM `tabElitehr Requests`
        GROUP BY request_type_name
        ORDER BY total DESC
    """, as_dict=True)

    result = []

    for row in data:
        result.append({
            "type_name": row.request_type_name or "غير محدد",
            "count": row.total
        })

    return result


@frappe.whitelist()
def get_yearly_monthly_requests_report(year=None):
    if not year:
        year = datetime.now().year
    res = frappe.db.sql(f"""
        SELECT
            MONTH(creation) as month,
            YEAR(creation) as year,
            status,
            COUNT(name) as count
        FROM `tabElitehr Requests`
        WHERE YEAR(creation) = %s
        GROUP BY YEAR(creation), MONTH(creation), status
        ORDER BY year, month
    """,  (year,), as_dict=True)
    return res


@frappe.whitelist()
def get_leaves_summary_monthly_yearly(year=None):

    if not year:
        year = datetime.now().year

    leave_types = frappe.db.get_all(
        "Elitehr Requests Types",
        filters={"category": "أجازة"},
        pluck="name"
    )
    frappe.log(f"leave_types: {leave_types}")

    data = frappe.db.sql("""
        SELECT
            MONTH(creation) as month,
            YEAR(creation) as year,
            request_type_name,
            COUNT(name) as count
        FROM `tabElitehr Requests`
        WHERE YEAR(creation) = %s
        and type in %s
        GROUP BY YEAR(creation), MONTH(creation), request_type_name
        ORDER BY month
    """, (year,tuple(leave_types)), as_dict=True)

    return data


@frappe.whitelist()
def check_user_approval_rights(docname):
    doc = frappe.get_doc("Elitehr Requests", docname)
    
    # 1. إذا كان الطلب مكتمل او مرفوض، نوقف التحقق
    # all_reviewed = all(level.status is not None for level in doc.levels)
    # if all_reviewed or doc.status in ["Approved","Rejected"]:
    #     return {"can_approve": False}
    if doc.status in ["Approved","Rejected"]:
        return {"can_approve": False}

    current_user = frappe.session.user
    current_date = today()

    # جلب الموظف المرتبط بـ User الحالي
    user_emp = frappe.db.get_value(
        "Elitehr Employee", 
        {"login_data": current_user}, 
        ["name", "employee_name"], 
        as_dict=True
    )

    for level in doc.levels:
        # إذا كان المستوى مراجعاً بالفعل، نتخطاه للمستوى التالي
        # if level.status:
        #     continue

        resp_id = level.responsible_id
        if not resp_id:
            continue

        # أ) حالة 1: المستخدم الحالي هو المسؤول المباشر عن هذا المستوى
        if user_emp and user_emp.name == resp_id:
            return {
                "can_approve": True,
                "level_name": level.name,
                "current_status": level.status,
                "approved_by": user_emp.employee_name
            }

        # ب) حالة 2: المستخدم الحالي مفوّض (Delegated) عن المسؤول
        delegations = frappe.get_all(
            "Elitehr Authorization Management",
            filters={
                "authorizer_original_authorizer": resp_id,
                "delegator_email": current_user,
                "start_date": ["<=", current_date],
                "to_date": [">=", current_date],
                "docstatus": 1
            },
            fields=["delegator_name", "request_type_optional"]
        )

        for delg in delegations:
            # التحقق من أن نوع الطلب مطابق أو عام (None)
            if not delg.request_type_optional or delg.request_type_optional == doc.type:
                return {
                    "can_approve": True,
                    "level_name": level.name,
                    "current_status": level.status,
                    "approved_by": delg.delegator_name
                }

    return {"can_approve": False}