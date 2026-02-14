localStorage.container_fullwidth = true;
$( document ).ajaxSuccess(function(){
    let container = document.querySelector('div[item-name="لوحة التحكم"]')
    if (container) {
        if (container.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']") && window.location.pathname == "/app/%D9%84%D9%88%D8%AD%D8%A9-%D8%A7%D9%84%D8%AA%D8%AD%D9%83%D9%85") {
            container.querySelector(".drop-icon:not(.hidden)").click()
        }
    }
});


// $(document).ready(function() {
//     alert("done")
//     d = document.querySelector('div[item-name="لوحة التحكم"]')
//     if(d.querySelector(".drop-icon:not(.hidden) use[href='#es-line-down']")){
//         d.querySelector(".drop-icon:not(.hidden)").click()
//     }
// })


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
