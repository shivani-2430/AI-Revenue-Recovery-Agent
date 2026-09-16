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

            updateAIInsight(
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


    const updateAIInsight = (failureReasons) => {

        const heading =
            document.querySelector(
                "#ai-insight-heading"
            );

        const description =
            document.querySelector(
                "#ai-insight-description"
            );

        if (!heading || !description) {
            return;
        }

        if (
            !failureReasons ||
            !failureReasons.length
        ) {
            heading.textContent =
                "No failure pattern detected yet.";

            description.textContent =
                "AI insight will appear when failure data is available.";

            return;
        }

        const topReason =
            [...failureReasons].sort(
                (a, b) =>
                    Number(
                        b.revenue_at_risk || 0
                    ) -
                    Number(
                        a.revenue_at_risk || 0
                    )
            )[0];

        const totalVolume =
            failureReasons.reduce(
                (total, item) =>
                    total +
                    Number(
                        item.volume || 0
                    ),
                0
            );

        const volume =
            Number(
                topReason.volume || 0
            );

        const revenueAtRisk =
            Number(
                topReason.revenue_at_risk || 0
            );

        const failureShare =
            totalVolume > 0
                ? (
                    volume /
                    totalVolume
                ) * 100
                : 0;

        const reasonName =
            String(
                topReason.reason ||
                "Unknown"
            ).replaceAll(
                "_",
                " "
            );

        heading.textContent =
            `${reasonName} shows the highest revenue at risk.`;

        description.textContent =
            `${volume.toLocaleString(
                "en-IN"
            )} recorded failures account for approximately ` +
            `${failureShare.toFixed(1)}% of the displayed failure volume, ` +
            `with ${formatCurrency(
                revenueAtRisk
            )} at risk. Prioritize recovery actions for this segment.`;
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

                if (state === "EXECUTED") {

                    status.textContent =
                        "RECOVERED";

                } else if (state === "APPROVED") {

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
                ".trend-svg"
            );

        const labelsContainer =
            document.querySelector(
                ".chart-labels"
            );

        const tooltip =
            document.querySelector(
                ".chart-tooltip"
            );

        const yAxis =
            document.querySelector(
                ".y-axis"
            );

        if (!svg) {
            return;
        }

        svg.innerHTML = "";

        if (labelsContainer) {
            labelsContainer.innerHTML = "";
        }

        if (tooltip) {
            tooltip.innerHTML = "";
        }

        if (yAxis) {
            yAxis.innerHTML = "";
        }

        if (!items || !items.length) {
            return;
        }

        const width =
            svg.viewBox.baseVal.width || 700;

        const height =
            svg.viewBox.baseVal.height || 230;

        const paddingX = 35;
        const paddingY = 25;

        const values =
            items.map(
                item => Number(item.value || 0)
            );

        const maxValue =
            Math.max(...values, 1);

        const chartMax =
            maxValue * 1.15;

        const points =
            values.map((value, index) => {

                const x =
                    items.length === 1
                        ? width / 2
                        : paddingX +
                          (
                              index /
                              (items.length - 1)
                          ) *
                          (
                              width -
                              paddingX * 2
                          );

                const y =
                    height -
                    paddingY -
                    (
                        value /
                        chartMax
                    ) *
                    (
                        height -
                        paddingY * 2
                    );

                return {
                    x,
                    y,
                    value
                };
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


        const areaPoints = [
            `${points[0].x},${height - paddingY}`,
            ...points.map(
                point =>
                    `${point.x},${point.y}`
            ),
            `${points[points.length - 1].x},${height - paddingY}`
        ];

        const area =
            document.createElementNS(
                namespace,
                "polygon"
            );

        area.setAttribute(
            "points",
            areaPoints.join(" ")
        );

        area.setAttribute(
            "fill",
            "currentColor"
        );

        area.setAttribute(
            "opacity",
            "0.08"
        );

        group.appendChild(area);


        const line =
            document.createElementNS(
                namespace,
                "polyline"
            );

        line.setAttribute(
            "points",
            points
                .map(
                    point =>
                        `${point.x},${point.y}`
                )
                .join(" ")
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


        points.forEach(
            (point, index) => {

                const circle =
                    document.createElementNS(
                        namespace,
                        "circle"
                    );

                circle.setAttribute(
                    "cx",
                    point.x
                );

                circle.setAttribute(
                    "cy",
                    point.y
                );

                circle.setAttribute(
                    "r",
                    "4"
                );

                circle.setAttribute(
                    "fill",
                    "currentColor"
                );

                circle.style.cursor =
                    "pointer";

                circle.addEventListener(
                    "mouseenter",
                    () => {

                        if (!tooltip) {
                            return;
                        }

                        const date =
                            new Date(
                                items[index].date
                            );

                        const formattedDate =
                            date.toLocaleDateString(
                                "en-IN",
                                {
                                    day: "numeric",
                                    month: "short",
                                    year: "numeric"
                                }
                            );

                        tooltip.innerHTML = `
                            <strong>
                                ₹${Number(
                                    point.value
                                ).toLocaleString(
                                    "en-IN",
                                    {
                                        maximumFractionDigits: 2
                                    }
                                )}
                            </strong>
                            <span>
                                ${formattedDate}
                            </span>
                        `;

                        tooltip.style.opacity =
                            "1";
                    }
                );

                circle.addEventListener(
                    "mouseleave",
                    () => {

                        if (tooltip) {
                            tooltip.style.opacity =
                                "0";
                        }
                    }
                );

                group.appendChild(circle);
            }
        );


        svg.appendChild(group);


        if (labelsContainer) {

            const labelCount =
                Math.min(
                    items.length,
                    7
                );

            const step =
                items.length <= 7
                    ? 1
                    : Math.ceil(
                        (items.length - 1) /
                        (labelCount - 1)
                    );

            const indexes = [];

            for (
                let i = 0;
                i < items.length;
                i += step
            ) {
                indexes.push(i);
            }

            if (
                indexes[
                    indexes.length - 1
                ] !== items.length - 1
            ) {
                indexes.push(
                    items.length - 1
                );
            }

            indexes.forEach(
                index => {

                    const date =
                        new Date(
                            items[index].date
                        );

                    const label =
                        document.createElement(
                            "span"
                        );

                    label.textContent =
                        date.toLocaleDateString(
                            "en-IN",
                            {
                                day: "numeric",
                                month: "short"
                            }
                        );

                    labelsContainer.appendChild(
                        label
                    );
                }
            );
        }


        if (yAxis) {

            const axisSteps = 5;

            for (
                let i = axisSteps;
                i >= 0;
                i--
            ) {

                const label =
                    document.createElement(
                        "span"
                    );

                const value =
                    (chartMax / axisSteps) *
                    i;

                if (value >= 100000) {

                    label.textContent =
                        `₹${(
                            value / 100000
                        ).toFixed(1)}L`;

                } else if (
                    value >= 1000
                ) {

                    label.textContent =
                        `₹${(
                            value / 1000
                        ).toFixed(1)}K`;

                } else {

                    label.textContent =
                        `₹${Math.round(
                            value
                        )}`;
                }

                yAxis.appendChild(
                    label
                );
            }
        }


        if (
            tooltip &&
            items.length
        ) {

            const latest =
                items[
                    items.length - 1
                ];

            const latestDate =
                new Date(
                    latest.date
                );

            tooltip.innerHTML = `
                <strong>
                    ₹${Number(
                        latest.value || 0
                    ).toLocaleString(
                        "en-IN",
                        {
                            maximumFractionDigits: 2
                        }
                    )}
                </strong>
                <span>
                    ${latestDate.toLocaleDateString(
                        "en-IN",
                        {
                            day: "numeric",
                            month: "short",
                            year: "numeric"
                        }
                    )}
                </span>
            `;

            tooltip.style.opacity =
                "1";
        }


        svg.setAttribute(
            "aria-label",
            `${metric} revenue trend`
        );
    };


    /* =========================================
       REVENUE TREND SELECTOR
    ========================================= */

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


    /* =========================================
       DASHBOARD NAVIGATION
    ========================================= */

    const viewDetailsButtons =
        document.querySelectorAll(
            ".view-details"
        );


    if (viewDetailsButtons.length >= 3) {

        /* Payment Recovery Funnel */

        viewDetailsButtons[0].addEventListener(
            "click",
            () => {

                window.location.href =
                    "/recovery-queue";
            }
        );


        /* Top Failure Reasons */

        viewDetailsButtons[1].addEventListener(
            "click",
            () => {

                window.location.href =
                    "/transactions";
            }
        );


        /* Recent AI Recovery Decisions */

        viewDetailsButtons[2].addEventListener(
            "click",
            () => {

                window.location.href =
                    "/ai-decisions";
            }
        );
    }


    /* =========================================
       AI RECOMMENDATION
    ========================================= */

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