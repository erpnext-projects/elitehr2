# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class ElitehrRequests(Document):
    def validate(self):
        if self.status == "Completed":
            frappe.throw("غير مسموح بتعديل الطلب بعد اكتماله")

    def before_save(self):
        self.getRequestLevels()
        self.checkAllLevelsApproved()



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
                frappe.throw(f"No active approval workflow found for request type: {self.type}")
            
            department = frappe.get_doc("Elitehr Employee",self.employee)
            departmentId = department.department
            departmentName = department.department_name
            departmentManager = frappe.get_doc("Elitehr Fingerprint Sites",departmentId).manager
            if departmentManager is None:
                frappe.throw(f"لم يتم العثور علي مدير الفرع {departmentName}")

            manager = frappe.get_doc("Elitehr Employee",departmentManager)

            directSupervisor = frappe.get_doc('Elitehr Employee', self.employee).manager
            
            directSupervisor = frappe.get_doc('Elitehr Employee', directSupervisor)

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
                    responsible = directSupervisor.employee_name
                    responsibleId = directSupervisor.name
                
                # frappe.log(approvedType)

                self.append('levels', {
                        'approved_type': approvedType,
                        "responsible": responsible,
                        "responsible_id": responsibleId
                })
                frappe.log(self.levels)

    def checkAllLevelsApproved(self):
        # Check if all levels have been approved
        frappe.log(self.levels[0].status)
        if self.levels and all(l.status is not None for l in self.levels):
            self.status = "Completed"


@frappe.whitelist()
def get_requests_list(request_type):
    requests = frappe.get_all(
        "Elitehr Requests",
        filters={"request_type_code": request_type},
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
