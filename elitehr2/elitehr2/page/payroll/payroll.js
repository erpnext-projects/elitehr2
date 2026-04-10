const wrapperContent = $('<div dir="rtl" class="custom-page"></div>');
let tabsContainer = $('<div class="tabs-container"></div>');
let cardRow = $('<div class="cardContainers"></div>');
let tableHeader = $('<br><div class="table-header" dir="rtl"></div>');
let tableContainer = $('<div class="requests-table" dir="rtl"></div>');
let filtersContainer = $(`<div class="myFiltersContainer"></div>`);
// let bySectionContainer = $(`<div class="myBySectionContainer"></div>`);
// let collectiveDisclosureContainer = $(`<div class="CollectiveDisclosure"></div>`);
let fromDateField;
let toDateField;
let employeeField;
let departmentField;
let selectedFromDate;
let selectedEndDate;
let requestsData = [];

frappe.pages['payroll'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payroll',
		single_column: true
	});

	wrapperContent.appendTo(page.main);
	// Containers
	$(`<h2><svg class="icon text-ink-gray-7 current-color icon-sm" stroke="currentColor" style="" aria-hidden="true"><use class="" href="#icon-wallet"></use></svg>${__("Payroll")}</h2>`).appendTo(wrapperContent);
	$(`<span>${__("Managing and calculating employee and seasonal worker salaries")}</span><br>`).appendTo(wrapperContent);
	cardRow.appendTo(wrapperContent);
	filtersContainer.appendTo(wrapperContent);

	tabsContainer.appendTo(wrapperContent);
	tabsContainer.html(`
		<ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#RegularSalaries" type="button" role="tab">الرواتب المنتظمة</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#BySection" type="button" role="tab">حسب الأقسام </button>
            </li>
			<li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#CollectiveDisclosure" type="button" role="tab">الكشف المجمع</button>
            </li>
			
        </ul>

        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade show active" id="RegularSalaries" role="tabpanel"></div>
            <div class="tab-pane fade" id="BySection" role="tabpanel"></div>
            <div class="tab-pane fade" id="CollectiveDisclosure" role="tabpanel" class="custom-card p-4"></div>
        </div>
	`);
	// تفعيل التبديل بين التبويبات يدوياً
    tabsContainer.on('click', '.nav-link', function (e) {
        e.preventDefault();
        tabsContainer.find('.nav-link').removeClass('active');
        $(this).addClass('active');
        const target = $(this).attr('data-bs-target');
        tabsContainer.find('.tab-pane').removeClass('show active');
        $(target).addClass('show active');
    });

	// tab RegularSalaries Content
	tableHeader.appendTo(tabsContainer.find('#RegularSalaries'));
	tableContainer.appendTo(tabsContainer.find('#RegularSalaries'));


	// tab BySection Content
	// bySectionContainer.appendTo(tabsContainer.find('#BySection'));
	// tab CollectiveDisclosure Content
	// collectiveDisclosureContainer.appendTo(tabsContainer.find('#CollectiveDisclosure'));

	loadStatistics();
	renderFormFields();
	renderPageButtons(page);

}


function loadStatistics() {

	cardRow.html(`
		<div class="card">
			<div class="card-title">${__("Total Salaries")}</div>
			<div id="totalSalaries" class="card-value">0</div>
		</div>
		<div class="card">
			<div class="card-title">${__("Permanent Employees")}</div>
			<div id="permanentEmployees" class="card-value ">0</div>
		</div>
		<div class="card">
			<div class="card-title">${__("Seasonal Employees")}</div>
			<div id="seasonalEmployees" class="card-value ">0</div>
		</div>
		<div class="card">
			<div class="card-title">${__("Total Deductions")}</div>
			<div id="totalDeductions" class="card-value">0</div>
		</div>
	`);

	
	// load salaries statistics
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_monthly_comparison_stats",
		args: { field: "net_salary" },
		callback: function (r) {
			const stats = r.message || {};
			let totalSalariesContainer = cardRow.find("#totalSalaries")
			totalSalariesContainer.text(stats.total || 0);
			totalSalariesContainer.after(`<div class="color5 card-diff ${stats.diff_percent >= 0 ? 'positive' : 'negative'}">${stats.diff_text} عن الشهر الماضي</div>`);			
		}
	});
	
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee.elitehr_employee.get_employee_growth_stats",
		callback: function (r) {
			const stats = r.message || {};
			console.log(stats);
			
			let permanentEmployeesContainer = cardRow.find("#permanentEmployees")
			permanentEmployeesContainer.text(stats.total || 0);
			permanentEmployeesContainer.after(`<div class="color5 card-diff ${stats.diff_percent >= 0 ? 'positive' : 'negative'}">${stats.diff_text} عن الشهر الماضي</div>`);			
		}
	});

	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_monthly_comparison_stats",
		args: { field: "total_deductions" },
		callback: function (r) {
			const stats = r.message || {};
			let totalDeductionsContainer = cardRow.find("#totalDeductions")
			totalDeductionsContainer.text(stats.total || 0);
			totalDeductionsContainer.after(`<div class="color5 card-diff ${stats.diff_percent >= 0 ? 'positive' : 'negative'}">${stats.diff_text} عن الشهر الماضي</div>`);			
		}
	});


}

