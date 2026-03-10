// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Leaves balances"] = {
	filters: [
		// {
		// 	"fieldname": "my_filter",
		// 	"label": __("My Filter"),
		// 	"fieldtype": "Data",
		// 	"reqd": 1,
		// },
		{
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Elitehr Employee"
        }
	],
};
