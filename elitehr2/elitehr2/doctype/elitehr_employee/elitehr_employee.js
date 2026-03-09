// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Employee", {
	refresh(frm) {

        setupFilterToFingerPrintSites(frm);
        // make leaves unique
        // let leaves_ids = frm.map(l => l.leave);
        
        frm.set_query("leave", "table_leaves", function (doc, cdt, cdn) {
            let existing_leaves = doc.table_leaves.map(l => l.leave).filter(l => l);
            console.log(existing_leaves);
            
            return {
                "filters": {
                    "name": ["not in",existing_leaves]
                },
            };
        });
       
	},
    
});


function setupFilterToFingerPrintSites(frm){
    frm.fields_dict.fingerprint_sites.get_query = function (doc) {
        return {
            filters: {
            active: ["=", "1"],
            },
        }
    }   
}


function setupLeaves(frm) {
    // let leaves_ids = frm.doc.table_leaves.map(l => l.leave);
        
    //     frm.add_custom_button(__("اضافة اجازة"), function() {

    //         frappe.prompt([
    //             {
    //                 label: 'السياسة',
    //                 fieldname: 'leave',
    //                 fieldtype: 'Link',
    //                 options: 'Elitehr Leave Policies',
    //                 reqd: 1,
    //                 filters: {
    //                     'name': ['not in', leaves_ids]
    //                 }
    //             },
    //             {
    //                 fetch_from: "leave.ar_name",
    //                 fieldname: "leave_name",
    //                 fieldtype: "Data",
    //                 in_list_view: 1,
    //                 label: "اسم الاجازة",
    //                 read_only: 1
    //             },
    //             {
    //                 fetch_from: "leave.normal_days",
    //                 fieldname: "days",
    //                 fieldtype: "Data",
    //                 in_list_view: 1,
    //                 label: "عدد الايام",
    //                 read_only: 1
    //             },
    //         ], (values) => {
    //             console.log(values);
    //             let child = frm.add_child("table_leaves");
    //             child.leave = values.leave;
    //             child.leave_name = values.leave_name;
    //             child.days = values.days;
    //             frm.refresh_field("table_leaves");

    //             frappe.msgprint('تم اضافة الاجازة');
    //         })


    //     });
}