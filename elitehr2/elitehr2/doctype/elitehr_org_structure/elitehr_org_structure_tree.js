// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.treeview_settings["Elitehr Org Structure"] = {
    // order_by: "order asc",
    breadcrumb: "Elitehr Org Structure",
    get_tree_nodes: "elitehr2.elitehr2.doctype.elitehr_org_structure.elitehr_org_structure.get_children",
    onrender: function (node) {
        let $label = $(`span[data-label="${node.data.value}"] .tree-label`);
        frappe.db.get_value("Elitehr Org Structure", node.data.value, ["ar_name", "type"])
        .then(r => {
            if (r.message) {
                let ar_name = r.message.ar_name;
                let type = r.message.type;
                let color;
                
                console.log(type);
                switch (type) {
                    case "الشركة":
                        color = "#e67e22"; 
                        break;
                    case "الفرع":
                        color = "#2277e6";
                        break;
                    case "المنطقة":
                        color = "#2ecc71";
                        break;
                    case "القسم":
                        color = "#8f5625"; 
                        break;
                    default:
                        color = "#7f8c8d"; 
                }
                $label.html(`
                    <span>${ar_name}</span>
                    <span style="color: ${color}; font-size: 0.85em; margin-right: 5px;">${type}</span>
                `);
            }
        });
    }
};