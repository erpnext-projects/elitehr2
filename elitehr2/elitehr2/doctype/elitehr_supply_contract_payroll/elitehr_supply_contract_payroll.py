# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ElitehrSupplyContractPayroll(Document):
	def validate(self):
		# نتأكد إن from_date أصغر من to_date
		if self.get("from") > self.get("to"):
			frappe.throw(_("من تاريخ لازم يكون قبل إلى تاريخ"))

		# نجيب أي كشف راتب متداخل
		overlapping = frappe.get_all(
			"Elitehr Supply Contract Payroll", 
			filters=[
				["name", "!=", self.name],
				["to", ">=", self.get("from")],  
				["from", "<=", self.get("to")], 
				["the_contract",self.the_contract]
			],
			fields=["name", "from", "to"]
		)

		if overlapping:
			frappe.throw(_(
				f"لا يمكن إنشاء كشف راتب في هذه الفترة لأنها متداخلة مع كشف راتب سابق: {overlapping[0].name}"
			))
