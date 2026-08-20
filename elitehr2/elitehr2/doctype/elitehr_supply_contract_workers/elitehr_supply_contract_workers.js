// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Supply Contract Workers", {
	refresh(frm) {
        // ID card
        add_btn_show_employee_card(frm)
	},
});


function add_btn_show_employee_card(frm) {
    frm.add_custom_button(__("ID card"), function () {
        frappe.db.get_single_value('Elitehr Company', 'company_name')
        .then(function (company_name) {
            let card_data = {
                company_name: company_name,
                employee_name: frm.doc.full_name,
                designation: frm.doc.job_title,
                employee_id: frm.doc.name,
                phone: frm.doc.phone_number,
                email: "",
                national_id: frm.doc.the_contract,
                qr_data: frm.doc.name
            };
            frappe.show_employee_card(card_data);
        });
    });
}