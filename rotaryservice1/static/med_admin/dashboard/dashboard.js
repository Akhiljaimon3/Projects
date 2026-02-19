document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded");

    const colors = ["#a6bdd2","#b8a383","#fafafa","#E5C80A","#b0e9eb","#F8F7A7","#eea5d1"];

    const donutChartEl = document.getElementById("donutChart");
    const donutLegendEl = document.getElementById("donutLegend");

    function renderDoughnutWithLegend(ctx, legendContainer, labels, data, colors) {
        if (ctx.chart) ctx.chart.destroy();

        // Set border only for white slice
        const borders = colors.map(c => c === "#fafafa" ? "#d2d2d2ff" : "#fff");
        const borderWidths = colors.map(c => c === "#fafafa" ? .5 : 1);

        ctx.chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: borders,
                    borderWidth: borderWidths
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { legend: { display: false } } 
            }
        });

        // Custom legend
        legendContainer.innerHTML = '';
        labels.forEach((label, i) => {
            const item = document.createElement('div');
            item.style.display = 'flex';
            item.style.alignItems = 'center';
            item.style.gap = '10px';

            const colorBox = document.createElement('div');
            colorBox.style.width = '15px';
            colorBox.style.height = '15px';
            colorBox.style.backgroundColor = colors[i];
            colorBox.style.border = colors[i] === "#fafafa" ? "1px solid #d2d2d2ff" : "none";
            colorBox.style.borderRadius = '3px';

            const text = document.createElement('span');
            text.textContent = label;

            item.appendChild(colorBox);
            item.appendChild(text);
            legendContainer.appendChild(item);
        });
        console.log("Pie chart rendered with white border");
    }

    renderDoughnutWithLegend(donutChartEl, donutLegendEl, labels, data, colors);

    const barChartEl = document.getElementById("deptChart");

    if (barChartEl) {
        if (barChartEl.chart) barChartEl.chart.destroy();

        barChartEl.chart = new Chart(barChartEl, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Enrolled Patients',
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 5,
                    borderColor: colors.map(c => c === "#fafafa" ? "#999" : "#f4f4f4ff"),
                    borderWidth: colors.map(c => c === "#fafafa" ? .5 : 0)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
        console.log("Bar chart rendered with white border");
    }
});