function checkRequestsHasData(requests,containerData) {
	if (!requests || requests.length === 0) {
		containerData.html('<p>لا توجد طلبات لعرضها</p>');
		return false;
	}
	return true;
}

function loadRegularSalariesData(requests) {

		// openPayslipModal(requests[0]);
		

		tableContainer.empty();
		if (checkRequestsHasData(requests,tableContainer) === false) {
			tableHeader.find(".totalNumber").empty();
			return;
		}


		let totalSalaries = requests.reduce((sum, r) => sum + (parseFloat(r.net_salary) || 0), 0);
		tableHeader.html(`<h3> كشف رواتب الموظفين الدائمين </h3><h3 class="color5 totalNumber"> الإجمالي: ${totalSalaries} </h3>`);

		if (employeeField.get_value()) {
			requests = requests.filter(r => r.employee == employeeField.get_value());
		}

		if (departmentField.get_value()) {
			requests = requests.filter(r => r.department == departmentField.get_value());
		}			


		const columns = [
			{ id: "employee_name", name: "الموظف",count:true,textBefore: "الإجمالي (", textAfter: " موظف)" },
			{ id: "department_name", name: "القسم" },
			{ id: "basic_salary", name: "الراتب الاساسي",sum:true},
			{ id: "total_allowances", name: "البدلات",sum: true },
			{ id: "total_deductions", name: "الخصومات" ,sum: true},
			{ id: "net_salary", name: "صافي الراتب" ,sum: true},
			{ id: "status", name: "الحالة", format: (value) => `<span class="${value=='Salary Disbursement'?'color3':'color1'}">${__(value)}</span>` },
			{ id: "actions", name: "الإجراءات", format: (value,row) => `<a href='#' class="btn" data-name='${row.name}'><i class="fa fa-eye" aria-hidden="true"></i> عرض</a>` }

		];

		tableContainer.off('click', 'tr').on('click', 'tr', function (e) {
			const name = $(this).find("a.btn").data('name') || $(this).data('name');
			const rowData = requests.find(r => r.name === name);
			if (rowData) {
				openPayslipModal(rowData);
			}
		});
		new CustomTable({
			container: tableContainer,
			columns: columns,
			data: requests
		});
		tableContainer.find('tbody tr').css('cursor', 'pointer');
}

function renderBySectionData(requests) {
	let container = tabsContainer.find('#BySection');

	container.empty();
	if (checkRequestsHasData(requests,container) === false) {
		return;
	}
	
	// group by department
	let dataByDepartment = {};
	requests.forEach(r => {
		if (!dataByDepartment[r.department_name]) {
			dataByDepartment[r.department_name] = [];
		}
		dataByDepartment[r.department_name].push(r);
	});
	// console.log("dataByDepartment",dataByDepartment);

	container.empty();
	for (let dept in dataByDepartment) {
		let section = $(`
			<br>
			<div class="by-section">
				<h3>${dept} (${dataByDepartment[dept].length }) موظف</h3>
				<div class="section-content"></div>
			</div>
		`);
		let totalSalaries = dataByDepartment[dept].reduce((sum, r) => sum + (parseFloat(r.net_salary) || 0), 0);
		section.find("h3").append(`<span class="color5" style="font-size: 16px;"> - إجمالي الرواتب: ${totalSalaries} </span>`);
		let sectionContent = section.find(".section-content");


		const columns = [
			{ id: "employee_name", name: "الموظف" },
			{ id: "basic_salary", name: "الراتب الاساسي"},
			{ id: "total_allowances", name: "البدلات" },
			{ id: "total_deductions", name: "الخصومات" },
			{ id: "net_salary", name: "صافي الراتب" },
			{ id: "status", name: "الحالة", format: (value) => __(value) },
		];

		new CustomTable({
			container: sectionContent,
			columns: columns,
			data: dataByDepartment[dept]
		});

		container.append(section);
	}

}

