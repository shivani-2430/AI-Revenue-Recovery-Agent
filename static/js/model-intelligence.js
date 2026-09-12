document.addEventListener(
	"DOMContentLoaded",
	() => {
		loadModelIntelligence();
	}
);


async function loadModelIntelligence() {

	try {

		const response =
			await fetch(
				"/api/model-intelligence"
			);

		if (!response.ok) {
			throw new Error(
				`API request failed with status ${response.status}`
			);
		}

		const result =
			await response.json();

		if (!result.success) {
			throw new Error(
				result.error ||
				"Unable to load model intelligence."
			);
		}

		const data =
			result.data || {};

		renderModel(
			data.model || {}
		);

		renderPerformance(
			data.performance || {}
		);

		renderFeatures(
			data.features || []
		);

		renderClassDistribution(
			data.class_distribution || {}
		);

		renderConfusionMatrix(
			data.confusion_matrix || {}
		);

		renderFeatureImportance(
			data.feature_importance || []
		);

		renderThresholdPolicy(
			data.threshold_policy || {}
		);

		console.log(
			"Model Intelligence loaded",
			data
		);

	}
	catch (error) {

		console.error(
			"Model Intelligence error:",
			error
		);

		showError(
			error.message
		);
	}
}


/* =========================================================
   MODEL
   ========================================================= */

function renderModel(model) {

	setText(
		"modelName",
		model.name || "Recovery Intelligence"
	);

	setText(
		"modelDescription",
		model.description ||
		"Machine learning model used for recovery prediction."
	);

	setText(
		"modelVersion",
		model.version || "-"
	);

	setText(
		"predictionTarget",
		model.target || "-"
	);

	setText(
		"trainingDataset",
		model.dataset || "-"
	);
}


/* =========================================================
   PERFORMANCE
   ========================================================= */

function renderPerformance(performance) {

	setMetric(
		"precision",
		performance.precision
	);

	setMetric(
		"recall",
		performance.recall
	);

	setMetric(
		"f1Score",
		performance.f1_score
	);

	setMetric(
		"rocAuc",
		performance.roc_auc
	);
}


function setMetric(id, value) {

	const element =
		document.getElementById(id);

	if (!element) {
		return;
	}

	if (
		value === null ||
		value === undefined ||
		value === ""
	) {
		element.textContent = "N/A";
		return;
	}

	const number =
		Number(value);

	if (Number.isNaN(number)) {

		element.textContent =
			String(value);

		return;
	}

	if (number <= 1) {

		element.textContent =
			`${(
				number * 100
			).toFixed(1)}%`;

		return;
	}

	element.textContent =
		`${number.toFixed(1)}%`;
}


/* =========================================================
   FEATURES
   ========================================================= */

function renderFeatures(features) {

	const container =
		document.getElementById(
			"featureList"
		);

	if (!container) {
		return;
	}

	if (!features.length) {

		container.innerHTML =
			`
			<div class="empty-state">
				Feature metadata is not available.
			</div>
			`;

		return;
	}

	container.innerHTML =
		features
			.map(
				feature => `
					<div class="feature-chip">
						${escapeHtml(feature)}
					</div>
				`
			)
			.join("");
}


/* =========================================================
   CLASS DISTRIBUTION
   ========================================================= */

function renderClassDistribution(
	distribution
) {

	const container =
		document.getElementById(
			"classDistribution"
		);

	if (!container) {
		return;
	}

	const entries =
		Object.entries(
			distribution
		);

	if (!entries.length) {

		container.innerHTML =
			`
			<div class="empty-state">
				Class distribution is not available.
			</div>
			`;

		return;
	}

	const total =
		entries.reduce(
			(
				sum,
				entry
			) => {
				return (
					sum +
					Number(
						entry[1] || 0
					)
				);
			},
			0
		);

	container.innerHTML =
		entries
			.map(
				([label, count]) => {

					const numericCount =
						Number(
							count || 0
						);

					const percentage =
						total > 0
							? (
								numericCount /
								total
							) * 100
							: 0;

					return `
						<div class="class-row">

							<div class="class-top">

								<span class="class-name">
									${escapeHtml(
										formatLabel(
											label
										)
									)}
								</span>

								<span class="class-count">
									${formatNumber(
										numericCount
									)}
									(
									${percentage.toFixed(1)}%
									)
								</span>

							</div>

							<div class="class-bar">

								<div
									class="class-fill"
									style="width:${percentage}%"
								></div>

							</div>

						</div>
					`;
				}
			)
			.join("");
}


/* =========================================================
   CONFUSION MATRIX
   ========================================================= */

