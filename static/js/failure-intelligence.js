document.addEventListener(
	"DOMContentLoaded",
	() => {

		loadFailureIntelligence();

		const refreshButton =
			document.getElementById(
				"refreshFailureIntelligence"
			);

		if (refreshButton) {

			refreshButton.addEventListener(
				"click",
				() => {

					loadFailureIntelligence();

				}
			);

		}

	}
);


/* =========================================================
   LOAD DATA
   ========================================================= */

async function loadFailureIntelligence() {

	try {

		const response = await fetch(
			"/api/failure-intelligence"
		);

		const result =
			await response.json();

		if (!result.success) {

			throw new Error(
				result.error ||
				"Unable to load failure intelligence."
			);

		}

		const data = result.data;

		renderSummary(
			data.summary
		);

		renderTrend(
			data.trend
		);

		renderFailureReasons(
			data.failure_reasons
		);

		renderRevenueImpact(
			data.failure_reasons
		);

		renderPaymentMethods(
			data.payment_methods
		);

		renderHighRiskPatterns(
			data.high_risk_patterns
		);

		renderInsight(
			data.insight
		);

		console.log(
			"Failure Intelligence loaded"
		);

	}
	catch (error) {

		console.error(
			"Failure Intelligence error:",
			error
		);

		showPageError(
			error.message
		);

	}

}


/* =========================================================
   SUMMARY
   ========================================================= */

function renderSummary(summary) {

	document.getElementById(
		"failedTransactions"
	).textContent =
		formatNumber(
			summary.failed_transactions
		);

	document.getElementById(
		"revenueLost"
	).textContent =
		summary.revenue_lost_display;

	document.getElementById(
		"revenueAtRisk"
	).textContent =
		summary.revenue_at_risk_display;

	document.getElementById(
		"recoverability"
	).textContent =
		`${summary.recoverability}%`;
}


/* =========================================================
   TREND
   ========================================================= */