function renderCollectiveDisclosure(requests) {
	let container = tabsContainer.find('#CollectiveDisclosure');
	
	container.empty();
	if (checkRequestsHasData(requests,container) === false) {
		return;
	}

	// توزيع الرواتب حسب الأقسام
	// group by department
	let dataByDepartment = {};
	requests.forEach(r => {
		if (!dataByDepartment[r.department_name]) {
			dataByDepartment[r.department_name] = [];
		}
		dataByDepartment[r.department_name].push(r);
	});

	// console.log("dataByDepartment",dataByDepartment);
	$(`<br><h3>توزيع الرواتب حسب الأقسام</h3><br>`).appendTo(container);
	let totalSectionSalaries = requests.reduce((sum, r) => sum + (parseFloat(r.net_salary) || 0), 0);
	for (const dept in dataByDepartment) {
		let totalSalaries = dataByDepartment[dept].reduce((sum, r) => sum + (parseFloat(r.net_salary) || 0), 0);
		let percentage = ((totalSalaries / totalSectionSalaries) * 100).toFixed(2)+ "%";
		$(`
			<div class="cardContainers">
				<h4 style="min-width: 100px;">${dept}</h4>
				<div class="progress" style="flex-grow:1">
					<div class="progress-bar" style="width:${percentage}">${percentage}</div>
				</div>
				<span class="color5" style="min-width: 50px;"> ${totalSalaries}</span>
			</div>`
		).appendTo(container);
	}

	$(`<br><h3>رواتب عقود التوريد</h3><br>`).appendTo(container);
	$(`
		<hr>
		<div class="flex justify-between"> 
			<h3>الإجمالي الكلي</h3>
			<h4 class="color5">${totalSectionSalaries}</h4>
		</div>	
	`).appendTo(container);
}


