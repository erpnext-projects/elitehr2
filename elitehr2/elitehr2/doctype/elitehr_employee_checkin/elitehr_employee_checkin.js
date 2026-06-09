// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Employee Checkin", {
    refresh: function(frm) {
      openGetLocation(frm)
    },
    log_type: function(frm) {
      openGetLocation(frm)
    }
});

function openGetLocation(frm) {
    if (frm.is_new()) {
        frm.disable_save(); 
        
        frm.add_custom_button(__('تسجيل البصمة بالموقع الحالي'), function() {
            frappe.getUserLocation(
                function(lat,long,device_name,device_id) {
                    frm.set_value('latitude', lat);
                    frm.set_value('longitude', long);
                    frm.set_value('device_name', device_name);
                    frm.set_value('device_id', device_id);
                    frappe.show_alert({message: __('تم جلب الموقع، جاري التحقق والحفظ...'), indicator: 'green'});
                    frm.save();
                }
            );
        }).addClass('btn-primary');
    }
}
