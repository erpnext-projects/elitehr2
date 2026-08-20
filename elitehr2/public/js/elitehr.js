localStorage.container_fullwidth = true;
$(document).ajaxSuccess(function () {
    // let container = document.querySelector('div[item-name="لوحة التحكم"]')
    // if (container) {
    //     if (container.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']") && window.location.pathname == "/app/%D9%84%D9%88%D8%AD%D8%A9-%D8%A7%D9%84%D8%AA%D8%AD%D9%83%D9%85") {
    //         container.querySelector(".drop-icon:not(.hidden)").click()
    //     }
    // }


    let route = frappe.get_route();
    if (route != null && route.length > 0 && route[0] === "dashboard-view") {
        let breadcrumbs = document.querySelectorAll(".navbar-breadcrumbs li");
        if (breadcrumbs.length > 2) {
            breadcrumbs.forEach((breadcrumb, index) => {
                if (index !== 0 && index !== breadcrumbs.length - 1) {
                    breadcrumb.remove();
                }
            });
        }
    }


    // Logout
    if (!document.querySelector(".logout-btn")) {
        const logoutItem = `
            <div class="nav-item logout-btn">
                <button class="nav-link bg-danger border-0" onclick="frappe.app.logout()">
                    <span class="sidebar-item-icon">
                        <svg class="icon icon-sm">
                            <use href="#icon-log-out"></use>
                        </svg>
                    </span>
    
                    <span class="sidebar-item-label logout-label d-none">
                        تسجيل الخروج
                    </span>
                </button>
            </div>
        `;

        document.querySelector(".body-sidebar-bottom .nav-item").insertAdjacentHTML("afterend", logoutItem);
    }

    document.querySelectorAll(".sidebar-item-container.section-item").forEach(
        e => {
            let hasActiveLink = [...e.querySelectorAll("a.item-anchor[href]")]
                .some(a => new URL(a.href).pathname === window.location.pathname);

            if (!hasActiveLink) {
                let btn = e.querySelector(
                    "button.drop-icon:has(use[href='#icon-chevron-down'])"
                );

                if (btn) {
                    btn.click();
                }
            }
        }
    )

    // frappe.router.on("change", () => {
    //     const preferredSidebar = localStorage.getItem("preferred_sidebar");

    //     if (preferredSidebar){
    //         const url = new URL(window.location.href);
    //         if (url.searchParams.has("sidebar")) {
    //             console.log("has sidebr");
    //             return
    //         };    
    //         url.searchParams.set("sidebar", "Hr Pro");
    //         window.location.href = url.toString();
    //     }else{
    //         console.log("not preferred_sidebar");

    //     }

    // });


});



// setInterval(update_notifications, 30000);
// update_notifications();
// function update_notifications() {
//     frappe.call({
//         method: "frappe.client.get_count",
//         args: {
//             doctype: "Notification Log",
//             filters: { read: 0, for_user: frappe.session.user }
//         },
//         callback: function (r) {
//             if (r.message > 0) {
//                 console.log("You have " + r.message + " unread notifications.");
//             }
//         }
//     });
// }

frappe.router.on('change', () => {

    // let route = frappe.get_route();
    // console.log(route);
    // if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "User") {
    // let urlParams = new URLSearchParams(window.location.search);
    // console.log(urlParams);
    // if (urlParams.get('sidebar') !== 'Hr Pro') {
    //     urlParams.set('sidebar', 'Hr Pro');
    //     let newUrl = window.location.pathname + '?' + urlParams.toString() + window.location.hash;
    //     window.location.replace(newUrl);
    // }
    // }




});

// frappe.ui.form.on('Dashboard', {
//     refresh: function(frm) {
//         // التأكد إننا في داشبورد "الرئيسية" فقط
//         if (frm.doc.name === 'الرئيسية') {
//             frappe.breadcrumbs.add("Elitehr2");
//         }
//         alert("done")
//     }
// });


$(document).ready(function () {
    //     alert("done")
    //     d = document.querySelector('div[item-name="لوحة التحكم"]')
    //     if(d.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']")){
    //         d.querySelector(".drop-icon:not(.hidden)").click()
    //     }
    // Report Style (like: Employee Leaves balances)
    let start = 0;
    document.querySelectorAll(".datatable .dt-scrollable .dt-row").forEach(e => {
        e.style.top = start + "px";
        start += 52;
    })


    // frappe.realtime.off("notification");

    // frappe.realtime.on("notification", function(data) {
    //     console.log("NOTIFICATION RECEIVED", data);

    //     frappe.call({
    //         method: "frappe.client.get_count",
    //         args: {
    //             doctype: "Notification Log",
    //             filters: {
    //                 read: 0,
    //                 for_user: frappe.session.user
    //             }
    //         },
    //         callback: function(r) {
    //             console.log("Unread Count:", r.message);
    //         }
    //     });
    // });


})


