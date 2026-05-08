const wrapperContent = $('<div dir="rtl" class="custom-page"></div>');
let tableContainer = $('<div class="requests-table" dir="rtl"></div>');
let filtersContainer = $(`<div class="myFiltersContainer mt-4"></div>`);
let dateField;
let selectedDate;

let employeeField;
let departmentField;

let dataFromServer = { "data": [], "active_employee": 0 };
const attendanceStatusConfig = {
	Present: {
		label: "حاضر",
		bg: "#d1fae5",
		color: "#10b981",
		icon: "✓"
	},
	Absent: {
		label: "غائب",
		bg: "#fee2e2",
		color: "#ef4444",
		icon: "✕"
	},
	Late: {
		label: "متأخر",
		bg: "#fef3c7",
		color: "#f59e0b",
		icon: "◔"
	},
	Leave: {
		label: "إجازة",
		bg: "#dbeafe",
		color: "#3b82f6",
		icon: "✈"
	},
	"Early Out": {
		label: "انصراف مبكر",
		bg: "#fef3c7",
		color: "#f59e0b",
		icon: "◔"
	},
	Weekend: {
		label: "أجازة اسبوعية",
		bg: "#94a3b8",
		color: "#fff",
		icon: ""
	},
	Holiday: {
		label: "أجازة",
		bg: "#d8b4fe",
		color: "#fff",
		icon: ""
	}
};



frappe.pages['monthly-attendance-report'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Monthly attendance report',
		single_column: true
	});

	wrapperContent.appendTo(page.main);
	// Containers
	$(`<h2>${__("Monthly attendance report")}</h2>`).appendTo(wrapperContent);
	$(`<span>${__("A detailed report of employee attendance and absence during the month")}</span>`).appendTo(wrapperContent);
	filtersContainer.appendTo(wrapperContent);
	$(`
		<h4 class="mt-4">
			<svg class="icon text-ink-gray-7  icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-calendar"></use>
			</svg>
			${__("Attendance Schedule")}
		</h4>
	`).appendTo(wrapperContent);
	renderAttendanceLegend(wrapperContent);
	tableContainer.appendTo(wrapperContent)


	renderFormFields();
	// renderPageButtons(page);
}


function getAttendanceBox(statusCode = "Weekend", title = "") {
	let item = attendanceStatusConfig[statusCode] || attendanceStatusConfig.Weekend;

	return `
		<div>
			<div
				class="d-flex align-items-center justify-content-center rounded m-auto mr-2 ml-2 "
				title="${title || item.label}"
				style="
					width:32px;
					height:32px;
					background:${item.bg};
					color:${item.color};
					font-weight:bold;
					margin:auto;
					cursor:pointer;
				"
			>
				${item.icon}
			</div>
		</div>
	`;
}

function renderAttendanceLegend(container) {

	let html = `
		<div class="bg-light rounded p-3 mb-3">
			<div class="d-flex flex-wrap gap-3 align-items-center">
	`;

	Object.keys(attendanceStatusConfig).forEach(key => {
		let item = attendanceStatusConfig[key];

		html += `
			<div class="d-flex align-items-center gap-2 m-2">
				${getAttendanceBox(key, item.label)}
				<span class="mr-2 ml-2">${item.label}</span>
			</div>
		`;
	});

	html += `
			</div>
		</div>
	`;

	$(html).appendTo(container);
}

