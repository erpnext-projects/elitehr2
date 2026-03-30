frappe.pages['missions'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Missions',
		single_column: true
	});

	page.add_inner_button(__("تحديث"), function() {
		loadRequests();
	});

	// Outer wrapper with margin
    const wrapperContent = $('<div dir="rtl" class="custom-page"></div>').appendTo(page.main);

    // Containers
    $(`
		<h2>
			<svg class="icon text-ink-gray-7 current-color icon-sm" stroke="currentColor" style="" aria-hidden="true">
				<use class="" href="#icon-map-pin">
				</use>
			</svg>
			${__("Missions")}
		</h2>
		`).appendTo(wrapperContent);
    $(`<span>${__("Management of work assignments and secondments")}</span><br>`).appendTo(wrapperContent);
	
    const cardRow = $('<div class="cardContainers"></div>').appendTo(wrapperContent);
    const tableContainer = $('<div class="requests-table" dir="rtl"></div>').appendTo(wrapperContent);

    // Load data
	loadRequests();


	function loadRequests() {
        frappe.call({
            method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_list",
            args: { request_type: "MISSIONS" },
            callback: function(r) {
                const requests = r.message || [];
                console.log(requests);
                
                const total = requests.length;
                const newCount = requests.filter(r => r.status === "New" ).length;
                const completed = requests.filter(r => r.status === "Completed" ).length;
                
                // Cards
                cardRow.html(`
					<div class="card">
						<div class="card-title">إجمالي الطلبات</div>
						<div class="card-value color4">${total}</div>
					</div>
                    <div class="card">
                        <div class="card-title">طلبات جديدة</div>
                        <div class="card-value color2">${newCount}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">مكتملة</div>
                        <div class="card-value color5">${completed}</div>
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

		const columns = [
			{ id: "employee_name", name: "الموظف" },
			{ id: "department", name: "القسم" },
			{ id: "creation", name: "تاريخ الطلب",
				format: (value) => value ? value.split(' ')[0] : ''
			},
			{ id: "docstatus", name: "الحالة",
				format: (value) => value == 1
					? `<span class="color3"><i class="fa fa-check-circle" aria-hidden="true"></i> معتمد</span>`
					: `<span class="color1"><i class="fa fa-clock-o" aria-hidden="true"></i> قيد الانتظار</span>`
			},
			{ id: "name", name: "الإجراءات",
				format: (value) => `<a href='/desk/elitehr-requests/${value}'><i class="fa fa-eye" aria-hidden="true"></i> عرض وتعديل</a>`
			}
		];

		new CustomTable({
			container: tableContainer,
			columns: columns,
			data: requests
		});
	}
	

}