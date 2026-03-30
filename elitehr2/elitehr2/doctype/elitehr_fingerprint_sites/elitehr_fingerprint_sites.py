# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ElitehrFingerprintSites(Document):
    def before_save(self):
        if self.is_new():
            self.active = False
            frappe.msgprint("تم إنشاء موقع بصمة جديد. يرجى تفعيله.", alert=True)

        if self.active:
            to = self.who_can_fingerprint_from_this_site
            if to == "All employees":
                employees = frappe.get_all("Elitehr Employee",pluck="name")
                self.assignSite(employees)
                
            elif to == "Everyone except specific employees":
                exceptEmployees = [emp.employee for emp in self.employees]
                employees = frappe.get_all("Elitehr Employee",pluck="name",filters={"name": ["not in", exceptEmployees]})
                self.assignSite(employees)

            elif self.who_can_fingerprint_from_this_site == "Specific employees only":
                expectEmployees = [emp.employee for emp in self.employees]
                employees = frappe.get_all("Elitehr Employee",pluck="name",filters={"name": ["in", expectEmployees]})
                self.assignSite(employees)
            
            elif self.who_can_fingerprint_from_this_site == "Specific departments only":
                departments = [dep.department for dep in self.department]
                employees = frappe.get_all("Elitehr Employee",pluck="name",filters={"department": ["in", departments]})
                self.assignSite(employees)


    def assignSite(self,employees):
        total = len(employees)
        checked = 0
        updated = 0
        frappe.log(employees)

        for emp_name in employees:
            checked += 1
            employee = frappe.get_doc("Elitehr Employee",emp_name)
            exists = any(site.site_name == self.name for site in employee.fingerprint_sites)
            frappe.log(self.site_name)
            if not exists :
                employee.append("fingerprint_sites", {
                    "site_name": self.name
                })
                employee.save()
                updated += 1
                
            frappe.publish_progress(
                percent=int((checked / total) * 100),
                title="Processing Employees",
                description=f"Checked {checked} of {total}"
            )
        frappe.msgprint(
            f"تم مراجعة {checked} موظف<br>"
            f"تم إضافة الموقع إلى {updated} موظف"
        )
