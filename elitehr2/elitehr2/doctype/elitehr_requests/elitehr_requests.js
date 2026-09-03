// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt
const REQUEST_EXTRA_STATUS = {
    OVERTIME: [
        "Disbursement of Dues"
    ],

    ADVANCE_SALARY: [
        "Disbursement of Dues"
    ],

    EXPENSE_PURCHASE: [
        "Under Liquidation",
        "Disbursement of Dues"
    ],

    EXPENSE_TRAVEL: [
        "Under Liquidation",
        "Disbursement of Dues"
    ],

    MISSIONS: [
        "Disbursement of Dues"
    ],

};

frappe.ui.form.on("Elitehr Requests", {
    refresh(frm) {
        frm.set_query("to_department", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "site_name": ["not in", doc.from_department]
                },
            };
        });
        frm.set_query("to_branch", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "branch_name": ["not in", doc.from_branch]
                },
            };
        });

        updateStatusBtn(frm);

        requestForReview(frm);


    },
    start_date(frm) {
        calculate_total_days(frm);
    },
    end_date(frm) {
        calculate_total_days(frm);
    },
    request_type_name(frm){
        if (!frm.doc.subject) {
            frm.set_value("subject", frm.doc.request_type_name);
        }   
    }
});

function calculate_total_days(frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
        let start = frappe.datetime.str_to_obj(frm.doc.start_date);
        let end = frappe.datetime.str_to_obj(frm.doc.end_date);

        let diff = frappe.datetime.get_diff(end, start);

        if (diff < 0) {
            frappe.msgprint(__("End Date must be greater than Start Date"));
            frm.set_value("total_days", 0);
            return;
        }

        let days = diff + 1; // include both start and end day

        frm.set_value("total_days", days);
    }
}

function updateStatusBtn(frm) {

    if (frm.doc.status == "Approved" || frm.doc.status == "Rejected" || frm.is_new()) {
        return;
    }

    frappe.call({
        method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.check_user_approval_rights", 
        args: {
            docname: frm.doc.name
        },
        callback: function (r) {
            if (r.message && r.message.can_approve) {
                render_status_button(frm, r.message);
            }
        }
    });
}


function render_status_button(frm, approval_data) {
    const statusOptions = ["Approved", ...(REQUEST_EXTRA_STATUS[frm.doc.type] || []), "Rejected"];

    frm.add_custom_button(__("Edit Request Status"), function () {
        frappe.prompt([
            {
                label: 'Status',
                fieldname: 'status',
                fieldtype: 'Select',
                options: statusOptions,
                reqd: 1,
                default: approval_data.current_status
            }
        ], (values) => {
            frappe.call({
                method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.update_approval",
                args: {
                    docname: frm.doc.name,
                    status: values.status,
                    level_name: approval_data.level_name,
                    approved_by: approval_data.approved_by
                },
                callback: function () {
                    frm.reload_doc();
                }
            });
        });
    });
}



function requestForReview(frm) {
    if (frm.doc.status == "Approved" || frm.doc.status == "Rejected" ) {
        frm.set_read_only();
        frm.disable_save();
        frm.add_custom_button(__("Request for review"), function () {
            frappe.confirm(
                __("Are you sure you want to request a review of the application?"),
                function () {
                    frappe.call({
                        method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.request_for_review",
                        args: {
                            docname: frm.doc.name
                        },
                        callback: function () {
                            frm.reload_doc();
                        }
                    });
                }
            )

        });
    }

}