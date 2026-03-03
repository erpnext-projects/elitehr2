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
        hierarchy["branches"].append({
            "name": b.branch_name or b.name,
            "id": b.name,
            "fingerSites": fingerSites
        })
        # frappe.log("fingerSites")
        # frappe.log(fingerSites)
    frappe.log(hierarchy)
    return hierarchy