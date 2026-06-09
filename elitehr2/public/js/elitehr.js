localStorage.container_fullwidth = true;
$( document ).ajaxSuccess(function(){
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
                if (index !== 0 && index !== breadcrumbs.length - 1){
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


     document.querySelectorAll(".sidebar-item-container.section-item").forEach(
        e => {            
            if(!e.querySelector(".active-sidebar") && e.querySelector("button.drop-icon[data-state='opened']")){
                e.querySelector("button.drop-icon[data-state='opened']").click()
            }
        }
    )

    


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
    let route = frappe.get_route();
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


$(document).ready(function() {
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




frappe.getUserLocation = function(onSuccess) {
    if (navigator.geolocation) {
        frappe.show_alert({message: __('جاري تحديد موقعك الجغرافي بدقة...'), indicator: 'blue'});

        navigator.geolocation.getCurrentPosition(
            function(position) {
                let latitude =  position.coords.latitude;
                let longitude =  position.coords.longitude;
                onSuccess(latitude,longitude,"Web Browser",navigator.userAgent)
            },
            function(error) {
                let errorMsg = "فشل جلب الموقع: ";
                if (error.code == error.PERMISSION_DENIED) {
                    errorMsg += "يجب السماح للمتصفح بالوصول إلى الـ GPS لتتمكن من تسجيل الحضور.";
                } else {
                    errorMsg += "يرجى التأكد من تفعيل خدمة الموقع في جهازك.";
                }
                frappe.msgprint({ title: __('خطأ'), indicator: 'red', message: __(errorMsg) });
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    } else {
        frappe.throw(__("متصفحك لا يدعم تتبع الموقع الجغرافي."));
    }
};