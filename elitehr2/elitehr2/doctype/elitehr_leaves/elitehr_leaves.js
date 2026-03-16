// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Leaves", {
    end_date: function(frm) {
        calculate_days(frm);
    },
    _date: function(frm) {
        calculate_days(frm);
    },
    employee: function(frm) {
        frm.set_value("type", null);
        if (frm.doc.employee) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Elitehr Employee",
                    name: frm.doc.employee,
                },
                callback(r) {
                    if (r.message) {
                        let leaves = r.message.table_leaves.map(l => l.leave);
                        frm.set_query("type", function () {
                            return {
                                filters: {
                                    name: ["in", leaves]
                                }
                            };
                        });
                    }
                }
            });
        }
    },
	refresh(frm) {
        calculate_days(frm);
	},
});

function calculate_days(frm) {
    if (frm.doc.start_date && frm.doc.end_date) {  
        let days = frappe.datetime.get_day_diff(frm.doc.end_date, frm.doc.start_date) + 1;   
        frm.set_value("days", days);
    }else{
        frm.set_value("days", 0);
    }
}
