let currentAuditPage = 1;


document.addEventListener(
	"DOMContentLoaded",
	() => {

		const search =
			document.getElementById(
				"auditSearch"
			);

		const status =
			document.getElementById(
				"auditStatus"
			);

		const action =
			document.getElementById(
				"auditAction"
			);

		const guardrail =
			document.getElementById(
				"auditGuardrail"
			);

		const refresh =
			document.getElementById(
				"refreshAudit"
			);

		const previous =
			document.getElementById(
				"previousAudit"
			);

		const next =
			document.getElementById(
				"nextAudit"
			);


		if (search) {

			search.addEventListener(
				"input",
				debounce(
					() => {

						currentAuditPage = 1;

						loadAuditTrail();

					},
					300
				)
			);

		}


		[
			status,
			action,
			guardrail
		].forEach(
			element => {

				if (!element) {
					return;
				}

				element.addEventListener(
					"change",
					() => {

						currentAuditPage = 1;

						loadAuditTrail();

					}
				);

			}
		);


		if (refresh) {

			refresh.addEventListener(
				"click",
				() => {

					loadAuditTrail();

				}
			);

		}


		if (previous) {

			previous.addEventListener(
				"click",
				() => {

					if (
						currentAuditPage > 1
					) {

						currentAuditPage -= 1;

						loadAuditTrail();

					}

				}
			);

		}


		if (next) {

			next.addEventListener(
				"click",
				() => {

					currentAuditPage += 1;

					loadAuditTrail();

				}
			);

		}


		loadAuditTrail();

	}
);


/* =========================================================
   LOAD AUDIT TRAIL
========================================================= */

async function loadAuditTrail() {

	const tableBody =
		document.getElementById(
			"auditTableBody"
		);


	if (tableBody) {

		tableBody.innerHTML = `
			<tr>

				<td
					colspan="9"
					class="audit-loading"
				>

					<i
						class="fa-solid fa-circle-notch fa-spin"
					></i>

					Loading audit events...

				</td>

			</tr>
		`;

	}


	try {

		const searchElement =
			document.getElementById(
				"auditSearch"
			);

		const statusElement =
			document.getElementById(
				"auditStatus"
			);

		const actionElement =
			document.getElementById(
				"auditAction"
			);

		const guardrailElement =
			document.getElementById(
				"auditGuardrail"
			);


		const params =
			new URLSearchParams();


		params.set(
			"page",
			currentAuditPage
		);

		params.set(
			"per_page",
			15
		);


		if (
			searchElement &&
			searchElement.value.trim()
		) {

			params.set(
				"search",
				searchElement.value.trim()
			);

		}


		if (
			statusElement &&
			statusElement.value
		) {

			params.set(
				"status",
				statusElement.value
			);

		}


		if (
			actionElement &&
			actionElement.value
		) {

			params.set(
				"action",
				actionElement.value
			);

		}


		if (
			guardrailElement &&
			guardrailElement.value
		) {

			params.set(
				"guardrail",
				guardrailElement.value
			);

		}


		const response =
			await fetch(
				`/api/audit-trail?${params.toString()}`
			);


		if (!response.ok) {

			throw new Error(
				`Audit API failed with status ${response.status}`
			);

		}


		const result =
			await response.json();


		if (!result.success) {

			throw new Error(
				result.error ||
				"Unable to load audit trail."
			);

		}


		const data =
			result.data || {};


		renderSummary(
			data.summary || {}
		);


		renderRecords(
			data.records || []
		);


		renderPagination(
			data.pagination || {}
		);


		console.log(
			"Audit Trail loaded",
			data
		);

	}
	catch (error) {

		console.error(
			"Audit Trail error:",
			error
		);


		showError(
			error.message
		);

	}

}


/* =========================================================
   SUMMARY
========================================================= */

function renderSummary(
	summary
) {

	setText(
		"totalEvents",
		formatNumber(
			summary.total_events
		)
	);


	setText(
		"approvedEvents",
		formatNumber(
			summary.approved
		)
	);


	setText(
		"blockedEvents",
		formatNumber(
			summary.blocked
		)
	);


	setText(
		"escalatedEvents",
		formatNumber(
			summary.escalated
		)
	);


	setText(
		"revenueAtRisk",
		summary.revenue_at_risk_display ||
		"₹0.00"
	);


	setText(
		"recoveredRevenue",
		summary.recovered_revenue_display ||
		"₹0.00"
	);

}


/* =========================================================
   RECORDS
========================================================= */

