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
        columnDefs: [
            { responsivePriority: 1, targets: 1 }, // Name
            { responsivePriority: 2, targets: 2 }, // Contact
            { responsivePriority: 3, targets: -1 } // Added By
        ],
        searching: true,
        ordering: true,
        columnDefs: [
            { orderable: true, targets: [0,1,4,5] },
            { orderable: false, targets: [2,3] }
        ],
    });

    // ==================== RADIO BUTTON HANDLER (UPDATED) ====================
    $('input[name="addedby-type"]').on('change', function() {
        const selected = $(this).val();

        // Hide both filters initially
        $('#asha-filter, #rotorian-filter').hide();

        if (selected === "all") {
            // Show all data — no dropdown visible
            $("#category").val("");
            $("#rotorian").val("");
            fetchPatients();
        } 
        else if (selected === "asha") {
            // Show ASHA dropdown only
            $('#asha-filter').show();
            $("#rotorian").val("");
            $("#rotorianInput").val(""); // clear rotarian
            $("#dropdownInput").val("All ASHA Workers");
            $("#category").val(""); // means "all"
            fetchPatients();
        } 
        else if (selected === "rotarian") {
            // Show Rotarian dropdown only
            $('#rotorian-filter').show();
            $("#category").val("");
            $("#dropdownInput").val(""); // clear asha
            $("#rotorianInput").val("All Rotarians");
            $("#rotorian").val(""); // means "all"
            fetchPatients();
        }
    });

    // AJAX function to fetch filtered patients
    function fetchPatients() {
        $.ajax({
            url: PATIENT_REPORT_URL,
            type: "POST",
            data: {
                department: $("#department-filter").val(),
                followup: $("#followup-filter").is(":checked"),
                spot: $("#spot-filter").is(":checked"),
                addedby: $("#category").val(),
                rotorian: $("#rotorian").val(),
                addedby_type: $('input[name="addedby-type"]:checked').val()
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
    $("#department-filter, #followup-filter, #spot-filter").on("change", fetchPatients);


    // ================= DROPDOWN: ASHA FILTER =================
    const input = document.getElementById('dropdownInput');
    const list = document.getElementById('dropdownResults');
    const hidden = document.getElementById('category');

    const data = JSON.parse(document.getElementById("asha-data").textContent);

    const fullData = [{ id: '', name: 'All ASHA Workers', ward: '' }, ...data];

    input.value = 'All ASHA Workers';
    hidden.value = ''; 

    function populateList(filteredData) {
        list.innerHTML = '';
        filteredData.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.id === '' ? item.name : `${item.name}-${item.ward}`;
            li.dataset.id = item.id;
            list.appendChild(li);
        });
        list.style.display = filteredData.length ? 'block' : 'none';
    }

    // Show all when focused
    input.addEventListener('focus', () => populateList(fullData));

    // Filter by name or ward (still includes "All" if user types nothing)
    input.addEventListener('input', () => {
        const query = input.value.toLowerCase();
        const filtered = fullData.filter(item => {
            if (item.id === '') return query === ''; // Show "All" only if no search
            const nameMatch = item.name.toLowerCase().includes(query);
            const wardMatch = item.ward.toString().includes(query);
            return nameMatch || wardMatch;
        });
        populateList(filtered);
    });

    // Select item from dropdown
    list.addEventListener('click', e => {
        if (e.target.tagName === 'LI') {
            input.value = e.target.textContent;
            hidden.value = e.target.dataset.id; // empty if "All" selected
            list.style.display = 'none';
            fetchPatients(); // trigger AJAX immediately
        }
    });

    // Hide dropdown when clicking outside
    document.addEventListener('click', e => {
        if (!list.contains(e.target) && e.target !== input) {
            list.style.display = 'none';
        }
    });

    // Keyboard navigation
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

    // ================= DROPDOWN: ROTARIAN FILTER =================
    const rotorianInput = document.getElementById('rotorianInput');
    const rotorianList = document.getElementById('rotorianResults');
    const rotorianHidden = document.getElementById('rotorian');

    const rotorianData = JSON.parse(document.getElementById("rotorian-data").textContent);

    const fullRotorianData = [{ id: '', name: 'All Rotorians', club: '' }, ...rotorianData];

    rotorianInput.value = 'All Rotorians';
    rotorianHidden.value = ''; 

    function populateRotorianList(filteredData) {
        rotorianList.innerHTML = '';
        filteredData.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.id === '' ? item.name : `${item.name}`;
            li.dataset.id = item.id;
            rotorianList.appendChild(li);
        });
        rotorianList.style.display = filteredData.length ? 'block' : 'none';
    }

    rotorianInput.addEventListener('focus', () => populateRotorianList(fullRotorianData));

    rotorianInput.addEventListener('input', () => {
        const query = rotorianInput.value.toLowerCase();
        const filtered = fullRotorianData.filter(item => {
            if (item.id === '') return query === '';
            const nameMatch = item.name.toLowerCase().includes(query);
            const clubMatch = item.club?.toLowerCase().includes(query);
            return nameMatch || clubMatch;
        });
        populateRotorianList(filtered);
    });

    rotorianList.addEventListener('click', e => {
        if (e.target.tagName === 'LI') {
            rotorianInput.value = e.target.textContent;
            rotorianHidden.value = e.target.dataset.id;
            rotorianList.style.display = 'none';
            fetchPatients(); // refresh table
        }
    });

    document.addEventListener('click', e => {
        if (!rotorianList.contains(e.target) && e.target !== rotorianInput) {
            rotorianList.style.display = 'none';
        }
    });
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
    let title = "Patients Report";

    const fromDate = $("#from")?.val();
    const toDate = $("#to")?.val();

    if (fromDate && toDate) title += ` (${fromDate} to ${toDate})`;
    else if (fromDate) title += ` (From ${fromDate})`;
    else if (toDate) title += ` (Up to ${toDate})`;

    function safeFileName(name) {
        return name.replace(/[^a-z0-9_\-()\s]/gi, "_");
    }

    // Collect visible table data
    const table = $("#patients_table").DataTable();

    let tableData = table
    .rows({ search: 'applied' }) // all filtered rows
    .data()
    .toArray()
    .map(row => {
        // Convert row data to plain array of cell values
        return Array.from(row);
    });

    // ================= PDF Export =================
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
        doc.text("Patients Report", pageWidth / 2, topMargin + 25, { align: "center" });

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
        if ($("#spot-filter").is(":checked")) filters.push({ label: "Spot Register", value: "Yes" });

        const addedByType = $('input[name="addedby-type"]:checked').val();
        if (addedByType === "asha") {
            const ashaVal = $("#dropdownInput").val();
            if (ashaVal) filters.push({ label: "Added By", value: ashaVal });
        } else if (addedByType === "rotarian") {
            const rotarianVal = $("#rotorianInput").val();
            if (rotarianVal) filters.push({ label: "Added By", value: rotarianVal });
        } else if (addedByType === "all") {
            filters.push({ label: "Added By", value: "All" });
        }

        if (addedByType === "rotarian" && $("#rotorian").val()) {
            filters.push({ label: "Rotarians", value: $("#rotorian").val() });
        }

        if (filters.length) {
            const leftX = 15;
            const rowHeight = 5;
            filters.forEach(filter => {
                // Label (English)
                doc.setFont("helvetica", "bold");
                doc.setFontSize(10);
                doc.setTextColor(60);
                doc.text(filter.label + ":", leftX, cursorY);

                // Value (Malayalam if present)
                doc.setFont("NotoMalayalam", "normal");
                doc.setFontSize(10);
                doc.setTextColor(20);
                doc.text(filter.value, leftX + 25, cursorY);

                cursorY += rowHeight;
            });
            cursorY += 0;
        }

        // === Clean Department column (extract English only) ===
        function extractEnglish(deptName) {
            const match = deptName?.match(/\(([^)]+)\)/);  // get text inside parentheses
            return match ? match[1].trim() : deptName;     // fallback if no ()
        }

        // Apply to all rows in tableData (assuming Department is column 8)
        tableData = tableData.map(row => {
            if (row[7]) {
                row[7] = extractEnglish(row[7]);
            }
            return row;
        });

        // Adjusted column widths for A4
        const colWidths = [10, 31, 22, 10, 13, 13, 21, 37, 31];

        doc.autoTable({
            startY: cursorY,
            head: [["SL","Name","Contact","Age","Code","Pin", "Added on","Department","Added By"]],
            body: tableData,
            styles: { font: "NotoMalayalam", fontSize: 8, cellPadding: 1, valign: 'middle' }, // Malayalam for table
            headStyles: { fillColor: [41,128,185], textColor: 255, halign: 'center', fontStyle: 'bold' },
            alternateRowStyles: { fillColor: [245,245,245] },
            columnStyles: {
                0: { cellWidth: colWidths[0], halign: 'center' },
                1: { cellWidth: colWidths[1] },
                2: { cellWidth: colWidths[2], halign: 'center' },
                3: { cellWidth: colWidths[3], halign: 'center' },
                4: { cellWidth: colWidths[4], halign: 'center' },
                5: { cellWidth: colWidths[5], halign: 'center' },
                6: { cellWidth: colWidths[6] },
                7: { cellWidth: colWidths[7] },
                8: { cellWidth: colWidths[8] }
            },
            theme: 'grid',
            margin: { left: 11, right: 11 },
            didDrawPage: function (data) {
                const pageHeight = doc.internal.pageSize.getHeight();
                doc.setFont("helvetica", "normal"); // page number in English
                doc.setFontSize(8);
                doc.setTextColor(100);
                doc.text(`Page ${doc.internal.getNumberOfPages()}`, pageWidth - 20, pageHeight - 10, { align: 'right' });
            }
        });

        doc.save(safeFileName("Patients Report") + ".pdf");
    }

    // ================= Excel Export =================
    if (type === "excel") {
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet("Patient Report");
        let rowCursor = 1;

        // ===== Title =====
        const titleRow = worksheet.getRow(rowCursor++);
        titleRow.getCell(1).value = "Rotary Santhwana Sparsham 2025";
        titleRow.getCell(1).font = { size: 20, bold: true };
        titleRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
        worksheet.mergeCells(`A${titleRow.number}:I${titleRow.number}`);
        titleRow.height = 28;

        // Subtitle
        const subTitleRow = worksheet.getRow(rowCursor++);
        subTitleRow.getCell(1).value = "Free Mega Medical Camp";
        subTitleRow.getCell(1).font = { size: 13, bold: false };
        subTitleRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
        worksheet.mergeCells(`A${subTitleRow.number}:I${subTitleRow.number}`);
        subTitleRow.height = 20;

        // Report Name
        const reportRow = worksheet.getRow(rowCursor++);
        reportRow.getCell(1).value = "Patients Report";
        reportRow.getCell(1).font = { size: 15, bold: true };
        reportRow.getCell(1).alignment = { horizontal: "center", vertical: "middle" };
        worksheet.mergeCells(`A${reportRow.number}:I${reportRow.number}`);
        reportRow.height = 22;

        // Small spacing row
        rowCursor++;

        // ===== Filters (stacked like PDF) =====
        const filters = [];
        const dept = $("#department-filter option:selected").text();
        if (dept && dept !== "All Departments") filters.push({ label: "Department", value: dept });
        if ($("#followup-filter").is(":checked")) filters.push({ label: "Follow-up", value: "Yes" });
        if ($("#spot-filter").is(":checked")) filters.push({ label: "Spot Register", value: "Yes" });
        const addedBy = $("#dropdownInput").val();
        if (addedBy) filters.push({ label: "Added By", value: addedBy });
        const rotorian = $("#rotorian").val();
        if (rotorian) filters.push({ label: "Rotarians", value: rotorian });

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
            if (row[7]) {
                row[7] = extractEnglish(row[7]);
            }
            return row;
        });

        // ===== Headers =====
        const headers = ["SL", "Name", "Contact", "Age", "Code", "Pin", "Added on", "Department", "Added By"];
        const headerRow = worksheet.getRow(rowCursor++);
        headers.forEach((header, i) => {
            const cell = headerRow.getCell(i + 1);
            cell.value = header;
            cell.font = { bold: true, size: 12, color: { argb: "FF000000" } };
            cell.alignment = { horizontal: "center", vertical: "middle" };
            cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFE5E5E5" } };
            cell.border = { top: { style: "thin" }, left: { style: "thin" }, bottom: { style: "thin" }, right: { style: "thin" } };
        });
        headerRow.height = 25;

        // ===== Body =====
        tableData.forEach(rowData => {
            const row = worksheet.getRow(rowCursor++);
            row.height = 28;
            rowData.forEach((val, i) => {
                const cell = row.getCell(i + 1);
                cell.value = val;
                cell.alignment = {
                    vertical: "middle",
                    horizontal: i === 0 || i === 2 || i === 3 ? "center" : "left",
                    wrapText: true
                };
                cell.border = { top: { style: "thin" }, left: { style: "thin" }, bottom: { style: "thin" }, right: { style: "thin" } };
            });
        });

        // ===== Column Widths =====
        worksheet.columns = [
            { width: 5 }, { width: 20 }, { width: 15 },
            { width: 10 },{ width: 10 },{ width: 10 }, { width: 20 }, { width: 20 }, { width: 25 }
        ];

        // ===== Page Setup =====
        worksheet.pageSetup = {
            paperSize: 9,           // A4
            orientation: 'portrait',
            fitToPage: true,         // scale to fit page width
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
        link.download = safeFileName("Patient Report") + ".xlsx";
        link.click();
    }
});