// frappe.after_ajax(() => {
// d = document.querySelector('div[item-name="لوحة التحكم"]')
// if(d.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']")){
//     d.querySelector(".drop-icon:not(.hidden)").click()
// }
// });


// frappe.ready(() => {
//     setTimeout(() => {
//         d = document.querySelector('div[item-name="لوحة التحكم"]')
//         if(d.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']")){}
//         const groups = document.querySelectorAll(
//             ".workspace-sidebar .standard-sidebar-item .octicon-chevron-right"
//         );

//         if (!groups.length) return;

//         groups.forEach(el => {
//             if (el) el.click();
//         });

//     }, 1000);
// });




frappe.getUserLocation = function (onSuccess) {
    if (navigator.geolocation) {
        frappe.show_alert({ message: __('جاري تحديد موقعك الجغرافي بدقة...'), indicator: 'blue' });

        navigator.geolocation.getCurrentPosition(
            function (position) {
                let latitude = position.coords.latitude;
                let longitude = position.coords.longitude;
                onSuccess(latitude, longitude, "Web Browser", navigator.userAgent)
            },
            function (error) {
                let errorMsg = "فشل جلب الموقع: ";
                if (error.code == error.PERMISSION_DENIED) {
                    errorMsg += "يجب السماح للمتصفح بالوصول إلى الـ GPS لتتمكن من تسجيل الحضور.";
                } else {
                    errorMsg += "يرجى التأكد من تفعيل خدمة الموقع في جهازك.";
                }
                frappe.msgprint({ title: __('خطأ'), indicator: 'red', message: __(errorMsg) });
            },
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
        );
    } else {
        frappe.throw(__("متصفحك لا يدعم تتبع الموقع الجغرافي."));
    }
};


