let policies = {};


document.addEventListener(
	"DOMContentLoaded",
	() => {

		bindPolicyEvents();

		loadPolicies();

	}
);


/* =========================================================
   LOAD
========================================================= */

async function loadPolicies() {

	try {

		const response =
			await fetch(
				"/api/policies"
			);


		if (!response.ok) {

			throw new Error(
				`Policy API failed with status ${response.status}`
			);

		}


		const result =
			await response.json();


		if (!result.success) {

			throw new Error(
				result.error ||
				"Unable to load policies."
			);

		}


		policies =
			result.data || {};


		populateForm(
			policies
		);


		console.log(
			"Policies loaded",
			policies
		);

	}
	catch (error) {

		console.error(
			"Policy loading error:",
			error
		);


		showMessage(
			error.message,
			true
		);

	}

}


/* =========================================================
   POPULATE FORM
========================================================= */

function populateForm(
	data
) {

	setValue(
		"minimumRecoveryProbability",
		data.minimum_recovery_probability
	);

	setRangeText(
		"minimumRecoveryProbabilityValue",
		data.minimum_recovery_probability,
		"%"
	);


	setValue(
		"escalationThreshold",
		data.escalation_threshold
	);

	setRangeText(
		"escalationThresholdValue",
		data.escalation_threshold,
		"%"
	);


	setValue(
		"highValueThreshold",
		data.high_value_threshold
	);


	setValue(
		"maximumAutoRetryAmount",
		data.maximum_auto_retry_amount
	);


	setValue(
		"maximumRetryCount",
		data.maximum_retry_count
	);


	setValue(
		"retryCooldown",
		data.retry_cooldown_minutes
	);


	const methods =
		Array.isArray(
			data.allowed_payment_methods
		)
			? data.allowed_payment_methods
			: [];


	document
		.querySelectorAll(
			".payment-method"
		)
		.forEach(
			checkbox => {

				checkbox.checked =
					methods.includes(
						checkbox.value
					);

			}
		);


	const stopRules =
		data.stop_rules || {};


	setChecked(
		"stopAfterSuccess",
		stopRules.stop_after_success
	);


	setChecked(
		"stopAfterMaxRetries",
		stopRules.stop_after_max_retries
	);


	setChecked(
		"stopForLowProbability",
		stopRules.stop_for_low_probability
	);


	setChecked(
		"stopForHighValue",
		stopRules.stop_for_high_value_without_review
	);

}


/* =========================================================
   EVENTS
========================================================= */

function bindPolicyEvents() {

	const probability =
		document.getElementById(
			"minimumRecoveryProbability"
		);


	if (probability) {

		probability.addEventListener(
			"input",
			() => {

				setRangeText(
					"minimumRecoveryProbabilityValue",
					probability.value,
					"%"
				);

			}
		);

	}


	const escalation =
		document.getElementById(
			"escalationThreshold"
		);


	if (escalation) {

		escalation.addEventListener(
			"input",
			() => {

				setRangeText(
					"escalationThresholdValue",
					escalation.value,
					"%"
				);

			}
		);

	}


	const save =
		document.getElementById(
			"savePolicies"
		);


	if (save) {

		save.addEventListener(
			"click",
			savePolicies
		);

	}


	const reset =
		document.getElementById(
			"resetPolicies"
		);


	if (reset) {

		reset.addEventListener(
			"click",
			resetPolicies
		);

	}

}


/* =========================================================
   SAVE
========================================================= */

