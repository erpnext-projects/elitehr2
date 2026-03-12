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

        setupSubmitBtn(frm);
	},
});

function setupSubmitBtn(frm) {
     // let leaves_ids = frm.doc.table_leaves.map(l => l.leave);
        // emptyLevelStatus = list(filter(lambda l: l.status is None, self.levels))
        // if len(emptyLevelStatus)  != len(self.levels):

        let emptyLevelStatus = frm.doc.levels.filter(l => l.status === undefined);
        if(emptyLevelStatus.length > 0){
            frm.add_custom_button(__("Submit"), function() {
                frappe.prompt([
                    {
                        label: 'Status',
                        fieldname: 'status',
                        fieldtype: 'Select',
                        options: ["Rejected","Approve","Under Liquidation","Disbursement of Dues"],
                        reqd: 1
                    }
                ], (values) => {
                    frappe.call({
                        method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.update_approval",
                        args: {
                            docname: frm.doc.name,
                            status: values.status
                        },
                        callback: function() {
                            frm.reload_doc();
                        }
                    });
                })
    
    
            });   
        }
}