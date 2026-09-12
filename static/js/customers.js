/* =========================================================
   CUSTOMERS
   PostgreSQL-backed customer directory
   ========================================================= */

let currentPage = 1;
let currentSearch = "";
const perPage = 20;


/* =========================================================
   HELPERS
   ========================================================= */

function formatCurrency(value) {
    const amount = Number(value || 0);

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0
    }).format(amount);
}


function formatNumber(value) {
    return new Intl.NumberFormat("en-IN").format(
        Number(value || 0)
    );
}


function formatDate(value) {

    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}


function getInitials(customerId) {

    if (!customerId) {
        return "CU";
    }

    const clean = String(customerId)
        .replace(/[^a-zA-Z0-9]/g, "");

    return clean.substring(0, 2).toUpperCase();
}


/* =========================================================
   LOAD CUSTOMERS
   ========================================================= */

async function loadCustomers() {

    const tableBody = document.getElementById(
        "customerTableBody"
    );

    const emptyState = document.getElementById(
        "emptyCustomers"
    );

    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="loading-cell">
                <i class="fa-solid fa-spinner fa-spin"></i>
                Loading customers...
            </td>
        </tr>
    `;

    emptyState.style.display = "none";

    try {

        const params = new URLSearchParams({
            page: currentPage,
            per_page: perPage
        });

        if (currentSearch) {
            params.set("search", currentSearch);
        }

        const response = await fetch(
            `/api/customers?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(
                `Customer API returned ${response.status}`
            );
        }

        const result = await response.json();

        renderCustomers(result.customers || []);
        renderPagination(result.pagination);

        updateSummary(result.customers || [], result.pagination);

    } catch (error) {

        console.error(
            "Failed to load customers:",
            error
        );

        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-cell">
                    Unable to load customers.
                </td>
            </tr>
        `;

        document.getElementById(
            "customerCount"
        ).textContent = "Unable to load customers";

    }
}


/* =========================================================
   RENDER CUSTOMERS
   ========================================================= */

function renderCustomers(customers) {

    const tableBody = document.getElementById(
        "customerTableBody"
    );

    const emptyState = document.getElementById(
        "emptyCustomers"
    );

    if (!customers.length) {

        tableBody.innerHTML = "";
        emptyState.style.display = "block";

        return;
    }

    emptyState.style.display = "none";

    tableBody.innerHTML = customers.map(customer => {

        const successRate = Math.max(
            0,
            Math.min(
                100,
                Number(customer.historical_success_rate || 0)
            )
        );

        return `
            <tr>

                <td>

                    <div class="customer-cell">

                        <div class="customer-avatar">
                            ${escapeHtml(
                                getInitials(customer.customer_id)
                            )}
                        </div>

                        <div class="customer-info">

                            <strong>
                                ${escapeHtml(
                                    customer.customer_id
                                )}
                            </strong>

                            <span>
                                Customer ID
                            </span>

                        </div>

                    </div>

                </td>


                <td>

                    <span class="segment-badge">
                        ${escapeHtml(
                            customer.customer_segment || "Unknown"
                        )}
                    </span>

                </td>


                <td>
                    ${formatDate(customer.customer_since)}
                </td>


                <td>

                    <span class="payment-success">
                        ${formatNumber(
                            customer.successful_payments
                        )}
                    </span>

                </td>


                <td>

                    <span class="payment-failed">
                        ${formatNumber(
                            customer.failed_payments
                        )}
                    </span>

                </td>


                <td>

                    <div class="success-rate">

                        <div class="success-rate-value">
                            ${successRate.toFixed(1)}%
                        </div>

                        <div class="success-rate-bar">

                            <span
                                style="width: ${successRate}%"
                            ></span>

                        </div>

                    </div>

                </td>


                <td>

                    <span class="customer-value">
                        ${formatCurrency(
                            customer.customer_value
                        )}
                    </span>

                </td>


                <td>

                    <strong>
                        ${formatNumber(
                            customer.transaction_count
                        )}
                    </strong>

                </td>

            </tr>
        `;

    }).join("");
}


/* =========================================================
   SUMMARY
   ========================================================= */

function updateSummary(customers, pagination) {

    document.getElementById(
        "totalCustomers"
    ).textContent = formatNumber(
        pagination?.total || 0
    );

    const successful = customers.reduce(
        (total, customer) =>
            total + Number(
                customer.successful_payments || 0
            ),
        0
    );

    const failed = customers.reduce(
        (total, customer) =>
            total + Number(
                customer.failed_payments || 0
            ),
        0
    );

    const value = customers.reduce(
        (total, customer) =>
            total + Number(
                customer.customer_value || 0
            ),
        0
    );

    document.getElementById(
        "successfulPayments"
    ).textContent = formatNumber(successful);

    document.getElementById(
        "failedPayments"
    ).textContent = formatNumber(failed);

    document.getElementById(
        "customerValue"
    ).textContent = formatCurrency(value);

    const total = pagination?.total || 0;

    document.getElementById(
        "customerCount"
    ).textContent =
        `${formatNumber(total)} customer${total === 1 ? "" : "s"}`;
}


/* =========================================================
   PAGINATION
   ========================================================= */

function renderPagination(pagination) {

    const container = document.getElementById(
        "customerPagination"
    );

    if (!pagination || pagination.pages <= 1) {

        container.innerHTML = "";
        return;
    }

    const page = Number(pagination.page);
    const pages = Number(pagination.pages);

    let html = "";

    html += `
        <button
            class="pagination-button"
            ${page <= 1 ? "disabled" : ""}
            onclick="changeCustomerPage(${page - 1})"
        >
            Previous
        </button>
    `;

    const start = Math.max(1, page - 2);
    const end = Math.min(pages, page + 2);

    for (let number = start; number <= end; number++) {

        html += `
            <button
                class="pagination-button ${number === page ? "active" : ""}"
                onclick="changeCustomerPage(${number})"
            >
                ${number}
            </button>
        `;
    }

    html += `
        <button
            class="pagination-button"
            ${page >= pages ? "disabled" : ""}
            onclick="changeCustomerPage(${page + 1})"
        >
            Next
        </button>
    `;

    container.innerHTML = html;
}


function changeCustomerPage(page) {

    if (page < 1) {
        return;
    }

    currentPage = page;

    loadCustomers();
}


/* =========================================================
   SEARCH
   ========================================================= */

let searchTimeout;

document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById(
        "customerSearch"
    );

    const clearButton = document.getElementById(
        "clearSearch"
    );

    searchInput.addEventListener(
        "input",
        () => {

            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(() => {

                currentSearch = searchInput.value.trim();
                currentPage = 1;

                loadCustomers();

            }, 300);
        }
    );


    clearButton.addEventListener(
        "click",
        () => {

            searchInput.value = "";
            currentSearch = "";
            currentPage = 1;

            loadCustomers();
        }
    );


    loadCustomers();
});


/* =========================================================
   HTML SAFETY
   ========================================================= */

function escapeHtml(value) {

    const div = document.createElement("div");

    div.textContent = value ?? "";

    return div.innerHTML;
}