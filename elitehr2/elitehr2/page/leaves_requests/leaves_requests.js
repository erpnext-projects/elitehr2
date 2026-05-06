let cardRow = $('<div class="cardContainers"></div>')
let tableContainer = $('<div class="requests-table" dir="rtl"></div>')

frappe.pages['leaves-requests'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Leaves Requests',
		single_column: true
	});

	page.add_inner_button(__("تحديث"), function () {
		loadRequests();
	});

	// Outer wrapper with margin
	const wrapperContent = $('<div dir="rtl" class="custom-page"></div>').appendTo(page.main);


	// Containers
	$(`
		<h2>
			<svg class="icon text-ink-gray-7  icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-calendar-plus">
				</use>
			</svg>
			طلبات الاجازات
		</h2>
		`).appendTo(wrapperContent);
	$(`<span>إدارة طلبات الاجازات</span><br>`).appendTo(wrapperContent);

	cardRow.appendTo(wrapperContent);
	tableContainer.appendTo(wrapperContent);

	// Load data
	loadRequests();
}

function loadRequests() {
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_list",
		args: { request_type: "LEAVE" },
		callback: function (r) {
			const requests = r.message || [];
			console.log(requests);

			const total = requests.length;
			const newCount = requests.filter(r => r.status === "New").length;
			const completed = requests.filter(r => r.status === "Completed").length;

			// Cards
			cardRow.html(`
                    <div class="card">
                        <div class="card-title">طلبات جديدة</div>
                        <div class="card-value ">${newCount}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">مكتملة</div>
                        <div class="card-value color5">${completed}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">إجمالي الطلبات</div>
                        <div class="card-value color2">${total}</div>
                    </div>
                `);

			renderTable(requests);
		}
	});
}


function renderTable(requests) {
	if (!requests || requests.length === 0) {
		tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
		return;
	}
	// get all leave types from leave type doctype and map them by name
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Elitehr Leave Policies",
			fields: ["name", "ar_name"]
		},
		callback: function (r) {
			const leaveTypes = r.message || [];
			const leaveTypeMap = {};
			leaveTypes.forEach(lt => {
				leaveTypeMap[lt.name] = lt.ar_name;
			});


			const columns = [
				{ id: "employee_name", name: "الموظف" },
				{ id: "department", name: "القسم" },		
				{ id: "leave_type", name: "نوع الاجازة", format: value => leaveTypeMap[value] || value },
				{ id: "creation", name: "تاريخ الطلب", format: (value) => value ? value.split(' ')[0] : '' },
				{ id: "start_date", name: "تاريخ البدء" },
				{ id: "end_date", name: "تاريخ الانتهاء" },
				{ id: "total_days", name: "عدد الأيام" },
				{
					id: "status", name: "الحالة",
					format: (value) => value == "Completed" ? `<span class='color3'><i class="fa fa-check-circle" aria-hidden="true"></i> مكتمل</span>` : `<span class='color1'><i class="fa fa-clock-o" aria-hidden="true"></i> قيد الانتظار</span>`
				},
				{ id: "name", name: "الإجراءات", format: value => `<a href='/desk/elitehr-requests/${value}'><i class="fa fa-eye" aria-hidden="true"></i> عرض وتعديل</a>` }
		
			];
		
			new CustomTable({
				container: tableContainer,
				columns: columns,
				data: requests
			})
			
		}
	});


}