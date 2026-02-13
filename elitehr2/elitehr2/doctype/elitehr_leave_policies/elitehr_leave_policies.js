// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Leave Policies", {
	refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("تطبيق السياسة"), function() {
                frappe.confirm('تأكيد تطبيق السياسة ؟', () => {
                    frappe.call({
                        method: "elitehr.elitehr.doctype.elitehr_leave_policies.elitehr_leave_policies.apply_policy",
                        args: {
                            policy_name: frm.doc.name
                        },
                        callback: function(r) {
                            if (r.message) {
                                frappe.msgprint('تم تطبيق السياسة بنجاح', alert=True);
                            }
                        }
                    });
                });
            });
        }

        
	},
});
