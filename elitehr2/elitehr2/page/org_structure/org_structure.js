frappe.pages['org-structure'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Organization Structure',
		single_column: true
	});
	frappe.require([
    "https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/jstree.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/style.min.css"
], () => {
	// Create a container for the jsTree
	const tree_container = $('<div id="org-tree" style="padding:20px"></div>')
            .appendTo(page.main);

	// Fetch organization structure data from the server
	frappe.call({
		method: 'elitehr2.elitehr2.page.org_structure.org_structure.get_company_tree_data',
		callback: function(r) {
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
								children: branch.fingerSites.map(f=>{ 									
									return{
										id: f.name,
										text: `
											<span class="tree-body">${f.site_name}</span>
											<span class="tree-badge color3">(موقع البصمة)</span>
											`,
										icon: "fa fa-map-marker",
										state: { opened: true },
										children: f.employees.map(emp=>{
											return {
												id: emp.id,
												text: `
													<span class="tree-body">${emp.employee_name}</span>
													<span class="tree-badge color5">(موظف)</span>
												`,
												icon: "fa fa-user",
												
											}
										})
									} 
								}),
								state: { opened: true },
                            };
                        })
                    }
                ];

                $('#org-tree').jstree({
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