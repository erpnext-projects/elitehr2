frappe.pages['hr-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Hr Dashboard',
		single_column: true
	});
}