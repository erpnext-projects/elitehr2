// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Employee", {
    refresh(frm) {

        setupFilterToFingerPrintSites(frm);
        // make leaves unique
        // let leaves_ids = frm.map(l => l.leave);

        frm.set_query("manager", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "name": ["not in", doc.name]
                },
            };
        });

        frm.set_query("leave", "table_leaves", function (doc, cdt, cdn) {
            let existing_leaves = doc.table_leaves.map(l => l.leave).filter(l => l);
            console.log(existing_leaves);

            return {
                "filters": {
                    "name": ["not in", existing_leaves]
                },
            };
        });

        frm.add_custom_button(frappe._("Employee Leave Balance"), function () {
            frappe.route_options = {
                "employee": frm.doc.name
            };
            frappe.set_route( "employee-leaves-balances");

        });

        if (!frm.is_new()) {
            frm.add_custom_button(__("Create Login Data"), function () {
                createLoginData(frm);
            });
        }

        // ID card
        add_btn_show_employee_card(frm)


    },

});


function setupFilterToFingerPrintSites(frm) {
    frm.fields_dict.fingerprint_sites.get_query = function (doc) {
        return {
            filters: {
                active: ["=", "1"],
                branch: doc.branche
            },
        }
    }
}


function createLoginData(frm) {
    frappe.call({
        method: "elitehr2.elitehr2.doctype.elitehr_employee.elitehr_employee.createLoginData",
        args: { name: frm.doc.name },
        callback: function (r) {
            if (r.message) {
                frm.doc.login_data = r.message.login_data;
                frm.doc.modified = r.message.modified;
                frm.refresh_field('login_data');
            }
        }
    });
}






function add_btn_show_employee_card(frm) {
    frm.add_custom_button(__("ID card"), function () {
        frappe.db.get_single_value('Elitehr Company', 'company_name')
        .then(function (company_name) {
            let card_data = {
                company_name: company_name,
                employee_name: frm.doc.employee_name,
                designation: frm.doc.manager == "" ? __("مدير") : __("موظف"),
                employee_id: frm.doc.name,
                phone: frm.doc.phone_number,
                email: frm.doc.email,
                national_id: frm.doc.account_number ? `********${frm.doc.account_number.slice(-4)}` : '',
                qr_data: frm.doc.name
            };
            frappe.show_employee_card(card_data);
        });
    });
}
