frappe.listview_settings['Elitehr Workers Check_in_out'] = {
    refresh: function (listview) {

        listview.page.add_inner_button(__("Attendance recording device"), function () {
            frappe.showAttendanceModal(
                (values, d) => {
                    submitAttendance(values.employee_id, d)
                }
            );
        });

    }
};



function submitAttendance(worker_id, d) {
    if (!worker_id) return;

    frappe.call({
        method: "elitehr2.elitehr2.doctype.elitehr_workers_check_in_out.elitehr_workers_check_in_out.set_attendance_by_worker_id",
        args: { worker_id: worker_id },
        callback: function (r) {
            if (r.message) {
                frappe.show_alert({ message: __('تم التسجيل بنجاح'), subtitle: 'success' });
                d.hide();
            }
        }
    });

}