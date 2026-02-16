# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.nestedset import NestedSet, rebuild_tree


class ElitehrCompany(Document):
	def on_update(self):
		tree_doctype = "Elitehr Org Structure"
		parent_field = "parent_elitehr_org_structure"

		# 1. تأكد إن اسم الشركة مش فاضي
		if not self.company_name or self.company_name == "0":
			return

		# 2. البحث عن الـ Root الحالي (اللي ملوش Parent)
		root_node = frappe.get_all(tree_doctype, filters={parent_field: ("is", "not set")}, limit=1)
		if root_node:
			old_root_name = root_node[0].name
			
			# تحديث الاسم العربي (العرض)
			frappe.db.set_value(tree_doctype, old_root_name, "ar_name", self.company_name)
			
			# لو عايز تغير الـ ID (الاسم التقني) ليكون مطابق لاسم الشركة الجديد
			if old_root_name != self.company_name:
				# rename_doc بتغير الاسم وتحدث كل الجداول المرتبطة به أوتوماتيكياً
				new_root_name = frappe.rename_doc(tree_doctype, old_root_name, self.company_name, force=True)
				root_name = new_root_name
			else:
				root_name = old_root_name
		else:
			# لو مفيش Root، انشئ واحد باسم الشركة
			new_root = frappe.get_doc({
				"doctype": tree_doctype,
				"ar_name": self.company_name,
				"is_group": 1
			})
			new_root.insert(ignore_permissions=True)
			root_name = new_root.name
		# 3. "لمّ الشمل" - أي عنصر ملوش Parent حطه تحت الـ Root ده
		# ده بيضمن إن مفيش حاجة تضيع برا الشجرة
		frappe.db.sql(f"""
			UPDATE `tab{tree_doctype}`
			SET {parent_field} = %s
			WHERE ({parent_field} IS NULL OR {parent_field} = '' OR {parent_field} = '0')
			AND name != %s
		""", (root_name, root_name))

		# 4. إعادة بناء الشجرة مرة واحدة عشان الـ lft و rgt يتظبطوا
		rebuild_tree(tree_doctype)
	