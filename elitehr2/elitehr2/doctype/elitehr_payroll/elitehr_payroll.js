// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Payroll", {
	refresh(frm) {

        if (!frm.is_new() && frm.doc.status == "Under review") {
			frm.add_custom_button("إعادة احتساب الراتب", () => {3
                frappe.dom.freeze(__('جاري إعادة الاحتساب...'));
                frm.dirty();
                frm.save().then(() => {
                    frappe.dom.unfreeze();
                    frappe.show_alert({
                        message: __('تم تحديث البيانات وإعادة الاحتساب بنجاح'),
                        indicator: 'green'
                    });
                }).catch(() => {
                    frappe.dom.unfreeze();
                });
			});
		}

	}
});
