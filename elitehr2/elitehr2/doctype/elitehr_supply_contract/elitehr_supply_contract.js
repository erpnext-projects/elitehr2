// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Supply Contract", {
	refresh(frm) {
        // console.log(frm.doc);

        let wrapper = $(frm.fields_dict.tabs_html.wrapper);
        wrapper.empty();

        let mainContainer = $('<div></div>');
        wrapper.append(mainContainer);
        renderTabs(mainContainer);

        loadWorkersData(frm);
        loadPayroll(frm);
	},
});



function renderTabs(wrapper) {
	let tabsContainer = $('<div class="tabs-container"></div>');
	tabsContainer.appendTo(wrapper);
	tabsContainer.html(`
		<ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#workers" type="button" role="tab">${__("Workers")}</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#attendance" type="button" role="tab">${__("Attendance Log")}</button>
            </li>
			<li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#payroll" type="button" role="tab">${__("Payroll")}</button>
            </li>
			<li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#awaiting-approval" type="button" role="tab">${__("Awaiting Approval")}</button>
            </li>
			
        </ul>

        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade show active" id="workers" role="tabpanel">${__("Loading...")}</div>
            <div class="tab-pane fade" id="attendance" role="tabpanel">${__("Loading...")}</div>
            <div class="tab-pane fade" id="payroll" role="tabpanel" class="custom-card p-4">${__("Loading...")}</div>
            <div class="tab-pane fade" id="awaiting-approval" role="tabpanel" class="custom-card p-4">${__("Loading...")}</div>
        </div>
	`);

	
	// main tabs
	tabsContainer.on('click', '#myTab .nav-link', function () {
		tabsContainer.find('#myTab .nav-link').removeClass('active');
		$(this).addClass('active');

		let target = $(this).attr('data-bs-target');
		tabsContainer.find('> .tab-content > .tab-pane').removeClass('show active');
		$(target).addClass('show active');
	});
	
}

function loadWorkersData(frm) {
    // workers
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Elitehr Supply Contract Workers",
            filters: {"the_contract": frm.doc.name},
            fields: ["*"]
        },
        callback(r) {
            let data = r.message;
            if (data) {
                // console.log("result: ",data);
                loadAttendanceData(data)

                $("#myTab button[data-bs-target='#workers']").text(`${__("Workers")} (${data.length})`)

                // workers
                let workersContainer = $("#workers")
                workersContainer.empty();
                let tableContainer = $(`<div class="table_container"></div>`);
                tableContainer.appendTo(workersContainer);
                new CustomTable({
                    container: tableContainer,
                    columns: [
                        {id: "name", name: "رقم العامل"},
                        {id: "full_name", name: "اسم العامل"},
                        {id:"nationality",name:"الجنسية",format:(value)=>__(value)},
                        {id:"job_title",name:"المسمى"},
                        {id:"daily_wage",name:"الأجر اليومي"},
                        {id:"status",name:"الحالة",format:(value)=>__(value)},
                        { id: "actions", name: "الإجراءات", format: (value,row) => `<a href='#' class="btn" data-name='${row.name}'><i class="fa fa-eye" aria-hidden="true"></i> عرض</a>` }
                    ],
                    data: data
                });
                tableContainer.find('tbody tr').css('cursor', 'pointer');
                tableContainer.off('click', 'tr').on('click', 'tr', function (e) {
                    const name = $(this).find("a.btn").data('name') || $(this).data('name');
                    // const rowData = requests.find(r => r.name === name);
                    if (name) {
                        window.open(`/app/elitehr-supply-contract-workers/${name}`, '_self');
                    }
                });

            }

        }
    });
}

