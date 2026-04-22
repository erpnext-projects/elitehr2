// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

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
    }
});


function calculate(frm) {
    let fromDate = frm.doc.from;
    let toDate = frm.doc.to;

    if (!fromDate || !toDate) return;

    // console.log("Calculating: ", fromDate, toDate);

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Elitehr Workers Check_in_out",
            filters: {"date": ["between",[fromDate,toDate]]},
            fields: ["*"]
        },
        callback(r) {
            let data = r.message;
            if (data) {   
                // console.log(data);

                // STEP 1: GROUP attendance
                let grouped = {};
                for (let item of data) {
                    let w = item.the_worker;
                    if (!grouped[w]) {
                        grouped[w] = {
                            worker: w,
                            worker_name: item.worker_name,
                            days: new Set(),
                            total_seconds: 0
                        };
                    }
                    grouped[w].days.add(item.date);
                    grouped[w].total_seconds += item.working_seconds || 0;
                }
                // console.log("grouped",grouped);
                

                let totalSeconds = 0;
                let totalTotal = 0;
                let totalNet = 0;
                let totalDeductions = 0;
                // STEP 2: BUILD PAYROLL
                let payroll = Object.values(grouped).map(r => {
                    totalSeconds += r.total_seconds;
                    let hours = Math.floor(r.total_seconds / 3600);
                    let minutes = Math.floor((r.total_seconds % 3600) / 60);
                    let working_hours = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                    let daily_wage = 50; // replace later from contract
                    let total = r.days.size * daily_wage;
                    totalTotal+=total;
                    let deduction_percentage = frm.doc.deduction_percentage || 0;
                    let deduction = total * (deduction_percentage / 100);
                    totalDeductions+=deduction;
                    let net = total - deduction;
                    totalNet+=net;
                    return {
                        worker: r.worker,
                        worker_name: r.worker_name,
                        days: r.days.size,
                        working_hours: working_hours,
                        daily_wage: daily_wage,
                        total: Number(total.toFixed(2)),
                        deduction: deduction,
                        net: Number(net.toFixed(2))
                    };
                });
                
                renderTable(frm,payroll);
                frm.set_value("workers", payroll.length);
                let hours = Math.floor(totalSeconds / 3600);
                let minutes = Math.floor((totalSeconds % 3600) / 60);
                let working_hours = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                frm.set_value("total_seconds", totalSeconds);
                frm.set_value("hours", working_hours);
                frm.set_value("total", totalTotal);
                frm.set_value("net", totalNet);
                frm.set_value("total_deductions", totalDeductions);
            }
            
        }

    });
    
}

function renderTable(frm,data) {
    let wrapper = $(frm.fields_dict.table.wrapper);
    wrapper.empty();
    
    let tableContainer = $(`<div class="table_container"></div>`);
    tableContainer.appendTo(wrapper);

    new CustomTable({
        container: tableContainer,
        columns: [
            {id: "worker_name", name: "العامل"},
            {id: "days", name: "الأيام"},
            {id: "working_hours", name: "الساعات"},
            {id: "daily_wage", name: "الأجر اليومي"},
            {id: "total", name: "الأجمالي"},
            {id: "deduction", name: "الخصم"},
            {id: "net", name: "الصافي"},
        ],
        data: data
    });
}