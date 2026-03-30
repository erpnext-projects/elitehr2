frappe.pages['resignations'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Resignations',
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
				<use class="" href="#icon-user-minus">
				</use>
			</svg>
			الاستقالات وإنهاء الخدمة
		</h2>
		`).appendTo(wrapperContent);
    $(`<span>إدارة طلبات الاستقالة وإجراءات إنهاء الخدمة</span><br>`).appendTo(wrapperContent);
	
    const cardRow = $('<div class="cardContainers"></div>').appendTo(wrapperContent);
    const tableContainer = $('<div class="requests-table" dir="rtl"></div>').appendTo(wrapperContent);

    // Load data
	loadRequests();

    function loadRequests() {
        frappe.call({
            method: "elitehr2.elitehr2.doctype.elitehr_requests.elitehr_requests.get_requests_list",
            args: { request_type: "RESIGNATION" },
            callback: function(r) {
                const requests = r.message || [];
                console.log(requests);
                
                const total = requests.length;
                const newCount = requests.filter(r => r.status === "New" ).length;
                const underLiquidation = requests.filter(r => r.status === "Under Liquidation").length;
                const completed = requests.filter(r => r.status === "Completed" ).length;
                
                // Cards
                cardRow.html(`
                    <div class="card">
                        <div class="card-title">طلبات جديدة</div>
                        <div class="card-value color2">${newCount}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">قيد التصفية</div>
                        <div class="card-value color1">${underLiquidation}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">مكتملة</div>
                        <div class="card-value color5">${completed}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">إجمالي الطلبات</div>
                        <div class="card-value color4">${total}</div>
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
                // { id: "name", name: "رقم الطلب",editable: false,dropdown:false,format: (value) => `<a href='/desk/elitehr-requests/${value}'>${value}</a>`},
                { id: "employee_name", name: "الموظف"},
                { id: "department", name: "القسم"},
                { id: "empty", name: "الوظيفة"},
                { id: "creation", name: "تاريخ الطلب", format: (value) => value ? value.split(' ')[0] : ''},
                { id: "last_suggested_working_day", name: "اخر يوم"},
                { id: "docstatus", name: "الحالة",
                    format: (value)=> value == 1 ? `<span class='color3'><i class="fa fa-check-circle" aria-hidden="true"></i> معتمد</span>` : `<span class='color1'><i class="fa fa-clock-o" aria-hidden="true"></i> قيد الانتظار</span>` 
                },
                { id: "name", name: "الإجراءات",format: value => `<a href='/desk/elitehr-requests/${value}'><i class="fa fa-eye" aria-hidden="true"></i> عرض وتعديل</a>`}

            ];

        new CustomTable({
			container: tableContainer,
			columns: columns,
			data: requests
		})

    }

    function renderTable_old(requests) {
		if (!requests || requests.length === 0) {
			tableContainer.html('<p>لا توجد طلبات لعرضها</p>');
			return;
		}
        console.log(requests);
        
        const columns = [
                // { id: "name", name: "رقم الطلب",editable: false,dropdown:false,format: (value) => `<a href='/desk/elitehr-requests/${value}'>${value}</a>`},
                { id: "employee_name", name: "الموظف",editable: false,dropdown:false},
                { id: "department", name: "القسم",editable: false,dropdown:false},
                { id: "empty", name: "الوظيفة",editable: false,dropdown:false},
                { id: "creation", name: "تاريخ الطلب",editable: false,dropdown:false, format: (value) => value ? value.split(' ')[0] : ''},
                { id: "last_suggested_working_day", name: "اخر يوم",editable: false,dropdown:false},
                { id: "docstatus", name: "الحالة",editable: false,dropdown:false,
                    format: (value)=> value == 1 ? `<span class='color3'><i class="fa fa-check-circle" aria-hidden="true"></i> معتمد</span>` : `<span class='color1'><i class="fa fa-clock-o" aria-hidden="true"></i> قيد الانتظار</span>` 
                },
                { id: "name", name: "الإجراءات",editable: false,dropdown:false,format: value => `<a href='/desk/elitehr-requests/${value}'><i class="fa fa-eye" aria-hidden="true"></i> عرض وتعديل</a>`}

            ];
        tableContainer.empty();
        new DataTable(tableContainer[0],{
			columns: columns,
			data: requests,
            layout: "fluid",
			serialNoColumn: true,
			dynamicRowHeight: true,
			direction: 'rtl',
			inlineFilters: true,
        });
    }
}