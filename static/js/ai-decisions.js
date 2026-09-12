document.addEventListener(
    "DOMContentLoaded",
    () => {

        const state = {
            page: 1,
            perPage: 10,
            search: "",
            status: "",
            action: "",
            guardrail: "",
            decisions: [],
            selectedId: null
        };


        const elements = {

            total:
                document.getElementById(
                    "totalDecisions"
                ),

            approved:
                document.getElementById(
                    "approvedDecisions"
                ),

            blocked:
                document.getElementById(
                    "blockedDecisions"
                ),

            escalated:
                document.getElementById(
                    "escalatedDecisions"
                ),

            search:
                document.getElementById(
                    "decisionSearch"
                ),

            status:
                document.getElementById(
                    "statusFilter"
                ),

            guardrail:
                document.getElementById(
                    "guardrailFilter"
                ),

            feed:
                document.getElementById(
                    "decisionFeed"
                ),

            loading:
                document.getElementById(
                    "feedLoading"
                ),

            empty:
                document.getElementById(
                    "feedEmpty"
                ),

            previous:
                document.getElementById(
                    "previousPage"
                ),

            next:
                document.getElementById(
                    "nextPage"
                ),

            currentPage:
                document.getElementById(
                    "currentPage"
                ),

            paginationInfo:
                document.getElementById(
                    "paginationInfo"
                ),

            refresh:
                document.getElementById(
                    "refreshDecisions"
                ),

            detailEmpty:
                document.getElementById(
                    "detailEmpty"
                ),

            detail:
                document.getElementById(
                    "decisionDetail"
                )
        };


        // ====================================================
        // ESCAPE HTML
        // ====================================================

        function escapeHtml(value) {

            return String(
                value ?? ""
            )
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


        // ====================================================
        // LOAD
        // ====================================================

        async function loadDecisions() {

            elements.loading.hidden =
                false;

            elements.empty.hidden =
                true;


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


            if (state.search) {

                params.set(
                    "search",
                    state.search
                );
            }


            if (state.status) {

                params.set(
                    "status",
                    state.status
                );
            }


            if (state.action) {

                params.set(
                    "action",
                    state.action
                );
            }


            if (state.guardrail) {

                params.set(
                    "guardrail",
                    state.guardrail
                );
            }


            try {

                const response =
                    await fetch(
                        `/api/ai-decisions?${params.toString()}`,
                        {
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
                        "AI Decisions request failed."
                    );
                }


                if (!payload.success) {

                    throw new Error(
                        payload.error ||
                        "Unable to load AI decisions."
                    );
                }


                render(
                    payload.data
                );


            } catch (error) {

                console.error(
                    "AI Decisions error:",
                    error
                );

                renderError(
                    error.message
                );
            }
        }


        // ====================================================
        // RENDER
        // ====================================================

        function render(data) {

            elements.loading.hidden =
                true;


            renderSummary(
                data.summary || {}
            );


            renderFeed(
                data.decisions || []
            );


            renderPagination(
                data.pagination || {}
            );


            if (
                data.decisions
                &&
                data.decisions.length
                &&
                !state.selectedId
            ) {

                selectDecision(
                    data.decisions[0]
                );
            }
        }


        // ====================================================
        // SUMMARY
        // ====================================================

        function renderSummary(
            summary
        ) {

            elements.total.textContent =
                summary.total_label
                ?? "0";


            elements.approved.textContent =
                summary.approved_label
                ?? "0";


            elements.blocked.textContent =
                summary.blocked_label
                ?? "0";


            elements.escalated.textContent =
                summary.escalated_label
                ?? "0";
        }


        // ====================================================
        // FEED
        // ====================================================

        function renderFeed(
            decisions
        ) {

            state.decisions =
                decisions;


            if (
                !Array.isArray(
                    decisions
                )
                ||
                decisions.length === 0
            ) {

                elements.feed.innerHTML =
                    "";

                elements.empty.hidden =
                    false;

                elements.detail.hidden =
                    true;

                elements.detailEmpty.hidden =
                    false;

                return;
            }


            elements.empty.hidden =
                true;


            elements.feed.innerHTML =
                decisions
                    .map(
                        buildDecisionItem
                    )
                    .join("");


            document
                .querySelectorAll(
                    ".decision-item"
                )
                .forEach(
                    item => {

                        item.addEventListener(
                            "click",
                            () => {

                                const id =
                                    item.dataset.id;


                                const decision =
                                    state.decisions.find(
                                        current =>
                                            current.decision_id
                                            === id
                                    );


                                if (
                                    decision
                                ) {

                                    selectDecision(
                                        decision
                                    );
                                }
                            }
                        );
                    }
                );


            if (state.selectedId) {

                const selected =
                    decisions.find(
                        item =>
                            item.decision_id
                            === state.selectedId
                    );


                if (selected) {

                    selectDecision(
                        selected
                    );

                } else {

                    selectDecision(
                        decisions[0]
                    );
                }

            }
        }


        // ====================================================
        // DECISION ITEM
        // ====================================================

        function buildDecisionItem(
            item
        ) {

            const status =
                String(
                    item.status ||
                    "BLOCKED"
                ).toLowerCase();


            const guardrail =
                String(
                    item.guardrail ||
                    "BLOCKED"
                ).toLowerCase();


            const selected =
                item.decision_id
                === state.selectedId
                    ? "selected"
                    : "";


            return `
                <article
                    class="decision-item ${selected}"
                    data-id="${escapeHtml(
                        item.decision_id
                    )}"
                >

                    <div
                        class="decision-item-top"
                    >

                        <div
                            class="decision-main"
                        >

                            <div
                                class="decision-id"
                            >
                                ${escapeHtml(
                                    item.decision_id
                                )}
                            </div>

                            <div
                                class="decision-action"
                            >
                                ${escapeHtml(
                                    item.recommended_action
                                )}
                            </div>

                            <div
                                class="decision-transaction"
                            >
                                ${escapeHtml(
                                    item.transaction_id
                                )}
                            </div>

                        </div>


                        <div
                            class="decision-right"
                        >

                            <div
                                class="decision-amount"
                            >
                                ${escapeHtml(
                                    item.amount_label
                                )}
                            </div>

                            <div
                                class="decision-probability"
                            >
                                ${Number(
                                    item.recovery_probability
                                    || 0
                                ).toFixed(1)}% recovery
                            </div>

                        </div>

                    </div>


                    <div
                        class="decision-item-bottom"
                    >

                        <div
                            class="decision-meta"
                        >

                            <span
                                class="meta-chip"
                            >
                                ${escapeHtml(
                                    item.failure_reason
                                )}
                            </span>

                            <span
                                class="meta-chip"
                            >
                                ${escapeHtml(
                                    item.payment_method
                                )}
                            </span>

                            <span
                                class="meta-chip"
                            >
                                ${escapeHtml(
                                    item.guardrail
                                )}
                            </span>

                        </div>


                        <span
                            class="decision-status status-${status}"
                        >
                            ${escapeHtml(
                                item.status
                            )}
                        </span>

                    </div>

                </article>
            `;
        }


        // ====================================================
        // DETAIL
        // ====================================================

        function selectDecision(
            decision
        ) {

            if (!decision) {
                return;
            }


            state.selectedId =
                decision.decision_id;


            elements.detailEmpty.hidden =
                true;


            elements.detail.hidden =
                false;


            setText(
                "detailAction",
                decision.recommended_action
            );


            setText(
                "detailDecisionId",
                decision.decision_id
            );


            const statusElement =
                document.getElementById(
                    "detailStatus"
                );


            statusElement.textContent =
                decision.status;


            statusElement.className =
                `decision-status status-${String(
                    decision.status
                ).toLowerCase()}`;


            const transaction =
                document.getElementById(
                    "detailTransaction"
                );


            transaction.textContent =
                decision.transaction_id;


            transaction.href =
                `/transactions/${encodeURIComponent(
                    decision.transaction_id
                )}`;


            setText(
                "detailProbability",
                `${Number(
                    decision.recovery_probability
                    || 0
                ).toFixed(1)}%`
            );


            setText(
                "detailConfidence",
                `${Number(
                    decision.confidence
                    || 0
                ).toFixed(1)}%`
            );


            setText(
                "detailRevenueRisk",
                decision.revenue_at_risk_label
            );


            setText(
                "detailExpectedRecovery",
                decision.expected_recovery_label
            );


            setText(
                "detailExplanation",
                decision.explanation
            );


            renderReasons(
                decision.reasons || []
            );


            setText(
                "detailPolicy",
                decision.policy
            );


            const guardrail =
                document.getElementById(
                    "detailGuardrail"
                );


            guardrail.textContent =
                decision.guardrail;


            guardrail.className =
                `guardrail-result guardrail-${String(
                    decision.guardrail
                ).toLowerCase()}`;


            setText(
                "detailCustomer",
                decision.customer_id
            );


            setText(
                "detailPaymentMethod",
                decision.payment_method
            );


            setText(
                "detailFailure",
                decision.failure_reason
            );


            setText(
                "detailRetryCount",
                decision.retry_count
            );


            setText(
                "detailModel",
                decision.model
            );


            document
                .querySelectorAll(
                    ".decision-item"
                )
                .forEach(
                    item => {

                        item.classList.toggle(
                            "selected",
                            item.dataset.id
                            === decision.decision_id
                        );
                    }
                );
        }


        // ====================================================
        // REASONS
        // ====================================================

        function renderReasons(
            reasons
        ) {

            const container =
                document.getElementById(
                    "detailReasons"
                );


            if (
                !Array.isArray(
                    reasons
                )
                ||
                reasons.length === 0
            ) {

                container.innerHTML =
                    `
                        <div
                            class="reason-item"
                        >
                            <i
                                class="fa-solid fa-circle-info"
                            ></i>

                            <span>
                                No additional reasoning factors available.
                            </span>

                        </div>
                    `;

                return;
            }


            container.innerHTML =
                reasons
                    .map(
                        reason => `
                            <div
                                class="reason-item"
                            >

                                <i
                                    class="fa-solid fa-check"
                                ></i>

                                <span>
                                    ${escapeHtml(
                                        reason
                                    )}
                                </span>

                            </div>
                        `
                    )
                    .join("");
        }


        // ====================================================
        // PAGINATION
        // ====================================================

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
                `Showing ${start}-${end} of ${total}`;


            elements.currentPage.textContent =
                page;


            elements.previous.disabled =
                page <= 1;


            elements.next.disabled =
                page >= totalPages;
        }


        // ====================================================
        // ERROR
        // ====================================================

        function renderError(
            message
        ) {

            elements.loading.hidden =
                true;


            elements.empty.hidden =
                true;


            elements.feed.innerHTML = `
                <div
                    class="feed-loading"
                >

                    <i
                        class="fa-solid fa-triangle-exclamation"
                    ></i>

                    <strong>
                        Unable to load AI decisions
                    </strong>

                    <div>
                        ${escapeHtml(
                            message
                        )}
                    </div>

                </div>
            `;
        }


        // ====================================================
        // TEXT HELPER
        // ====================================================

        function setText(
            id,
            value
        ) {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.textContent =
                    value ?? "--";
            }
        }


        // ====================================================
        // SEARCH
        // ====================================================

        let searchTimer;


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


                            state.selectedId =
                                null;


                            loadDecisions();

                        },
                        350
                    );
            }
        );


        // ====================================================
        // STATUS
        // ====================================================

        elements.status.addEventListener(
            "change",
            event => {

                state.status =
                    event.target.value;


                state.page =
                    1;


                state.selectedId =
                    null;


                loadDecisions();
            }
        );


        // ====================================================
        // GUARDRAIL
        // ====================================================

        elements.guardrail.addEventListener(
            "change",
            event => {

                state.guardrail =
                    event.target.value;


                state.page =
                    1;


                state.selectedId =
                    null;


                loadDecisions();
            }
        );


        // ====================================================
        // PAGINATION
        // ====================================================

        elements.previous.addEventListener(
            "click",
            () => {

                if (
                    state.page > 1
                ) {

                    state.page--;

                    loadDecisions();
                }
            }
        );


        elements.next.addEventListener(
            "click",
            () => {

                state.page++;

                loadDecisions();
            }
        );


        // ====================================================
        // REFRESH
        // ====================================================

        elements.refresh.addEventListener(
            "click",
            () => {

                loadDecisions();
            }
        );


        // ====================================================
        // INITIALIZE
        // ====================================================

        console.log(
            "AI Decisions initialized"
        );


        loadDecisions();

    }
);