function renderRecords(
	records
) {

	const tableBody =
		document.getElementById(
			"auditTableBody"
		);

	const empty =
		document.getElementById(
			"auditEmpty"
		);


	if (!tableBody) {
		return;
	}


	if (
		!records ||
		records.length === 0
	) {

		tableBody.innerHTML = "";


		if (empty) {

			empty.hidden = false;

		}


		return;

	}


	if (empty) {

		empty.hidden = true;

	}


	tableBody.innerHTML =
		records
			.map(
				record => {

					const probability =
						Number(
							record.recovery_probability || 0
						);


					return `
						<tr>

							<td>

								<div class="audit-decision">

									${escapeHtml(
										record.decision_id
									)}

								</div>

							</td>


							<td>

								<div class="audit-transaction">

									${escapeHtml(
										record.transaction_id
									)}

								</div>

								<div class="audit-model">

									${escapeHtml(
										record.customer_id
									)}

								</div>

							</td>


							<td>

								${escapeHtml(
									formatTimestamp(
										record.timestamp
									)
								)}

							</td>


							<td>

								<div class="audit-model">

									${escapeHtml(
										record.model ||
										"Recovery Intelligence"
									)}

								</div>

								<div class="audit-score">

									${probability.toFixed(1)}%

								</div>

							</td>


							<td>

								${escapeHtml(
									formatLabel(
										record.recommendation
									)
								)}

							</td>


							<td>

								<span
									class="audit-badge ${guardrailClass(
										record.guardrail
									)}"
								>

									${escapeHtml(
										formatLabel(
											record.guardrail
										)
									)}

								</span>

							</td>


							<td>

								<span
									class="audit-badge ${statusClass(
										record.status
									)}"
								>

									${escapeHtml(
										record.status
									)}

								</span>

							</td>


							<td>

								<span
									class="audit-outcome ${outcomeClass(
										record.outcome
									)}"
								>

									${escapeHtml(
										formatLabel(
											record.outcome
										)
									)}

								</span>

							</td>


							<td>

								${escapeHtml(
									record.recovered_amount_display ||
									"₹0.00"
								)}

							</td>

						</tr>
					`;

				}
			)
			.join("");

}


/* =========================================================
   PAGINATION
========================================================= */

function renderPagination(
	pagination
) {

	const page =
		Number(
			pagination.page || 1
		);


	const totalPages =
		Number(
			pagination.total_pages || 1
		);


	const total =
		Number(
			pagination.total || 0
		);


	setText(
		"auditCurrentPage",
		page
	);


	const info =
		document.getElementById(
			"auditPaginationInfo"
		);


	if (info) {

		if (!total) {

			info.textContent =
				"No events";

		}
		else {

			const perPage =
				Number(
					pagination.per_page || 15
				);


			const start =
				(
					(page - 1) *
					perPage
				) + 1;


			const end =
				Math.min(
					page * perPage,
					total
				);


			info.textContent =
				`Showing ${start}-${end} of ${total}`;

		}

	}


	const previous =
		document.getElementById(
			"previousAudit"
		);


	const next =
		document.getElementById(
			"nextAudit"
		);


	if (previous) {

		previous.disabled =
			page <= 1;

	}


	if (next) {

		next.disabled =
			page >= totalPages;

	}


	currentAuditPage =
		Math.min(
			Math.max(
				page,
				1
			),
			totalPages
		);

}


/* =========================================================
   STATUS
========================================================= */

function statusClass(
	status
) {

	const value =
		String(
			status || ""
		).toLowerCase();


	if (
		value === "approved"
	) {

		return "approved";

	}


	if (
		value === "blocked"
	) {

		return "blocked";

	}


	return "escalated";

}


/* =========================================================
   GUARDRAIL
========================================================= */

function guardrailClass(
	guardrail
) {

	const value =
		String(
			guardrail || ""
		)
		.toUpperCase();


	if (
		value === "PASSED"
	) {

		return "passed";

	}


	return "review";

}


/* =========================================================
   OUTCOME
========================================================= */

function outcomeClass(
	outcome
) {

	const value =
		String(
			outcome || ""
		)
		.toUpperCase();


	if (
		value === "RECOVERED"
	) {

		return "recovered";

	}


	return "not-recovered";

}


/* =========================================================
   LABEL FORMATTER
========================================================= */

function formatLabel(
	value
) {

	return String(
		value || ""
	)
		.toLowerCase()
		.replace(
			/_/g,
			" "
		)
		.replace(
			/\b\w/g,
			character =>
				character.toUpperCase()
		);

}


/* =========================================================
   NUMBER FORMATTER
========================================================= */

function formatNumber(
	value
) {

	return Number(
		value || 0
	).toLocaleString(
		"en-IN"
	);

}


/* =========================================================
   TIMESTAMP FORMATTER
========================================================= */

function formatTimestamp(
	value
) {

	if (!value) {

		return "-";

	}


	const date =
		new Date(value);


	if (
		Number.isNaN(
			date.getTime()
		)
	) {

		return String(value);

	}


	return date.toLocaleString(
		"en-IN",
		{
			dateStyle: "medium",
			timeStyle: "short"
		}
	);

}


/* =========================================================
   SET TEXT
========================================================= */

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
			value;

	}

}


/* =========================================================
   DEBOUNCE
========================================================= */

function debounce(
	callback,
	delay
) {

	let timer;


	return function () {

		clearTimeout(
			timer
		);


		timer =
			setTimeout(
				callback,
				delay
			);

	};

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(
	value
) {

	return String(
		value ?? ""
	)
		.replace(
			/&/g,
			"&amp;"
		)
		.replace(
			/</g,
			"&lt;"
		)
		.replace(
			/>/g,
			"&gt;"
		)
		.replace(
			/"/g,
			"&quot;"
		)
		.replace(
			/'/g,
			"&#039;"
		);

}


/* =========================================================
   ERROR
========================================================= */

function showError(
	message
) {

	const tableBody =
		document.getElementById(
			"auditTableBody"
		);


	if (!tableBody) {
		return;
	}


	tableBody.innerHTML = `
		<tr>

			<td
				colspan="9"
				class="audit-loading"
			>

				<i
					class="fa-solid fa-triangle-exclamation"
				></i>

				${escapeHtml(
					message
				)}

			</td>

		</tr>
	`;

}