from datetime import datetime

from flask import (
	render_template,
	redirect,
	url_for,
	request,
	jsonify,
)

from database.db import db

from models import (
	Customer,
	Transaction,
	PaymentAttempt,
	RecoveryAction,
	RecoveryOutcome,
	AuditLog,
)
from flask import render_template, request, redirect, url_for, jsonify
from services.customer_service import get_customers

from services.mock_transaction_service import (
	get_transaction_details,
)
from services.recovery_pipeline_service import (
	process_recovery,
)
from services.razorpay_webhook_service import (
    verify_signature,
    process_webhook,
)

from services.recovery_queue_service import (
    get_recovery_queue,
)

from services.mock_ai_decisions_service import (
	get_ai_decisions,
)
from services.mock_failure_intelligence_service import (
	get_failure_intelligence,
)
from services.mock_recovery_simulator_service import (
	run_simulation,
)
from services.model_intelligence_service import (
    get_model_intelligence,
)
from services.mock_audit_trail_service import (
	get_audit_trail,
)
from services.mock_policies_service import (
	get_policies,
	update_policies,
	reset_policies,
)
def register_routes(app):

	# =========================================================
	# HOME
	# =========================================================

	@app.route("/")
	def home():

		return redirect(
			url_for("dashboard")
		)


	# =========================================================
	# DASHBOARD
	# FRONTEND PHASE
	# =========================================================

	@app.route("/dashboard")
	def dashboard():

		return render_template(
			"dashboard.html"
		)
	
	@app.route("/api/dashboard", methods=["GET"])
	def dashboard_api():

		from sqlalchemy import func

		failed_transactions = (
			Transaction.query
			.filter(
				func.upper(Transaction.status) == "FAILED"
			)
			.count()
		)

		successful_transactions = (
			Transaction.query
			.filter(
				func.upper(Transaction.status) == "SUCCESS"
			)
			.count()
		)

		recovery_actions = RecoveryAction.query.count()
		ai_eligible = (
    		Transaction.query
    		.filter(
        		func.upper(Transaction.status) == "FAILED",
        		Transaction.retry_count < 3,
        		Transaction.customer_id.isnot(None),
    		)
    		.count()
		)

		approved_actions = (
			RecoveryAction.query
			.filter_by(status="APPROVED")
			.count()
		)

		executed_actions = (
			RecoveryAction.query
			.filter_by(status="EXECUTED")
			.count()
		)

		blocked_actions = (
			RecoveryAction.query
			.filter_by(status="BLOCKED")
			.count()
		)

		escalated_actions = (
			RecoveryAction.query
			.filter_by(status="ESCALATED")
			.count()
		)

		revenue_at_risk = (
			db.session.query(
				func.coalesce(
					func.sum(
						RecoveryAction.revenue_at_risk
					),
					0
				)
			)
			.scalar()
		)

		recovered_revenue = (
			db.session.query(
				func.coalesce(
					func.sum(
						RecoveryOutcome.amount_recovered
					),
					0
				)
			)
			.filter(
				RecoveryOutcome.outcome == "SUCCESS"
			)
			.scalar()
		)

		successful_recoveries = (
			db.session.query(
				func.count(RecoveryOutcome.id)
			)
			.filter(
				RecoveryOutcome.outcome == "SUCCESS"
			)
			.scalar()
		)

		expected_recovery = (
			db.session.query(
				func.coalesce(
					func.sum(
						RecoveryAction.revenue_at_risk
						* RecoveryAction.recovery_probability
					),
					0
				)
			)
			.scalar()
		)

		recovery_rate = (
			(
				float(recovered_revenue or 0)
				/ float(revenue_at_risk or 0)
			) * 100
			if revenue_at_risk
			else 0
		)

		failure_reasons = (
			db.session.query(
				Transaction.failure_reason,
				func.count(Transaction.id),
				func.sum(Transaction.amount)
			)
			.filter(
				func.upper(Transaction.status) == "FAILED"
			)
			.group_by(
				Transaction.failure_reason
			)
			.order_by(
				func.count(Transaction.id).desc()
			)
			.limit(6)
			.all()
		)

		recent_actions = (
			RecoveryAction.query
			.join(Transaction)
			.order_by(
				RecoveryAction.created_at.desc()
			)
			.limit(5)
			.all()
		)

		return jsonify({
			"success": True,
			"data": {
				"kpis": {
					"revenue_at_risk": round(
						float(revenue_at_risk or 0),
						2
					),
					"expected_recovery": round(
						float(expected_recovery or 0),
						2
					),
					"recovered_revenue": round(
						float(recovered_revenue or 0),
						2
					),
					"recovery_rate": round(
						recovery_rate,
						2
					)
				},
				"funnel": {
					"failed_payments": failed_transactions,
					"revenue_at_risk": round(
						float(revenue_at_risk or 0),
						2
					),
					"ai_eligible": ai_eligible,
					"recovery_actions": recovery_actions,
					"successfully_recovered": successful_recoveries,
				},
				"actions": {
					"approved": approved_actions,
					"executed": executed_actions,
					"blocked": blocked_actions,
					"escalated": escalated_actions
				},
				"failure_reasons": [
					{
						"reason": reason or "UNKNOWN",
						"volume": count,
						"revenue_at_risk": round(
							float(amount or 0),
							2
						)
					}
					for reason, count, amount
					in failure_reasons
				],
				"recent_decisions": [
					{
						"transaction_id": (
							action.transaction.transaction_id
						),
						"amount": float(
							action.transaction.amount or 0
						),
						"failure_reason": (
							"RECOVERED"
							if action.status == "EXECUTED"
							and action.transaction.status == "SUCCESS"
							else (
								action.transaction.failure_reason
								or "UNKNOWN"
							)
						),
						"status": action.status,
						"recovery_probability": round(
							float(
								action.recovery_probability or 0
							) * 100,
							2
						)
					}
					for action in recent_actions
				]
			}
		})
	@app.route("/api/dashboard/trend", methods=["GET"])
	def dashboard_trend():

		from sqlalchemy import func

		metric = request.args.get(
			"metric",
			"risk"
		).lower()

		data = []

		# -----------------------------------------------------
		# RISK TREND
		# -----------------------------------------------------
		if metric == "risk":

			rows = (
				db.session.query(
					func.date(
						Transaction.transaction_timestamp
					).label("date"),
					func.sum(
						Transaction.amount
					).label("amount")
				)
				.filter(
					func.upper(
						Transaction.status
					) == "FAILED"
				)
				.group_by(
					func.date(
						Transaction.transaction_timestamp
					)
				)
				.order_by(
					func.date(
						Transaction.transaction_timestamp
					).desc()
				)
				.limit(30)
				.all()
			)

			for date_value, amount in reversed(rows):

				data.append({
					"date": str(date_value),
					"value": round(
						float(amount or 0),
						2
					)
				})

		# -----------------------------------------------------
		# RECOVERED TREND
		# -----------------------------------------------------
		elif metric == "recovered":

			rows = (
				db.session.query(
					func.date(
						RecoveryOutcome.completed_at
					).label("date"),
					func.sum(
						RecoveryOutcome.amount_recovered
					).label("amount")
				)
				.filter(
					RecoveryOutcome.outcome == "SUCCESS"
				)
				.group_by(
					func.date(
						RecoveryOutcome.completed_at
					)
				)
				.order_by(
					func.date(
						RecoveryOutcome.completed_at
					).desc()
				)
				.limit(30)
				.all()
			)

			for date_value, amount in reversed(rows):

				data.append({
					"date": str(date_value),
					"value": round(
						float(amount or 0),
						2
					)
				})

		# -----------------------------------------------------
		# EXPECTED RECOVERY TREND
		# -----------------------------------------------------
		elif metric == "expected":

			rows = (
				db.session.query(
					func.date(
						RecoveryAction.created_at
					).label("date"),
					func.sum(
						RecoveryAction.revenue_at_risk
						* RecoveryAction.recovery_probability
					).label("amount")
				)
				.group_by(
					func.date(
						RecoveryAction.created_at
					)
				)
				.order_by(
					func.date(
						RecoveryAction.created_at
					).desc()
				)
				.limit(30)
				.all()
			)

			for date_value, amount in reversed(rows):

				data.append({
					"date": str(date_value),
					"value": round(
						float(amount or 0),
						2
					)
				})

		# -----------------------------------------------------
		# INVALID METRIC
		# -----------------------------------------------------
		else:

			return jsonify({
				"success": False,
				"error": (
					"Invalid metric. "
					"Use risk, recovered, or expected."
				)
			}), 400

		return jsonify({
			"success": True,
			"metric": metric,
			"data": data
		})

	# =========================================================
	# TRANSACTIONS
	# FRONTEND PHASE
	# =========================================================

	@app.route("/transactions")
	def transactions():

		return render_template(
			"transactions.html"
		)
	


	# =========================================================
	# TRANSACTION DETAILS
	# FRONTEND PHASE
	# DYNAMIC DATA PROVIDER
	# =========================================================

	@app.route(
		"/transactions/<transaction_id>"
	)
	def transaction_details(
		transaction_id
	):

		return render_template(
			"transaction_details.html",
			transaction_id=transaction_id,
		)


	# =========================================================
	# TRANSACTION DETAILS API
	# FRONTEND PHASE
	# =========================================================

	@app.route(
		"/api/transactions/<transaction_id>",
		methods=["GET"]
	)
	def get_transaction(
		transaction_id
	):

		transaction = get_transaction_details(
			transaction_id
		)

		return jsonify(
			{
				"success": True,
				"data": transaction,
			}
		)


	# =========================================================
