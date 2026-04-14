
let attendanceTimeInterval = null;
let selectedDate = frappe.datetime.get_today();
const wrapperContent = $('<div dir="rtl" class="custom-page"></div>');
let cardRow = $('<div class="cardContainers"></div>');
let tableContainer = $('<div class="requests-table" dir="rtl"></div>');
let filterDate = $(`<div class="myFiltersContainer"></div>`);

frappe.pages['attendance-log'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Attendance Log',
		single_column: true
	});
	
	wrapperContent.appendTo(page.main);

	// Containers
	$(`
		<h2>
			<svg class="icon text-ink-gray-7 current-color icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-alarm-clock-plus">
				</use>
			</svg>
			${__("Attendance Log")}
		</h2>
		`).appendTo(wrapperContent);
	$(`<span>${__("Monitoring employee attendance and departure records")}</span><br>`).appendTo(wrapperContent);

	cardRow.appendTo(wrapperContent);
	filterDate.appendTo(wrapperContent);
	tableContainer.appendTo(wrapperContent);


	filterDate.html(`
			<label>التاريخ:</label>
			<input type="date" id="attendance-date" class="form-control" style="max-width: 250px;">
	`)
	$('#attendance-date').val(selectedDate);
	$('#attendance-date').on('change', function () {
		selectedDate = $(this).val();
		loadStatistics(selectedDate);
	});

	// Load data
	loadStatistics(selectedDate);


	page.add_inner_button(__("تسجيل حضور يدوي"), function () {
		manualAttendanceRegistration()
	});
	page.add_inner_button(__("جهاز تسجيل الحضور"), function () {
		showAttendanceModal(cardRow,tableContainer);
	});
	page.add_inner_button(__("Update"), function () {
		loadStatistics(selectedDate);
	});



}

function manualAttendanceRegistration() {
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.loggedin_manual_attendance",
		callback: function (r) {
			if (r.message) {
				frappe.show_alert({
					message: __('تم تسجيل الحضور بنجاح'),
					indicator: 'green'
				});
				// تحديث البيانات
				loadStatistics(frappe.datetime.get_today());
			}
		}
	});
}


function loadStatistics(selectedDate) {
	// const cardRow = $(".cardContainers")
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.get_all_employees_attendance",
		args: { date: selectedDate },
		callback: function (r) {
			const requests = r.message || [];

			const presentCount = requests.filter(r => r.check_in && r.check_in !== "").length;
			const absentCount = requests.filter(r => !r.check_in || r.check_in === "").length;
			const lateCount = requests.filter(r => r.check_in && r.late_minutes > 0).length;

			// Cards
			cardRow.html(`
					<div class="card">
						<div class="card-title">الحاضرون</div>
						<div class="card-value color5">${presentCount}</div>
					</div>
                    <div class="card">
                        <div class="card-title">المتأخرون</div>
                        <div class="card-value color1">${lateCount}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">الغائبون</div>
                        <div class="card-value color4">${absentCount}</div>
                    </div>
					<div class="card">
                        <div class="card-title">في أجازة</div>
                        <div class="card-value">0</div>
                    </div>
                `);

			renderTable(requests,selectedDate);
		}
	});
}


