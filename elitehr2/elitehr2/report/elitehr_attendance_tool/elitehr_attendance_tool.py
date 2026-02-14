# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
    return [
        {"label": _("الموظف"), "fieldname": "employee", "fieldtype": "Link", "options": "Elitehr Employee", "width": 150},
        {"label": _("التاريخ"), "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": _("وقت الدخول"), "fieldname": "entry_date", "fieldtype": "Datetime", "width": 160},
        {"label": _("وقت الخروج"), "fieldname": "out_date", "fieldtype": "Datetime", "width": 160},
        {"label": _("ساعات العمل"), "fieldname": "work_hours", "fieldtype": "Duration", "width": 120},
        {"label": _("الحالة"), "fieldname": "status", "fieldtype": "Link", "options": "Elitehr Attendance Status", "width": 120},
    ]

def get_data(filters):
    # بناء الفلاتر بناءً على اختيار المستخدم في التقرير
    query_filters = {}
    if filters.get("from_date") and filters.get("to_date"):
        query_filters["date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
    if filters.get("employee"):
        query_filters["employee"] = filters.get("employee")

    # جلب البيانات من الجدول المخصص بتاعك
    data = frappe.get_all("Elitehr Attendance", 
        filters=query_filters,
        fields=["employee", "date", "entry_date", "out_date", "work_hours", "status"],
        order_by="date desc"
    )
    return data

# def get_columns() -> list[dict]:
# 	"""Return columns for the report.

# 	One field definition per column, just like a DocType field definition.
# 	"""
# 	return [
# 		{
# 			"label": _("Column 1"),
# 			"fieldname": "column_1",
# 			"fieldtype": "Data",
# 		},
# 		{
# 			"label": _("Column 2"),
# 			"fieldname": "column_2",
# 			"fieldtype": "Int",
# 		},
# 	]


# def get_data() -> list[list]:
# 	"""Return data for the report.

# 	The report data is a list of rows, with each row being a list of cell values.
# 	"""
# 	return [
# 		["Row 1", 1],
# 		["Row 2", 2],
# 	]
