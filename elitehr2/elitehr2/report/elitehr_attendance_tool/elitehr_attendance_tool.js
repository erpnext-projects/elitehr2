// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.query_reports["EliteHr Attendance Tool"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("من تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("إلى تاريخ"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "employee",
            "label": __("الموظف"),
            "fieldtype": "Link",
            "options": "Elitehr Employee"
        }
    ]
};
