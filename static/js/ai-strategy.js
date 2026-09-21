document.addEventListener("DOMContentLoaded", async () => {
    console.log("RecoverAI AI Strategy initialized");

    const pathParts = window.location.pathname
        .split("/")
        .filter(part => part);

    /*
     * Expected page URL:
     * /ai-strategy/TXN_00008727
     *
     * The last part is the transaction ID.
     */
    const transactionId = pathParts[pathParts.length - 1];

    if (!transactionId) {
        console.error("Transaction ID not found in URL");
        return;
    }

    try {
        const response = await fetch(
            `/api/ai-strategy/${encodeURIComponent(transactionId)}`
        );

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.error || "Unable to load AI recovery strategy."
            );
        }

        const strategy = result.data;

        console.log("AI Strategy loaded:", strategy);

        /*
         * =====================================================
         * TRANSACTION CONTEXT
         * =====================================================
         */

        const context = strategy.recovery_context || {};

        setText("transactionId", context.transaction_id);
        setText("amount", formatCurrency(context.amount));
        setText("failureReason", context.failure_reason);
        setText("paymentMethod", context.payment_method);
        setText("customerId", context.customer_id);
        setText("customerSegment", context.customer_segment);
        setText("retryCount", context.retry_count);

        if (context.recovery_probability !== null &&
            context.recovery_probability !== undefined) {

            setText(
                "recoveryProbability",
                `${Number(context.recovery_probability).toFixed(1)}%`
            );

        } else {

            setText(
                "recoveryProbability",
                "Not available"
            );
        }


        /*
         * =====================================================
         * AI DIAGNOSIS
         * =====================================================
         */

        const diagnosis = strategy.diagnosis || {};

        setText(
            "diagnosis",
            diagnosis.diagnosis || "No diagnosis available."
        );

        if (diagnosis.confidence !== undefined) {

            setText(
                "diagnosisConfidence",
                `Confidence: ${formatConfidence(
                    diagnosis.confidence
                )}`
            );

        } else {

            setText(
                "diagnosisConfidence",
                "Confidence: N/A"
            );
        }


        /*
         * =====================================================
         * EVIDENCE
         * =====================================================
         */

        const evidenceList =
            document.getElementById("evidenceList");

        if (evidenceList) {

            evidenceList.innerHTML = "";

            const evidence = diagnosis.evidence || [];

            if (evidence.length === 0) {

                const item = document.createElement("li");
                item.textContent = "No supporting evidence available.";
                evidenceList.appendChild(item);

            } else {

                evidence.forEach(item => {

                    const li = document.createElement("li");

                    li.textContent = item;

                    evidenceList.appendChild(li);

                });
            }
        }


        /*
         * =====================================================
         * FINAL STRATEGY
         * =====================================================
         */

        const finalStrategy =
            strategy.final_strategy || {};

        setText(
            "recommendedAction",
            formatAction(
                finalStrategy.recommended_action
            )
        );

        setText(
            "strategyReason",
            finalStrategy.reason ||
            "No strategy reasoning available."
        );

        setText(
            "expectedImpact",
            finalStrategy.expected_recovery_impact ||
            "No expected impact information available."
        );

        setText(
            "strategyConfidence",
            formatConfidence(
                finalStrategy.confidence
            )
        );


        /*
         * =====================================================
         * RECOVERY ACTIONS
         * =====================================================
         */

        renderRecoveryActions(
            strategy.recovery_actions || []
        );


        /*
         * =====================================================
         * SHOW PAGE
         * =====================================================
         */

        showContent();

    } catch (error) {

        console.error(
            "AI Strategy loading failed:",
            error
        );

        showError(
            error.message ||
            "Unable to load AI recovery strategy."
        );
    }
});


/*
 * =========================================================
 * SET TEXT SAFELY
 * =========================================================
 */

function setText(elementId, value) {

    const element =
        document.getElementById(elementId);

    if (!element) {
        return;
    }

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        element.textContent = "N/A";

    } else {

        element.textContent = value;
    }
}


/*
 * =========================================================
 * CURRENCY FORMATTER
 * =========================================================
 */

function formatCurrency(value) {

    if (
        value === null ||
        value === undefined ||
        isNaN(Number(value))
    ) {
        return "N/A";
    }

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2
        }
    ).format(Number(value));
}


/*
 * =========================================================
 * CONFIDENCE FORMATTER
 * =========================================================
 */

function formatConfidence(value) {

    if (
        value === null ||
        value === undefined ||
        isNaN(Number(value))
    ) {
        return "N/A";
    }

    let confidence = Number(value);

    /*
     * Backend confidence values are between 0 and 1.
     * Convert them to percentage.
     */
    if (confidence <= 1) {
        confidence = confidence * 100;
    }

    return `${confidence.toFixed(1)}%`;
}


/*
 * =========================================================
 * ACTION NAME FORMATTER
 * =========================================================
 */

function formatAction(action) {

    if (!action) {
        return "No recommendation";
    }

    return action
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/\b\w/g, letter =>
            letter.toUpperCase()
        );
}


/*
 * =========================================================
 * RECOVERY ACTIONS
 * =========================================================
 */

function renderRecoveryActions(actions) {

    const container =
        document.getElementById("actionsList");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!actions.length) {

        const emptyMessage =
            document.createElement("div");

        emptyMessage.className =
            "action-item";

        emptyMessage.textContent =
            "No recovery actions were generated.";

        container.appendChild(emptyMessage);

        return;
    }


    actions.forEach(action => {

        const actionItem =
            document.createElement("div");

        actionItem.className =
            "action-item";


        const header =
            document.createElement("div");

        header.className =
            "action-header";


        const actionName =
            document.createElement("div");

        actionName.className =
            "action-name";

        actionName.textContent =
            formatAction(action.action);


        const priority =
            document.createElement("span");

        priority.className =
            "priority";

        priority.textContent =
            action.priority || "NORMAL";


        header.appendChild(actionName);
        header.appendChild(priority);


        const reason =
            document.createElement("div");

        reason.className =
            "action-reason";

        reason.textContent =
            action.reason ||
            "No reason provided.";


        const impact =
            document.createElement("div");

        impact.className =
            "action-impact";

        impact.textContent =
            `Expected Impact: ${
                action.expected_impact ||
                "Not specified"
            }`;


        actionItem.appendChild(header);
        actionItem.appendChild(reason);
        actionItem.appendChild(impact);

        container.appendChild(actionItem);

    });
}


/*
 * =========================================================
 * SHOW CONTENT
 * =========================================================
 */

function showContent() {

    const loading =
        document.getElementById("loading");

    const content =
        document.getElementById("content");

    if (loading) {
        loading.classList.add("hidden");
    }

    if (content) {
        content.classList.remove("hidden");
    }
}


/*
 * =========================================================
 * SHOW ERROR
 * =========================================================
 */

function showError(message) {

    const loading =
        document.getElementById("loading");

    const errorBox =
        document.getElementById("errorBox");

    if (loading) {
        loading.classList.add("hidden");
    }

    if (errorBox) {

        errorBox.textContent = message;

        errorBox.classList.remove("hidden");
    }
}