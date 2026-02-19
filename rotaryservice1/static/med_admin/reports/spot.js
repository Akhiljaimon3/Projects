const csrftoken = document.querySelector('[name=csrf-token]').content;

// Setup CSRF for all AJAX requests
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^GET|HEAD|OPTIONS|TRACE$/.test(settings.type))) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function() {
    const $table = $('#patients_table');

    // Initialize DataTable
    const dt = $table.DataTable({
        pageLength: 50,
        lengthMenu: [[50, 100, 150, -1],[50, 100, 150, "All"]],
        searching: true,
        ordering: true,
        columnDefs: [
            { orderable: true, targets: [0,1,6,7] },
            { orderable: false, targets: [2,3,4,5] }
        ],
    });

    // AJAX function to fetch filtered patients
    function fetchPatients() {
        $.ajax({
            url: TOKEN_REPORT_URL,
            type: "POST",
            data: {
                department: $("#department-filter").val(),
                followup: $("#followup-filter").is(":checked"),
                addedby: $("#category").val(),
            },
            success: function(res) {
                $table.find("tbody").html(res.table_html);
                dt.clear();
                dt.rows.add($table.find("tbody tr")).draw();
            },
            error: function(xhr, status, error) {
                console.error("AJAX Error:", status, error);
            }
        });
    }

    // Trigger fetch on department or follow-up change
    $("#department-filter, #followup-filter").on("change", fetchPatients);

    // ================= DROPDOWN: ASHA FILTER =================
    const input = document.getElementById('dropdownInput');
    const list = document.getElementById('dropdownResults');
    const hidden = document.getElementById('category');

    const data = JSON.parse(document.getElementById("reg-data").textContent);

    // ✅ Add “All ASHA Workers” option to the top of the list
    const fullData = [{ id: '', name: 'All', ward: '' }, ...data];
    input.value = 'All';
    hidden.value = ''; 

    function populateList(filteredData) {
        list.innerHTML = '';
        filteredData.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.id === '' ? item.name : `${item.name}`;
            li.dataset.id = item.id;
            list.appendChild(li);
        });
        list.style.display = filteredData.length ? 'block' : 'none';
    }

    input.addEventListener('focus', () => populateList(fullData));

    input.addEventListener('input', () => {
        const query = input.value.toLowerCase();
        const filtered = fullData.filter(item => {
            if (item.id === '') return query === '';
            return item.name.toLowerCase().includes(query);
        });
        populateList(filtered);
    });

    list.addEventListener('click', e => {
        if (e.target.tagName === 'LI') {
            input.value = e.target.textContent;
            hidden.value = e.target.dataset.id;
            list.style.display = 'none';
            fetchPatients();
        }
    });

    document.addEventListener('click', e => {
        if (!list.contains(e.target) && e.target !== input) {
            list.style.display = 'none';
        }
    });

    let currentFocus = -1;
    input.addEventListener("keydown", function(e) {
        const items = list.getElementsByTagName("li");
        if (list.style.display !== "block" || items.length === 0) return;

        if (e.key === "ArrowDown") {
            currentFocus++;
            if (currentFocus >= items.length) currentFocus = 0;
            addActive(items);
            e.preventDefault();
        } else if (e.key === "ArrowUp") {
            currentFocus--;
            if (currentFocus < 0) currentFocus = items.length - 1;
            addActive(items);
            e.preventDefault();
        } else if (e.key === "Enter") {
            if (currentFocus > -1) items[currentFocus].click();
            e.preventDefault();
        } else if (e.key === "Escape") {
            list.style.display = "none";
        }
    });

    function addActive(items) {
        removeActive(items);
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add("active");
            items[currentFocus].scrollIntoView({ block: "nearest" });
        }
    }

    function removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove("active");
        }
    }
});

