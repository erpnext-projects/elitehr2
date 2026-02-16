# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class ElitehrOrgStructure(NestedSet):
	def validate(self):
		# 1. التأكد من وجود اسم الشركة في الإعدادات
		company_name = frappe.db.get_single_value("Elitehr Company", "company_name")
		if not company_name or company_name == "0":
			frappe.throw("برجاء تسجيل الشركة الرئيسية أولاً في صفحة الإعدادات.")

		# 2. التأكد من وجود Root واحد فقط
		if not self.parent_elitehr_org_structure:
			existing_root = frappe.db.exists(self.doctype, {"parent_elitehr_org_structure": ("is", "not set"), "name": ("!=", self.name)})
			if existing_root:
				frappe.throw("لا يمكن إنشاء أكثر من Root واحد للشجرة. برجاء اختيار أب لهذا العنصر.")
		


@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False):
    filters = {}

    if parent and parent != "All Elitehr Org Structure":
        filters["parent_elitehr_org_structure"] = parent
    else:
        filters["parent_elitehr_org_structure"] = ["is", "not set"]

    return frappe.get_all(
        "Elitehr Org Structure",
        filters=filters,
        fields=[
            "name as value",
            "ar_name as title",
            "is_group as expandable"
        ],
        order_by="order asc"   # 👈 هنا السر
    )