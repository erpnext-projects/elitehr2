// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Elitehr Fingerprint Sites", {
	refresh(frm) {
        render_radius_slider(frm);
        drawMap(frm);
	},
    find_my_current_location:function(frm) {
        getCurrentLocation(frm);
    }
});





function getCurrentLocation(frm) {
    if (!navigator.geolocation) {
            frappe.msgprint("المتصفح لا يدعم تحديد الموقع");
            return;
        }
        navigator.geolocation.getCurrentPosition(function(position) {

            let lat = position.coords.latitude;
            let lng = position.coords.longitude;

            frm.set_value("latitude", lat);
            frm.set_value("longitude", lng);

            if (frm.map) {
                frm.map.setView([lat, lng], 16);

                if (frm.marker) {
                    frm.marker.setLatLng([lat, lng]);
                } else {
                    frm.marker = L.marker([lat, lng]).addTo(frm.map);
                }
            }

        }, function(error){
            frappe.msgprint("لم يتم الحصول على الموقع" + " " + error.message);
            
        });
}

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

function drawMap(frm) {

    if (frm.map) {
        return;
    }
    frm.fields_dict.map_html.$wrapper.html(`<div id="map" style="height:400px"></div>`);

    frm.map = L.map('map').setView([30.0444, 31.2357], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'OpenStreetMap'
    }).addTo(frm.map);

    frm.map.on('click', function(e) {

        let lat = e.latlng.lat;
        let lng = e.latlng.lng;

        frm.set_value("latitude", lat);
        frm.set_value("longitude", lng);

        set_marker(frm, lat, lng);

    });

    // 👇 رسم الماركر بعد الحفظ
    if (frm.doc.latitude && frm.doc.longitude) {

        set_marker(frm, frm.doc.latitude, frm.doc.longitude);

        frm.map.setView([frm.doc.latitude, frm.doc.longitude], 16);
    }
}


function set_marker(frm, lat, lng) {

    if (frm.marker) {
        frm.marker.setLatLng([lat, lng]);
    } else {
        frm.marker = L.marker([lat, lng]).addTo(frm.map);
    }

}