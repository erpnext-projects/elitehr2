# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ElitehrLeavePolicies(Document):
	pass

@frappe.whitelist()
def apply_policy(policy_name):
	# Logic to apply the leave policy to employees
	doc_policy = frappe.get_doc("Elitehr Leave Policies", policy_name)
	docs = frappe.get_all("Elitehr Employee")
	frappe.log(docs)
	dones = 0
	for doc in docs:
		doc_emp = frappe.get_doc("Elitehr Employee", doc.name)
		leave_ids = [d.leave for d in doc_emp.table_leaves]
		frappe.log(f"{doc_policy.name} {leave_ids} {str(doc_policy.name) not in leave_ids}")
		if str(doc_policy.name) not in leave_ids:
			doc_emp.append("table_leaves", {
				"leave": doc_policy.name,
				"leave_name": doc_policy.ar_name,
				"days": doc_policy.normal_days
			})
			doc_emp.save()
			dones += 1
	frappe.msgprint(f'تم تطبيق السياسة بنجاح علي عدد {dones} موظف.')
	frappe.msgprint(f"موظفين لديهم السياسة بالفعل: {len(docs) - dones}")
	
	# frappe.log(f"Applying policy: {policy_name}")
