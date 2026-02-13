// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Employee", {
	refresh(frm) {
        let leaves_ids = frm.doc.table_leaves.map(l => l.leave);
        
        frm.add_custom_button(__("اضافة اجازة"), function() {

            frappe.prompt([
                {
                    label: 'السياسة',
                    fieldname: 'leave',
                    fieldtype: 'Link',
                    options: 'Elitehr Leave Policies',
                    reqd: 1,
                    filters: {
                        'name': ['not in', leaves_ids]
                    }
                },
                {
                    fetch_from: "leave.ar_name",
                    fieldname: "leave_name",
                    fieldtype: "Data",
                    in_list_view: 1,
                    label: "اسم الاجازة",
                    read_only: 1
                },
                {
                    fetch_from: "leave.normal_days",
                    fieldname: "days",
                    fieldtype: "Data",
                    in_list_view: 1,
                    label: "عدد الايام",
                    read_only: 1
                },
            ], (values) => {
                console.log(values);
                let child = frm.add_child("table_leaves");
                child.leave = values.leave;
                child.leave_name = values.leave_name;
                child.days = values.days;
                frm.refresh_field("table_leaves");

                frappe.msgprint('تم اضافة الاجازة');
            })


        });

       
	},
});
