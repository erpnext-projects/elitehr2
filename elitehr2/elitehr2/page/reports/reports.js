const monthsNames = [
	"يناير","فبراير","مارس","أبريل","مايو","يونيو",
	"يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"
];

frappe.pages['reports'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Reports',
		single_column: true
	});

	let dashboardContainer = $(`<div class="custom-page"></div>`);
	dashboardContainer.appendTo(page.main)

	renderStatistics(dashboardContainer);
	loadStatisticsData();


	renderTabs(dashboardContainer);
}

function renderStatistics(wrapper) {	
	$(`
        <div class="">
			
			<!-- HEADER -->
			<div class="d-flex justify-content-between align-items-center">
				<div>
					
					<h2>
						${__("Reports and Analysis")}
					</h2>
					<h5>
						${__("Comprehensive analysis of attendance and payroll data")}
					<h5>
				</div> 
			</div>

            
			<!-- Cards -->
			<div class="cardContainers flex-wrap">
			${statisticsCard("attendanceRate",__("Attendance rate"), __("Loading..."), "#3B82F6","/assets/elitehr2/icons/users.svg")}
			${statisticsCard("averageWorkingRate",__("Average working hours"), __("Loading..."), "#14B8A6","/assets/elitehr2/icons/clock.svg")}
			${statisticsCard("totalPay",__("Total pay"), __("Loading..."), "#10B981","/assets/elitehr2/icons/wallet.svg")}
			${statisticsCard("tardinessRate",__("Tardiness rate"), __("Loading..."), "#F59E0B","/assets/elitehr2/icons/arrow.svg ")}
			</div>
			 
		</div>

    `).appendTo(wrapper);
}
function statisticsCard(id,title, value, background,icon) {
    return `
        <div id="${id}" class="card">
            
            <div class="row">
				<div class="col-8">
					<div class="card-title">${title}</div>
					<div class="card-value">${value}</div>
				</div>
				
				<div class="col-4">
					<div class="flex justify-center rounded icon-bg m-3 p-3" style="background:${background};">
						<img class="icon" alt="icon" src="${icon}"/>
					</div>
				</div>
			</div>

        </div>
    `;
}

function loadStatisticsData() {
	Promise.all([getEmployees(), getAttendance()])
		.then(([empRes, attRes]) => {

			let employees = empRes.message || [];
			let attendance = attRes.message || [];

			let totalEmployee = employees.length;

			let present = attendance.filter(e => e.status_code === "Present").length;
			let absent = attendance.filter(e => e.status_code === "Absent").length;
			let late = attendance.filter(e => e.status_code === "Late").length;

			// $("#attendanceRate .card-value").text(totalEmployee);
			// $("#presenToday .card-value").text(present);
			// $("#absentToday .card-value").text(absent);
			$("#tardinessRate .card-value").text(getPrecent(late,totalEmployee));
			$("#attendanceRate .card-value").text(getPrecent(present+late,totalEmployee));


		});

	// latestLogs();
	// incominVacation()

	frappe.call(
		{
			method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_monthly_total_net_salary",
			callback: function(r) {
				if (r.message) {
					let data = r.message;
					if (data) {						
						$("#totalPay .card-value").text(data.total_salary + " " + __(data.currency));
					}
				}
			}
		}
	)
}