function renderTrend(trend) {

	const container =
		document.getElementById(
			"failureTrend"
		);

	if (!trend || trend.length === 0) {

		container.innerHTML =
			emptyState(
				"No failure trend available."
			);

		return;
	}

	const width = 700;

	const height = 220;

	const padding = {
		top: 20,
		right: 20,
		bottom: 35,
		left: 45
	};

	const chartWidth =
		width -
		padding.left -
		padding.right;

	const chartHeight =
		height -
		padding.top -
		padding.bottom;

	const values = trend.map(
		item =>
			Number(
				item.revenue_lost
			)
	);

	const maxValue =
		Math.max(
			...values,
			1
		);

	const points =
		trend.map(
			(item, index) => {

				const x =
					padding.left +
					(
						index /
						Math.max(
							trend.length - 1,
							1
						)
					) *
					chartWidth;

				const y =
					padding.top +
					chartHeight -
					(
						Number(
							item.revenue_lost
						) /
						maxValue
					) *
					chartHeight;

				return {
					x,
					y,
					item
				};

			}
		);

	const linePath =
		points
			.map(
				(point, index) =>
					`${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
			)
			.join(" ");

	const areaPath =
		`${linePath}
		L ${points[points.length - 1].x}
		${height - padding.bottom}
		L ${points[0].x}
		${height - padding.bottom}
		Z`;

	let html = `
		<svg
			class="trend-svg"
			viewBox="0 0 ${width} ${height}"
			preserveAspectRatio="none"
		>
	`;

	for (let i = 0; i <= 4; i++) {

		const y =
			padding.top +
			(
				i / 4
			) *
			chartHeight;

		html += `
			<line
				x1="${padding.left}"
				x2="${width - padding.right}"
				y1="${y}"
				y2="${y}"
				class="trend-grid-line"
			/>
		`;

	}

	html += `
		<path
			d="${areaPath}"
			class="trend-area"
		/>

		<path
			d="${linePath}"
			class="trend-line"
		/>
	`;

	points.forEach(
		(point, index) => {

			if (
				index === 0 ||
				index === points.length - 1 ||
				index % Math.ceil(
					points.length / 5
				) === 0
			) {

				html += `
					<circle
						cx="${point.x}"
						cy="${point.y}"
						r="4"
						class="trend-point"
					/>

					<text
						x="${point.x}"
						y="${height - 10}"
						text-anchor="middle"
						class="trend-label"
					>
						${formatDate(
							point.item.date
						)}
					</text>
				`;

			}

		}
	);

	html += `
		</svg>
	`;

	container.innerHTML = html;
}


/* =========================================================
   FAILURE REASONS
   ========================================================= */

function renderFailureReasons(
	reasons
) {

	const container =
		document.getElementById(
			"failureReasons"
		);

	if (!reasons || reasons.length === 0) {

		container.innerHTML =
			emptyState(
				"No failure reasons available."
			);

		return;
	}

	const topReasons =
		reasons.slice(
			0,
			6
		);

	container.innerHTML =
		topReasons
			.map(
				reason => {

					return `
						<div class="failure-reason-row">

							<div class="reason-row-top">

								<span class="reason-name">
									${formatLabel(
										reason.failure_reason
									)}
								</span>

								<span class="reason-share">
									${reason.share}%
								</span>

							</div>

							<div class="reason-bar">

								<div
									class="reason-bar-fill"
									style="width: ${Math.min(
										reason.share,
										100
									)}%"
								></div>

							</div>

							<div class="reason-meta">

								<span>
									${formatNumber(
										reason.transactions
									)} transactions
								</span>

								<span>
									${reason.recoverability}%
									recoverable
								</span>

							</div>

						</div>
					`;

				}
			)
			.join("");
}


/* =========================================================
   REVENUE IMPACT
   ========================================================= */

function renderRevenueImpact(
	reasons
) {

	const container =
		document.getElementById(
			"revenueImpact"
		);

	if (!reasons || reasons.length === 0) {

		container.innerHTML =
			emptyState(
				"No revenue impact data available."
			);

		return;
	}

	container.innerHTML = `

		<div class="impact-row">

			<strong>
				Failure Type
			</strong>

			<strong>
				Events
			</strong>

			<strong>
				Revenue Lost
			</strong>

			<strong>
				Recovered
			</strong>

			<strong>
				Recoverability
			</strong>

		</div>

		${reasons
			.slice(0, 7)
			.map(
				item => {

					return `

						<div class="impact-row">

							<div class="impact-failure">
								${formatLabel(
									item.failure_reason
								)}
							</div>

							<div class="impact-count">
								${formatNumber(
									item.transactions
								)}
							</div>

							<div class="impact-value">
								${item.revenue_lost_display}
							</div>

							<div class="impact-recovered">
								${item.recovered_revenue_display}
							</div>

							<div class="impact-recoverability">
								${item.recoverability}%
							</div>

						</div>

					`;

				}
			)
			.join("")}
	`;
}


/* =========================================================
   PAYMENT METHODS
   ========================================================= */

function renderPaymentMethods(
	methods
) {

	const container =
		document.getElementById(
			"paymentMethods"
		);

	if (!methods || methods.length === 0) {

		container.innerHTML =
			emptyState(
				"No payment method data available."
			);

		return;
	}

	const maxTransactions =
		Math.max(
			...methods.map(
				item =>
					item.transactions
			),
			1
		);

	container.innerHTML =
		methods
			.map(
				item => {

					const width =
						(
							item.transactions /
							maxTransactions
						) *
						100;

					return `

						<div class="payment-method-row">

							<div class="payment-method-name">
								${formatLabel(
									item.payment_method
								)}
							</div>

							<div class="payment-method-bar">

								<div
									class="payment-method-fill"
									style="width: ${width}%"
								></div>

							</div>

							<div class="payment-method-score">
								${item.recoverability}%
							</div>

						</div>

					`;

				}
			)
			.join("");
}


/* =========================================================
   HIGH RISK PATTERNS
   ========================================================= */

function renderHighRiskPatterns(
	patterns
) {

	const container =
		document.getElementById(
			"highRiskPatterns"
		);

	if (
		!patterns ||
		patterns.length === 0
	) {

		container.innerHTML =
			emptyState(
				"No high-value failure patterns found."
			);

		return;
	}

	container.innerHTML =
		patterns
			.map(
				pattern => {

					return `

						<div class="risk-pattern">

							<div>

								<div class="pattern-title">
									${formatLabel(
										pattern.failure_reason
									)}
								</div>

								<div class="pattern-subtitle">
									${formatLabel(
										pattern.payment_method
									)}
									&nbsp; • &nbsp;
									${formatNumber(
										pattern.transactions
									)}
									transactions
								</div>

							</div>

							<div class="pattern-right">

								<div class="pattern-revenue">
									${pattern.revenue_at_risk_display}
								</div>

								<div class="pattern-recovery">
									${pattern.recoverability}%
									recoverable
								</div>

							</div>

						</div>

					`;

				}
			)
			.join("");
}


/* =========================================================
   INSIGHT
   ========================================================= */

function renderInsight(
	insight
) {

	document.getElementById(
		"insightTitle"
	).textContent =
		insight.title;

	document.getElementById(
		"insightDescription"
	).textContent =
		insight.description;

	const severity =
		document.getElementById(
			"insightSeverity"
		);

	severity.textContent =
		insight.severity;

	severity.className =
		"insight-severity";

	if (
		insight.severity === "HIGH"
	) {

		severity.style.background =
			"#FFF0F0";

		severity.style.color =
			"#C92A2A";

	}
	else if (
		insight.severity === "MEDIUM"
	) {

		severity.style.background =
			"#EEF0FF";

		severity.style.color =
			"#4F46E5";

	}
	else {

		severity.style.background =
			"#EAFBF5";

		severity.style.color =
			"#087F5B";

	}
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
		value || "UNKNOWN"
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


function formatDate(
	value
) {

	const date =
		new Date(
			value
		);

	if (
		Number.isNaN(
			date.getTime()
		)
	) {

		return value;

	}

	return date.toLocaleDateString(
		"en-IN",
		{
			day: "2-digit",
			month: "short"
		}
	);
}


function emptyState(
	message
) {

	return `
		<div class="chart-loading">
			<i class="fa-regular fa-folder-open"></i>
			${message}
		</div>
	`;
}


function showPageError(
	message
) {

	const containers = [
		"failureTrend",
		"failureReasons",
		"revenueImpact",
		"paymentMethods",
		"highRiskPatterns"
	];

	containers.forEach(
		id => {

			const element =
				document.getElementById(
					id
				);

			if (element) {

				element.innerHTML = `
					<div class="chart-loading">
						<i class="fa-solid fa-triangle-exclamation"></i>
						${message}
					</div>
				`;

			}

		}
	);

	console.error(
		message
	);
}