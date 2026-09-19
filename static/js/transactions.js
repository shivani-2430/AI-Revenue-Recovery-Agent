document.addEventListener(
    "DOMContentLoaded",
    () => {

        const searchInput =
            document.getElementById(
                "transactionSearch"
            );

        const statusFilter =
            document.getElementById(
                "statusFilter"
            );

        const failureFilter =
            document.getElementById(
                "failureFilter"
            );

        const methodFilter =
            document.getElementById(
                "methodFilter"
            );

        const clearFilters =
            document.getElementById(
                "clearFilters"
            );

        const tableBody =
            document.getElementById(
                "transactionTableBody"
            );

        const emptyState =
            document.getElementById(
                "emptyTransactions"
            );

        const transactionCount =
            document.getElementById(
                "transactionCount"
            );

        const paginationButtons =
            document.querySelectorAll(
                ".pagination-button"
            );

        let currentPage = 1;

        const perPage = 10;


        // =====================================================
        // LOAD TRANSACTIONS
        // =====================================================

        async function loadTransactions() {

            try {

                const params =
                    new URLSearchParams(
                        {
                            search:
                                searchInput
                                    ? searchInput.value.trim()
                                    : "",

                            status:
                                statusFilter
                                    ? statusFilter.value
                                    : "all",

                            failure:
                                failureFilter
                                    ? failureFilter.value
                                    : "all",

                            method:
                                methodFilter
                                    ? methodFilter.value
                                    : "all",

                            page:
                                currentPage,

                            per_page:
                                perPage,
                        }
                    );


                const response =
                    await fetch(
                        `/api/transactions?${params.toString()}`
                    );


                if (!response.ok) {

                    throw new Error(
                        "Failed to load transactions"
                    );

                }


                const result =
                    await response.json();


                if (
                    !result.success
                ) {

                    throw new Error(
                        "Transaction data unavailable"
                    );

                }


                renderTransactions(
                    result.data || []
                );


                updatePagination(
                    result.pagination
                );


            } catch (error) {

                console.error(
                    "Transaction loading error:",
                    error
                );

                tableBody.innerHTML = "";

                emptyState.style.display =
                    "flex";

                transactionCount.textContent =
                    "Unable to load transactions";

            }

        }


        // =====================================================
        // RENDER TRANSACTIONS
        // =====================================================

        function renderTransactions(
            transactions
        ) {

            tableBody.innerHTML = "";


            if (
                !transactions.length
            ) {

                emptyState.style.display =
                    "flex";

                transactionCount.textContent =
                    "Showing 0 transactions";

                return;

            }


            emptyState.style.display =
                "none";


            transactions.forEach(
                transaction => {

                    const row =
                        document.createElement(
                            "tr"
                        );


                    row.dataset.status =
                        normalizeStatus(
                            transaction.status
                        );

                    row.dataset.failure =
                        normalizeFailure(
                            transaction.failure_reason
                        );

                    row.dataset.method =
                        normalizeMethod(
                            transaction.payment_method
                        );


                    const score =
                        transaction.recovery_probability;


                    const scoreValue =
                        score !== null &&
                        score !== undefined
                            ? `${Number(score).toFixed(0)}%`
                            : "--";


                    const scoreWidth =
                        score !== null &&
                        score !== undefined
                            ? Math.max(
                                0,
                                Math.min(
                                    100,
                                    Number(score)
                                )
                            )
                            : 0;


                    const statusClass =
                        getStatusClass(
                            transaction.status
                        );


                    const initials =
                        getInitials(
                            transaction.customer_id
                        );


                    row.innerHTML = `

                        <td>

                            <div
                                class="transaction-id"
                            >
                                ${escapeHtml(
                                    transaction.transaction_id
                                )}
                            </div>

                            <div
                                class="transaction-time"
                            >
                                ${formatTime(
                                    transaction.timestamp
                                )}
                            </div>

                        </td>


                        <td>

                            <div
                                class="customer-cell"
                            >

                                <div
                                    class="customer-avatar"
                                >
                                    ${escapeHtml(
                                        initials
                                    )}
                                </div>

                                <div>

                                    <strong>
                                        ${escapeHtml(
                                            transaction.customer_id
                                            || "Unknown"
                                        )}
                                    </strong>

                                    <span>
                                        ${escapeHtml(
                                            transaction.customer_id
                                            || "N/A"
                                        )}
                                    </span>

                                </div>

                            </div>

                        </td>


                        <td>

                            <strong
                                class="amount"
                            >
                                ${formatCurrency(
                                    transaction.amount
                                )}
                            </strong>

                        </td>


                        <td>

                            <span
                                class="method-badge"
                            >
                                ${escapeHtml(
                                    formatMethod(
                                        transaction.payment_method
                                    )
                                )}
                            </span>

                        </td>


                        <td>

                            <span
                                class="failure-reason"
                            >
                                ${escapeHtml(
                                    formatFailureReason(
                                        transaction.failure_reason
                                    )
                                )}
                            </span>

                        </td>


                        <td>

                            <div
                                class="
                                    recovery-score
                                    ${
                                        score !== null &&
                                        Number(score) < 35
                                            ? "low"
                                            : ""
                                    }
                                "
                            >

                                <div
                                    class="score-number"
                                >
                                    ${scoreValue}
                                </div>

                                <div
                                    class="score-bar"
                                >

                                    <span
                                        style="
                                            width: ${scoreWidth}%;
                                        "
                                    ></span>

                                </div>

                            </div>

                        </td>


                        <td>

                            <span
                                class="
                                    status-badge
                                    ${statusClass}
                                "
                            >
                                ${escapeHtml(
                                    transaction.status
                                )}
                            </span>

                        </td>


                        <td>

                            <a
                                href="/transactions/${encodeURIComponent(
                                    transaction.transaction_id
                                )}"
                                class="row-action"
                                aria-label="
                                    View transaction
                                "
                            >

                                <i
                                    class="
                                        fa-solid
                                        fa-arrow-right
                                    "
                                ></i>

                            </a>

                        </td>

                    `;


                    tableBody.appendChild(
                        row
                    );

                }
            );


            transactionCount.textContent =
                `Showing ${
                    transactions.length
                } transactions`;

        }


        // =====================================================
        // PAGINATION
        // =====================================================

        function updatePagination(
            pagination
        ) {

            if (
                !pagination
            ) {
                return;
            }


            const previousButton =
                paginationButtons[0];

            const nextButton =
                paginationButtons[1];


            if (
                previousButton
            ) {

                previousButton.disabled =
                    pagination.page <= 1;

            }


            if (
                nextButton
            ) {

                nextButton.disabled =
                    pagination.page >=
                    pagination.total_pages;

            }


            const pageLabel =
                document.querySelector(
                    ".table-pagination span"
                );


            if (
                pageLabel
            ) {

                pageLabel.textContent =
                    `${pagination.page} of ${
                        pagination.total_pages || 1
                    }`;

            }

        }


        if (
            paginationButtons[0]
        ) {

            paginationButtons[0]
                .addEventListener(
                    "click",
                    () => {

                        if (
                            currentPage > 1
                        ) {

                            currentPage -= 1;

                            loadTransactions();

                        }

                    }
                );

        }


        if (
            paginationButtons[1]
        ) {

            paginationButtons[1]
                .addEventListener(
                    "click",
                    () => {

                        currentPage += 1;

                        loadTransactions();

                    }
                );

        }


        // =====================================================
        // FILTER EVENTS
        // =====================================================

        if (
            searchInput
        ) {

            let searchTimer;

            searchInput
                .addEventListener(
                    "input",
                    () => {

                        clearTimeout(
                            searchTimer
                        );


                        searchTimer =
                            setTimeout(
                                () => {

                                    currentPage =
                                        1;

                                    loadTransactions();

                                },
                                300
                            );

                    }
                );

        }


        if (
            statusFilter
        ) {

            statusFilter
                .addEventListener(
                    "change",
                    () => {

                        currentPage =
                            1;

                        loadTransactions();

                    }
                );

        }


        if (
            failureFilter
        ) {

            failureFilter
                .addEventListener(
                    "change",
                    () => {

                        currentPage =
                            1;

                        loadTransactions();

                    }
                );

        }


        if (
            methodFilter
        ) {

            methodFilter
                .addEventListener(
                    "change",
                    () => {

                        currentPage =
                            1;

                        loadTransactions();

                    }
                );

        }


        if (
            clearFilters
        ) {

            clearFilters
                .addEventListener(
                    "click",
                    () => {

                        if (
                            searchInput
                        ) {
                            searchInput.value =
                                "";
                        }


                        if (
                            statusFilter
                        ) {
                            statusFilter.value =
                                "all";
                        }


                        if (
                            failureFilter
                        ) {
                            failureFilter.value =
                                "all";
                        }


                        if (
                            methodFilter
                        ) {
                            methodFilter.value =
                                "all";
                        }


                        currentPage =
                            1;

                        loadTransactions();

                    }
                );

        }


        // =====================================================
        // HELPERS
        // =====================================================

        function formatCurrency(
            amount
        ) {

            return new Intl.NumberFormat(
                "en-IN",
                {
                    style: "currency",
                    currency: "INR",
                    maximumFractionDigits: 0,
                }
            ).format(
                Number(amount || 0)
            );

        }


        function formatTime(
            timestamp
        ) {

            if (
                !timestamp
            ) {
                return "";
            }


            const date =
                new Date(
                    timestamp
                );


            if (
                Number.isNaN(
                    date.getTime()
                )
            ) {

                return "";

            }


            return date.toLocaleString(
                "en-IN",
                {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                }
            );

        }


        function formatMethod(
            method
        ) {

            if (
                !method
            ) {
                return "Unknown";
            }


            const value =
                String(method)
                    .toLowerCase();


            if (
                value.includes("net")
            ) {
                return "Net Banking";
            }


            if (
                value.includes("card")
            ) {
                return "Card";
            }


            if (
                value.includes("upi")
            ) {
                return "UPI";
            }


            if (
                value.includes("wallet")
            ) {
                return "Wallet";
            }


            return method;

        }


        function formatFailureReason(
            reason
        ) {

            if (
                !reason
            ) {
                return "N/A";
            }


            return String(reason)
                .replaceAll(
                    "_",
                    " "
                )
                .replace(
                    /\b\w/g,
                    character =>
                        character.toUpperCase()
                );

        }


        function normalizeStatus(
            status
        ) {

            return String(
                status || ""
            )
                .toLowerCase()
                .replaceAll(
                    " ",
                    "-"
                );

        }


        function normalizeFailure(
            failure
        ) {

            const value =
                String(
                    failure || ""
                ).toLowerCase();


            if (
                value.includes("network")
            ) {
                return "network";
            }


            if (
                value.includes("bank")
            ) {
                return "bank";
            }


            if (
                value.includes("insufficient")
            ) {
                return "funds";
            }


            if (
                value.includes("authentication")
            ) {
                return "auth";
            }


            if (
                value.includes("gateway")
            ) {
                return "gateway";
            }


            return "";

        }


        function normalizeMethod(
            method
        ) {

            const value =
                String(
                    method || ""
                ).toLowerCase();


            if (
                value.includes("upi")
            ) {
                return "upi";
            }


            if (
                value.includes("card")
            ) {
                return "card";
            }


            if (
                value.includes("net")
            ) {
                return "netbanking";
            }


            if (
                value.includes("wallet")
            ) {
                return "wallet";
            }


            return "";

        }


        function getStatusClass(
            status
        ) {

            const value =
                String(
                    status || ""
                ).toLowerCase();


            if (
                value === "recovered"
            ) {
                return "recovered";
            }


            if (
                value === "recoverable"
            ) {
                return "recoverable";
            }


            if (
                value === "escalate"
            ) {
                return "escalate";
            }


            return "stopped";

        }


        function getInitials(
            value
        ) {

            if (
                !value
            ) {
                return "?";
            }


            const parts =
                String(value)
                    .split("_");


            if (
                parts.length > 1
            ) {

                return parts
                    .slice(-1)[0]
                    .slice(0, 2)
                    .toUpperCase();

            }


            return String(value)
                .slice(0, 2)
                .toUpperCase();

        }


        function escapeHtml(
            value
        ) {

            if (
                value === null ||
                value === undefined
            ) {

                return "";

            }


            return String(value)
                .replaceAll(
                    "&",
                    "&amp;"
                )
                .replaceAll(
                    "<",
                    "&lt;"
                )
                .replaceAll(
                    ">",
                    "&gt;"
                )
                .replaceAll(
                    '"',
                    "&quot;"
                )
                .replaceAll(
                    "'",
                    "&#039;"
                );

        }


        // =====================================================
        // INITIAL LOAD
        // =====================================================

        loadTransactions();

    }
);