function renderTabs(wrapper) {
	let tabsContainer = $('<div class="tabs-container"></div>');
	tabsContainer.appendTo(wrapper);
	tabsContainer.html(`
		<ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#attendance-reports" type="button" role="tab">${__("Attendance reports")}</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#payroll-reports" type="button" role="tab">${__("Payroll reports")}</button>
            </li>
			<li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#vacation-reports" type="button" role="tab">${__("Vacation reports")}</button>
            </li>
			<li class="nav-item" role="presentation">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#approvals-reports" type="button" role="tab">${__("Approvals reports")}</button>
            </li>
			
        </ul>

        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade show active" id="attendance-reports" role="tabpanel">
				<!-- Nested Tabs -->
				<ul class="nav nav-tabs mt-3" id="attendanceSubTabs">
					<li class="nav-item">
						<button class="nav-link active" data-sub="#attendance-overview">${__("Overview")}</button>
					</li>
					<li class="nav-item">
						<button class="nav-link " data-sub="#attendance-detailed-report">${__("Detailed Report")}</button>
					</li>
				</ul>

				<div class="tab-content mt-2">
					<div class="tab-pane  show active" id="attendance-overview">${__("Loading...")}</div>
					<div class="tab-pane" id="attendance-detailed-report">${__("Loading...")}</div>
				</div>
			</div>
            <div class="tab-pane fade" id="payroll-reports" role="tabpanel">${__("Loading...")}</div>
            <div class="tab-pane fade" id="vacation-reports" role="tabpanel" class="custom-card p-4">${__("Loading...")}</div>
            <div class="tab-pane fade" id="approvals-reports" role="tabpanel" class="custom-card p-4">${__("Loading...")}</div>
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


	// nested tabs
	tabsContainer.on('click', '#attendanceSubTabs .nav-link', function () {
		$('#attendanceSubTabs .nav-link').removeClass('active');
		$(this).addClass('active');

		let target = $(this).attr('data-sub');
		$('#attendance-reports .tab-pane').removeClass('show active');
		$(target).addClass('show active');
	});	

	renderAttendanceOverview($("#attendance-overview"));
	renderAttendanceDetailedReport($("#attendance-detailed-report"));
	renderPayrollReport($("#payroll-reports"))
	renderVacationReport($("#vacation-reports"))
	renderApprovalsReport($("#approvals-reports"))
	
}

function renderApprovalsReport(container) {
	container.html(`
		<div>
				<div class="row p-4">
				
					<div  class="col-6">
						<div class="custom-card h-100">
						<h3 class="p-3">${__("Requests status")}</h3>
						<div id="requestsStatus"></div>
						</div>
					</div>
					
					<div class="col-6">
						<div class="custom-card h-100">
							<h3 class="p-3">${__("Approvals by type")}</h3>
							<canvas id="approvalsByTypeCanvas"  style="max-height: 500px;"></canvas>
						</div>
					</div>

				</div>
				
				<div class="col-12">
					<h3>${__("Monthly approval trend")}</h3>
					<canvas style="" class="col-12 pt-5" id="monthlyApprovalTrends"></canvas>
				</div>
		</div>
	`);
	


	// حالة الطبات
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_approval_report",
		callback: function(r) {
			if (r.message) {
				let data = r.message;
				if (data) {
					// console.log("get_requests_approval_report",data.data.request_status);
					let requestsStatusHtml = ''
					data.data.request_status.forEach(e => 
						requestsStatusHtml += `
							<div class="m-2 mt-4">
								<div class="d-flex justify-between">
									<strong>${e.title}</strong>
									<span>${e.count} طلب (${e.percentage}%)</span>
								</div>
								<div class="m-2">
									<div class="progress" style="flex-grow:1">
										<div class="progress-bar" style="width:${e.percentage}%;background:${e.bg}"></div>
									</div>
								</div>
							</div>
						`
					)
					requestsStatusHtml += "<hr><span>ملخص سريع</span>"
					
					let summary = data.data.summary

					requestsStatusHtml += `
						<div class="row m-3">
							${requestStatusCard("نسبة الموافقة",summary.approval_rate+"%")}
							${requestStatusCard("إجمالي الطلبات",summary.total_requests)}
							${requestStatusCard("طلبات معلقة",summary.pending_requests)}
							${requestStatusCard("متوسط وقت المعالجة (يوم)",summary.avg_processing_days)}
						</div>
					`

					function requestStatusCard(text,num) {
						return `
							<div class="col-6 p-2">
								<div class="p-4 text-center bg-gray-100 rounded">
									<h3>${num}</h3>
									<h5>${text}</h5>
								</div>
							</div>
						`
					}
					
					$("#requestsStatus").html(requestsStatusHtml)


				}
			}
		}
	});

	// الطلبات حسب النوع
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_by_type_report",
		callback: function(r) {
			if (r.message) {
				let data = r.message;
				if (data) {
					// console.log("get_requests_by_type_report: ",data);
						initChart(
							$("#approvalsByTypeCanvas"),
							"doughnut",
							{
								labels: data.map(e=> e.type_name + " " + e.count),
								datasets: [{data: data.map(e=>e.count),}]
							},
						);						
				}
			}
		}
	});

	// اتجاه الموافقات الشهري
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_yearly_monthly_requests_report",
		callback: function(r) {
			if (r.message) {
				let data = r.message;
				if (data) {
					// console.log("get_yearly_monthly_requests_report:",data);
					 const labels = monthsNames;
					 const statusMap = {};  // { Approve: Array(12) [ 0, 0, 1, … ] }
					 data.forEach(row => {
						const monthIndex = row.month - 1;
						const status = row.status;

						if (!statusMap[status]) {
							statusMap[status] = Array(12).fill(0);
						}

						statusMap[status][monthIndex] = row.count;
					});
					const datasets = Object.keys(statusMap).map(status => ({
						label: __(status),
						data: statusMap[status],
						borderWidth: 2
					}));
					// console.log(statusMap);
					
					initChart(
						$("#monthlyApprovalTrends"),
						"bar",
						{
							labels: labels,
							datasets: datasets
						}
					)
					
				}
			}
		}
	});
}

function renderVacationReport(container) {
	container.html(`
		<div>
			<div class="row p-4">
				<div class="col-12">
					<h3>${__("Monthly Vacation Statistics")}</h3>
					<canvas style="" class="col-12 pt-5" id="monthlyVacationTrends"></canvas>
					<br>
				</div>
				<div  class="col-6">
					<div class="custom-card h-100">
						<h3 class="p-3">${__("Employees with the Most Vacation Time")}</h3>
						<div id="employeesWithTheMostVacationTime"></div>
					</div>
				</div>
				<div class="col-6">
					<div class="custom-card h-100">
						<h3 class="p-3">${__("Vacation Summary")}</h3>
						<div id="vacationSummary"></div>
					</div>
				</div>
				
			</div>
		</div>
	`);

	let today = frappe.datetime.get_today();
	let from_date = frappe.datetime.month_start(today);
	let to_date = frappe.datetime.month_end(today);

	// إحصائيات الإجازات الشهرية
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_leaves_summary_monthly_yearly",
		callback: function(r) {
			let data = r.message
			if (data) {
				console.log("get_leaves_summary_monthly_yearly",data);
				const labels = monthsNames;
				const resultMap = {};  // { " عمل إضافي": (12) […], " نقل": (12) […],
				data.forEach(row => {
					const monthIndex = row.month - 1;
					const request_type = row.request_type_name;

					if (!resultMap[request_type]) {
						resultMap[request_type] = Array(12).fill(0);
					}

					resultMap[request_type][monthIndex] = row.count;
				});
				const datasets = Object.keys(resultMap).map(request_type => ({
					label: __(request_type),
					data: resultMap[request_type],
					borderWidth: 2
				}));
				// console.log(resultMap);
				
				initChart(
					$("#monthlyVacationTrends"),
					"bar",
					{
						labels: labels,
						datasets: datasets
					}
				);
			}
		}
	});

	// اكثر الموظفين اجازة
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_top_employees_leaves",
		callback: function(r) {
			if (r.message) {
				let html = "";
				r.message.forEach((emp, index) => {
					html += topEmployeeRow(
						emp.total_days,
						emp.employee_name,
						emp.job_title || "",
						index + 1 
					);
				});
				$("#employeesWithTheMostVacationTime").html(html);
			}
		}
	});

	// ملخص الإجازات
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_leaves_summary",
		callback: function(r) {
			// اكثر الموظفين اجازة
			if (r.message) {
				// console.log("get_leaves_summary");
				// console.log(r.message);
				let html = r.message.map(e=> leaveSummaryRow(e.total_days,e.leave_type)).join("");
				$("#vacationSummary").html(html);
			}
		}
	});
	


	function topEmployeeRow(days,name,title,index) {
		return `
			<div class="p-3 d-flex align-items-center justify-content-between bg-gray-100 mb-4">
				<div class="right d-flex align-center">
					<div class="flex rounded icon-bg m-3 p-3" style="">
						${days} أيام
					</div>
					<div class="d-flex flex-column align-content-center">
						<strong>${name}</strong>
						<span>${title}</span>
					</div>
				</div>
				<div class="flex rounded-circle m-3 p-3" style="background:#0284C5;width:50px;height:50px">
					<span class="text-white m-auto font-weight-bold">${index}</span>
				</div>
			</div>
		`;
	}

	function leaveSummaryRow(days,name) {
		return `
			<div class="p-3 d-flex align-items-center justify-content-between bg-gray-100 mb-4">
				<div class="right d-flex align-center">
					<div class="d-flex flex-column align-content-center">
						<strong>${days} أيام</strong>
					</div>
				</div>
				<div class="flex rounded m-3 p-3" style="background:#0284C5">
					<span class="text-white m-auto font-weight-bold">${name}</span>
				</div>
			</div>
		`;
	}
	
}

function renderPayrollReport(container) {
	container.html(`
		<div>
			<div class="row p-4">
				<div  class="col-6">
					<h3>${__("Monthly distribution of discounts")}</h3>
					<canvas style="max-height: 400px;" id="distributionOfDiscounts"></canvas>
				</div>
				<div class="col-6">
					<h3>${__("Monthly payroll trends")}</h3>
					<canvas style="max-height: 400px;" id="monthlyPayrollTrends"></canvas>
				</div>
			</div>

			<h3>${__("Monthly payroll distribution (number of employees)")}</h3>
			<canvas style="" class="col-12 pt-5" id="monthlyDistributionTrends"></canvas>

		</div>
	`);

	let today = frappe.datetime.get_today();
	let from_date = frappe.datetime.month_start(today);
	let to_date = frappe.datetime.month_end(today);

	// توزيع الخصومات
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_deductions_summary",
		args: {
			from_date: from_date,
			to_date: to_date
		},
		callback: function(r) {
			if (r.message) {
				initChart(
					$("#distributionOfDiscounts"),
					"doughnut",
					{
						labels: r.message.data.map(d => `${d.type} ( ${d.percentage} % )`),
						datasets: [{data: r.message.data.map(d => d.amount),}]
					},
				);	
			}
		}
	});

	// اتجاه الرواتب الشهري
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_monthly_payroll_trend",
		callback: function(r) {
			let data = r.message;
			// console.log("get_monthly_payroll_trend",data);
			
			if (data) {
				initChart(
					$("#monthlyPayrollTrends"),
					"line",
					{
						labels: data.months.map(m => monthsNames[m - 1]),
						datasets: [
							{
								label: "صافي الرواتب",
								data: data.salaries,
								borderWidth: 2
							},
							{
								label: "الخصومات",
								data: data.deductions,
								borderWidth: 2
							},
							{
								label: "البدلات",
								data: data.allowances,
								borderWidth: 2
							}
						]
					},
				);	
			}
		}
	});
	
	// توزيع الرواتب الشهرية (عدد الموظفين)
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_payroll.elitehr_payroll.get_salary_distribution",
		args: {
			from_date: from_date,
			to_date: to_date
		},
		callback: function(r) {
			let data = r.message;
			// console.log("get_monthly_payroll_trend",data);
			
			if (data) {
				initChart(
					$("#monthlyDistributionTrends"),
					"bar",
					{
						labels: Object.keys(data),
						datasets: [
							{
								label: "عدد الموظفين",
								data: Object.values(data),
								backgroundColor: [
									"#3b82f6", // أزرق
									"#10b981", // أخضر
									"#f59e0b", // أصفر
									"#8b5cf6", // بنفسجي
									"#ef4444", // أحمر
									"#14b8a6"  // تركواز
								],
							}
						]
					},
					{
						indexAxis: 'y',
						scales: {
								x: {
									ticks: {
										stepSize: 1,
										precision: 0 
									}
								}
							}
					}
				);	
			}
		}
	});

	
	
}


function renderAttendanceOverview(container) {
	container.html(`
			<div>
				<div class="row p-4">
					<div  class="col-6">
						<h3>${__("Monthly attendance by department")}</h3>
						<canvas style="max-height: 400px;" id="monthlyAttendanceByDepartment"></canvas>
					</div>
					<div class="col-6">
						<h3>${__("Monthly attendance trend")}</h3>
						<canvas style="max-height: 400px;" id="monthlyAttendanceTrend"></canvas>
					</div>
				</div>

				<h3>${__("Weekly attendance trend")}</h3>
				<canvas style="" class="col-12 pt-5" id="weeklyAttendanceTrend"></canvas>

			</div>
		`);


		const today = frappe.datetime.get_today();

	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_employee_attendance_handler",
		args: { 
			from_date: moment(today).startOf("month").format("YYYY-MM-DD"),
			to_date: moment(today).endOf("month").format("YYYY-MM-DD"),
		},
		callback: function (r) {
			let data = r.message;
			// console.log("r data");
			// console.log(data);
			const resultByDepartment = {};
			data.forEach(item => {
				const dept = item.department || "Unknown";
				resultByDepartment[dept] = (resultByDepartment[dept] || 0) + 1;
			});
			const labels = Object.keys(resultByDepartment);
			const values = Object.values(resultByDepartment);
			initChart(
				$("#monthlyAttendanceByDepartment"),
				"doughnut",
				{
					labels: labels,
					datasets: [{data: values,}]
				},
			);	
		}
	});


	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_year_monthes_employees",
		callback: function(r) {
			let data = r.message || []
			const labels = data.map(d => monthsNames[d.month - 1]);
			const present = data.map(d => d.present);
			const late = data.map(d => d.late);
			const absent = data.map(d => d.absent);
			initChart(
				$("#monthlyAttendanceTrend"),
				"bar",
				{
					labels: labels,
					datasets: [
						{
							label: "غائب",
							data: absent,
							backgroundColor: "#e43832",
							borderRadius: 6
						},
						{
							label: "متأخر",
							data: late,
							backgroundColor: "#F59E0B",
							borderRadius: 6
						},
						{
							label:"حاضر",
							data: present,
							backgroundColor: "#10B981",
							borderRadius: 6
						},
				]
				},
				
			);
		}
	})

	// السبت = نرجع كام يوم؟
	const diff = (new Date(today).getDay() + 1) % 7;
	const from_date = frappe.datetime.add_days(today, -diff);
	const to_date = today;
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_employee_attendance_handler",
		args: { 
			from_date: from_date,
			to_date: to_date,
		},
		callback: function(r) {
			let data = r.message || []
			const resultByDate = {};
			data.forEach(item => {
				const date = item.date.split(" ")[0];
				resultByDate[date] = resultByDate[date] || 0
				if(["Present","Late"].includes(item.status_code)){								
					resultByDate[date] = resultByDate[date] + 1;
				}
			});						

			initChart($("#weeklyAttendanceTrend"), "line", {
				labels: Object.keys(resultByDate),
				datasets: [
					{
						label: "حاضر",
						data: Object.values(resultByDate),
						backgroundColor: "rgba(16,185,129,0.2)",
						borderColor: "#10B981",
						tension: 0.4,
						fill: true
					}
				]
			});
		}
	});
				
}


let attendanceDetailedReportFromDateField;
let attendanceDetailedReportToDateField;
let attendanceDetailedReportEmployeeField;
let attendanceDetailedReportDepartmentField;
let attendanceDetailedReportSatusField;
let attendanceDetailedReportData = [];
let attendanceDetailedReportSelectedFromDate;
let attendanceDetailedReportSelectedEndDate;

function renderAttendanceDetailedReport(container) {
	container.html("");
	let filtersContainer = $(`<div class="myFiltersContainer"></div>`)
	let tableContainer = $(`<div class="table_container"></div>`)
	filtersContainer.appendTo(container);
	tableContainer.appendTo(container);

	attendanceDetailedReportFromDateField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {
			label: __('من تاريخ:'),
			fieldname: 'from_date',
			fieldtype: 'Date',
			change: onFieldsUpdate
		},
		render_input: true
	});
	attendanceDetailedReportFromDateField.set_value(frappe.datetime.month_start());


	attendanceDetailedReportToDateField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {
			label: __('الي تاريخ:'),
			fieldname: 'to_date',
			fieldtype: 'Date',
			change: onFieldsUpdate
		},
		render_input: true
	});
	attendanceDetailedReportToDateField.set_value(frappe.datetime.month_end());

	attendanceDetailedReportEmployeeField = frappe.ui.form.make_control({
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

	attendanceDetailedReportDepartmentField = frappe.ui.form.make_control({
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

	attendanceDetailedReportSatusField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {

			label: 'الحالة',
			fieldname: 'status',
			fieldtype: 'Select',
			options: ["","Present","Late","Absent"],
			change: onFieldsUpdate
		},
		render_input: true
	});
	$(attendanceDetailedReportSatusField.wrapper).css({
		// "flex": "1 1 auto",
		"min-width": "250px"
	});
	
	function onFieldsUpdate() {
		
		if(attendanceDetailedReportSelectedFromDate == attendanceDetailedReportFromDateField.get_value() && attendanceDetailedReportSelectedEndDate == attendanceDetailedReportToDateField.get_value() && attendanceDetailedReportData.length > 0){
			tableContainer.html('<p>جاري التحميل...</p>');
			// console.log(attendanceDetailedReportSelectedFromDate,attendanceDetailedReportSelectedEndDate);
			// console.log("onFieldsUpdate data from memory: ",attendanceDetailedReportData);
			renderAttendanceDetailedReportTable(tableContainer,attendanceDetailedReportData);

		}else if (attendanceDetailedReportFromDateField.get_value() && attendanceDetailedReportToDateField.get_value()) {
			tableContainer.html('<p>جاري التحميل...</p>');
			frappe.call({
				method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_employee_attendance_handler",
				args: { 
					from_date: attendanceDetailedReportFromDateField.get_value(),
					to_date: attendanceDetailedReportToDateField.get_value(),
				},
				callback: function(r) {
					let data = r.message || []
					attendanceDetailedReportSelectedFromDate = attendanceDetailedReportFromDateField.get_value();
					attendanceDetailedReportSelectedEndDate = attendanceDetailedReportToDateField.get_value();
					attendanceDetailedReportData = data;
					// console.log("onFieldsUpdate data from server: ",data);
					renderAttendanceDetailedReportTable(tableContainer,attendanceDetailedReportData);
					
				}
			})
		}
	
	}
	
}


function renderAttendanceDetailedReportTable(tableContainer,requests) {
	tableContainer.empty();
	
	if (!requests || requests.length === 0) {
		tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
		return;
	}

	requests.sort((a, b) => new Date(a.date) - new Date(b.date));

	// filters
	if (attendanceDetailedReportEmployeeField.get_value()) {
		requests = requests.filter(r => r.employee == attendanceDetailedReportEmployeeField.get_value());
	}

	if (attendanceDetailedReportDepartmentField.get_value()) {
		requests = requests.filter(r => r.department == attendanceDetailedReportDepartmentField.get_value());
	}

	if (attendanceDetailedReportSatusField.get_value()) {
		requests = requests.filter(r => r.status_code == attendanceDetailedReportSatusField.get_value());
	}

	

	const columns = [
		{ id: "date", name: "التاريخ" },
		{ id: "employee_name", name: "الموظف" },
		{ id: "department_name", name: "القسم" },
		{
			id: "check_in", name: "الحضور",
			format: (value) => `<span class='color3'><i class="fa fa-clock-o" aria-hidden="true"></i></span> ${value} `
		},
		{
			id: "check_out", name: "الانصراف",
			format: (value) => `<i class="fa fa-clock-o" aria-hidden="true"></i> ${value} `
		},
		{
			id: "status", name: "الحالة",
			format: (value, row) => {
				return `<span class='${row.status_color}'>${value}</span>`
			}
		},
		{ id: "working_hours", name: "الساعات" }
	]
	
	new CustomTable({
		container: tableContainer,
		columns: columns,
		data: requests
	});
}

function initChart(chartContainer,type,data, extraOptions = {}) {

    if (!chartContainer) return;

	 // destroy old chart
    if (chartContainer.chartInstance) {
        chartContainer.chartInstance.destroy();
    }

	const ctx = chartContainer[0].getContext("2d");
	
    chartContainer.chartInstance = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            cutout: type === "doughnut" ? "70%" : undefined,
			...extraOptions,
            plugins: {
                legend: {
                    display: true,
					position: 'bottom'
                }
            }
        }
    });
}

function getEmployees() {
    return frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Elitehr Employee",
            filters: { status: "Active" },
            fields: ["name"]
        }
    });
}

function getAttendance() {
    return frappe.call({
        method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_employee_attendance_handler",
        args: { from_date: frappe.datetime.get_today() }
    });
}

function getPrecent(count,totalEmployee) {
	return totalEmployee > 0
				? (( count / totalEmployee) * 100).toFixed(1) + " %"
				: "0 %"
}
