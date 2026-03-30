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

        this.container.append(table);
    }
}