import frappe

@frappe.whitelist()
def get_company_tree_data():
    company_name = frappe.db.get_single_value("Elitehr Company", "company_name")
    branches = frappe.get_all("Elitehr Branches", fields=["name","branch_name"],order_by='order asc',)
    hierarchy = {
        "parent": company_name,
        "parent_id": company_name,
        "branches": []
    }

    for b in branches:
        fingerSites = frappe.db.get_all("Elitehr Fingerprint Sites",fields=["name","site_name","branch"],filters={"branch":b.name})

        fingerSitesList = []
        for site in fingerSites:
            employee_links = frappe.db.get_all(
                "Elitehr Employee Fingerprint Sites",
                fields=["parent", "site_name"], 
                filters={"site_name": site.name}
            )
            # employees = []
            # for e in employee_links:
            #     emp_doc = frappe.get_doc("Elitehr Employee", e.parent)
            #     employees.append({
            #         "id": emp_doc.name,
            #         "employee_name": emp_doc.employee_name
            #     })

            emp_map = {}
            for e in employee_links:
                emp_doc = frappe.get_doc("Elitehr Employee", e.parent)

                emp_map[emp_doc.name] = {
                    "id": emp_doc.name,
                    "employee_name": emp_doc.employee_name,
                    "manager": emp_doc.manager,
                    "children": []
                }

            # بناء الشجرة
            employees_tree = []
            for emp_id, emp in emp_map.items():
                manager_id = emp["manager"]

                if manager_id and manager_id in emp_map:
                    emp_map[manager_id]["children"].append(emp)
                else:
                    employees_tree.append(emp)
            frappe.log("employees_tree")
            frappe.log(employees_tree)

            fingerSitesList.append({
                "site_name": site.site_name,
                "site_id": site.name,
                "employees": employees_tree
            })

            
        # fingerprint_sites
        hierarchy["branches"].append({
            "name": b.branch_name or b.name,
            "id": b.name,
            "fingerSites": fingerSitesList,
        })
        # frappe.log("fingerSites")
        # frappe.log(fingerSites)
        # frappe.log("employees")
        # frappe.log(employees)
    frappe.log(hierarchy)
    return hierarchy