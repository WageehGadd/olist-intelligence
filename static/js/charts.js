(() => {
    const PLOTLY_SRC = "https://cdn.plot.ly/plotly-basic-2.35.2.min.js";
    const FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
    const COLORS = {
        sage: "#879B83",
        sageDark: "#657A62",
        orange: "#D97745",
        text: "#3F4940",
        grid: "#E2E4DA",
    };
    const TOP_CATEGORIES = 15;
    const CONFIG = { responsive: true, displayModeBar: false };

    const axis = (extra = {}) => ({
        automargin: true,
        gridcolor: COLORS.grid,
        linecolor: COLORS.grid,
        zerolinecolor: COLORS.grid,
        ...extra,
    });

    const layout = ({ xaxis, yaxis, ...rest } = {}) => ({
        autosize: true,
        margin: { l: 16, r: 16, t: 16, b: 16 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { family: FONT, size: 12, color: COLORS.text },
        showlegend: false,
        xaxis: axis(xaxis),
        yaxis: axis(yaxis),
        ...rest,
    });

    const formatName = (name) => name.replace(/_/g, " ");

    function horizontalBars(entries, { color, axisTitle, hover }) {
        if (!entries.length) {
            return null;
        }

        const top = entries.sort((a, b) => b[1] - a[1]).slice(0, TOP_CATEGORIES);

        return {
            data: [{
                type: "bar",
                orientation: "h",
                x: top.map(([, value]) => value),
                y: top.map(([name]) => formatName(name)),
                marker: { color },
                hovertemplate: hover,
            }],
            layout: layout({
                xaxis: { title: { text: axisTitle }, tickformat: "~s" },
                yaxis: { type: "category", autorange: "reversed" },
            }),
        };
    }

    // Series arrive as the backend's chart envelope `series`; KPI charts receive the `kpis` mapping.
    const renderers = {
        "category-value": (rows) => {
            const totals = new Map();
            rows.forEach(({ category_name: name, item_value_brl: value }) => {
                totals.set(name, (totals.get(name) ?? 0) + value);
            });

            return horizontalBars([...totals], {
                color: COLORS.sage,
                axisTitle: "Item value (BRL)",
                hover: "<b>%{y}</b><br>BRL %{x:,.2f}<extra></extra>",
            });
        },

        "category-count": (rows) => horizontalBars(
            rows.map((row) => [row.category_name, row.item_count]),
            {
                color: COLORS.sageDark,
                axisTitle: "Number of items",
                hover: "<b>%{y}</b><br>%{x:,} items<extra></extra>",
            },
        ),

        "price-distribution": (rows) => ({
            data: [{
                type: "bar",
                x: rows.map((row) => row.bin_label),
                y: rows.map((row) => row.item_count),
                marker: { color: COLORS.sage },
                texttemplate: "%{y:,}",
                textposition: "outside",
                cliponaxis: false,
                hovertemplate: "BRL %{x}<br>%{y:,} items<extra></extra>",
            }],
            layout: layout({
                margin: { l: 16, r: 16, t: 28, b: 16 },
                xaxis: { type: "category", title: { text: "Price range (BRL)" } },
                yaxis: { title: { text: "Number of items" }, tickformat: "~s" },
            }),
        }),

        "delivery-monthly": (rows) => {
            if (!rows.some((row) => row.value !== null)) {
                return null;
            }

            return {
                data: [{
                    type: "scatter",
                    mode: "lines+markers",
                    x: rows.map((row) => row.period),
                    y: rows.map((row) => row.value),
                    customdata: rows.map((row) => [row.numerator_count, row.denominator_count]),
                    connectgaps: false,
                    line: { color: COLORS.orange, width: 2.5 },
                    marker: { size: 6 },
                    hovertemplate: "%{x}<br>Delay rate: %{y:.1%}<br>%{customdata[0]:,} late of %{customdata[1]:,} eligible orders<extra></extra>",
                }],
                layout: layout({
                    xaxis: { type: "category" },
                    yaxis: { title: { text: "Delay rate" }, tickformat: ".0%", rangemode: "tozero" },
                }),
            };
        },

        "overview-sales": (kpis) => {
            const parts = [
                ["Item value", kpis.item_value_delivered],
                ["Freight charged", kpis.freight_charged_delivered],
            ].filter(([, kpi]) => kpi?.value != null);

            if (!parts.length) {
                return null;
            }

            const unit = parts[0][1].unit;

            return {
                data: [{
                    type: "bar",
                    x: parts.map(([label]) => label),
                    y: parts.map(([, kpi]) => kpi.value),
                    marker: { color: [COLORS.sage, COLORS.sageDark] },
                    hovertemplate: `%{x}<br>%{y:,.2f} ${unit}<extra></extra>`,
                }],
                layout: layout({
                    xaxis: { type: "category" },
                    yaxis: { title: { text: unit }, tickformat: "~s" },
                }),
            };
        },

        "overview-delivery": (kpis) => {
            const { numerator_count: late, denominator_count: eligible } = kpis.delay_rate_calendar ?? {};

            if (!eligible) {
                return null;
            }

            return {
                data: [{
                    type: "pie",
                    hole: 0.6,
                    sort: false,
                    labels: ["Late", "Not late"],
                    values: [late, eligible - late],
                    marker: { colors: [COLORS.orange, COLORS.sage] },
                    textinfo: "percent",
                    textposition: "outside",
                    hovertemplate: "%{label}: %{value:,} orders<extra></extra>",
                }],
                layout: layout({
                    margin: { l: 16, r: 16, t: 24, b: 48 },
                    showlegend: true,
                    legend: { orientation: "h", x: 0.5, xanchor: "center", y: -0.05 },
                }),
            };
        },
    };

    function showMessage(element, text) {
        const message = document.createElement("div");
        message.className = "chart-message";
        message.textContent = text;

        element.removeAttribute("role");
        element.removeAttribute("aria-label");
        element.replaceChildren(message);
    }

    async function render(element, Plotly) {
        try {
            const payload = JSON.parse(element.dataset.payload);
            const figure = renderers[element.dataset.chart]?.(payload);

            if (!figure) {
                showMessage(element, "No plottable data is available for this chart.");
                return;
            }

            await Plotly.newPlot(element, figure.data, figure.layout, CONFIG);
        } catch {
            showMessage(element, "This chart could not be displayed.");
        }
    }

    function loadPlotly() {
        if (window.Plotly) {
            return Promise.resolve(window.Plotly);
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = PLOTLY_SRC;
            script.onload = () => resolve(window.Plotly);
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    const chartElements = document.querySelectorAll("[data-chart]");

    if (chartElements.length) {
        loadPlotly()
            .then((Plotly) => chartElements.forEach((element) => render(element, Plotly)))
            .catch(() => chartElements.forEach((element) => showMessage(
                element,
                "Charts could not be loaded. Check your connection and reload the page.",
            )));
    }
})();
