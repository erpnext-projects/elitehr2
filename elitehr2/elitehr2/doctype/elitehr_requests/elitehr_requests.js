// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Requests", {
	refresh(frm) {
        frm.set_query("to_department", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "site_name": ["not in",doc.from_department]
                },
            };
        });
        frm.set_query("to_branch", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "branch_name": ["not in",doc.from_branch]
                },
            };
        });
	},
});