function renderConfusionMatrix(matrix) {

	const container =
		document.getElementById(
			"confusionMatrix"
		);

	if (!container) {
		return;
	}

	const values =
		extractMatrixValues(
			matrix
		);

	if (!values) {

		container.innerHTML =
			`
			<div class="empty-state">
				Confusion matrix is not available.
			</div>
			`;

		return;
	}

	const tn =
		values[0][0];

	const fp =
		values[0][1];

	const fn =
		values[1][0];

	const tp =
		values[1][1];

	container.innerHTML =
		`
		<div class="matrix-cell matrix-header">
			Actual / Predicted
		</div>

		<div class="matrix-cell matrix-header">
			Not Recoverable
		</div>

		<div class="matrix-cell matrix-header">
			Recoverable
		</div>

		<div class="matrix-cell matrix-header">
			Not Recoverable
		</div>

		<div class="matrix-cell">
			${formatNumber(tn)}
		</div>

		<div class="matrix-cell">
			${formatNumber(fp)}
		</div>

		<div class="matrix-cell matrix-header">
			Recoverable
		</div>

		<div class="matrix-cell">
			${formatNumber(fn)}
		</div>

		<div class="matrix-cell">
			${formatNumber(tp)}
		</div>
		`;
}


function extractMatrixValues(matrix) {

	if (
		Array.isArray(matrix) &&
		matrix.length >= 2 &&
		Array.isArray(matrix[0]) &&
		Array.isArray(matrix[1])
	) {
		return matrix;
	}

	if (
		matrix &&
		Array.isArray(matrix.matrix) &&
		matrix.matrix.length >= 2
	) {
		return matrix.matrix;
	}

	if (
		matrix &&
		Array.isArray(matrix.values) &&
		matrix.values.length >= 2
	) {
		return matrix.values;
	}

	if (
		matrix &&
		matrix.tn !== undefined &&
		matrix.fp !== undefined &&
		matrix.fn !== undefined &&
		matrix.tp !== undefined
	) {
		return [
			[
				Number(matrix.tn),
				Number(matrix.fp)
			],
			[
				Number(matrix.fn),
				Number(matrix.tp)
			]
		];
	}

	return null;
}


/* =========================================================
   FEATURE IMPORTANCE
   ========================================================= */

function renderFeatureImportance(
	importance
) {

	const container =
		document.getElementById(
			"featureImportance"
		);

	if (!container) {
		return;
	}

	if (!importance.length) {

		container.innerHTML =
			`
			<div class="empty-state">
				Feature importance is not available.
			</div>
			`;

		return;
	}

	const items =
		importance
			.map(
				item => {

					return {
						name:
							item.feature ||
							item.name ||
							"Feature",

						value:
							Number(
								item.importance ??
								item.value ??
								0
							)
					};
				}
			)
			.sort(
				(
					first,
					second
				) =>
					second.value -
					first.value
			);

	const maxValue =
		Math.max(
			...items.map(
				item =>
					item.value
			),
			0
		);

	container.innerHTML =
		items
			.map(
				item => {

					const width =
						maxValue > 0
							? (
								item.value /
								maxValue
							) * 100
							: 0;

					return `
						<div class="importance-row">

							<div class="importance-top">

								<span class="importance-name">
									${escapeHtml(
										item.name
									)}
								</span>

								<span class="importance-value">
									${(
										item.value *
										100
									).toFixed(1)}%
								</span>

							</div>

							<div class="importance-bar">

								<div
									class="importance-fill"
									style="width:${width}%"
								></div>

							</div>

						</div>
					`;
				}
			)
			.join("");
}


/* =========================================================
   POLICY
   ========================================================= */

function renderThresholdPolicy(
	policy
) {

	const title =
		policy.title ||
		policy.name ||
		policy.threshold;

	const description =
		policy.description ||
		policy.rule ||
		policy.details;

	setText(
		"thresholdTitle",
		title ||
		"Policy configuration unavailable"
	);

	setText(
		"thresholdDescription",
		description ||
		"The active recovery threshold policy has not been published to the model metadata."
	);
}


/* =========================================================
   ERROR
   ========================================================= */

function showError(message) {

	const containers = [
		"featureList",
		"classDistribution",
		"confusionMatrix",
		"featureImportance"
	];

	containers.forEach(
		id => {

			const element =
				document.getElementById(id);

			if (!element) {
				return;
			}

			element.innerHTML =
				`
				<div class="empty-state">
					${escapeHtml(message)}
				</div>
				`;
		}
	);
}


/* =========================================================
   HELPERS
   ========================================================= */

function setText(
	id,
	value
) {

	const element =
		document.getElementById(id);

	if (element) {
		element.textContent =
			value;
	}
}


function formatNumber(value) {

	return Number(
		value || 0
	).toLocaleString(
		"en-IN"
	);
}


function formatLabel(value) {

	return String(
		value || ""
	)
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


function escapeHtml(value) {

	return String(value)
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