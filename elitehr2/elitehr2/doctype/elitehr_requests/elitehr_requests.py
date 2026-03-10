# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class ElitehrRequests(Document):
    def before_save(self):
        workflow = frappe.get_last_doc(
            'Elitehr Approval Workflow',
            filters={'active': '1', "request_type": self.type}
        ) if frappe.db.exists('Elitehr Approval Workflow', {'active': '1', "request_type": self.type}) else None
        
        if workflow is None:
            frappe.throw(f"No active approval workflow found for request type: {self.type}")
        
        departmentId = frappe.get_doc("Elitehr Employee",self.employee).department
        departmentManager = frappe.get_doc("Elitehr Fingerprint Sites",departmentId).manager
        manager = frappe.get_doc("Elitehr Employee",departmentManager)

        directSupervisor = frappe.get_doc('Elitehr Employee', self.employee).manager
        directSupervisorName = frappe.get_doc('Elitehr Employee', directSupervisor).employee_name

        self.levels = []
        for level in workflow.levels:
            approvedType = level.approved_type
            responsible = None
            
            if approvedType == "Specific Employee":
                responsible = frappe.get_doc('Elitehr Employee', level.employee).employee_name
            elif approvedType == "Department Manager":
                responsible = manager.employee_name
            elif approvedType == "Direct Supervisor":
                responsible = directSupervisorName
            
            frappe.log(approvedType)

            self.append('levels', {
                    'approved_type': approvedType,
                    "responsible": responsible
            })



@frappe.whitelist()
def get_requests_list(request_type):
    requests = frappe.get_all(
        "Elitehr Requests",
        filters={"request_type_code": request_type},
        fields=["*"]
    )
    return requests