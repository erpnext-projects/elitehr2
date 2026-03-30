let tree_container = $('<div id="org-tree" style="padding:20px"></div>');

frappe.pages['org-structure'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Organization Structure',
		single_column: true
	});

	tree_container.appendTo(page.main);
	get_org_structure(page);

	page.add_inner_button(__("تحديث"), function () {
		get_org_structure(page);
	});
}


function get_org_structure(page) {
	frappe.require([
		"https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/jstree.min.js",
		"https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/style.min.css"
	], () => {
		// Create a container for the jsTree
		if (tree_container.jstree(true)) {
			tree_container.jstree("destroy");
		}
		tree_container.empty();
		function buildEmployeeTree(employees, site_id) {
			return employees.map(emp => {
				let isManager = emp.children && emp.children.length;
				console.log(isManager);

				return {
					id: site_id + "_" + emp.id,
					text: `
					<span class="tree-body">${emp.employee_name}</span>
					<span class="tree-badge color5">(${isManager ? "مدير" : "موظف"})</span>
				`,
					icon: "fa fa-user",
					children: emp.children && emp.children.length
						? buildEmployeeTree(emp.children, site_id)
						: []
				};
			});
		}

		// Fetch organization structure data from the server
		frappe.call({
			method: 'elitehr2.elitehr2.page.org_structure.org_structure.get_company_tree_data',
			callback: function (r) {
				let data = r.message;
				if (data) {
					let treeData = [
						{
							id: data.parent_id,
							text: `
							<span class="tree-head">${data.parent}</span>
							<span class="tree-badge color1">(الشركة)</span>
						`,
							state: { opened: true },
							icon: "fa fa-building",
							children: data.branches.map(branch => {
								return {
									id: branch.id,
									text: `
									<span class="tree-body">${branch.name}</span>
									<span class="tree-badge color2">(الفرع)</span>
									`,
									icon: "fa fa-building-o",
									children: branch.fingerSites.map(f => {
										return {
											id: f.name,
											text: `
											<span class="tree-body">${f.site_name}</span>
											<span class="tree-badge color3">(موقع البصمة)</span>
											`,
											icon: "fa fa-map-marker",
											state: { opened: true },
											children: buildEmployeeTree(f.employees, f.site_id)
										}
									}),
									state: { opened: true },
								};
							})
						}
					];

					tree_container.jstree({
						core: {
							data: treeData
						},
						plugins: ["wholerow"]
					});
				}
			}
		});
	});
}