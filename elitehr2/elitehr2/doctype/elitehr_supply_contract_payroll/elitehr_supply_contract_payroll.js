// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt
let tableContainer = $(`<div class="table_container"></div>`);

frappe.ui.form.on("Elitehr Supply Contract Payroll", {
	refresh(frm) {
        // calculate(frm);
        let table_data = frm.doc.table_data;
        if (typeof table_data === "string") {
			try {
				table_data = JSON.parse(table_data);
                renderTable(frm, table_data.data);
                
			} catch (error) {
				console.error("Invalid table_data JSON:", error);
				return;
			}
		}
        
	},
    from: function(frm) {
        // calculate(frm);
    },
    to: function(frm) {
        // calculate(frm);
    },
    // deduction_percentage: function(frm) {
    //     let val = frm.doc.deduction_percentage;
    //     if (val < 0) {
    //         frm.set_value("deduction_percentage", 0);
    //     }
    //     else if (val > 100) {
    //         frm.set_value("deduction_percentage", 100);
    //     }else{
    //         // calculate(frm);
    //     }
    // },
    the_contract: function(frm) {
        // calculate(frm);
    }
});

function renderTable(frm,data) {
    let wrapper = $(frm.fields_dict.table.wrapper);
    wrapper.empty();
    
    
    tableContainer.appendTo(wrapper);

    new CustomTable({
        container: tableContainer,
        columns: [
            {id: "worker_name", name: "العامل"},
            {id: "days", name: "الأيام"},
            {id: "working_hours", name: "الساعات"},
            // {id: "daily_wage", name: "الأجر اليومي"},
            {id: "total", name: "الأجمالي"},
            {id: "deduction", name: "الخصم"},
            {id: "net", name: "الصافي"},
        ],
        data: data
    });
}