// ================= TOMSELECT: DEPARTMENT / OTHER SELECTS =================
document.querySelectorAll("select.control-item, select.export-item").forEach(el => {
    new TomSelect(el, {
        create: false,
        maxItems: 1,
        hideSelected: true,
        controlInput: null,
        allowEmptyOption: true,
        render: {
            item: (data, escape) => `<div class="item">${escape(data.text)}</div>`,
            option: (data, escape) => `<div class="option">${escape(data.text)}</div>`
        }
    });
});

// ================= PDF and EXCEL Export =================
$("#export-btn").on("click", async function() {
    const type = $("#export-type").val();
    let title = "Token Report";

    const fromDate = $("#from")?.val();
    const toDate = $("#to")?.val();

    if (fromDate && toDate) title += ` (${fromDate} to ${toDate})`;
    else if (fromDate) title += ` (From ${fromDate})`;
    else if (toDate) title += ` (Up to ${toDate})`;

    function safeFileName(name) {
        return name.replace(/[^a-z0-9_\-()\s]/gi, "_");
    }

    // Collect all table data from DataTable (all pages, respecting filters)
    const table = $("#patients_table").DataTable();

    let tableData = table
    .rows({ search: 'applied' }) // all filtered rows
    .data()
    .toArray()
    .map(row => {
        // Convert row data to plain array of cell values
        return Array.from(row);
    });


    if (type === "pdf") {
        const { jsPDF } = window.jspdf;
        let doc = new jsPDF("p", "mm", "a4");

        // Load Malayalam font
        const response = await fetch(NOTO_MALAYALAM_FONT_URL);
        const buffer = await response.arrayBuffer();
        const ttfBytes = new Uint8Array(buffer);

        function arrayBufferToBase64(buffer) {
            let binary = '';
            const bytes = new Uint8Array(buffer);
            const len = bytes.byteLength;
            for (let i = 0; i < len; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            return window.btoa(binary);
        }

        const fontBase64 = arrayBufferToBase64(ttfBytes);
        doc.addFileToVFS("NotoSansMalayalam-Regular.ttf", fontBase64);
        doc.addFont("NotoSansMalayalam-Regular.ttf", "NotoMalayalam", "normal");

        let topMargin = 6;
        let cursorY = topMargin;
        const pageWidth = doc.internal.pageSize.getWidth();

        // ===== Professional Header =====
        // Title Section (English)
        doc.setFont("helvetica", "normal");
        doc.setFontSize(20);
        doc.setTextColor(33, 37, 41);
        doc.text("Rotary Santhwana Sparsham 2025", pageWidth / 2, topMargin + 12, { align: "center" });

        doc.setFontSize(13);
        doc.setTextColor(90, 90, 90);
        doc.text("Free Mega Medical Camp", pageWidth / 2, topMargin + 18, { align: "center" });

        doc.setFontSize(15);
        doc.setTextColor(0, 0, 0);
        doc.text("Spot Register Report", pageWidth / 2, topMargin + 25, { align: "center" });

        // Divider line
        doc.setDrawColor(180);
        doc.setLineWidth(0.5);
        doc.line(12, topMargin + 28, pageWidth - 12, topMargin + 28);

        cursorY = topMargin + 33;

        // === Filters Applied ===
        const filters = [];
        const dept = $("#department-filter option:selected").text();
        if (dept && dept !== "All Departments") filters.push({ label: "Department", value: dept });
        if ($("#followup-filter").is(":checked")) filters.push({ label: "Follow-up", value: "Yes" });
        const addedBy = $("#dropdownInput").val();
        if (addedBy) filters.push({ label: "Consulted By", value: addedBy });
        const rotorian = $("#rotorian").val();
        if (rotorian) filters.push({ label: "Rotorians", value: rotorian });

        if (filters.length) {
            const leftX = 12;       // left margin
            const rowHeight = 5;    // vertical spacing between filters

            cursorY += 0; // small top padding

            filters.forEach(filter => {
                // Label
                doc.setFont("helvetica", "bold");
                doc.setFontSize(10);
                doc.setTextColor(60);
                doc.text(filter.label + ":", leftX, cursorY);

                // Value
                doc.setFont("NotoMalayalam", "normal");
                doc.setFontSize(10);
                doc.setTextColor(20);
                doc.text(filter.value, leftX + 24, cursorY);

                cursorY += rowHeight; // move down for next filter
            });

            cursorY += 0; // space before next section (like table)
        }

        // === Clean Department column (extract English only) ===
        function extractEnglish(deptName) {
            const match = deptName?.match(/\(([^)]+)\)/);  // get text inside parentheses
            return match ? match[1].trim() : deptName;     // fallback if no ()
        }

        // Apply to all rows in tableData (assuming Department is column 8)
        tableData = tableData.map(row => {
            if (row[8]) {
                row[8] = extractEnglish(row[8]);
            }
            return row;
        });

        // Adjusted column widths for A4
        const colWidths = [10, 28, 20, 10, 12, 12, 12, 21, 37, 28]; 

        doc.autoTable({
            startY: cursorY,
            head: [["SL","Name","Contact","Age","Code","Pin", "Token", "Added on","Department","Added By"]],
            body: tableData,
            styles: {
                font: "NotoMalayalam",
                fontSize: 8,
                cellPadding: 1,
                valign: 'middle',
                overflow: 'linebreak'
            },
            headStyles: {
                fillColor: [41, 128, 185],
                textColor: 255,
                halign: 'center',
                fontStyle: 'bold'
            },
            alternateRowStyles: { fillColor: [245, 245, 245] },
            columnStyles: {
                0: { cellWidth: colWidths[0], halign: 'center' }, // SL
                1: { cellWidth: colWidths[1] },                   // Name
                2: { cellWidth: colWidths[2], halign: 'center' }, // Contact
                3: { cellWidth: colWidths[3], halign: 'center' }, // Age
                4: { cellWidth: colWidths[4], halign: 'center' }, // Code
                5: { cellWidth: colWidths[5], halign: 'center' }, // Pin
                6: { cellWidth: colWidths[6], halign: 'center' }, // Token
                7: { cellWidth: colWidths[7] },                   // Added On
                8: { cellWidth: colWidths[8] },                   // Department
                9: { cellWidth: colWidths[9] }                    // Added By
            },
            theme: 'grid',
            margin: { left: 10, right: 10 },            didDrawPage: function(data) {
                const pageHeight = doc.internal.pageSize.getHeight();
                doc.setFontSize(8);
                doc.setTextColor(100);
                doc.text(`Page ${doc.internal.getNumberOfPages()}`, pageWidth - 20, pageHeight - 10, { align: 'right' });
            }
        });

        doc.save(safeFileName('Spot Register Report') + ".pdf");
    }

    // ================= Excel Export =================
if (type === "excel") {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet("Token Report");
    let rowCursor = 1;

        // ===== Title =====
    const titleRow = worksheet.getRow(rowCursor++);
    titleRow.getCell(1).value = "Rotary Santhwana Sparsham 2025";
    titleRow.getCell(1).font = { size: 20, bold: true };
    titleRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
    worksheet.mergeCells(`A${titleRow.number}:J${titleRow.number}`);
    titleRow.height = 28;

    // Subtitle
    const subTitleRow = worksheet.getRow(rowCursor++);
    subTitleRow.getCell(1).value = "Free Mega Medical Camp";
    subTitleRow.getCell(1).font = { size: 13, bold: false };
    subTitleRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
    worksheet.mergeCells(`A${subTitleRow.number}:J${subTitleRow.number}`);
    subTitleRow.height = 20;

    // Report Name
    const reportRow = worksheet.getRow(rowCursor++);
    reportRow.getCell(1).value = "Spot Register Report";
    reportRow.getCell(1).font = { size: 15, bold: true };
    reportRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
    worksheet.mergeCells(`A${reportRow.number}:J${reportRow.number}`);
    reportRow.height = 22;

    // Small spacing row
    rowCursor++;

    // ===== Filters (stacked like PDF) =====
    const filters = [];
    const dept = $("#department-filter option:selected").text();
    if (dept && dept !== "All Departments") filters.push({ label: "Department", value: dept });
    if ($("#followup-filter").is(":checked")) filters.push({ label: "Follow-up", value: "Yes" });
    const addedBy = $("#dropdownInput").val();
    if (addedBy) filters.push({ label: "Confirmed By", value: addedBy });

    const leftCol = 1;  // start in first column
    filters.forEach(f => {
        const row = worksheet.getRow(rowCursor++);
        row.getCell(leftCol).value = `${f.label}: ${f.value}`;
        row.getCell(leftCol).font = { bold: true, size: 11 };
        row.getCell(leftCol).alignment = { horizontal: "left", vertical: "middle", wrapText: true };
        worksheet.mergeCells(`A${row.number}:C${row.number}`); // merge 3 columns for left-aligned stacked filters
        row.height = 18;  // row height
    });

    // Small spacing before table
    rowCursor++;

    // === Clean Department column (extract English only) ===
    function extractEnglish(deptName) {
        const match = deptName?.match(/\(([^)]+)\)/);  // capture text inside parentheses
        return match ? match[1].trim() : deptName;     // fallback if no ()
    }

    // Apply to all rows in tableData (assuming Department is column 8)
    tableData = tableData.map(row => {
        if (row[8]) {
            row[8] = extractEnglish(row[8]);
        }
        return row;
    });

    // ===== Headers =====
    const headers = ["SL","Name","Contact","Age","Code","Pin", "Token", "Added on","Department","Added By"];
    const headerRow = worksheet.getRow(rowCursor++);
    headers.forEach((header, i) => {
        const cell = headerRow.getCell(i + 1);
        cell.value = header;
        cell.font = { bold: true, color: { argb: "FF000000" } };
        cell.alignment = { horizontal: "center", vertical: "middle" };
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFE5E5E5" } };
        cell.border = { top: { style: "thin" }, left: { style: "thin" }, bottom: { style: "thin" }, right: { style: "thin" } };
    });
    headerRow.height = 22;

    // ===== Body =====
    tableData.forEach(rowData => {
        const row = worksheet.getRow(rowCursor++);
        row.height = 28;
        rowData.forEach((val, i) => {
            const cell = row.getCell(i + 1);
            cell.value = val;

            // Center specific columns: SL(0), Contact(2), Code(3), PIN(4), Token(5)
            const centerColumns = [0, 2, 3, 4, 5];
            cell.alignment = {
                vertical: "middle",
                horizontal: centerColumns.includes(i) ? "center" : "left",
                wrapText: true
            };

            cell.border = {
                top: { style: "thin" },
                left: { style: "thin" },
                bottom: { style: "thin" },
                right: { style: "thin" }
            };
        });
    });

    // ===== Column Widths =====
    worksheet.columns = [
        { width: 5 },  // SL
        { width: 20 }, // Name
        { width: 15 }, // Contact
        { width: 10 }, // Age
        { width: 10 }, // Code
        { width: 10 }, // PIN
        { width: 10 }, // Token
        { width: 20 }, // Addon
        { width: 20 }, // Department
        { width: 20 }  // Confirmed By
    ];

    // ===== Page Setup =====
    worksheet.pageSetup = {
        paperSize: 9,           // A4
        orientation: 'portrait',
        fitToPage: true,
        fitToWidth: 1,
        fitToHeight: 0,
        margins: {
            left: 0.5,
            right: 0.5,
            top: 0.60,
            bottom: 0.60,
            header: 0,
            footer: 0
        }
    };

    // ===== Download =====
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: "application/octet-stream" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = safeFileName("Spot Register Report") + ".xlsx";
    link.click();
}

});
