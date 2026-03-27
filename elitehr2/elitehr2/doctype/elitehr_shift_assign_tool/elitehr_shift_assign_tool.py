# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ElitehrShiftAssignTool(Document):
    def before_save(self):
        to = self.appointment_for
        if to == "Employee":
            expectEmployees = [emp.employee for emp in self.employees]
            employees = frappe.get_all("Elitehr Employee",pluck="name",filters={"name": ["in", expectEmployees]})            
            self.assignShift(employees)
        
        elif to == "Department":
            employees = frappe.get_all("Elitehr Employee",pluck="name",filters={"department": self.department})
            self.assignShift(employees)



    def assignShift(self,employees):
        total = len(employees)
        checked = 0
        updated = 0
        for emp_name in employees:
            checked += 1
            employee = frappe.get_doc("Elitehr Employee",emp_name)
            employee.shift = self.shift
            employee.save()
            updated += 1

        frappe.msgprint(
            f"تم مراجعة {checked} موظف<br>"
            f"تم إضافة الوردية إلى {updated} موظف"
        )