function renderTable(requests,selectedDate) {
	// tableContainer = $(".requests-table");
	tableContainer.empty();
	tableContainer.html('<p>جاري التحميل...</p>');
	if (!requests || requests.length === 0) {
		tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
		return;
	}

	const columns = [
		{ id: "employee_name", name: "الموظف" },
		{ id: "department", name: "القسم" },
		{
			id: "check_in", name: "الحضور",
			format: (value) => `<span class='color3'><i class="fa fa-clock-o" aria-hidden="true"></i></span> ${value} `
		},
		{
			id: "check_out", name: "الانصراف",
			format: (value) => `\<i class="fa fa-clock-o" aria-hidden="true"></i> ${value} `
		},
		{
			id: "status", name: "الحالة",
			format: (value, row) => {
				return `<span class='${row.status_color}'>${value}</span>`
			}
		},
		{ id: "working_hours", name: "الساعات" },
		{
			id: "actions",
			name: "الإجراءات",
			format: (value, row) => {
				if (selectedDate != frappe.datetime.get_today()) {
					return "";
				}
				if (row.check_out == "" && row.check_in != "") {
					return `
							<button class="btn btn-xs btn-danger btn-check-in-out" 
									data-employee="${row.employee}" 
									data-logType="Check Out" 
									style="padding: 2px 8px;">
								${__("Check Out")}
							</button>
						`;
				}
				if (row.check_in == "") {
					return `
							<button class="btn btn-xs btn-primary btn-check-in-out" 
									data-employee="${row.employee}" 
									data-logType="Check In" 
									style="padding: 2px 8px;">
								${__("Check In")}
							</button>
						`;
				}
			}
		}

	];

	// ربط حدث الضغط على زرار الانصراف
	tableContainer.on('click', '.btn-check-in-out', function (e) {
		e.preventDefault();
		e.stopImmediatePropagation();
		const employee_id = $(this).data('employee');
		const logType = $(this).data('logtype');
		const btn = $(this);

		frappe.confirm(__(`هل أنت متأكد من تسجيل ${__(logType)} لهذا الموظف؟`), () => {
			// تعطيل الزرار لمنع الضغط المتكرر
			btn.prop('disabled', true).text(__('جاري التسجيل...'));
			frappe.call({
				method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.set_attendance",
				args: {
					logType: logType,
					employee: employee_id,
					date: selectedDate // التاريخ اللي أنت واقف عليه في الفلتر
				},
				callback: function (r) {
					if (!r.exc) {
						frappe.show_alert({ message: __(`تم تسجيل ${__(logType)} بنجاح`), subtitle: 'success' });
						// إعادة تحميل البيانات لتحديث الجدول والكروت
						loadStatistics(selectedDate);
					} else {
						btn.prop('disabled', false).text(__('Check Out'));
					}
				}
			});
		});
	});

	new CustomTable({
		container: tableContainer,
		columns: columns,
		data: requests
	});
}



function showAttendanceModal(cardRow,tableContainer) {
	let now = new Date();
	let date = now.toLocaleDateString("ar-EG");

	let d = new frappe.ui.Dialog({
		title: __('جهاز تسجيل الحضور والإنصراف'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'realtime_display',
				options: `
						<div class="text-center" style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-bottom: 15px;">
							<h1 id="modal-live-time" style="font-weight: bold; color: #171717; font-size: 3rem; margin: 0;">00:00:00</h1>
							<h3 id="modal-live-date" style="margin-bottom: 5px;">---</h3>
						</div>
						<div class="text-center" style="margin-bottom: 20px;">
							<button class="btn btn-primary btn-lg btn-block" id="start-scan-btn">
								<i class="fa fa-qrcode"></i> ${__("ابدأ المسح (Scan)")}
							</button>
						</div>
					`
			},
			{
				label: __('بحث برقم الموظف (ID)'),
				fieldtype: 'Data',
				fieldname: 'employee_id',
				description: __('اضغط Enter بعد إدخال الكود')
			}
		],
		primary_action_label: __('تسجيل'),
		primary_action(values) {
			submitAttendance(values.employee_id, d);
		}
	});

	d.show();

	d.on_page_show = function () {
		d.$wrapper.find('#modal-live-date').text(date);
		startTimeOnlyTimer(d);
	};


	d.$wrapper.on('click', '#start-scan-btn', function () {
		d.fields_dict.employee_id.$input.focus();
	});


}


function submitAttendance(emp_id, d) {
	if (!emp_id) return;
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin.set_attendance_by_employee_id",
		args: {
			employee_id: emp_id
		},
		callback: function (r) {
			if (r.message) {
				frappe.show_alert({ message: __('تم التسجيل بنجاح'), subtitle: 'success' });
				loadStatistics(frappe.datetime.get_today());
				d.hide();
			}
		}
	});
}




function startTimeOnlyTimer(dialog) {

	clearInterval(attendanceTimeInterval);

	function updateTime() {
		let now = new Date();

		let time = now.toLocaleTimeString('ar-EG');

		let timeEl = dialog?.$wrapper?.find('#modal-live-time');
		if (timeEl?.length) timeEl.text(time);
	}

	// عرض فوري
	updateTime();

	attendanceTimeInterval = setInterval(updateTime, 1000);
}