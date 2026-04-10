// Copyright (c) 2026, Mohamed Elgohary and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Leaves balances"] = {
	filters: [
		// {
		// 	"fieldname": "my_filter",
		// 	"label": __("My Filter"),
		// 	"fieldtype": "Data",
		// 	"reqd": 1,
		// },
		{
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Elitehr Employee"
        }
	],
	formatter: function(value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (column.fieldname == "percentage" && data) {

            let percent = data.percentage || 0;

            let color = "#28a745";

            if (percent > 70) {
                color = "#dc3545";
            } else if (percent > 40) {
                color = "#ffc107";
            }
                // <div class="progress" style="flex-grow:1">
				// 	<div class="progress-bar" style="width:${percentage}">${percentage}</div>
				// </div>
                // <div style="
                //         background:#e9ecef;
                //         border-radius:6px;
                //         height:20px;
                //         overflow:hidden;
                //     ">
                //         <div style="
                //             width:${percent}%;
                //             background:${color};
                //             height:20px;
                //         "></div>
                //     </div>
            value = `
                <div style="width:150px;">
                    <div class="progress" style="flex-grow:1">
                        <div class="progress-bar" style="width:${percent}%">${percent} %</div>
                    </div>
                    <div style="font-size:11px;margin-top:2px;text-align:center">
                        ${percent}%
                    </div>	
                </div>
            `;
        }

        return value;
    }
};
