document.addEventListener("DOMContentLoaded", () => {

    const state = {
        page: 1,
        perPage: 10,
        priority: "",
        status: "",
        failureReason: "",
        paymentMethod: "",
        search: "",
        sort: "opportunity"
    };


    const elements = {

        eligible:
            document.getElementById(
                "eligibleOpportunities"
            ),

        revenueAtRisk:
            document.getElementById(
                "revenueAtRisk"
            ),

        expectedRecovery:
            document.getElementById(
                "expectedRecovery"
            ),

        highPriority:
            document.getElementById(
                "highPriority"
            ),

        recoveryPotential:
            document.getElementById(
                "recoveryPotential"
            ),

        aiFocus:
            document.getElementById(
                "aiFocus"
            ),

        strategyFocus:
            document.getElementById(
                "strategyFocus"
            ),

        strategyCount:
            document.getElementById(
                "strategyOpportunityCount"
            ),

        strategyRecovery:
            document.getElementById(
                "strategyRecovery"
            ),

        table:
            document.getElementById(
                "opportunityTable"
            ),

        tableEmpty:
            document.getElementById(
                "tableEmpty"
            ),

        search:
            document.getElementById(
                "queueSearch"
            ),

        status:
            document.getElementById(
                "statusFilter"
            ),

        failure:
            document.getElementById(
                "failureFilter"
            ),

        currentPage:
            document.getElementById(
                "currentPage"
            ),

        paginationInfo:
            document.getElementById(
                "paginationInfo"
            ),

        previous:
            document.getElementById(
                "previousPage"
            ),

        next:
            document.getElementById(
                "nextPage"
            ),

        drivers:
            document.getElementById(
                "failureDrivers"
            ),

        paymentMethods:
            document.getElementById(
                "paymentMethods"
            ),

        allCount:
            document.getElementById(
                "allCount"
            ),

        highCount:
            document.getElementById(
                "highCount"
            ),

        mediumCount:
            document.getElementById(
                "mediumCount"
            ),

        lowCount:
            document.getElementById(
                "lowCount"
            ),

        sort:
            document.getElementById(
                "sortSelect"
            ),

        refresh:
            document.getElementById(
                "refreshQueue"
            )
    };


    // ========================================================
    // HTML ESCAPING
    // ========================================================

    function escapeHtml(value) {

        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }


    // ========================================================
    // LOAD QUEUE
    // ========================================================

    async function loadQueue() {

        showLoading();

        const params =
            new URLSearchParams();

        params.set(
            "page",
            state.page
        );

        params.set(
            "per_page",
            state.perPage
        );

        params.set(
            "sort",
            state.sort
        );


        if (state.search) {

            params.set(
                "search",
                state.search
            );
        }


        if (state.priority) {

            params.set(
                "priority",
                state.priority
            );
        }


        if (state.status) {

            params.set(
                "status",
                state.status
            );
        }


        if (state.failureReason) {

            params.set(
                "failure_reason",
                state.failureReason
            );
        }


        if (state.paymentMethod) {

            params.set(
                "payment_method",
                state.paymentMethod
            );
        }


        try {

            const response =
                await fetch(
                    `/api/recovery-queue?${params.toString()}`,
                    {
                        method: "GET",
                        headers: {
                            "Accept":
                                "application/json"
                        }
                    }
                );


            const payload =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    payload.error ||
                    "Recovery Queue API request failed."
                );
            }


            if (!payload.success) {

                throw new Error(
                    payload.error ||
                    "Recovery Queue returned an unsuccessful response."
                );
            }


            renderQueue(
                payload.data
            );


        } catch (error) {

            console.error(
                "Recovery Queue error:",
                error
            );

            renderError(
                error.message
            );
        }
    }


    // ========================================================
    // LOADING
    // ========================================================

    function showLoading() {

        if (!elements.table) {
            return;
        }

        elements.tableEmpty.hidden =
            true;

        elements.table.innerHTML = `
            <tr>
                <td colspan="10">
                    <div class="queue-loading">

                        <i class="fa-solid fa-circle-notch fa-spin"></i>

                        <div>
                            Loading recovery opportunities...
                        </div>

                    </div>
                </td>
            </tr>
        `;
    }


    // ========================================================
    // RENDER COMPLETE QUEUE
    // ========================================================

    function renderQueue(data) {

        if (!data) {

            throw new Error(
                "Recovery Queue returned no data."
            );
        }


        renderSummary(
            data.summary || {}
        );


        renderOpportunities(
            data.opportunities || []
        );


        renderDrivers(
            data.drivers || []
        );


        renderPaymentMethods(
            data.payment_methods || []
        );


        renderStrategy(
            data.ai_strategy || {}
        );


        renderPagination(
            data.pagination || {}
        );
    }


    // ========================================================
    // SUMMARY
    // ========================================================

    function renderSummary(summary) {

        elements.eligible.textContent =
            summary.eligible_opportunities_label
            ?? "0";


        elements.revenueAtRisk.textContent =
            summary.revenue_at_risk_label
            ?? "₹0";


        elements.expectedRecovery.textContent =
            summary.expected_recovery_label
            ?? "₹0";


        elements.highPriority.textContent =
            summary.high_priority_label
            ?? "0";


        elements.recoveryPotential.textContent =
            `${summary.recovery_potential ?? 0}%`;


        elements.aiFocus.textContent =
            summary.high_priority > 0

                ? `${summary.high_priority_label} high-priority opportunities require the strongest recovery attention.`

                : "No high-priority recovery opportunities currently require immediate action.";


        elements.allCount.textContent =
            summary.eligible_opportunities_label
            ?? "0";


        elements.highCount.textContent =
            summary.high_priority_label
            ?? "0";


        elements.mediumCount.textContent =
            summary.medium_priority_label
            ?? "0";


        elements.lowCount.textContent =
            summary.low_priority_label
            ?? "0";
    }


    // ========================================================
    // OPPORTUNITY TABLE
    // ========================================================

    function renderOpportunities(
        opportunities
    ) {

        if (
            !Array.isArray(
                opportunities
            ) ||
            opportunities.length === 0
        ) {

            elements.table.innerHTML =
                "";

            elements.tableEmpty.hidden =
                false;

            return;
        }


        elements.tableEmpty.hidden =
            true;


        elements.table.innerHTML =
            opportunities
                .map(
                    opportunityRow
                )
                .join("");
    }


    // ========================================================
    // TABLE ROW
    // ========================================================

    function opportunityRow(
        item
    ) {

        const probability =
            Number(
                item.recovery_probability
            ) || 0;


        const priorityClass =
            String(
                item.priority || "LOW"
            )
            .toLowerCase();


        const statusClass =
            `status-${String(
                item.status || "STOPPED"
            ).toLowerCase()}`;


        const guardrailClass =
            `guardrail-${String(
                item.guardrail || "BLOCKED"
            ).toLowerCase()}`;


        return `
            <tr>

                <td>

                    <span
                        class="priority-badge ${priorityClass}"
                    >
                        ${escapeHtml(
                            item.priority
                        )}
                    </span>

                </td>


                <td>

                    <a
                        class="transaction-link"
                        href="/transactions/${encodeURIComponent(
                            item.transaction_id
                        )}"
                    >
                        ${escapeHtml(
                            item.transaction_id
                        )}
                    </a>

                </td>


                <td>

                    <span class="customer-id">
                        ${escapeHtml(
                            item.customer_label
                        )}
                    </span>

                    <span class="customer-segment">
                        ${escapeHtml(
                            item.customer_segment
                        )}
                    </span>

                </td>


                <td>

                    <span class="amount-cell">
                        ${escapeHtml(
                            item.amount_label
                        )}
                    </span>

                </td>


                <td>

                    <span class="failure-cell">
                        ${escapeHtml(
                            item.failure_reason
                        )}
                    </span>

                </td>


                <td class="recovery-cell">

                    <div class="recovery-number">

                        <span>
                            ${probability.toFixed(1)}%
                        </span>

                    </div>


                    <div class="progress-track">

                        <div
                            class="progress-fill"
                            style="width:${probability}%"
                        ></div>

                    </div>

                </td>


                <td>

                    <span class="action-cell">
                        ${escapeHtml(
                            item.recommended_action
                        )}
                    </span>

                </td>


                <td>

                    <span
                        class="guardrail-badge ${guardrailClass}"
                    >
                        ${escapeHtml(
                            item.guardrail
                        )}
                    </span>

                </td>


                <td>

                    <span
                        class="status-badge ${statusClass}"
                    >
                        ${escapeHtml(
                            item.status
                        )}
                    </span>

                </td>


                <td>

                    <button
                        class="row-action"
                        type="button"
                        title="Open transaction"
                        data-transaction-id="${escapeHtml(
                            item.transaction_id
                        )}"
                    >
                        <i
                            class="fa-solid fa-arrow-right"
                        ></i>
                    </button>

                </td>

            </tr>
        `;
    }


    // ========================================================
    // FAILURE DRIVERS
    // ========================================================

    function renderDrivers(
        drivers
    ) {

        if (
            !Array.isArray(drivers)
            || drivers.length === 0
        ) {

            elements.drivers.innerHTML = `
                <p class="empty-message">
                    No recovery driver data available.
                </p>
            `;

            return;
        }


        elements.drivers.innerHTML =
            drivers
                .map(
                    driver => {

                        const share =
                            Number(
                                driver.share
                            ) || 0;


                        return `
                            <div class="driver-item">

                                <div class="driver-top">

                                    <span>
                                        ${escapeHtml(
                                            driver.name
                                        )}
                                    </span>

                                    <span>
                                        ${share.toFixed(1)}%
                                    </span>

                                </div>


                                <div class="driver-bar">

                                    <span
                                        style="width:${share}%"
                                    ></span>

                                </div>

                            </div>
                        `;
                    }
                )
                .join("");
    }


    // ========================================================
    // PAYMENT METHODS
    // ========================================================

    function renderPaymentMethods(
        methods
    ) {

        if (
            !Array.isArray(methods)
            || methods.length === 0
        ) {

            elements.paymentMethods.innerHTML = `
                <p class="empty-message">
                    No payment method data available.
                </p>
            `;

            return;
        }


        elements.paymentMethods.innerHTML =
            methods
                .map(
                    method => {

                        const share =
                            Number(
                                method.share
                            ) || 0;


                        return `
                            <div class="payment-item">

                                <span class="payment-dot"></span>

                                <span class="payment-name">
                                    ${escapeHtml(
                                        method.name
                                    )}
                                </span>

                                <span class="payment-share">
                                    ${share.toFixed(1)}%
                                </span>

                            </div>
                        `;
                    }
                )
                .join("");
    }


    // ========================================================
    // AI STRATEGY
    // ========================================================

    function renderStrategy(
        strategy
    ) {

        elements.strategyFocus.textContent =
            strategy.focus ||
            "No recovery strategy is currently available.";


        elements.strategyCount.textContent =
            strategy.opportunity_count
            ?? 0;


        elements.strategyRecovery.textContent =
            strategy.expected_recovery_label
            ?? "₹0";
    }


    // ========================================================
    // PAGINATION
    // ========================================================

    function renderPagination(
        pagination
    ) {

        const total =
            Number(
                pagination.total
            ) || 0;


        const page =
            Number(
                pagination.page
            ) || 1;


        const perPage =
            Number(
                pagination.per_page
            ) || state.perPage;


        const totalPages =
            Number(
                pagination.total_pages
            ) || 1;


        const start =
            total === 0
                ? 0
                : (
                    (page - 1)
                    * perPage
                ) + 1;


        const end =
            Math.min(
                page * perPage,
                total
            );


        elements.paginationInfo.textContent =
            `Showing ${start}-${end} of ${total} opportunities`;


        elements.currentPage.textContent =
            page;


        elements.previous.disabled =
            page <= 1;


        elements.next.disabled =
            page >= totalPages;
    }


    // ========================================================
    // FAILURE FILTER OPTIONS
    // ========================================================

    function updateFailureFilters(
        drivers
    ) {

        const current =
            state.failureReason;


        elements.failure.innerHTML = `
            <option value="">
                All Failure Reasons
            </option>
        `;


        drivers.forEach(
            driver => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    driver.name;


                option.textContent =
                    driver.name;


                if (
                    driver.name
                    === current
                ) {

                    option.selected =
                        true;
                }


                elements.failure.appendChild(
                    option
                );
            }
        );
    }


    // ========================================================
    // ERROR
    // ========================================================

    function renderError(
        message
    ) {

        elements.tableEmpty.hidden =
            true;


        elements.table.innerHTML = `
            <tr>

                <td colspan="10">

                    <div class="queue-loading">

                        <i
                            class="fa-solid fa-triangle-exclamation"
                        ></i>

                        <div
                            style="margin-top:10px;"
                        >
                            Unable to load recovery opportunities.
                        </div>

                        <small
                            style="
                                display:block;
                                margin-top:7px;
                                color:#98A2B3;
                            "
                        >
                            ${escapeHtml(
                                message
                            )}
                        </small>

                    </div>

                </td>

            </tr>
        `;
    }


    // ========================================================
    // PRIORITY TABS
    // ========================================================

    document
        .querySelectorAll(
            ".queue-tab"
        )
        .forEach(
            tab => {

                tab.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".queue-tab"
                            )
                            .forEach(
                                item => {
                                    item.classList.remove(
                                        "active"
                                    );
                                }
                            );


                        tab.classList.add(
                            "active"
                        );


                        state.priority =
                            tab.dataset.priority
                            || "";


                        state.page =
                            1;


                        loadQueue();
                    }
                );
            }
        );


    // ========================================================
    // SEARCH
    // ========================================================

    let searchTimer = null;


    elements.search.addEventListener(
        "input",
        event => {

            clearTimeout(
                searchTimer
            );


            searchTimer =
                setTimeout(
                    () => {

                        state.search =
                            event.target.value
                                .trim();


                        state.page =
                            1;


                        loadQueue();

                    },
                    350
                );
        }
    );


    // ========================================================
    // STATUS FILTER
    // ========================================================

    elements.status.addEventListener(
        "change",
        event => {

            state.status =
                event.target.value;


            state.page =
                1;


            loadQueue();
        }
    );


    // ========================================================
    // FAILURE FILTER
    // ========================================================

    elements.failure.addEventListener(
        "change",
        event => {

            state.failureReason =
                event.target.value;


            state.page =
                1;


            loadQueue();
        }
    );


    // ========================================================
    // SORT
    // ========================================================

    if (elements.sort) {

        elements.sort.addEventListener(
            "change",
            event => {

                state.sort =
                    event.target.value;


                state.page =
                    1;


                loadQueue();
            }
        );
    }


    // ========================================================
    // CLEAR FILTERS
    // ========================================================

    document
        .getElementById(
            "clearFilters"
        )
        .addEventListener(
            "click",
            () => {

                state.search =
                    "";

                state.priority =
                    "";

                state.status =
                    "";

                state.failureReason =
                    "";

                state.paymentMethod =
                    "";

                state.page =
                    1;


                elements.search.value =
                    "";

                elements.status.value =
                    "";

                elements.failure.value =
                    "";


                document
                    .querySelectorAll(
                        ".queue-tab"
                    )
                    .forEach(
                        tab => {

                            tab.classList.remove(
                                "active"
                            );
                        }
                    );


                document
                    .querySelector(
                        '.queue-tab[data-priority=""]'
                    )
                    ?.classList.add(
                        "active"
                    );


                loadQueue();
            }
        );


    // ========================================================
    // PAGINATION
    // ========================================================

    elements.previous.addEventListener(
        "click",
        () => {

            if (
                state.page > 1
            ) {

                state.page--;

                loadQueue();
            }
        }
    );


    elements.next.addEventListener(
        "click",
        () => {

            state.page++;

            loadQueue();
        }
    );


    // ========================================================
    // REFRESH
    // ========================================================

    if (elements.refresh) {

        elements.refresh.addEventListener(
            "click",
            () => {

                loadQueue();
            }
        );
    }


    // ========================================================
    // ROW ACTION
    // ========================================================

    elements.table.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".row-action"
                );


            if (!button) {
                return;
            }


            const transactionId =
                button.dataset.transactionId;


            if (!transactionId) {
                return;
            }


            window.location.href =
                `/transactions/${encodeURIComponent(
                    transactionId
                )}`;
        }
    );


    // ========================================================
    // INITIAL LOAD
    // ========================================================

    console.log(
        "Recovery Queue initialized"
    );


    loadQueue();

});