function renderTableData(data) {
	tableContainer.empty()

	// filters
	if (employeeField.get_value()) {
		data = data.filter(r => r.employee == employeeField.get_value());
	}

	if (departmentField.get_value()) {
		data = data.filter(r => r.department == departmentField.get_value());
	}

	if (data) {
		let columns = [
			{
				id: "employee_name",
				name: __("Employee"),
				width: "220px",
				format: (value, row) => {
					return `
								<div>
									<strong>${row.employee_name}</strong>
									<br>
									<small>${row.job_title || ""}</small>
								</div>
							`;
				}
			},
			{
				id: "presents",
				name: __("Attendance"),
				format: v => `<strong class="text-white badge2 bg3">${v}</strong>`
			},
			{
				id: "absens",
				name: __("Absence"),
				format: v => `<strong class="text-white badge2 bg4">${v}</strong>`
			},
			{
				id: "lates",
				name: __("Tardiness"),
				format: v => `<strong class="text-white badge2 bg1">${v}</strong>`
			},
			{
				id: "leaves",
				name: __("Vacations"),
				format: v => `<strong class="text-white badge2 bg-secondary">${v}</strong>`
			}
		];

		// const startDay = frappe.datetime.str_to_obj(selectedDate).getDate();
		// const lastDayOfMonth = frappe.datetime.month_end(selectedDate)
		// const lastDay = frappe.datetime.str_to_obj(lastDayOfMonth).getDate();
		// console.log(data);
		
		// أعمدة الأيام
		const firstRow = data[0] || []
		for (const day in firstRow.days) {
			columns.push({
				id: `day_${day}`,
				name: `<div>
					${day} \n
					${__(firstRow.days[day].day_name)}
				</div>`,
				format: (value, row) => {
					let dayData = row.days?.[day];
					if (dayData.status_code == "Weekend") {
						return getAttendanceBox("Weekend", "");
					} else if (dayData.status_code == "Absent") {
						return getAttendanceBox('Absent')
					} else if (dayData.status_code == "Late") {
						return getAttendanceBox('Late')
					} else if (dayData.status_code == "Present") {
						return getAttendanceBox('Present')
					} else if (dayData.status_code == "Early Out") {
						return getAttendanceBox('Early Out')
					}else if (dayData.status_code == "Leave") {
						return getAttendanceBox('Leave')
					}
					else{
						console.error("monthly_attendance_report/status_code is not found",dayData);
						return "";
					}

				}
			});
		}
		// for (let day = startDay; day <= lastDay; day++) {
		// 	columns.push({
		// 		id: `day_${day}`,
		// 		name: day,
		// 		format: (value, row) => {
		// 			let dayData = row.days?.[day];
		// 			if (!dayData) {
		// 				return getAttendanceBox("Weekend", "");
		// 			} else if (dayData.status_code == "Absent") {
		// 				return getAttendanceBox('Absent')
		// 			} else if (dayData.status_code == "Late") {
		// 				return getAttendanceBox('Late')
		// 			} else if (dayData.status_code == "Present") {
		// 				return getAttendanceBox('Present')
		// 			} else if (dayData.status_code == "Early Out") {
		// 				return getAttendanceBox('Early Out')
		// 			}

		// 		}
		// 	});
		// }

		new CustomTable({
			container: tableContainer,
			columns: columns,
			data: Object.values(data)
		});
	}


}

function renderFormFields() {
	dateField = frappe.ui.form.make_control({
		parent: filtersContainer,
		df: {
			label: __('حدد الشهر :'),
			fieldname: 'date',
			fieldtype: 'Date',
			change: onFieldsUpdate
		},
		render_input: true
	});
	dateField.set_value(frappe.datetime.month_start());

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
	if (selectedDate == dateField.get_value() && dataFromServer.data.length > 0) {
		renderTableData(dataFromServer);

	} else if (dateField.get_value()) {
		fetchRequestsData(dateField.get_value(), function (dataFromServer) {
			selectedDate = dateField.get_value();
			dataFromServer = dataFromServer;
			renderTableData(dataFromServer);
		});
	}

}

function fetchRequestsData(date, onComplete) {
	frappe.dom.freeze("جاري تحميل التقرير...");
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_monthly_attendance_matrix",
		args: { from_date: date, to_date: frappe.datetime.month_end(date) },
		callback: function (r) {
			let dataFromServer = r.message || [];
			onComplete(dataFromServer);
			frappe.dom.unfreeze();
		}
	});
}

function renderPageButtons(page) {

	page.add_inner_button(__("Update"), function () {
		requestsData = {};
		onFieldsUpdate();
	});
}