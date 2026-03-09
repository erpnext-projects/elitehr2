// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Fingerprint Sites", {
	refresh(frm) {
        render_radius_slider(frm);
	},
});


function render_radius_slider(frm) {

    let value = frm.doc.allowed_range || 10;

    let html = `
        <div class="radius-container" style="margin-bottom:10px">

            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                <label style="font-weight:600">
                    ${__("Allowed Attendance Radius")}
                </label>

                <span class="radius-value badge badge-dark">
                    ${value} ${__("meter")}
                </span>
            </div>

            <input 
                type="range"
                class="radius-slider"
                min="10"
                max="500"
                step="10"
                value="${value}"
                style="width:100%"
            >

            <div class="SliderInfo" style="font-size:12px;color:#6c757d;margin-top:6px">
                ${__("Employees can check-in if they are within {0} meters from this location", [value])}
            </div>

        </div>
    `;

    frm.fields_dict.allowed_range_slider.$wrapper.html(html);

    frm.fields_dict.allowed_range_slider.$wrapper
        .find(".radius-slider")
        .on("input", function () {

            let val = $(this).val();

            frm.set_value("allowed_range", val);

            frm.fields_dict.allowed_range_slider.$wrapper
                .find(".radius-value")
                .text(val + " " + __("meter"));

            frm.fields_dict.allowed_range_slider.$wrapper
                .find(".SliderInfo")
                .text(
                    __("Employees can check-in if they are within {0} meters from this location", [val])
                );
        });
}