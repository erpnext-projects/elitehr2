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


    

});

frappe.router.on('change', () => {
    let route = frappe.get_route();
    // console.log(route);
    if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "User") {
        // let urlParams = new URLSearchParams(window.location.search);
        // console.log(urlParams);
        // if (urlParams.get('sidebar') !== 'Hr Pro') {
        //     urlParams.set('sidebar', 'Hr Pro');
        //     let newUrl = window.location.pathname + '?' + urlParams.toString() + window.location.hash;
        //     window.location.replace(newUrl);
        // }
    }
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
})


// frappe.after_ajax(() => {
//     d = document.querySelector('div[item-name="لوحة التحكم"]')
//     if(d.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']")){
//         d.querySelector(".drop-icon:not(.hidden)").click()
//     }
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




