# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class ElitehrRequests(Document):
	pass



@frappe.whitelist()
def get_requests_list(request_type):
    requests = frappe.get_all(
        "Elitehr Requests",
        filters={"request_type_code": request_type},
        fields=["*"]
    )
    return requests