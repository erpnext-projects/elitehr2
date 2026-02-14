// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.query_reports["ارصدة الموظفين"] = {
	"filters": [
		{
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Elitehr Employee"
        }
	]
};