async function savePolicies() {

	const button =
		document.getElementById(
			"savePolicies"
		);


	const payload = {
		minimum_recovery_probability:
			getNumber(
				"minimumRecoveryProbability"
			),

		maximum_retry_count:
			getNumber(
				"maximumRetryCount"
			),

		retry_cooldown_minutes:
			getNumber(
				"retryCooldown"
			),

		maximum_auto_retry_amount:
			getNumber(
				"maximumAutoRetryAmount"
			),

		escalation_threshold:
			getNumber(
				"escalationThreshold"
			),

		high_value_threshold:
			getNumber(
				"highValueThreshold"
			),

		allowed_payment_methods:
			getPaymentMethods(),

		stop_rules: {

			stop_after_success:
				getChecked(
					"stopAfterSuccess"
				),

			stop_after_max_retries:
				getChecked(
					"stopAfterMaxRetries"
				),

			stop_for_low_probability:
				getChecked(
					"stopForLowProbability"
				),

			stop_for_high_value_without_review:
				getChecked(
					"stopForHighValue"
				)

		}

	};


	try {

		setButtonLoading(
			button,
			true
		);


		const response =
			await fetch(
				"/api/policies",
				{
					method: "PUT",

					headers: {
						"Content-Type":
							"application/json"
					},

					body:
						JSON.stringify(
							payload
						)
				}
			);


		const result =
			await response.json();


		if (!response.ok || !result.success) {

			throw new Error(
				result.error ||
				"Unable to save policies."
			);

		}


		policies =
			result.data || payload;


		populateForm(
			policies
		);


		showMessage(
			"Recovery policies saved successfully.",
			false
		);


		console.log(
			"Policies updated",
			policies
		);

	}
	catch (error) {

		console.error(
			"Policy save error:",
			error
		);


		showMessage(
			error.message,
			true
		);

	}
	finally {

		setButtonLoading(
			button,
			false
		);

	}

}


/* =========================================================
   RESET
========================================================= */

async function resetPolicies() {

	const button =
		document.getElementById(
			"resetPolicies"
		);


	try {

		setButtonLoading(
			button,
			true
		);


		const response =
			await fetch(
				"/api/policies/reset",
				{
					method: "POST"
				}
			);


		const result =
			await response.json();


		if (!response.ok || !result.success) {

			throw new Error(
				result.error ||
				"Unable to reset policies."
			);

		}


		policies =
			result.data || {};


		populateForm(
			policies
		);


		showMessage(
			"Policies reset to default values.",
			false
		);

	}
	catch (error) {

		console.error(
			"Policy reset error:",
			error
		);


		showMessage(
			error.message,
			true
		);

	}
	finally {

		setButtonLoading(
			button,
			false
		);

	}

}


/* =========================================================
   PAYMENT METHODS
========================================================= */

function getPaymentMethods() {

	return Array.from(
		document.querySelectorAll(
			".payment-method:checked"
		)
	).map(
		checkbox =>
			checkbox.value
	);

}


/* =========================================================
   HELPERS
========================================================= */

function getNumber(id) {

	const element =
		document.getElementById(
			id
		);


	if (!element) {
		return 0;
	}


	const value =
		Number(
			element.value
		);


	return Number.isFinite(
		value
	)
		? value
		: 0;

}


function setValue(
	id,
	value
) {

	const element =
		document.getElementById(
			id
		);


	if (element) {

		element.value =
			value ?? "";

	}

}


function setChecked(
	id,
	value
) {

	const element =
		document.getElementById(
			id
		);


	if (element) {

		element.checked =
			Boolean(value);

	}

}


function getChecked(id) {

	const element =
		document.getElementById(
			id
		);


	return Boolean(
		element &&
		element.checked
	);

}


function setRangeText(
	id,
	value,
	suffix
) {

	const element =
		document.getElementById(
			id
		);


	if (element) {

		element.textContent =
			`${Number(value || 0)}${suffix}`;

	}

}


/* =========================================================
   BUTTON STATE
========================================================= */

function setButtonLoading(
	button,
	loading
) {

	if (!button) {
		return;
	}


	if (loading) {

		button.disabled = true;

		button.dataset.originalText =
			button.innerHTML;

		button.innerHTML = `
			<i
				class="fa-solid fa-circle-notch fa-spin"
			></i>

			Working...
		`;

	}
	else {

		button.disabled = false;

		button.innerHTML =
			button.dataset.originalText ||
			"Save";

	}

}


/* =========================================================
   MESSAGE
========================================================= */

function showMessage(
	message,
	isError
) {

	const element =
		document.getElementById(
			"policyMessage"
		);


	if (!element) {
		return;
	}


	element.hidden = false;

	element.textContent =
		message;


	element.classList.toggle(
		"error",
		Boolean(isError)
	);


	clearTimeout(
		window.policyMessageTimer
	);


	window.policyMessageTimer =
		setTimeout(
			() => {

				element.hidden = true;

			},
			4000
		);

}