function loadAttendanceData(workersData) {
    let workers = workersData.map(e => e.name);
    // console.log("workers",workers);
    
    // workers
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Elitehr Workers Check_in_out",
            filters: {"the_worker": ["in",workers]},
            fields: ["*"]
        },
        callback(r) {
            let data = r.message;
            if (data) {
                // console.log("loadAttendanceData result: ",data);

                loadAwaitingApprovalAttendanceData(data);

                let attendanceContainer = $("#attendance")
                attendanceContainer.empty();
                let tableContainer = $(`<div class="table_container"></div>`);
                tableContainer.appendTo(attendanceContainer);
                new CustomTable({
                    container: tableContainer,
                    columns: [
                        {id: "date", name: "التاريخ"},
                        {id: "worker_name", name: "العامل"},
                        {id: "check_in", name: "الحضور"},
                        {id: "check_out", name: "الانصراف"},
                        {id: "working_hours", name: "الساعات"},
                        {id: "productivity", name: "الإنتاج",format: (value,row)=>row['production_quantity'] + " " + row['unit_of_measurement']},
                        {id: "status", name: "الحالة",format:(value)=>__(value)},
                        { id: "actions", name: "الإجراءات", format: (value,row) => `<a href='#' class="btn" data-name='${row.name}'><i class="fa fa-eye" aria-hidden="true"></i> عرض</a>` }
                    ],
                    data: data
                });
                tableContainer.find('tbody tr').css('cursor', 'pointer');
                tableContainer.off('click', 'tr').on('click', 'tr', function (e) {
                    const name = $(this).find("a.btn").data('name') || $(this).data('name');
                    // const rowData = requests.find(r => r.name === name);
                    if (name) {
                        window.open(`/app/elitehr-workers-check_in_out/${name}`, '_self');
                    }
                });
            }

        }
    });
    
}


function loadAwaitingApprovalAttendanceData(attendanceData) {
    let data = attendanceData.filter(e => e.status != "Approved");
    console.log("data",data);
    
    // Awaiting Approval Attendance
    $("#myTab button[data-bs-target='#awaiting-approval']").text(`${__("Awaiting Approval")} (${data.length})`)
    let awaitingAttendanceContainer = $("#awaiting-approval")
    awaitingAttendanceContainer.empty();
    let tableContainer = $(`<div class="table_container"></div>`);
    tableContainer.appendTo(awaitingAttendanceContainer);
    new CustomTable({
        container: tableContainer,
        columns: [
            {id: "date", name: "التاريخ"},
            {id: "worker_name", name: "العامل"},
            {id: "check_in", name: "الحضور"},
            {id: "check_out", name: "الانصراف"},
            {id: "working_hours", name: "الساعات"},
            {id: "productivity", name: "الإنتاج",format: (value,row)=>row['production_quantity'] + " " + row['unit_of_measurement']},
            {id: "status", name: "الحالة",format:(value)=>__(value)},
            { id: "actions", name: "الإجراءات", format: (value,row) => `<a href='#' class="btn" data-name='${row.name}'><i class="fa fa-eye" aria-hidden="true"></i> عرض</a>` }
        ],
        data: data
    });
    tableContainer.find('tbody tr').css('cursor', 'pointer');
    tableContainer.off('click', 'tr').on('click', 'tr', function (e) {
        const name = $(this).find("a.btn").data('name') || $(this).data('name');
        // const rowData = requests.find(r => r.name === name);
        if (name) {
            window.open(`/app/elitehr-workers-check_in_out/${name}`, '_self');
        }
    });
    
}


function loadPayroll(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Elitehr Supply Contract Payroll",
            filters: {"the_contract": frm.doc.name},
            fields: ["*"]
        },
        callback(r) {
            let data = r.message;
            if (data) {
                console.log("loadPayroll result: ",data);

                // // payroll
                let payrollContainer = $("#payroll")
                payrollContainer.empty();
                let tableContainer = $(`<div class="table_container"></div>`);
                tableContainer.appendTo(payrollContainer);
                new CustomTable({
                    container: tableContainer,
                    columns: [
                        {id: "period", name: "الفترة", format:(value,row)=> `${row['from']} - ${row['to']}`},
                        {id: "workers", name: "عدد العمال"},
                        {id:"hours",name:"الساعات"},
                        {id:"total",name:"الإجمالي"},
                        {id:"total_deductions",name:"الخصومات"},
                        {id:"net",name:"الصافي"},
                        {id:"status",name:"الحالة",format:(value)=>__(value)},
                        { id: "actions", name: "الإجراءات", format: (value,row) => `<a href='#' class="btn" data-name='${row.name}'><i class="fa fa-eye" aria-hidden="true"></i> عرض</a>` }
                    ],
                    data: data
                });
                tableContainer.find('tbody tr').css('cursor', 'pointer');
                tableContainer.off('click', 'tr').on('click', 'tr', function (e) {
                    const name = $(this).find("a.btn").data('name') || $(this).data('name');
                    if (name) {
                        window.open(`/app/elitehr-supply-contract-payroll/${name}`, '_self');
                    }
                });

            }

        }
    });
    
}