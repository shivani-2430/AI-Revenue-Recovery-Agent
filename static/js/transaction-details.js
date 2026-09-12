document.addEventListener("DOMContentLoaded", async () => {

    const page =
        document.getElementById(
            "transactionPage"
        );

    const loading =
        document.getElementById(
            "transactionLoading"
        );

    const error =
        document.getElementById(
            "transactionError"
        );

    const content =
        document.getElementById(
            "transactionContent"
        );


    const transactionId =
        page.dataset.transactionId;


    // =====================================================
    // FETCH TRANSACTION
    // =====================================================

    try {

        const response = await fetch(
            `/api/transactions/${transactionId}`
        );


        if (!response.ok) {

            throw new Error(
                "Transaction request failed"
            );

        }


        const result =
            await response.json();


        if (
            !result.success ||
            !result.data
        ) {

            throw new Error(
                "Transaction data unavailable"
            );

        }


        const transaction =
            result.data;


        renderTransaction(
            transaction
        );


        loading.style.display =
            "none";

        content.style.display =
            "block";


    } catch (err) {

        console.error(err);

        loading.style.display =
            "none";

        error.style.display =
            "flex";

    }


    // =====================================================
    // RENDER EVERYTHING
    // =====================================================

    function renderTransaction(
        transaction
    ) {

        renderHeader(
            transaction
        );

        renderSummary(
            transaction
        );

        renderTimeline(
            transaction.timeline
        );

        renderAIDecision(
            transaction
        );

        renderOutcome(
            transaction
        );

        renderTechnicalDetails(
            transaction
        );

        renderAuditDetails(
            transaction
        );

        setupActions(
            transaction
        );

    }


    // =====================================================
    // HEADER
    // =====================================================

    function renderHeader(
        transaction
    ) {

        document.getElementById(
            "transactionId"
        ).textContent =
            transaction.transaction_id;


        const status =
            document.getElementById(
                "transactionStatus"
            );


        status.textContent =
            transaction.status;


        status.className =
            "main-status " +
            getStatusClass(
                transaction.status
            );


        document.getElementById(
            "createdAt"
        ).textContent =
            `Created ${transaction.created_at}`;


        document.getElementById(
            "recoveredAt"
        ).textContent =
            transaction.recovered_at
                ? `Recovered ${transaction.recovered_at}`
                : "Recovery pending";

    }


    // =====================================================
    // SUMMARY
    // =====================================================

    function renderSummary(
        transaction
    ) {

        const container =
            document.getElementById(
                "transactionSummary"
            );


        container.innerHTML = `

            ${summaryItem(
                "fa-indian-rupee-sign",
                "indigo",
                "Transaction Amount",
                transaction.amount_formatted
            )}

            ${summaryItem(
                "fa-building-columns",
                "indigo",
                "Payment Method",
                transaction.payment_method
            )}

            ${summaryItem(
                "fa-triangle-exclamation",
                "red",
                "Failure Reason",
                transaction.failure_reason
            )}

            ${summaryItem(
                "fa-user",
                "indigo",
                "Customer",
                transaction.customer_name,
                transaction.customer_id
            )}

            ${summaryItem(
                "fa-store",
                "indigo",
                "Merchant Category",
                transaction.merchant_category
            )}

            ${summaryItem(
                "fa-clock",
                "indigo",
                "Payment Type",
                transaction.payment_type
            )}

        `;

    }


    function summaryItem(
        icon,
        iconClass,
        label,
        value,
        secondary = ""
    ) {

        return `

            <div class="summary-item">

                <div
                    class="summary-icon ${iconClass}"
                >

                    <i
                        class="fa-solid ${icon}"
                    ></i>

                </div>

                <div>

                    <span class="summary-label">
                        ${escapeHtml(label)}
                    </span>

                    <strong
                        class="summary-value small"
                    >
                        ${escapeHtml(value)}
                    </strong>

                    ${
                        secondary
                            ? `
                                <span
                                    class="summary-secondary"
                                >
                                    ${escapeHtml(secondary)}
                                </span>
                              `
                            : ""
                    }

                </div>

            </div>
        `;
    }


    // =====================================================
    // TIMELINE
    // =====================================================

    function renderTimeline(
        timeline
    ) {

        const container =
            document.getElementById(
                "timeline"
            );


        container.innerHTML =
            timeline
                .map(
                    (item, index) => `

                    <div
                        class="
                            timeline-item
                            ${item.type}
                        "
                        style="
                            animation-delay:
                            ${index * 70}ms;
                        "
                    >

                        <div
                            class="timeline-time"
                        >
                            ${escapeHtml(
                                item.time
                            )}
                        </div>


                        <div
                            class="timeline-marker"
                        >

                            <i
                                class="fa-solid
                                ${item.icon}"
                            ></i>

                        </div>


                        <div
                            class="timeline-content"
                        >

                            <div
                                class="timeline-title-row"
                            >

                                <div>

                                    <h3>
                                        ${escapeHtml(
                                            item.title
                                        )}
                                    </h3>

                                    <p>
                                        ${escapeHtml(
                                            item.description
                                        )}
                                    </p>

                                </div>


                                <span
                                    class="
                                        timeline-status
                                        ${getTimelineStatusClass(
                                            item.status
                                        )}
                                    "
                                >
                                    ${escapeHtml(
                                        item.status
                                    )}
                                </span>

                            </div>

                        </div>

                    </div>
                `
                )
                .join("");

    }


    // =====================================================
    // AI DECISION
    // =====================================================

    function renderAIDecision(
        transaction
    ) {

        document.getElementById(
            "modelBadge"
        ).textContent =
            transaction.model;


        document.getElementById(
            "aiRecommendation"
        ).innerHTML = `

            <div class="recommendation-icon">

                <i
                    class="fa-solid fa-brain"
                ></i>

            </div>


            <div class="recommendation-main">

                <h3>
                    ${escapeHtml(
                        transaction.recovery_action
                    )}
                </h3>

                <span>
                    AI-recommended recovery action
                </span>

            </div>


            <div class="probability-box">

                <strong>
                    ${transaction.recovery_probability}%
                </strong>

                <span>
                    Recovery Probability
                </span>

            </div>

        `;


        document.getElementById(
            "decisionExplanation"
        ).textContent =
            getDecisionExplanation(
                transaction
            );


        document.getElementById(
            "decisionMetrics"
        ).innerHTML = `

            ${metric(
                "Failure Pattern",
                transaction.failure_pattern
            )}

            ${metric(
                "Customer Value",
                transaction.customer_value,
                transaction.customer_value === "High"
            )}

            ${metric(
                "Amount at Risk",
                transaction.amount_formatted
            )}

            ${metric(
                "Confidence",
                `${transaction.recovery_probability}%`,
                true
            )}

        `;


        document.getElementById(
            "decisionReasons"
        ).innerHTML =
            transaction.reasons
                .map(
                    reason => `

                    <div class="reason-item">

                        <i
                            class="fa-solid fa-check"
                        ></i>

                        <span>
                            ${escapeHtml(reason)}
                        </span>

                    </div>
                `
                )
                .join("");


        const execute =
            document.getElementById(
                "executeDecision"
            );


        const isBlocked =
            transaction.guardrail ===
            "BLOCKED";


        execute.innerHTML = `

            <div class="execute-icon">

                <i
                    class="fa-solid
                    ${
                        isBlocked
                            ? "fa-ban"
                            : "fa-shield-halved"
                    }"
                ></i>

            </div>


            <div>

                <strong>
                    Decision:
                    ${
                        isBlocked
                            ? "STOP"
                            : "EXECUTE"
                    }
                </strong>

                <span>
                    ${
                        isBlocked
                            ? "Recovery action blocked by policy."
                            : "All guardrails passed."
                    }
                </span>

            </div>

        `;

    }


    function metric(
        label,
        value,
        green = false
    ) {

        return `

            <div>

                <span>
                    ${escapeHtml(label)}
                </span>

                <strong
                    class="${green
                        ? "green-text"
                        : ""
                    }"
                >
                    ${escapeHtml(value)}
                </strong>

            </div>

        `;
    }


    // =====================================================
    // OUTCOME
    // =====================================================

    function renderOutcome(
        transaction
    ) {

        const container =
            document.getElementById(
                "recoveryOutcome"
            );


        if (
            transaction.status ===
            "RECOVERED"
        ) {

            container.innerHTML = `

                <div class="recovered-box">

                    <div class="trophy-icon">

                        <i
                            class="fa-solid fa-trophy"
                        ></i>

                    </div>


                    <span>
                        Transaction Recovered
                    </span>


                    <strong>
                        ${transaction.amount_recovered_formatted}
                    </strong>


                    <small>
                        Successfully recovered in
                        ${transaction.recovery_time_label}
                    </small>

                </div>


                <h3 class="impact-title">
                    Recovery Impact
                </h3>


                <div class="impact-list">

                    ${impact(
                        "fa-money-bill-trend-up",
                        "Revenue Recovered",
                        transaction.amount_recovered_formatted
                    )}

                    ${impact(
                        "fa-chart-column",
                        "Recovery Time",
                        transaction.recovery_time_label
                    )}

                    ${impact(
                        "fa-percent",
                        "Recovery Probability",
                        `${transaction.recovery_probability}%`
                    )}

                    ${impact(
                        "fa-user-check",
                        "Customer Value",
                        transaction.customer_value
                    )}

                </div>


                <div class="outcome-message">

                    <i
                        class="fa-solid fa-quote-left"
                    ></i>

                    <p>
                        AI-powered recovery converted
                        a failed payment into recovered
                        revenue.
                    </p>

                    <span>
                        RecoverAI Decision Engine
                    </span>

                </div>

            `;

        } else {

            container.innerHTML = `

                <div
                    class="recovered-box pending-outcome"
                >

                    <div class="trophy-icon">

                        <i
                            class="fa-solid fa-hourglass-half"
                        ></i>

                    </div>


                    <span>
                        Recovery Pending
                    </span>


                    <strong>
                        ${transaction.amount_recovered_formatted}
                    </strong>


                    <small>
                        Revenue currently at risk:
                        ${transaction.amount_formatted}
                    </small>

                </div>


                <h3 class="impact-title">
                    Current Recovery State
                </h3>


                <div class="impact-list">

                    ${impact(
                        "fa-chart-line",
                        "Recovery Probability",
                        `${transaction.recovery_probability}%`
                    )}

                    ${impact(
                        "fa-shield-halved",
                        "Guardrail",
                        transaction.guardrail
                    )}

                    ${impact(
                        "fa-bolt",
                        "Recommended Action",
                        transaction.recovery_action
                    )}

                    ${impact(
                        "fa-clock",
                        "Status",
                        transaction.status
                    )}

                </div>

            `;

        }

    }


    function impact(
        icon,
        label,
        value
    ) {

        return `

            <div class="impact-item">

                <div class="impact-icon">

                    <i
                        class="fa-solid ${icon}"
                    ></i>

                </div>


                <span>
                    ${escapeHtml(label)}
                </span>


                <strong>
                    ${escapeHtml(value)}
                </strong>

            </div>

        `;
    }


    // =====================================================
    // TECHNICAL DETAILS
    // =====================================================

    function renderTechnicalDetails(
        transaction
    ) {

        const container =
            document.getElementById(
                "technicalDetails"
            );


        container.innerHTML = `

            ${technical(
                "Transaction ID",
                transaction.transaction_id,
                true
            )}

            ${technical(
                "Attempt ID",
                transaction.attempt_id,
                true
            )}

            ${technical(
                "Razorpay Payment ID",
                transaction.razorpay_payment_id,
                true
            )}

            ${technical(
                "Customer ID",
                transaction.customer_id,
                true
            )}

            ${technical(
                "Created At",
                transaction.created_at
            )}

            ${technical(
                "Recovered At",
                transaction.recovered_at || "Pending"
            )}

        `;

    }


    function technical(
        label,
        value,
        copyable = false
    ) {

        return `

            <div class="technical-item">

                <span>
                    ${escapeHtml(label)}
                </span>

                <strong>

                    ${escapeHtml(value)}

                    ${
                        copyable
                            ? `
                                <i
                                    class="
                                        fa-regular
                                        fa-copy
                                        copy-value
                                    "
                                    data-copy="${escapeHtml(
                                        value
                                    )}"
                                ></i>
                              `
                            : ""
                    }

                </strong>

            </div>

        `;
    }


    // =====================================================
    // AUDIT
    // =====================================================

    function renderAuditDetails(
        transaction
    ) {

        const container =
            document.getElementById(
                "auditDetails"
            );


        container.innerHTML = `

            ${technical(
                "Decision ID",
                transaction.decision_id,
                true
            )}

            ${technical(
                "Model",
                transaction.model
            )}

            ${technical(
                "Policy",
                transaction.policy
            )}

            ${technical(
                "Guardrail",
                transaction.guardrail
            )}

            ${technical(
                "Outcome",
                transaction.status
            )}

        `;

    }


    // =====================================================
    // BUTTONS
    // =====================================================

    function setupActions(
        transaction
    ) {

        document
            .getElementById(
                "shareButton"
            )
            .addEventListener(
                "click",
                async () => {

                    const shareText =
                        `${transaction.transaction_id} · ` +
                        `${transaction.amount_formatted} · ` +
                        `${transaction.status}`;


                    if (
                        navigator.share
                    ) {

                        await navigator.share({
                            title:
                                "RecoverAI Transaction",
                            text:
                                shareText,
                        });

                    } else {

                        await navigator.clipboard.writeText(
                            shareText
                        );

                    }

                }
            );


        document
            .getElementById(
                "downloadButton"
            )
            .addEventListener(
                "click",
                () => {

                    window.print();

                }
            );


        document
            .getElementById(
                "actionButton"
            )
            .addEventListener(
                "click",
                () => {

                    const button =
                        document.getElementById(
                            "actionButton"
                        );


                    button.classList.toggle(
                        "action-open"
                    );

                }
            );


        setupCopyButtons();

    }


    // =====================================================
    // COPY
    // =====================================================

    function setupCopyButtons() {

        document
            .querySelectorAll(
                ".copy-value"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        async () => {

                            const value =
                                button.dataset.copy;


                            try {

                                await navigator.clipboard
                                    .writeText(
                                        value
                                    );


                                button.classList
                                    .remove(
                                        "fa-copy"
                                    );

                                button.classList
                                    .add(
                                        "fa-check"
                                    );


                                setTimeout(
                                    () => {

                                        button.classList
                                            .remove(
                                                "fa-check"
                                            );

                                        button.classList
                                            .add(
                                                "fa-copy"
                                            );

                                    },
                                    1200
                                );

                            } catch (error) {

                                console.error(
                                    error
                                );

                            }

                        }
                    );

                }
            );

    }


    // =====================================================
    // HELPERS
    // =====================================================

    function getStatusClass(
        status
    ) {

        const normalized =
            status.toLowerCase();


        if (
            normalized ===
            "recovered"
        ) {

            return "recovered";

        }


        if (
            normalized ===
            "recoverable"
        ) {

            return "recoverable";

        }


        if (
            normalized ===
            "escalate"
        ) {

            return "escalate";

        }


        return "stopped";

    }


    function getTimelineStatusClass(
        status
    ) {

        if (
            status === "FAILED"
        ) {

            return "failed-status";

        }


        if (
            [
                "ANALYZED",
                "GENERATED",
            ].includes(status)
        ) {

            return "analyzed";

        }


        return "success";

    }


    function getDecisionExplanation(
        transaction
    ) {

        if (
            transaction.status ===
            "RECOVERED"
        ) {

            return (
                `${transaction.failure_reason} showed a ` +
                `strong recovery pattern. The model estimated ` +
                `${transaction.recovery_probability}% recovery ` +
                `probability and the selected action passed ` +
                `all configured guardrails.`
            );

        }


        if (
            transaction.status ===
            "STOP"
        ) {

            return (
                `The model estimated only ` +
                `${transaction.recovery_probability}% recovery ` +
                `probability. The policy engine therefore ` +
                `prevents automatic recovery execution.`
            );

        }


        return (
            `The model estimates a ` +
            `${transaction.recovery_probability}% recovery ` +
            `probability. RecoverAI selected ` +
            `${transaction.recovery_action} while respecting ` +
            `the configured recovery policy.`
        );

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
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    }

});