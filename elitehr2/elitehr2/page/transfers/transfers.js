const wrapperContent = $('<div dir="rtl" class="custom-page"></div>');
let cardRow = $('<div class="cardContainers"></div>');
let tableContainer = $('<div class="requests-table" dir="rtl"></div>');
let departmentsMap = {};
let branchesMap = {};

frappe.pages['transfers'].on_page_load = async function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Transfers',
		single_column: true
	});

	await preloadLookups();
	wrapperContent.appendTo(page.main);

	// Containers
	$(`
		<h2>
			<svg class="icon text-ink-gray-7 current-color icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-repeat">
				</use>
			</svg>
			${__("Transfers")}
		</h2>
		`).appendTo(wrapperContent);
	$(`<span>${__("Managing employee transfer requests between departments and branches")}</span><br>`).appendTo(wrapperContent);

	cardRow.appendTo(wrapperContent);
	tableContainer.appendTo(wrapperContent);



	page.add_inner_button(__("تحديث"), function () {
		loadStatistics();
	});
	loadStatistics();
}



function loadStatistics() {
	// const cardRow = $(".cardContainers")
	frappe.call({
		method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_list",
		args: { request_type: "TRANSFER" },
		callback: function (r) {
			const requests = r.message || [];

			const total = requests.length;
			const newCount = requests.filter(r => r.status === "New").length;
			const completed = requests.filter(r => r.status === "Completed").length;

			// Cards
			cardRow.html(`
                    <div class="card">
						<div class="card-title">قيد الانتظار </div>
						<div class="card-value color2">${newCount}</div>
                    </div>
                    <div class="card">
						<div class="card-title">مكتمل</div>
						<div class="card-value color5">${completed}</div>
                    </div>
					<div class="card">
						<div class="card-title">إجمالي التحويلات</div>
						<div class="card-value color4">${total}</div>
					</div>
                `);

			renderTable(requests);
		}
	});
}

function renderTable(requests) {
	console.log(requests);
	
	tableContainer.empty();
	tableContainer.html('<p>جاري التحميل...</p>');
	if (!requests || requests.length === 0) {
		tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
		return;
	}

	const columns = [
		{ id: "employee_name", name: "الموظف" },
		{
			id: "creation", name: "تاريخ الطلب",
			format: (value) => value ? value.split(' ')[0] : ''
		},
		{ id: "department", name: " من القسم" },
		{ 
			id: "to_department",
			name: "الي القسم",
			format: (value) => departmentsMap[value] || value
		},
		{id:"from_branch", name:"من الفرع"},
		{id:"to_branch", name:"الي الفرع",format: (value) => branchesMap[value] || value},
		{
			id: "docstatus", name: "الحالة",
			format: (value) => value == 1
				? `<span class="color3"><i class="fa fa-check-circle" aria-hidden="true"></i> معتمد</span>`
				: `<span class="color1"><i class="fa fa-clock-o" aria-hidden="true"></i> قيد الانتظار</span>`
		},
		{
			id: "name", name: "الإجراءات",
			format: (value) => `<a href='/desk/elitehr-requests/${value}'><i class="fa fa-eye" aria-hidden="true"></i> عرض وتعديل</a>`
		}
	];

	new CustomTable({
		container: tableContainer,
		columns: columns,
		data: requests
	});
}



async function preloadLookups() {
	let deps = await frappe.db.get_list('Elitehr Fingerprint Sites', {
		fields: ['name', 'site_name'],
		limit: 1000
	});

	deps.forEach(d => {
		departmentsMap[d.name] = d.site_name;
	});

	let branches = await frappe.db.get_list('Elitehr Branches', {
		fields: ['name', 'branch_name'],
		limit: 1000
	});

	branches.forEach(b => {
		branchesMap[b.name] = b.branch_name;
	});
}