# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds, nowdate, nowtime

class ElitehrWorkersCheck_in_out(Document):
    def before_save(self):
        # Working Hours
        working_seconds = 0
        working_hours = ""

        if self.check_in and self.check_out:
            total_seconds = time_diff_in_seconds(self.check_out, self.check_in)
            if total_seconds > 0:
                working_seconds = total_seconds
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                working_hours = f"{hours:02d}:{minutes:02d}"
        
        self.working_seconds = working_seconds
        self.working_hours = working_hours
        
    def validate(self):
        existing_attendance = frappe.db.exists(
            "Elitehr Workers Check_in_out",
            {
                "the_worker": self.the_worker,
                "date": self.date,
                "name": ["!=", self.name]
            }
        )
        if existing_attendance:
            frappe.throw(
                _("تم تسجيل حضور الموظف {0} بالفعل اليوم").format(self.worker_name)
            )


@frappe.whitelist()
def set_attendance_by_worker_id(worker_id):
    worker = frappe.db.get_value(
        "Elitehr Supply Contract Workers",
        worker_id,
        ["name", "full_name"],
        as_dict=True
    )

    if not worker:
        frappe.throw(_("عذراً، لم يتم العثور على موظف بهذا الرقم: {0}").format(worker.name))

    
    attendance = frappe.get_doc({
        "doctype": "Elitehr Workers Check_in_out",
        "the_worker": worker.name,
        "date": nowdate(),
        "check_in": nowtime(),
        "status": "Under review"
    })

    attendance.insert(ignore_permissions=True)

    return True