# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds

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
