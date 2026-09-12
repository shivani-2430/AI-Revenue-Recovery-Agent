document.addEventListener(
	"DOMContentLoaded",
	() => {

		const probability =
			document.getElementById(
				"minProbability"
			);

		const retries =
			document.getElementById(
				"maxRetries"
			);

		const probabilityValue =
			document.getElementById(
				"probabilityValue"
			);

		const retryValue =
			document.getElementById(
				"retryValue"
			);

		const runButton =
			document.getElementById(
				"runSimulation"
			);


		if (probability) {

			probability.addEventListener(
				"input",
				() => {

					probabilityValue.textContent =
						`${probability.value}%`;

				}
			);

		}


		if (retries) {

			retries.addEventListener(
				"input",
				() => {

					retryValue.textContent =
						retries.value;

				}
			);

		}


		if (runButton) {

			runButton.addEventListener(
				"click",
				runSimulation
			);

		}


		runSimulation();

	}
);


/* =========================================================
   RUN SIMULATION
   ========================================================= */

async function runSimulation() {

	const runButton =
		document.getElementById(
			"runSimulation"
		);

	const batchSize =
		document.getElementById(
			"batchSize"
		).value;

	const minProbability =
		document.getElementById(
			"minProbability"
		).value;

	const maxRetries =
		document.getElementById(
			"maxRetries"
		).value;


	if (runButton) {

		runButton.disabled = true;

		runButton.innerHTML = `
			<i class="fa-solid fa-circle-notch fa-spin"></i>
			Running...
		`;

	}


	try {

		const params =
			new URLSearchParams(
				{
					batch_size: batchSize,
					min_probability: minProbability,
					max_retries: maxRetries
				}
			);

		const response =
			await fetch(
				`/api/recovery-simulator?${params.toString()}`
			);

		const result =
			await response.json();

		if (!result.success) {

			throw new Error(
				result.error ||
				"Simulation failed."
			);

		}

		renderSummary(
			result.data.summary
		);

		renderFunnel(
			result.data.funnel
		);

		renderActions(
			result.data.actions
		);

		renderResults(
			result.data.summary
		);

		renderInsight(
			result.data.insight
		);

		console.log(
			"Recovery Simulator loaded",
			result.data
		);

	}
	catch (error) {

		console.error(
			"Recovery Simulator error:",
			error
		);

		showError(
			error.message
		);

	}
	finally {

		if (runButton) {

			runButton.disabled = false;

			runButton.innerHTML = `
				<i class="fa-solid fa-play"></i>
				Run Simulation
			`;

		}

	}
}


/* =========================================================
   SUMMARY
   ========================================================= */

function renderSummary(
	summary
) {

	document.getElementById(
		"revenueAtRisk"
	).textContent =
		summary.revenue_at_risk_display;

	document.getElementById(
		"expectedRecovery"
	).textContent =
		summary.expected_recovery_display;

	document.getElementById(
		"recoveredRevenue"
	).textContent =
		summary.recovered_revenue_display;

	document.getElementById(
		"recoveryRate"
	).textContent =
		`${summary.recovery_rate}%`;
}


/* =========================================================
   FUNNEL
   ========================================================= */

function renderFunnel(
	funnel
) {

	const container =
		document.getElementById(
			"recoveryFunnel"
		);

	if (
		!funnel ||
		funnel.length === 0
	) {

		container.innerHTML =
			emptyMessage(
				"No simulation funnel data."
			);

		return;
	}

	const maxValue =
		Math.max(
			...funnel.map(
				item =>
					Number(
						item.value
					)
			),
			1
		);

	container.innerHTML =
		funnel
			.map(
				item => {

					const width =
						(
							Number(
								item.value
							) /
							maxValue
						) *
						100;

					return `

						<div class="funnel-item">

							<div class="funnel-label">
								${item.stage}
							</div>

							<div class="funnel-bar">

								<div
									class="funnel-fill"
									style="width:${width}%"
								></div>

							</div>

							<div class="funnel-value">
								${formatNumber(
									item.value
								)}
							</div>

						</div>

					`;

				}
			)
			.join("");
}


/* =========================================================
   ACTIONS
   ========================================================= */

function renderActions(
	actions
) {

	const container =
		document.getElementById(
			"actionDistribution"
		);

	if (
		!actions ||
		actions.length === 0
	) {

		container.innerHTML =
			emptyMessage(
				"No recovery actions generated."
			);

		return;
	}

	container.innerHTML =
		actions
			.map(
				action => {

					return `

						<div class="action-row">

							<div class="action-top">

								<span class="action-name">
									${formatLabel(
										action.action
									)}
								</span>

								<span class="action-share">
									${action.share}%
								</span>

							</div>

							<div class="action-bar">

								<div
									class="action-fill"
									style="width:${action.share}%"
								></div>

							</div>

							<div class="action-meta">

								<span>
									${formatNumber(
										action.count
									)}
									opportunities
								</span>

								<span>
									${action.recovered_display}
									recovered
								</span>

							</div>

						</div>

					`;

				}
			)
			.join("");
}


/* =========================================================
   RESULTS
   ========================================================= */

function renderResults(
	summary
) {

	document.getElementById(
		"failedPayments"
	).textContent =
		formatNumber(
			summary.failed_payments
		);

	document.getElementById(
		"eligibleOpportunities"
	).textContent =
		formatNumber(
			summary.eligible_opportunities
		);

	document.getElementById(
		"recoveryAttempts"
	).textContent =
		formatNumber(
			summary.attempted
		);

	document.getElementById(
		"recoveredTransactions"
	).textContent =
		formatNumber(
			summary.recovered_transactions
		);

	document.getElementById(
		"guardrailBlocked"
	).textContent =
		formatNumber(
			summary.guardrail_blocked
		);

	document.getElementById(
		"resultExpectedRecovery"
	).textContent =
		summary.expected_recovery_display;
}


/* =========================================================
   INSIGHT
   ========================================================= */

function renderInsight(
	insight
) {

	document.getElementById(
		"simulationInsightTitle"
	).textContent =
		insight.title;

	document.getElementById(
		"simulationInsightDescription"
	).textContent =
		insight.description;
}


/* =========================================================
   HELPERS
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
			char =>
				char.toUpperCase()
		);
}


function emptyMessage(
	message
) {

	return `
		<div class="simulation-loading">
			<i class="fa-regular fa-folder-open"></i>
			${message}
		</div>
	`;
}


function showError(
	message
) {

	const containers = [
		"recoveryFunnel",
		"actionDistribution"
	];

	containers.forEach(
		id => {

			const element =
				document.getElementById(
					id
				);

			if (element) {

				element.innerHTML = `
					<div class="simulation-loading">
						<i class="fa-solid fa-triangle-exclamation"></i>
						${message}
					</div>
				`;

			}

		}
	);
}