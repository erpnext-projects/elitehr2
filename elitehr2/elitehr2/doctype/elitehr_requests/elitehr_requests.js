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
    start_date(frm) {
        calculate_total_days(frm);
    },
    end_date(frm) {
        calculate_total_days(frm);
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
                            add_btn(emp.employee_name);
                        }
                    }
                }
            })

            // التفويضات
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Elitehr Authorization Management",
                    filters: {
                        authorizer_original_authorizer: level.responsible_id,
                        start_date: ["<=", frappe.datetime.get_today()],
                        to_date: [">=", frappe.datetime.get_today()],
                        request_type_optional: ["in", [null, frm.doc.type]],
                        docstatus: 1
                    },
                    fields: ["*"]
                },
                callback: function (r) {
                    let data = r.message;
                    data.forEach(row => {
                        console.log(row);    
                        if (row.delegator_email == frappe.session.user) {
                            add_btn(row.delegator_name);
                            return;
                        }
                            
                        
                    });
                }
            })

            function add_btn(approved_by) {
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
                                approved_by: approved_by
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