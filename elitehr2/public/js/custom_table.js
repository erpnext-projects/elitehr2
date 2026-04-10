class CustomTable {
    constructor({ container, columns, data }) {
        this.container = $(container);
        this.columns = columns;
        this.data = data;
        this.render();
    }

    render() {
        this.container.empty();

        const table = $(`
            <div class="custom-card">
                <table class="custom-table">
                    <thead></thead>
                    <tbody></tbody>
                    <tfoot></tfoot>
                </table>
            </div>
        `);

        // Header
        const thead = $("<tr></tr>");
        this.columns.forEach(col => {
            thead.append(`<th>${col.name}</th>`);
        });
        table.find("thead").append(thead);


        // Body
        const tbody = table.find("tbody");
        this.data.forEach(row => {
            const tr = $("<tr></tr>");

            this.columns.forEach(col => {
                let value = row[col.id];

                if (col.format) {
                    value = col.format(value, row);
                }

                tr.append(`<td>${value || ""}</td>`);
            });

            tbody.append(tr);
        });

        
        // footer
        const tfoot = table.find("tfoot");
        const footerRow = $("<tr class='total-row'></tr>");
        this.columns.forEach((col) => {
            let footerValue = "";
            if (col.sum) {
                // دالة الجمع: بتمشي على data وتجمع الـ id بتاع العمود ده
                const total = this.data.reduce((sum, row) => {
                    return sum + (parseFloat(row[col.id]) || 0);
                }, 0);
                // لو العمود له تنسيق (format) نطبقه على المجموع برضه
                footerValue = col.format ? col.format(total) : total;
            }else if (col.count) {                
                footerValue = `${col.textBefore || ""}${this.data.length}${col.textAfter || ""}`;
            }

            footerRow.append(`<td><strong>${footerValue}</strong></td>`);
        });
        tfoot.append(footerRow);



        this.container.append(table);
    }
}