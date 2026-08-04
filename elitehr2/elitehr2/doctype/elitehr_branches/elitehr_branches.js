// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Branches", {
	refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Fingerprint Sites'), function () {
                frappe.new_doc('Elitehr Fingerprint Sites',{
                    branch: frm.doc.name
                });
            });
        }
	},
});
