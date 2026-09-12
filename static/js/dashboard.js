document.addEventListener("DOMContentLoaded", () => {

    const formatCurrency = (value) => {
        const amount = Number(value || 0);

        if (amount >= 10000000) {
            return `₹${(amount / 10000000).toFixed(2)}Cr`;
        }

        if (amount >= 100000) {
            return `₹${(amount / 100000).toFixed(2)}L`;
        }

        if (amount >= 1000) {
            return `₹${(amount / 1000).toFixed(2)}K`;
        }

        return `₹${amount.toFixed(2)}`;
    };


    const loadDashboard = async () => {

        try {

            const response =
                await fetch("/api/dashboard");

            if (!response.ok) {
                throw new Error(
                    `Dashboard API returned ${response.status}`
                );
            }

            const result =
                await response.json();

            if (!result.success) {
                throw new Error(
                    result.error ||
                    "Dashboard API failed."
                );
            }

            const data = result.data || {};
            const kpis = data.kpis || {};
            const funnel = data.funnel || {};

            const kpiValues =
                document.querySelectorAll(".kpi-value");

            if (kpiValues.length >= 4) {

                kpiValues[0].textContent =
                    formatCurrency(
                        kpis.revenue_at_risk
                    );

                kpiValues[1].textContent =
                    formatCurrency(
                        kpis.expected_recovery
                    );

                kpiValues[2].textContent =
                    formatCurrency(
                        kpis.recovered_revenue
                    );

                kpiValues[3].textContent =
                    `${Number(
                        kpis.recovery_rate || 0
                    ).toFixed(1)}%`;
            }


            const funnelStages =
                document.querySelectorAll(
                    ".funnel-stage strong"
                );

            if (funnelStages.length >= 5) {

                funnelStages[0].textContent =
                    Number(
                        funnel.failed_payments || 0
                    ).toLocaleString();

                funnelStages[1].textContent =
                    formatCurrency(
                        funnel.revenue_at_risk
                    );

                funnelStages[2].textContent =
                    Number(
                        funnel.ai_eligible || 0
                    ).toLocaleString();

                funnelStages[3].textContent =
                    Number(
                        funnel.recovery_actions || 0
                    ).toLocaleString();

                funnelStages[4].textContent =
                    Number(
                        funnel.successfully_recovered || 0
                    ).toLocaleString();
            }


            updateFailureReasons(
                data.failure_reasons || []
            );

            updateRecentDecisions(
                data.recent_decisions || []
            );

        } catch (error) {

            console.error(
                "Dashboard loading failed:",
                error
            );
        }
    };


    const updateFailureReasons = (items) => {

        const rows =
            document.querySelectorAll(
                ".failure-row"
            );

        rows.forEach((row, index) => {

            const item = items[index];

            if (!item) {
                row.style.display = "none";
                return;
            }

            row.style.display = "";

            const spans =
                row.querySelectorAll("span");

            const amount =
                row.querySelector("strong");

            if (spans.length >= 2) {

                spans[1].textContent =
                    Number(
                        item.volume || 0
                    ).toLocaleString();
            }

            if (amount) {

                amount.textContent =
                    formatCurrency(
                        item.revenue_at_risk
                    );
            }

            const name =
                spans[0];

            if (name) {

                const icon =
                    name.querySelector("i");

                name.textContent = "";

                if (icon) {
                    name.appendChild(icon);
                }

                name.append(
                    ` ${item.reason}`
                );
            }
        });
    };


    const updateRecentDecisions = (items) => {

        const rows =
            document.querySelectorAll(
                ".decision-row"
            );

        rows.forEach((row, index) => {

            const item = items[index];

            if (!item) {
                row.style.display = "none";
                return;
            }

            row.style.display = "";

            const strong =
                row.querySelector("strong");

            const spans =
                row.querySelectorAll("span");

            const status =
                row.querySelector(
                    ".decision-status"
                );

            const score =
                row.querySelector(
                    ".decision-score"
                );

            if (strong) {
                strong.textContent =
                    item.transaction_id;
            }

            if (spans.length > 1) {

                spans[0].textContent =
                    `${formatCurrency(
                        item.amount
                    )} · ${item.failure_reason}`;
            }

            if (status) {

                const state =
                    String(
                        item.status || ""
                    ).toUpperCase();

                if (state === "APPROVED") {

                    status.textContent =
                        "RECOVERABLE";

                } else if (
                    state === "ESCALATED"
                ) {

                    status.textContent =
                        "ESCALATE";

                } else {

                    status.textContent =
                        "STOP";
                }
            }

            if (score) {

                score.textContent =
                    `${Number(
                        item.recovery_probability || 0
                    ).toFixed(0)}%`;
            }
        });
    };


    /* =========================================
       DYNAMIC REVENUE TREND
    ========================================= */

    const loadTrend = async (metric) => {

        try {

            const response =
                await fetch(
                    `/api/dashboard/trend?metric=${encodeURIComponent(metric)}`
                );

            if (!response.ok) {
                throw new Error(
                    `Trend API returned ${response.status}`
                );
            }

            const result =
                await response.json();

            if (!result.success) {
                throw new Error(
                    result.error ||
                    "Trend API failed."
                );
            }

            renderTrend(
                result.data || [],
                metric
            );

        } catch (error) {

            console.error(
                "Trend loading failed:",
                error
            );
        }
    };


    const renderTrend = (items, metric) => {

        const svg =
            document.querySelector(
                ".revenue-chart"
            );

        if (!svg) {
            return;
        }

        const oldDynamic =
            svg.querySelector(
                ".dynamic-trend"
            );

        if (oldDynamic) {
            oldDynamic.remove();
        }

        if (!items.length) {
            return;
        }

        const width =
            svg.viewBox.baseVal.width || 800;

        const height =
            svg.viewBox.baseVal.height || 300;

        const paddingX = 45;
        const paddingY = 35;

        const values =
            items.map(
                item => Number(item.value || 0)
            );

        const maxValue =
            Math.max(...values, 1);

        const minValue =
            Math.min(...values, 0);

        const range =
            Math.max(
                maxValue - minValue,
                1
            );

        const points =
            values.map((value, index) => {

                const x =
                    paddingX +
                    (
                        index /
                        Math.max(
                            items.length - 1,
                            1
                        )
                    ) *
                    (
                        width -
                        paddingX * 2
                    );

                const y =
                    height -
                    paddingY -
                    (
                        (value - minValue) /
                        range
                    ) *
                    (
                        height -
                        paddingY * 2
                    );

                return `${x},${y}`;
            });


        const namespace =
            "http://www.w3.org/2000/svg";

        const group =
            document.createElementNS(
                namespace,
                "g"
            );

        group.setAttribute(
            "class",
            "dynamic-trend"
        );


        const line =
            document.createElementNS(
                namespace,
                "polyline"
            );

        line.setAttribute(
            "points",
            points.join(" ")
        );

        line.setAttribute(
            "fill",
            "none"
        );

        line.setAttribute(
            "stroke",
            "currentColor"
        );

        line.setAttribute(
            "stroke-width",
            "3"
        );

        line.setAttribute(
            "stroke-linecap",
            "round"
        );

        line.setAttribute(
            "stroke-linejoin",
            "round"
        );

        group.appendChild(line);


        items.forEach((item, index) => {

            const value =
                Number(item.value || 0);

            const x =
                paddingX +
                (
                    index /
                    Math.max(
                        items.length - 1,
                        1
                    )
                ) *
                (
                    width -
                    paddingX * 2
                );

            const y =
                height -
                paddingY -
                (
                    (value - minValue) /
                    range
                ) *
                (
                    height -
                    paddingY * 2
                );

            const circle =
                document.createElementNS(
                    namespace,
                    "circle"
                );

            circle.setAttribute(
                "cx",
                x
            );

            circle.setAttribute(
                "cy",
                y
            );

            circle.setAttribute(
                "r",
                "4"
            );

            circle.setAttribute(
                "fill",
                "currentColor"
            );

            group.appendChild(circle);
        });


        svg.appendChild(group);


        const selector =
            document.querySelector(
                ".chart-selector"
            );

        if (selector) {

            selector.setAttribute(
                "aria-label",
                `Showing ${metric} trend`
            );
        }
    };


    const chartSelector =
        document.querySelector(
            ".chart-selector"
        );

    if (chartSelector) {

        chartSelector.addEventListener(
            "change",
            event => {

                loadTrend(
                    event.target.value
                );
            }
        );

        loadTrend(
            chartSelector.value || "risk"
        );

    } else {

        loadTrend("risk");
    }


    const recommendationButton =
        document.querySelector(
            ".recommendation-button"
        );

    if (recommendationButton) {

        recommendationButton.addEventListener(
            "click",
            () => {

                window.location.href =
                    "/ai-decisions";
            }
        );
    }


    loadDashboard();

    setInterval(
        loadDashboard,
        30000
    );

    setInterval(
        () => {

            const metric =
                chartSelector
                    ? chartSelector.value || "risk"
                    : "risk";

            loadTrend(metric);

        },
        30000
    );

});
