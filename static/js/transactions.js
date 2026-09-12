document.addEventListener("DOMContentLoaded", () => {

    const searchInput =
        document.getElementById("transactionSearch");

    const statusFilter =
        document.getElementById("statusFilter");

    const failureFilter =
        document.getElementById("failureFilter");

    const methodFilter =
        document.getElementById("methodFilter");

    const clearFilters =
        document.getElementById("clearFilters");

    const tableBody =
        document.getElementById("transactionTableBody");

    const transactionCount =
        document.getElementById("transactionCount");

    const emptyState =
        document.getElementById("emptyTransactions");


    function filterTransactions() {

        const search =
            searchInput.value
                .toLowerCase()
                .trim();

        const status =
            statusFilter.value;

        const failure =
            failureFilter.value;

        const method =
            methodFilter.value;


        const rows =
            Array.from(
                tableBody.querySelectorAll("tr")
            );


        let visibleCount = 0;


        rows.forEach(row => {

            const rowText =
                row.innerText.toLowerCase();

            const rowStatus =
                row.dataset.status;

            const rowFailure =
                row.dataset.failure;

            const rowMethod =
                row.dataset.method;


            const matchesSearch =
                !search ||
                rowText.includes(search);


            const matchesStatus =
                status === "all" ||
                rowStatus === status;


            const matchesFailure =
                failure === "all" ||
                rowFailure === failure;


            const matchesMethod =
                method === "all" ||
                rowMethod === method;


            const visible =
                matchesSearch &&
                matchesStatus &&
                matchesFailure &&
                matchesMethod;


            row.style.display =
                visible ? "" : "none";


            if (visible) {
                visibleCount++;
            }

        });


        transactionCount.textContent =
            `Showing ${visibleCount} transactions`;


        emptyState.style.display =
            visibleCount === 0
                ? "block"
                : "none";

    }


    searchInput.addEventListener(
        "input",
        filterTransactions
    );


    statusFilter.addEventListener(
        "change",
        filterTransactions
    );


    failureFilter.addEventListener(
        "change",
        filterTransactions
    );


    methodFilter.addEventListener(
        "change",
        filterTransactions
    );


    clearFilters.addEventListener(
        "click",
        () => {

            searchInput.value = "";

            statusFilter.value = "all";

            failureFilter.value = "all";

            methodFilter.value = "all";

            filterTransactions();

        }
    );

});