frappe.provide("frappe.setup");

frappe.pages["setup-wizard"].on_page_load = function(wrapper) {
    
    if (frappe.boot.setup_complete) {
        frappe.set_route("desk"); 
        return;
    }

    let wizard_settings = {
        parent: wrapper,
        slides: [
            {
                name: "test_slide",
                title: __("تجربة الإعداد الخاص"),
                fields: [
                    {
                        fieldname: "custom_name",
                        label: __("اسم المشروع بتاعك"),
                        fieldtype: "Data",
                        reqd: 1
                    },
                    {
                        fieldname: "customs_name",
                        label: __("اسم المشروع sبتاعك"),
                        fieldtype: "Data",
                        reqd: 1
                    }

                ]
            },
        ],
        slide_class: frappe.ui.Slide,
        unidirectional: 1,
        done_state: 1
    };

    frappe.wizard = new frappe.ui.Slides(wizard_settings);

    frappe.wizard.$complete_btn.on("click", function() {
        let values = frappe.wizard.get_values();
        if(!values) return;
        frappe.call({
            method: "elitehr.api.complete_setup",
            args: { args: values },
            callback: function(r) {
                console.log(r)
                if(r.message === "ok") {
                    window.location.href = "/app";
                }
            }
        });
    });
};