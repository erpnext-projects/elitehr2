// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt
let tableContainer = $(`<div class="table_container"></div>`);

frappe.ui.form.on("Elitehr Supply Contract Payroll", {
	refresh(frm) {
        calculate(frm);
	},
    from: function(frm) {
        calculate(frm);
    },
    to: function(frm) {
        calculate(frm);
    },
    deduction_percentage: function(frm) {
        let val = frm.doc.deduction_percentage;
        if (val < 0) {
            frm.set_value("deduction_percentage", 0);
        }
        else if (val > 100) {
            frm.set_value("deduction_percentage", 100);
        }else{
            calculate(frm);
        }
    },
    the_contract: function(frm) {
        calculate(frm);
    }
});

function calculate(frm) {
	let fromDate = frm.doc.from;
	let toDate = frm.doc.to;

	if (!fromDate || !toDate || !frm.doc.the_contract) {
        tableContainer.empty();
        return;
    }

	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_supply_contract_payroll.elitehr_supply_contract_payroll.get_payroll_data",
		args: {
            the_contract: frm.doc.the_contract,
            houry_wage: frm.doc.hourly_wage,
			from_date: fromDate,
			to_date: toDate,
			deduction_percentage: frm.doc.deduction_percentage || 0
		},
		callback(r) {
			if (!r.message) return;

			let response = r.message;

			renderTable(frm, response.payroll);

			frm.set_value("workers", response.workers);
			frm.set_value("total_seconds", response.total_seconds);
			frm.set_value("hours", response.hours);
			frm.set_value("total", response.total);
			frm.set_value("net", response.net);
			frm.set_value("total_deductions", response.total_deductions);
		}
	});
}

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