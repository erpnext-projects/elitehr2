let tableContainer = $('<div class="requests-table" dir="rtl"></div>')
let AllData = [];
let employee_filter = null;

frappe.pages['employee-leaves-balances'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Employee Leaves balances ',
		single_column: true
	});

	page.add_inner_button(__("تحديث"), function () {
		loadRequests();
	});

	// add filter for employee
	page.add_field({
		fieldname: "employee",
		label: "الموظف",
		fieldtype: "Link",
		options: "Elitehr Employee",
		onchange: function() {
			employee_filter = this.get_value();
			loadData();
		}
	});

	// Outer wrapper with margin
	const wrapperContent = $('<div dir="rtl" class="custom-page"></div>').appendTo(page.main);


	// Containers
	$(`
		<h2>
			<svg class="icon text-ink-gray-7  icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-file-user">
				</use>
			</svg>
			${__("Employee Leaves balances")} 
		</h2>
		`).appendTo(wrapperContent);

	tableContainer.appendTo(wrapperContent);

	// Load data
	loadData();
}

function loadData() {
	frappe.call({
		method: "elitehr2.api.get_employees_leave_summary",
		callback: function(r) {
			const data = r.message || [];
			AllData = data;
			console.log("Employee Leaves balances", data);
			renderTable();
		}
	});
}

function renderTable() {
	if (!AllData || AllData.length === 0) {
		tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
		return;
	}

	let data = AllData;
	if (employee_filter) {
		data = data.filter(d => d.employee === employee_filter);
	}
	


	const columns = [
		{ id: "employee", name: "الموظف" },
		{ id: "employee_name", name: " اسم الموظف " },
		{ id: "leave_name", name: " نوع الإجازة " },		
		{ id: "days", name: "الأيام" },
		{ id: "used_days", name: "الأيام المستخدمة" },
		{ id: "percentage", name: "النسبة المئوية",
			format: ( value, row ) => {
				// value => value ? `${value}%` : '0%'
				let percent = value || 0;

				let color = "#28a745";

				if (percent > 70) {
					color = "#dc3545";
				} else if (percent > 40) {
					color = "#ffc107";
				}
				return `
					<div style="width:150px;">
                    <div class="progress" style="flex-grow:1">
                        <div class="progress-bar" style="width:${percent}%"></div>
                    </div>
                    <div style="font-size:11px;margin-top:2px;text-align:center">
                        ${percent}%
                    </div>	
                </div>
				`;
			}
		},

	];

	new CustomTable({
		container: tableContainer,
		columns: columns,
		data: data
	})
		

}