function openPayslipModal(row) {
	console.log("row: ",row);
	
    let d = new frappe.ui.Dialog({
        title: `${__("كشف راتب")} - ${row.employee_name}`,
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'payslip_details',
            },
            // { fieldtype: 'Section Break', label: __('تصحيحات على الراتب والحالة') },
            // {
            //     fieldtype: 'Float',
            //     fieldname: 'correction_amount',
            //     label: __('تصحيح الراتب (موجب للإضافة / سالب للخصم)'),
            //     default: row.correction_amount || 0
            // },
            // {
            //     fieldtype: 'Select',
            //     fieldname: 'status',
            //     label: __('حالة الطلب'),
            //     options: ['Draft', 'Approved', 'Paid'],
            //     default: row.status
            // }
        ],
        primary_action_label: __('حفظ التعديلات'),
        primary_action(values) {
            // d.get_primary_btn().prop('disabled', true).text(__('جاري الحفظ...'));
            
            // // استدعاء السيرفر لحفظ التعديل
            // frappe.call({
            //     method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.update_payroll_entry",
            //     args: {
            //         docname: row.name,
            //         correction_amount: values.correction_amount,
            //         status: values.status
            //     },
            //     callback: function (r) {
            //         d.hide();
            //         frappe.show_alert({ message: __('تم تحديث كشف الراتب بنجاح'), subtitle: 'success' });
            //         // إعادة تحميل الجدول لمشاهدة التحديث
            //         renderTable(fromDateField.get_value(), toDateField.get_value());
            //     }
            // });
        }
    });

	// المستحقات
	let allowancesHTML = ''
	let totalAllowances = row.basic_salary;
	row.allowances.forEach(a => {
		let amount;
		if(a.type === "Percentage") {
			amount = (row.basic_salary * a.amount / 100).toFixed(2);
		}else {
			amount = a.amount;
		}
		totalAllowances += parseFloat(amount);
		allowancesHTML += `
			<div class="payslip-row">
				<span>${a.name1}</span> 
				<strong>${amount}</strong>
			</div>
		`;
	});

	// الاستقطاعات
	let deductionsHTML = ''
	let totalDeductions = 0;
	row.deductions.forEach(d => {
		let amount;
		if(d.type === "Percentage") {
			amount = (row.basic_salary * d.amount / 100).toFixed(2);
		}else {
			amount = d.amount;
		}
		totalDeductions += parseFloat(amount);
		deductionsHTML += `
			<div class="payslip-row">
				<span>${d.name1}</span> 
				<strong>${amount}</strong>
			</div>
		`
	});

	// تصحيحات على الراتب
	row.salary_correction.forEach(c => {
		if (c.type == "Addition (+)") {
			totalAllowances += parseFloat(c.amount);
			allowancesHTML += `
				<div class="payslip-row color2">
					<span>${__(c.addition_type)}</span> 
					<strong>${c.amount}</strong>
				</div>
			`;
		}else if (c.type == "Deduction (-)") {
			totalDeductions += parseFloat(c.amount);
			deductionsHTML += `
				<div class="payslip-row color2">
					<span>${__(c.deduction_type)}</span> 
					<strong>${c.amount}</strong>
				</div>
			`;
		}
	});

	// total Allowances and Deductions
	allowancesHTML += `
		<hr>
		<div class="payslip-row">
			<strong >إجمالي المستحقات</strong> 
			<strong>${totalAllowances}</strong>
		</div>
	`;
	deductionsHTML += `
		<hr>
		<div class="payslip-row">
			<strong >إجمالي الاستقطاعات</strong> 
			<strong>${totalDeductions}</strong>
		</div>
	`;

	// console.log("row",row);
	let workingHours;
	
	
    // رسم كشف الراتب (Payslip) بتنسيق شيك
	let ddate = new Date(row.creation);
	let month = ddate.getMonth() + 1;
	let year = ddate.getFullYear();
    const payslipHTML = `
		<h4> تفاصيل راتب شهر ${month} - ${year}  </h4>
		<h5 class="flex justify-between">
					حالة الراتب
			<span class="status badge color1">
				${__(row.status)}
			</span>
		</h5>
		<br>
		<div class="payslip-box">
			<div class="payslip-header">
				<div class="text-center">
					<strong>الرقم الوظيفي</strong> 
					<div>${row.employee_id}</div>
				</div>
				<div class="text-center">
					<strong>القسم</strong>
						<div>${row.department_name || ""}</div>
					</div>
			</div>
			<div class="payslip-header">
				<div class="text-center">
					<strong>نوع العقد</strong> 
					<div>${row.type_of_contract || ""}</div>
				</div>
				<div class="text-center">
					<strong>تاريخ التعيين</strong>
					<div>${row.date_of_appointment || ""}</div>
				</div>
			</div>
			
			<div class="payslip-details">

		
				<div class="payslip-card">
					<h5>ملخص الحضور والانصراف</h5>
					<div class="d-flex justify-between">
						<div class="align-center flex-column w-50">
							<span>ساعات العمل</span>
							<span>0 ساعة</span>
						</div>
						<div class="align-center flex-column w-50">
							<span>أيام العمل الفعلية </span>
							<span>0 يوم</span>
						</div>
					</div>
					<br>
					<div class="d-flex justify-between">
						<div class="align-center flex-column w-50">
							<span>أيام الغياب </span>
							<span>0 يوم</span>
						</div>
						<div class="align-center flex-column w-50">
							<span>أيام التأخير</span>
							<span>0 يوم</span>
						</div>
					</div>
				</div>

				<div class="payslip-card">
					<h5>اخر سجلات الحضور</h5>
					<div class="last-attendance">
						${__("Loading...")}
					</div>
				</div>
				
				<div class="payslip-card allowances">
					<h5>➕ المستحقات</h5>
					<div class="payslip-row">
						<span>الراتب الأساسي:</span> 
						<strong>${row.basic_salary}</strong>
					</div>
					${allowancesHTML}
				</div>

				<div class="payslip-card deductions">
					<h5>➖ الاستقطاعات</h5>
					${deductionsHTML}
				</div>
			</div>

			<div class="payslip-summary">
				<strong>صافي الراتب:</strong> 
				<span class="summary-value">
					${row.net_salary}
				</span>
			</div>
		</div>
	`;

    d.fields_dict.payslip_details.$wrapper.html(payslipHTML);
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_employee_checkin_list",
		args: { employee: row.employee },
		callback: function (r) {
			if (r.message) {
				console.log("data from chekin",r.message);
				const data = r.message;
				
				const attendanceTableHTML = `
					<table class="attendance-table  table text-center">
						<thead>
							<tr>
								<th>التاريخ</th>
								<th>دخول</th>
								<th>خروج</th>
								<th>الحالة</th>
							</tr>
						</thead>
						<tbody>
							${data.map(d => `
								<tr>
									<td>${d.date}</td>
									<td>${d.check_in || "غير مسجل"}</td>
									<td>${d.check_out || "غير مسجل"}</td>
									<td class="${d.status_color}">${d.status}</td>
								</tr>
							`).join("")}
						</tbody>
					</table>
				`;
				d.fields_dict.payslip_details.$wrapper.find(".last-attendance").html(attendanceTableHTML);
				let cont = d.fields_dict.payslip_details.$wrapper.find(".last-attendance")
				console.log(cont);
				
			}
		}
	});

	if (row.status != "Salary Disbursement") {
		d.set_primary_action(__("Change Payroll Status"), function() {
			frappe.prompt({
				label: 'Status',
				fieldname: 'status',
				fieldtype: 'Select',
				options: [
					"Under review",
					"Rejected",
					"Approved",
					"Salary Disbursement"
				],
				"reqd": 1
			}, (values) => {
				console.log("values",values,values.status);
				
				frappe.call({
					method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.update_payroll_status",
					args: { payroll: row.name, status: values.status },
					callback: function (r) {
						d.hide();
						updatePageData();
						frappe.show_alert('تم تغيير حالة الطب', 5);
					}
				});
			})
		});
	}else{
		d.set_primary_action(__(""), function() {});
	}

	d.show();


	if (row.status != "Salary Disbursement") {
		d.add_custom_action(__("تصحيح الراتب"), function () {
			// open doctype salary with name
			window.open(`/app/elitehr-payroll/${row.name}`, '_self');
			d.hide();
		});
	}
	// 	d.add_custom_action(__("Reject"), function() {
			
	// 	});
		
	
	// }

	// if (row.status == "Submit") {
	// 	d.add_custom_action(__("Salary Disbursement"),function() {
			
	// 	})
	// }

}


