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
				["the_contract","=",self.the_contract]
			],
			fields=["name", "from", "to"]
		)

		if overlapping:
			frappe.throw(_(
				f"لا يمكن إنشاء كشف راتب في هذه الفترة لأنها متداخلة مع كشف راتب سابق: {overlapping[0].name}"
			))


		# check contract value
		contract_value = frappe.get_value("Elitehr Supply Contract",self.the_contract,"contract_value") or 0		
		if float(contract_value) < float(self.net):
			frappe.throw(_(
				"Payroll net amount cannot exceed contract value"
			))





@frappe.whitelist()
def get_payroll_data(the_contract,houry_wage,from_date=None, to_date=None, deduction_percentage=0):
	
	if houry_wage == 0:
		frappe.msgprint(_("The selected contract does not have an hourly rate defined"))
		return {
			"payroll": [],
			"workers": 0,
			"total_seconds": 0,
			"hours": 0,
			"total": 0,
			"net": 0,
			"total_deductions": 0
		}

	contract_workers = frappe.get_all(
		"Elitehr Supply Contract Workers",
		filters={
			"the_contract": the_contract
		},
		fields=["name"]
	)
	worker_list = [d.name for d in contract_workers]
	frappe.log(worker_list)

	deduction_percentage = float(deduction_percentage or 0)

	rows = frappe.get_all(
		"Elitehr Workers Check_in_out",
		filters={
			"the_worker":["in",worker_list],
			"date": ["between", [from_date, to_date]],
		},
		fields=["*"]
	)

	grouped = {}

	for item in rows:
		worker = item.get("the_worker")

		if worker not in grouped:
			grouped[worker] = {
				"worker": worker,
				"worker_name": item.get("worker_name"),
				"days": set(),
				"total_seconds": 0
			}

		grouped[worker]["days"].add(str(item.get("date")))
		grouped[worker]["total_seconds"] += item.get("working_seconds") or 0

	payroll = []
	total_seconds = 0
	total_total = 0
	total_net = 0
	total_deductions = 0

	for row in grouped.values():
		total_seconds += row["total_seconds"]

		hours = int(row["total_seconds"] // 3600)
		minutes = int((row["total_seconds"] % 3600) // 60)

		working_hours = f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"

		total_hours_decimal = row["total_seconds"] / 3600
		# daily_wage = total_hours_decimal * float(houry_wage)

		total = total_hours_decimal * float(houry_wage)
		deduction = total * (deduction_percentage / 100)
		net = total - deduction

		total_total += total
		total_deductions += deduction
		total_net += net

		payroll.append({
			"worker": row["worker"],
			"worker_name": row["worker_name"],
			"days": len(row["days"]),
			"working_hours": working_hours,
			# "daily_wage": daily_wage,
			"total": round(total, 2),
			"deduction": round(deduction, 2),
			"net": round(net, 2)
		})

	total_hours = int(total_seconds // 3600)
	total_minutes = int((total_seconds % 3600) // 60)

	return {
		"payroll": payroll,
		"workers": len(payroll),
		"total_seconds": total_seconds,
		"hours": f"{str(total_hours).zfill(2)}:{str(total_minutes).zfill(2)}",
		"total": round(total_total, 2),
		"net": round(total_net, 2),
		"total_deductions": round(total_deductions, 2)
	}