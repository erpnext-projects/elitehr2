// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

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
});

function updateStatusBtn(frm) {
    if (frm.doc.status != "Completed") {
        for (const index in frm.doc.levels) {
            const level = frm.doc.levels[index];
            
            if (!level.responsible_id) {
                console.error("level not have responsible id")
                return;
            }
            
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Elitehr Employee",
                    name: level.responsible_id
                },
                callback: function (r) {   
                    let emp = r.message;        
                    if (emp) {
                        if (emp.login_data == frappe.session.user) {
                            frm.add_custom_button(__("Edit Request Status"), function () {
                                frappe.prompt([
                                    {
                                        label: 'Status',
                                        fieldname: 'status',
                                        fieldtype: 'Select',
                                        options: ["Rejected", "Approve", "Under Liquidation", "Disbursement of Dues"],
                                        reqd: 1,
                                        default: level.status
                                    }
                                ], (values) => {
                                    frappe.call({
                                        method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.update_approval",
                                        args: {
                                            docname: frm.doc.name,
                                            status: values.status,
                                            level_name: level.name,
                                            approved_by: emp.employee_name
                                        },
                                        callback: function () {
                                            frm.reload_doc();
                                        }
                                    });
                                })
    
    
                            });
                        }
                    }
                }
            })
        }
    }
}


function requestForReview(frm) {

    if (frm.doc.status === "Completed") {
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