// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt


let currency = null

frappe.ui.form.on("Elitehr Final settlement", {
	async refresh(frm) {

        if (!currency) {
            currency = await frappe.db.get_single_value(
                "Elitehr Company",
                "currency"
            );
            currency = __(currency)
        }

        // calculate_years_of_service(frm);
        render_disbursement_table(frm);
        render_deductions_table(frm);
        
    },
});




function calculate_years_of_service(frm) {
    if (!frm.doc.date_of_appointment || !frm.doc.last_day_of_work) {
        frm.set_value("years_of_service", 0);
        return;
    }

    const days = frappe.datetime.get_diff(
        frm.doc.last_day_of_work,
        frm.doc.date_of_appointment
    );

    frm.set_value(
        "years_of_service",
        (days / 365).toFixed(1)
    );
}

function render_disbursement_table(frm) {
    const wrapper = frm.fields_dict.disbursement_container.$wrapper;
    wrapper.empty();
    const tableContainer = $(`<div class="table_container"></div>`);
    wrapper.append(tableContainer);
    new CustomTable({
        container: tableContainer,
        columns: [
            { id: "Disbursement", name: __("Disbursement") ,width: "70%"},
            { id: "value", name: __("Value"), format: (val) => `${val} ${currency}`, sum: true  },
        ],
        data: [
            {
                Disbursement: `${__("Remaining Days Salary")}`,
                value: frm.doc.remaining_days_salary
            },
            {
                Disbursement: `${__("Vacation Allowance")} (${frm.doc.remaining_vacation_days})`,
                value: frm.doc.vacation_allowance
            },{
                Disbursement: `${__("End Of Service Reward")} (${frm.doc.years_of_service}) ${__("year")}`,
                value: frm.doc.end_of_service_reward
            },{
                Disbursement: `${__("Additional Bonuses")}`,
                value: frm.doc.additional_bonuses
            },{
                Disbursement: `${__("Other benefits")}`,
                value: frm.doc.other_benefits
            }
        ]
    });
}


function render_deductions_table(frm) {
    const wrapper = frm.fields_dict.deductions_table.$wrapper;
    wrapper.empty();
    const tableContainer = $(`<div class="table_container"></div>`);
    wrapper.append(tableContainer);
    new CustomTable({
        container: tableContainer,
        columns: [
            { id: "Deduction", name: __("Deductions"), format: (val) => `${__(val)}`,width: "70%" },
            { id: "value", name: __("Value"), format: (val) => `${val} ${currency}`, sum: true },
        ],
        data: [
            {
                Deduction: "Loan balance",
                value: frm.doc.loan_balance
            },
            {
                Deduction: "Credit balance",
                value: frm.doc.credit_balance
            },
            {
                Deduction: "Other discounts",
                value: frm.doc.other_discounts
            }
        ]
    });
}


