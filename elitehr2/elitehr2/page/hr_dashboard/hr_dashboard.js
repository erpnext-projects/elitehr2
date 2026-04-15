frappe.pages['hr-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Hr Dashboard',
		single_column: true
	});


	let dashboardContainer = $(`<div class="custom-page"></div>`);
	dashboardContainer.appendTo(page.main)
	renderUI(dashboardContainer);
	loadPageData();

	page.add_inner_button(__("Update"), function () {
		loadPageData()
	});
}

function loadPageData() {
	Promise.all([getEmployees(), getAttendance()])
		.then(([empRes, attRes]) => {

			let employees = empRes.message || [];
			let attendance = attRes.message || [];

			let totalEmployee = employees.length;

			let present = attendance.filter(e => e.status_code === "Present").length;
			let absent = attendance.filter(e => e.status_code === "Absent").length;
			let late = attendance.filter(e => e.status_code === "Late").length;

			$("#totalEmployee .card-value").text(totalEmployee);
			$("#presenToday .card-value").text(present);
			$("#absentToday .card-value").text(absent);
			$("#lateToday .card-value").text(late);
			$("#presenPrecentage .card-value").text(getPrecent(present+late,totalEmployee));


			frappe.require("https://cdn.jsdelivr.net/npm/chart.js", () => {
				initChart({
					present,
					late,
					absent,
					vacation: 0,
					totalEmployee: totalEmployee,
				});
			});

		});

	latestLogs();
	incominVacation()
}