frappe.show_employee_card = function (data) {

    let initials = frappe.get_abbr(data.employee_name || 'موظف');

    // 2. التصميم
    let html_content = `
    <style>
        
        .card-dialog-container { direction: rtl; font-family: 'Tajawal', sans-serif; display: flex; flex-direction: column; align-items: center; padding: 10px; background-color: #f4f5f9; }
        .employee-id-card { background: linear-gradient(135deg, #008dd2, #0073b7); width: 400px; border-radius: 20px; padding: 25px; color: white; box-shadow: 0 10px 20px rgba(0,0,0,0.1); position: relative; }
        .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 15px; margin-bottom: 20px; }
        .company-name { font-weight: bold; font-size: 16px; }
        .badge { background: white !important; color: #008dd2; padding: 5px 15px; border-radius: 15px; font-size: 12px; font-weight: bold; }
        .card-body { display: flex; align-items: center; margin-bottom: 25px; }
        .avatar { width: 80px; height: 80px; background: #e0f2fe; border-radius: 15px; display: flex; justify-content: center; align-items: center; font-size: 30px; font-weight: bold; color: #008dd2; margin-left: 20px; overflow: hidden; }
        .emp-info h3 { margin: 0 0 5px 0; font-size: 22px; color: white; }
        .emp-info p { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
        .emp-id-tag { background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 5px; font-size: 12px; display: inline-block; }
        .contact-info { margin-bottom: 25px; }
        .contact-info div { display: flex; align-items: center; margin-bottom: 10px; font-size: 13px; opacity: 0.9; }
        .card-footer { display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }
        .qr-text { font-size: 11px; opacity: 0.8; max-width: 60%; line-height: 1.5; }
        .qr-code { width: 80px; height: 80px; background: white; padding: 5px; border-radius: 10px; display: flex; justify-content: center; align-items: center; }
        
        .action-buttons { display: flex; gap: 15px; margin-top: 20px; }
        .btn-custom { padding: 10px 25px; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 8px; border: none; transition: 0.3s; }
        .btn-custom:hover { opacity: 0.9; transform: scale(1.02); }
        .btn-download { background: #008dd2; color: white; }
        .btn-print { background: #eef2f6; color: #333; border: 1px solid #d1d5db; }
        .icon { width: 15px; height: 15px; flex-shrink: 0; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; vertical-align: middle; margin:0 10px; }
        .btn-custom .icon { margin-left: 0; width: 16px; height: 16px; }
    </style>

    <div class="card-dialog-container">
        <div class="employee-id-card" id="card-to-download">
            <div class="card-header">
                <div class="company-name">${data.company_name || ''}</div>
                <div class="badge">بطاقة موظف</div>
            </div>
            
            <div class="card-body">
                <div class="avatar">${initials}</div>
                <div class="emp-info">
                    <h3>${data.employee_name}</h3>
                    <p>${data.designation}</p>
                    <div class="emp-id-tag">#${data.employee_id}</div>
                </div>
            </div>

            <div class="contact-info">
                <div><svg class="icon" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg> ${data.phone || 'غير متوفر'}</div>
                <div><svg class="icon" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg> ${data.email || 'غير متوفر'}</div>
                <div><svg class="icon" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><circle cx="8" cy="10" r="2"/><path d="M14 10h4M14 14h4M6 16h4"/></svg> ${data.national_id}</div>
            </div>

            <div class="card-footer">
                <div class="qr-text">امسح رمز QR للتحقق من الهوية أو تسجيل الحضور</div>
                <!-- مربع فارغ سنقوم بحقن الـ QR Code داخله -->
                <div class="qr-code" id="qr-code-container"></div>
            </div>
        </div>

        <div class="action-buttons">
            <button class="btn-custom btn-print"><svg class="icon" viewBox="0 0 24 24"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg> طباعة</button>
            <button class="btn-custom btn-download"><svg class="icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> تحميل صورة</button>
        </div>
    </div>
    `;

    let d = new frappe.ui.Dialog({
        title: 'بطاقة الهوية الوظيفية',
        size: 'large',
    });

    d.$wrapper.find('.modal-footer').hide();
    d.$wrapper.find('.modal-body').html(html_content);
    d.show();

    // 3. إنشاء الـ QR Code
    frappe.require('https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js', function () {
        let qrContainer = d.$wrapper.find('#qr-code-container')[0];
        new QRCode(qrContainer, {
            text: data.qr_data || data.employee_id,
            width: 70,   // الحجم المناسب للمربع
            height: 70,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    });

    // 4. وظيفة الطباعة
    d.$wrapper.find('.btn-print').on('click', function () {
        let printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html dir="rtl">
            <head>
                <title>طباعة بطاقة - ${data.employee_name}</title>
                ${d.$wrapper.find('style').prop('outerHTML')}
            </head>
            <body style="margin:0; display:flex; justify-content:center; align-items:center; height:100vh; background-color: white;">
                ${d.$wrapper.find('#card-to-download').prop('outerHTML')}
            </body>
            </html>
        `);
        printWindow.document.close();

        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 800);
    });

    // 5. وظيفة التحميل كصورة 
    d.$wrapper.find('.btn-download').on('click', function () {
        let btn = $(this);
        let originalText = btn.html();
        btn.prop('disabled', true).text('جاري التحميل...');

        let cardElement = document.getElementById('card-to-download');
        let width = cardElement.offsetWidth;
        let height = cardElement.offsetHeight;

        //
        let cardStyles = `
            .employee-id-card { background: linear-gradient(135deg, #008dd2, #0073b7); width: auto; border-radius: 20px; padding: 25px; color: white; box-shadow: 0 10px 20px rgba(0,0,0,0.1); position: relative; font-family: 'Tajawal', sans-serif; direction: rtl; }
            .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 15px; margin-bottom: 20px; }
            .company-name { font-weight: bold; font-size: 16px; }
            .badge { background: white !important; color: #008dd2; padding: 5px 15px; border-radius: 15px; font-size: 12px; font-weight: bold; }
            .card-body { display: flex; align-items: center; margin-bottom: 25px; }
            .avatar { width: 80px; height: 80px; background: #e0f2fe; border-radius: 15px; display: flex; justify-content: center; align-items: center; font-size: 30px; font-weight: bold; color: #008dd2; margin-left: 20px; overflow: hidden; }
            .emp-info h3 { margin: 0 0 5px 0; font-size: 22px; color: white; }
            .emp-info p { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
            .emp-id-tag { background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 5px; font-size: 12px; display: inline-block; }
            .contact-info { margin-bottom: 25px; }
            .contact-info div { display: flex; align-items: center; margin-bottom: 10px; font-size: 13px; opacity: 0.9; }
            .card-footer { display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }
            .qr-text { font-size: 11px; opacity: 0.8; max-width: 60%; line-height: 1.5; }
            .qr-code { width: 80px; height: 80px; background: white; padding: 5px; border-radius: 10px; display: flex; justify-content: center; align-items: center; }
            .icon { width: 15px; height: 15px; flex-shrink: 0; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; vertical-align: middle; margin-left: 10px; }
            .btn-custom .icon { margin-left: 0; width: 16px; height: 16px; }
        `;

        // XMLSerializer بيضمن XML صحيح 100% (بعكس outerHTML)
        let cardXml = new XMLSerializer().serializeToString(cardElement);

        let svgData = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
            <foreignObject width="100%" height="100%">
                <div xmlns="http://www.w3.org/1999/xhtml">
                    <style>${cardStyles}</style>
                    ${cardXml}
                </div>
            </foreignObject>
        </svg>`;

        let svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        let url = URL.createObjectURL(svgBlob);
        let img = new Image();
        console.log(url)
        img.onload = function () {
            try {
                let canvas = document.createElement('canvas');
                canvas.width = width * 2;
                canvas.height = height * 2;
                let ctx = canvas.getContext('2d');
                ctx.scale(2, 2);
                ctx.drawImage(img, 0, 0, width, height);
                URL.revokeObjectURL(url);

                let link = document.createElement('a');
                link.download = `بطاقة_موظف_${data.employee_name}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            } catch (err) {
                console.error("خطأ أثناء إنشاء الصورة:", err);
                frappe.msgprint(__("حدث خطأ أثناء محاولة تحميل البطاقة."));
            }
            btn.prop('disabled', false).html(originalText);
        };

        img.onerror = function (e) {
            console.error("فشل تحميل SVG:", e);
            console.log("افتح الرابط ده في تاب جديد عشان تشوف خطأ XML بالظبط:", url);
            frappe.msgprint(__("حدث خطأ أثناء محاولة تحميل البطاقة."));
            URL.revokeObjectURL(url);
            btn.prop('disabled', false).html(originalText);
        };

        img.src = url;
    });
}


frappe.showAttendanceModal = function (on_primary_action_click) {
    let now = new Date();
    let date = now.toLocaleDateString("ar-EG");

    let d = new frappe.ui.Dialog({
        title: __('جهاز تسجيل الحضور والإنصراف'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'realtime_display',
                options: `
						<div class="text-center" style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-bottom: 15px;">
							<h1 id="modal-live-time" style="font-weight: bold; color: #171717; font-size: 3rem; margin: 0;">00:00:00</h1>
							<h3 id="modal-live-date" style="margin-bottom: 5px;">---</h3>
						</div>
						<div class="text-center" style="margin-bottom: 20px;">
							<button class="btn btn-primary btn-lg btn-block" id="start-scan-btn">
								<i class="fa fa-qrcode"></i> ${__("ابدأ المسح (Scan)")}
							</button>
						</div>
					`
            },
            {
                label: __('بحث برقم الموظف (ID)'),
                fieldtype: 'Data',
                fieldname: 'employee_id',
                options: "Barcode",
                description: __('اضغط Enter بعد إدخال الكود')
            },

        ],
        primary_action_label: __('تسجيل'),
        primary_action(values) {
            on_primary_action_click(values,d);
            // submitAttendance(values.employee_id, d);
        }
    });

    d.show();

    d.on_page_show = function () {
        d.$wrapper.find('#modal-live-date').text(date);
        startTimeOnlyTimer(d);
    };


    d.$wrapper.on('click', '#start-scan-btn', function () {
        d.fields_dict.employee_id.$input.focus();

        new frappe.ui.Scanner({
            dialog: !0,
            multiple: !1,
            on_scan(e) {
                d.set_value('employee_id', e.result.text);
            }
        })



    });
    return d

}

let attendanceTimeInterval = null;

function startTimeOnlyTimer(dialog) {

	clearInterval(attendanceTimeInterval);

	function updateTime() {
		let now = new Date();

		let time = now.toLocaleTimeString('ar-EG');

		let timeEl = dialog?.$wrapper?.find('#modal-live-time');
		if (timeEl?.length) timeEl.text(time);
	}

	// عرض فوري
	updateTime();

	attendanceTimeInterval = setInterval(updateTime, 1000);
}