function renderFormFields() {
	fromDateField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {
			label: __('من تاريخ:'),
			fieldname: 'from_date',
			fieldtype: 'Date',
			change: onFieldsUpdate
		},
		render_input: true
	});
	fromDateField.set_value(frappe.datetime.month_start());


	toDateField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {
			label: __('الي تاريخ:'),
			fieldname: 'to_date',
			fieldtype: 'Date',
			change: onFieldsUpdate
		},
		render_input: true
	});
	toDateField.set_value(frappe.datetime.month_end());

	employeeField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {

			label: 'بحث عن موظف',
			fieldname: 'employee_search',
			fieldtype: 'Link',
			options: 'Elitehr Employee',
			placeholder: 'بحث عن موظف...',
			change: onFieldsUpdate
		},
		render_input: true
	});
	$(employeeField.wrapper).css({
		"flex": "1 1 auto",
		"min-width": "250px"
	});

	departmentField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {

			label: 'القسم',
			fieldname: 'department',
			fieldtype: 'Link',
			options: 'Elitehr Fingerprint Sites',
			default: '',
			change: onFieldsUpdate
		},
		render_input: true
	});
}

function onFieldsUpdate() {
	if (selectedFromDate == fromDateField.get_value() && selectedEndDate == toDateField.get_value() && requestsData.length > 0) {
		// console.log("Using cached data");
		loadRegularSalariesData(requestsData);
		renderBySectionData(requestsData);
		renderCollectiveDisclosure(requestsData);
		
	}else if (fromDateField.get_value() && toDateField.get_value()) {
		fetchRequestsData(fromDateField.get_value(), toDateField.get_value(), function(requests) {
			selectedFromDate = fromDateField.get_value();
			selectedEndDate = toDateField.get_value();
			requestsData = requests;
			loadRegularSalariesData(requests);
			renderBySectionData(requests);
			renderCollectiveDisclosure(requests);
		});
	}
	
}

function fetchRequestsData(fromDate, toDate,onComplete) {
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.payrloll",
		args: { fromDate: fromDate, toDate: toDate },
		callback: function (r) {
			let requests = r.message || [];
			onComplete(requests);
		}
	});
}

function renderPageButtons(page) {
	page.add_inner_button(__("Final Settlements"), function () {
		alert("جاري التطوير...");
	});
	page.add_inner_button(__("Payroll Calculation"), function () {
		payrollCalculation();
	});
	page.add_inner_button(__("Update"), function () {
		updatePageData()
	});
}


function updatePageData() {
	loadStatistics();
	requestsData = [];
	onFieldsUpdate();
}

function payrollCalculation() {
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.calculate_payroll_for_all_employees",
		args: {},
		callback: function (r) {
			if (r.message) {
				frappe.show_alert({ message: __('تم حساب الرواتب بنجاح') });
				requestsData = [];
				onFieldsUpdate();
			}
		}
	});
}


function openSalaryCorrectionDialog(row) {

}