# CUSTOMERS
# BACKEND READY
# =========================================================

	@app.route("/customers")
	def customers():

		customer_list = Customer.query.order_by(
			Customer.customer_value.desc()
		).all()

		return render_template(
			"customers.html",
			customers=customer_list,
		)

	@app.route("/api/customers", methods=["GET"])
	def customers_api():

		search = request.args.get("search", "").strip()

		try:
			page = max(int(request.args.get("page", 1)), 1)
		except (TypeError, ValueError):
			page = 1

		try:
			per_page = min(
				max(int(request.args.get("per_page", 20)), 1),
				100
			)
		except (TypeError, ValueError):
			per_page = 20

		data = get_customers(
			search=search or None,
			page=page,
			per_page=per_page,
		)

		return jsonify(data)

	# =========================================================
	# HEALTH CHECK
	# =========================================================

	@app.route("/api/health")
	def health():

		return jsonify(
			{
				"status": "healthy",
				"service": "AI Revenue Recovery Agent",
				"database": "connected",
				"timestamp": datetime.utcnow().isoformat(),
			}
		)


	# =========================================================
	# CREATE TRANSACTION
	# =========================================================

	@app.route(
		"/api/transactions",
		methods=["POST"]
	)
	def create_transaction():

		data = request.get_json(
			silent=True
		) or {}

		required_fields = [
			"transaction_id",
			"customer_id",
			"amount",
			"payment_method",
			"merchant_category",
			"status",
		]

		missing_fields = [
			field
			for field in required_fields
			if field not in data
		]

		if missing_fields:

			return jsonify(
				{
					"success": False,
					"error": "Missing required fields",
					"fields": missing_fields,
				}
			), 400


		# -----------------------------------------------------
		# FIND OR CREATE CUSTOMER
		# -----------------------------------------------------

		customer = Customer.query.filter_by(
			customer_id=data["customer_id"]
		).first()


		if not customer:

			customer = Customer(
				customer_id=data["customer_id"],

				customer_segment=data.get(
					"customer_segment",
					"STANDARD",
				),

				successful_payments=data.get(
					"successful_payments",
					0,
				),

				failed_payments=data.get(
					"failed_payments",
					0,
				),

				historical_success_rate=data.get(
					"historical_success_rate",
					0,
				),

				customer_value=data.get(
					"customer_value",
					0,
				),
			)

			db.session.add(
				customer
			)

			db.session.flush()


		# -----------------------------------------------------
		# DUPLICATE TRANSACTION CHECK
		# -----------------------------------------------------

		existing_transaction = (
			Transaction.query.filter_by(
				transaction_id=data[
					"transaction_id"
				]
			).first()
		)


		if existing_transaction:

			return jsonify(
				{
					"success": False,
					"error": "Transaction already exists",
				}
			), 409


		# -----------------------------------------------------
		# CREATE TRANSACTION
		# -----------------------------------------------------

		transaction = Transaction(

			transaction_id=data[
				"transaction_id"
			],

			customer_id=customer.id,

			amount=data[
				"amount"
			],

			payment_method=data[
				"payment_method"
			],

			merchant_category=data[
				"merchant_category"
			],

			status=data[
				"status"
			],

			failure_reason=data.get(
				"failure_reason"
			),

			subscription_status=data.get(
				"subscription_status"
			),

			retry_count=data.get(
				"retry_count",
				0,
			),
		)


		db.session.add(
			transaction
		)

		db.session.commit()


		return jsonify(
			{
				"success": True,
				"message": (
					"Transaction created successfully"
				),
				"transaction_id": (
					transaction.transaction_id
				),
			}
		), 201


	# =========================================================
	# RAZORPAY WEBHOOK
	# PLACEHOLDER FOR TEST MODE INTEGRATION
	# =========================================================

	@app.route(
		"/api/webhooks/razorpay",
		methods=["POST"]
	)
	def razorpay_webhook():
		raw_payload = request.get_data()

		signature = request.headers.get(
			"X-Razorpay-Signature"
		)

		if not verify_signature(
			raw_payload,
			signature,
		):
			return jsonify(
				{
					"success": False,
					"error": "Invalid webhook signature.",
				}
			), 401

		payload = request.get_json(
			silent=True
		) or {}

		try:
			result = process_webhook(
				payload
			)

			return jsonify(
				{
					"success": True,
					"data": result,
				}
			), 200

		except Exception as error:
			db.session.rollback()

			app.logger.exception(
				"Razorpay webhook processing failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to process Razorpay webhook."
					),
					"details": str(error),
				}
			), 500
	@app.route(
		"/api/recovery/process/<transaction_id>",
		methods=["POST"]
	)
	def process_recovery_api(
		transaction_id
	):
		try:
			data = process_recovery(
				transaction_id
			)

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			), 200

		except ValueError as error:
			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 400

		except Exception as error:
			db.session.rollback()

			app.logger.exception(
				"Recovery pipeline failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to process recovery."
					),
					"details": str(error),
				}
			), 500


	# =========================================================
	# RECOVERY QUEUE
	# FRONTEND PHASE
	# =========================================================

	@app.route("/recovery-queue")
	def recovery_queue():

		return render_template(
			"recovery_queue.html"
		)


	# =========================================================
	# RECOVERY QUEUE API
	# DYNAMIC DATA PROVIDER
	# =========================================================

	@app.route("/api/recovery-queue")
	def recovery_queue_api():

		try:

			data = get_recovery_queue(

				search=request.args.get(
					"search"
				),

				min_probability=request.args.get(
					"min_probability",
					0,
					type=float
				),

				max_retries=request.args.get(
					"max_retries",
					3,
					type=int
				),

				page=request.args.get(
					"page",
					1,
					type=int
				),

				per_page=request.args.get(
					"per_page",
					10,
					type=int
				)
			)

			return jsonify(
				{
					"success": True,
					"data": data
				}
			)

		except Exception as error:

			app.logger.exception(
				"Recovery Queue API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": str(error)
				}
			), 500


	# =========================================================
	# AI DECISIONS
	# FRONTEND PHASE
	# =========================================================

	@app.route("/ai-decisions")
	def ai_decisions():

		return render_template(
			"ai_decisions.html"
		)


	# =========================================================
	# AI DECISIONS API
	# DYNAMIC DATA PROVIDER
	# =========================================================

	@app.route("/api/ai-decisions")
	def ai_decisions_api():

		try:

			data = get_ai_decisions(

				search=request.args.get(
					"search"
				),

				status=request.args.get(
					"status"
				),

				action=request.args.get(
					"action"
				),

				guardrail=request.args.get(
					"guardrail"
				),

				page=request.args.get(
					"page",
					1,
					type=int,
				),

				per_page=request.args.get(
					"per_page",
					10,
					type=int,
				),
			)

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except FileNotFoundError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except ValueError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except Exception as error:

			app.logger.exception(
				"AI Decisions API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to load AI decisions."
					),
					"details": str(error),
				}
			), 500


	# =========================================================
	# 404 HANDLER
	# =========================================================

	@app.errorhandler(404)
	def not_found(error):

		return jsonify(
			{
				"success": False,
				"error": "Resource not found",
			}
		), 404


	# =========================================================
	# GENERAL ERROR HANDLER
	# =========================================================

	@app.errorhandler(500)
	def internal_error(error):

		db.session.rollback()

		return jsonify(
			{
				"success": False,
				"error": "Internal server error",
			}
		), 500
	# =========================================================
	# FAILURE INTELLIGENCE
	# FRONTEND PHASE
	# =========================================================

	@app.route("/failure-intelligence")
	def failure_intelligence():

		return render_template(
			"failure_intelligence.html"
		)
    

	# =========================================================
	# FAILURE INTELLIGENCE API
	# DYNAMIC DATA PROVIDER
	# =========================================================

	@app.route("/api/failure-intelligence")
	def failure_intelligence_api():

		try:

			data = get_failure_intelligence()

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except FileNotFoundError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except ValueError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except Exception as error:

			app.logger.exception(
				"Failure Intelligence API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to load failure intelligence."
					),
					"details": str(error),
				}
			), 500
	# =========================================================
	# RECOVERY SIMULATOR
	# FRONTEND PHASE
	# =========================================================

	@app.route("/simulator")
	@app.route("/recovery-simulator")
	def simulator():

		return render_template(
			"simulator.html"
		)


	# =========================================================
	# RECOVERY SIMULATOR API
	# DYNAMIC DATA PROVIDER
	# =========================================================

	@app.route("/api/recovery-simulator")
	def recovery_simulator_api():

		try:

			data = run_simulation(

				min_probability=request.args.get(
					"min_probability",
					40,
					type=float,
				),

				max_retries=request.args.get(
					"max_retries",
					3,
					type=int,
				),

				batch_size=request.args.get(
					"batch_size",
					1000,
					type=int,
				),
			)

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except FileNotFoundError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except ValueError as error:

			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 400

		except Exception as error:

			app.logger.exception(
				"Recovery Simulator API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to run recovery simulation."
					),
					"details": str(error),
				}
			), 500
	@app.route("/model-intelligence")
	def model_intelligence():
		return render_template(
			"model_intelligence.html"
		)


	@app.route("/api/model-intelligence")
	def model_intelligence_api():
		try:
			data = get_model_intelligence()

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except FileNotFoundError as error:
			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except Exception as error:
			app.logger.exception(
				"Model Intelligence API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": "Unable to load model intelligence.",
					"details": str(error),
				}
			), 500
	@app.route("/audit-trail")
	def audit_trail():
		return render_template(
			"audit_trail.html"
		)


	@app.route("/api/audit-trail")
	def audit_trail_api():
		try:
			data = get_audit_trail(
				search=request.args.get(
					"search"
				),
				status=request.args.get(
					"status"
				),
				action=request.args.get(
					"action"
				),
				guardrail=request.args.get(
					"guardrail"
				),
				page=request.args.get(
					"page",
					1,
					type=int,
				),
				per_page=request.args.get(
					"per_page",
					15,
					type=int,
				),
			)

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except FileNotFoundError as error:
			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 500

		except Exception as error:
			app.logger.exception(
				"Audit Trail API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to load audit trail."
					),
					"details": str(error),
				}
			), 500
	@app.route("/policies")
	def policies():
		return render_template(
			"policies.html"
		)


	@app.route("/api/policies", methods=["GET"])
	def policies_api():
		try:
			data = get_policies()

			return jsonify(
				{
					"success": True,
					"data": data,
				}
			)

		except Exception as error:
			app.logger.exception(
				"Policies API failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to load policies."
					),
					"details": str(error),
				}
			), 500


	@app.route(
		"/api/policies",
		methods=["PUT"]
	)
	def update_policies_api():
		try:
			payload = request.get_json(
				silent=True
			) or {}

			data = update_policies(
				minimum_recovery_probability=
					payload.get(
						"minimum_recovery_probability"
					),
				maximum_retry_count=
					payload.get(
						"maximum_retry_count"
					),
				retry_cooldown_minutes=
					payload.get(
						"retry_cooldown_minutes"
					),
				maximum_auto_retry_amount=
					payload.get(
						"maximum_auto_retry_amount"
					),
				escalation_threshold=
					payload.get(
						"escalation_threshold"
					),
				high_value_threshold=
					payload.get(
						"high_value_threshold"
					),
				allowed_payment_methods=
					payload.get(
						"allowed_payment_methods"
					),
				stop_rules=
					payload.get(
						"stop_rules"
					),
			)

			return jsonify(
				{
					"success": True,
					"message": (
						"Recovery policies updated."
					),
					"data": data,
				}
			)

		except ValueError as error:
			return jsonify(
				{
					"success": False,
					"error": str(error),
				}
			), 400

		except Exception as error:
			app.logger.exception(
				"Policy update failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to update policies."
					),
					"details": str(error),
				}
			), 500


	@app.route(
		"/api/policies/reset",
		methods=["POST"]
	)
	def reset_policies_api():
		try:
			data = reset_policies()

			return jsonify(
				{
					"success": True,
					"message": (
						"Policies reset to defaults."
					),
					"data": data,
				}
			)

		except Exception as error:
			app.logger.exception(
				"Policy reset failed"
			)

			return jsonify(
				{
					"success": False,
					"error": (
						"Unable to reset policies."
					),
					"details": str(error),
				}
			), 500
		
	