function renderUI(wrapper) {	
	let today = new Date();

    let formattedDate = today.toLocaleDateString('ar-EG', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
	
	$(wrapper).html(`
        <div class="dashboard-container">
			
			<!-- HEADER -->
			<div class="d-flex justify-content-between align-items-center">
				<div>
					
					<h2>
						${__("Welcome")}, ${frappe.session.user_fullname} 👋
					</h2>
					<h5>
						${__("Here's an overview of today's activity")} -  ${formattedDate}
					<h5>
				</div>
				<div class="">
					<div class="rounded-pill p-2 color6 mr-1 ml-1" style="background: #24A8711A;">
						<span class="rounded-circle bg-success d-inline-block" style="width:10px; height:10px;"></span>
						<span class="mr-1 ml-1">النظام يعمل بشكل طبيعي</span>
					</div>
				</div>
			</div>

            <!-- Cards -->
            <div class="cardContainers flex-wrap">
				${card("totalEmployee","إجمالي الموظفين", __("Loading..."), "color3")}
                ${card("presenToday"," الحاضرون اليوم", __("Loading..."), "color5")}
                ${card("lateToday","المتأخرون",__("Loading..."), "color1")}
                ${card("absentToday","الغائبون", __("Loading..."), "color4")}
                ${card("inHoliday","في إجازة", "0", "color2")}
                ${card("presenPrecentage","معدل الحضور", __("Loading..."), "color6")}
            </div>


			<!-- Quick Actions And Chart -->
			<div class="actions-and-charts row p-3">
				<!-- Quick Actions -->
				<div class="actions-box custom-card ">
					<h3 class="card-title">إجراءات سريعة</h3>

					<div class=actionsCardContainer>
						<div class="actions-grid">
							${quickAction("إضافة موظف","#3B82F6","/assets/elitehr2/icons/add_emp.png","/desk/elitehr-employee/new-elitehr-employee")}
							${quickAction("تسجيل حضور","#14B8A6","/assets/elitehr2/icons/doc_check.png","/desk/attendance-log")}
							${quickAction("طلب إجازة","#A855F7","/assets/elitehr2/icons/calendar.png","/desk/elitehr-requests/new-elitehr-requests")}
							${quickAction("إعداد الرواتب","#10B981","/assets/elitehr2/icons/wallet.svg","/desk/payroll")}
							${quickAction("تصدير تقرير","#F97316","/assets/elitehr2/icons/download.png","/desk/reports")}
							${quickAction("عرض التقارير","#EC4899","/assets/elitehr2/icons/doc.png","/desk/reports")}
						</div>
					</div>

				</div>

				<span class="p-3"></span>

				<!-- Chart -->
				<div class="custom-card chart-box">
					<div class="d-flex justify-content-between align-items-center">
						<h3>نظرة عامة على الحضور</h3>
						<span>اليوم</span>
					</div>

					<div class="d-flex justify-content-center">
						<canvas id="attendanceChart" style=""></canvas>
					</div>

					<div class="d-flex justify-content-center flex-wrap mt-3" id="attendanceLegend"></div>
				</div>
			</div>

			
			<!-- Latest Logs And Vacations-->
			<div class="row p-3">

				<!-- Latest Logs -->
				<div class="col-12 col-md-6">
					<div class="custom-card h-100">
						<h3 class="p-3">النشاط الأخير</h3>
						<div id="latest-log-list"></div>
					</div>
				</div>

				<!-- Vacations -->
				<div class="col-12 col-md-6">
					<div class="custom-card h-100">
						<h3 class="p-3">الإجازات القادمة</h3>
						<div id="incomin-vaction"></div>
					</div>
				</div>

			</div>


        </div>
    `);
}

function incominVacation() {
	frappe.call({
        method: "frappe.client.get_list",
        args: {
			doctype: "Elitehr Requests",
			fields:["*"], // "employee","employee_name","request_type_name",""
			filters:{"request_type_code":["in",["LEAVE_ANNUAL","LEAVE_SICK","LEAVE_EMERGENCY"]]},
			order_by: "creation desc",
			limit_page_length:10
		},
		callback: function (r) {
			let data = r.message || []	
			
			let html = data.map(e => {
				let diffDays = frappe.datetime.get_diff(e.end_date, e.start_date) + 1;
				return incominVacationRow(
						e.employee_name,
						e.status,
						e.request_type_name,
						`(${e.start_date}) - (${e.end_date})`,
						diffDays
					);
				}).join("");
			$("#incomin-vaction").html(html);
		}
	});

}

function incominVacationRow(name,status,desc,start_end,diffDays) {
	return `
		<div class="p-3 d-flex align-items-center justify-content-between bg-gray-100 mb-4">
			<div class="right d-flex align-center">
				<div class="flex rounded-circle icon-bg m-3 p-3 avatar" style="background:#0284C5;width: 46px;height: 46px;text-align: center;">
					<strong class="text-white">${name[0]}</strong>
				</div>
				<div class="d-flex flex-column align-content-center">
					<strong>${name} <span class="color3">(${__(status)})</span> </strong>
					<small class="text-muted">${desc}</small>
				</div>
			</div>
			<span class="left" style="text-align: end !important;">
				<div>${start_end}</div>
				<div class="text-muted">${diffDays} أيام</div>
			</span>
		</div>
	`;
}

function latestLogRow(icon,background,name,desc,time) {
	return `
		<div class="p-3 d-flex align-items-center justify-content-between bg-gray-100 mb-4">
			<div class="right d-flex align-center">
				<div class="flex rounded icon-bg m-3 p-3" style="background:${background};">
					<img alt="icon" src="${icon}"/>
				</div>
				<div class="d-flex flex-column align-content-center">
					<strong>${name}</strong>
					<span>${desc}</span>
				</div>
			</div>
			<span class="">
				<i class="fa fa-clock-o" aria-hidden="true"></i>
				${time}
			</span>
		</div>
	`;
}

function latestLogs() {
	frappe.call({
        method: "frappe.client.get_list",
        args: {
			doctype: "Elitehr Employee Checkin",
			fields:["employee","employee_name", "log_type", "time","date"],
			order_by: "creation desc",
			limit_page_length:10
		},
		callback: function (r) {
			let logs = r.message || []			
			let html = logs.map(l => {
				let action = l.log_type === "Check In" ? "سجل دخوله" : "سجل خروجه";
				let icon_name = l.log_type === "Check In" ? "check_in" : "check_out";
				let background = l.log_type === "Check In" ? "#24A8711A" : "#94A3B8";
				return latestLogRow(
						`/assets/elitehr2/icons/${icon_name}.png`,
						background,
						l.employee_name,
						action,
						l.time
					);
				}).join("");
			$("#latest-log-list").html(html);
		}
	});

}

let attendanceChart = null;
function initChart(stats) {

    let ctx = document.getElementById("attendanceChart");
    if (!ctx) return;

    if (attendanceChart) {
        attendanceChart.destroy();
    }

    attendanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ["حاضر", "متأخر", "غائب", "إجازة"],
            datasets: [{
                data: [
                    stats.present,
                    stats.late,
                    stats.absent,
                    stats.vacation
                ],
                backgroundColor: [
                    "#22c55e",
                    "#f59e0b",
                    "#ef4444",
                    "#0ea5e9"
                ]
            }]
        },
        options: {
            cutout: "70%",
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

	$("#attendanceLegend").html(`
        ${legendItem("حاضر", getPrecent((stats.present+stats.late),stats.totalEmployee), "#22c55e")}
        ${legendItem("متأخر", getPrecent(stats.late,stats.totalEmployee), "#f59e0b")}
        ${legendItem("غائب", getPrecent(stats.absent,stats.totalEmployee), "#ef4444")}
        ${legendItem("إجازة", getPrecent(stats.vacation,stats.totalEmployee), "#0ea5e9")}
    `);
}

function getPrecent(count,totalEmployee) {
	return totalEmployee > 0
				? (( count / totalEmployee) * 100).toFixed(1) + " %"
				: "0 %"
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

function legendItem(label, value, color) {
    return `
        <div class="d-flex align-items-center m-2 p-2 justify-content-between" style="background:#f3f4f6;border-radius:12px;">
            <div>
				<span style="width:10px;height:10px;background:${color};border-radius:50%;display:inline-block;margin-left:8px;"></span>
            	<strong>${label}</strong>
			</div>
            <span class="ml-2">${value}</span>
        </div>
    `;
}

function card(id,title, value, colorClass) {
    return `
        <div id="${id}" class="card">
            <div class="card-title">${title}</div>
            <div class="card-value ${colorClass}">${value}</div>
        </div>
    `;
}

function quickAction(text, background,icon,href = "") {
    return `
        <a href="${href}" class="d-flex flex-column p-4 align-items-center rounded">
			<div class="flex rounded icon-bg" style="background:${background};">
				<img alt="icon" src="${icon}"/>
			</div>
			<h4 class="pt-4">${text}</h4>
		</a>
    `;
}