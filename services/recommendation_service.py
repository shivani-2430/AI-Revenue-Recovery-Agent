class RecommendationService:

    @staticmethod
    def generate(project, risk):

        score = int(risk["score"])

        # =========================================================
        # PROJECT HEALTH
        # =========================================================

        if score >= 70:
            health = "Critical"

        elif score >= 40:
            health = "Moderate"

        else:
            health = "Healthy"

        # =========================================================
        # SUCCESS PROBABILITY
        # =========================================================

        success_probability = max(
            10,
            100 - score
        )

        # =========================================================
        # RISK VALUES
        # =========================================================

        budget_risk = int(
            risk.get("budget_percent", 0)
        )

        team_risk = int(
            risk.get("team_percent", 0)
        )

        timeline_risk = int(
            risk.get("timeline_percent", 0)
        )

        technology_risk = int(
            risk.get("technology_percent", 0)
        )

        # =========================================================
        # PRIORITY ACTIONS
        # =========================================================

        priority_actions = []

        risk_values = [
            ("budget", budget_risk),
            ("team", team_risk),
            ("timeline", timeline_risk),
            ("technology", technology_risk)
        ]

        # Highest-risk factors first
        risk_values.sort(
            key=lambda item: item[1],
            reverse=True
        )

        for factor, value in risk_values:

            if value < 30:
                continue

            if factor == "budget":
                priority_actions.append(
                    "Review Budget"
                )

            elif factor == "team":
                priority_actions.append(
                    "Strengthen Team"
                )

            elif factor == "timeline":
                priority_actions.append(
                    "Reassess Timeline"
                )

            elif factor == "technology":
                priority_actions.append(
                    "Validate Technology"
                )

        # If the project is relatively healthy
        if not priority_actions:

            priority_actions.append(
                "Continue Current Plan"
            )

        # Keep card compact
        priority_actions = priority_actions[:3]

        # =========================================================
        # RECOMMENDED TECHNOLOGIES
        # =========================================================

        technologies = []

        tech = (
            project.tech_stack or ""
        ).lower()

        description = (
            project.description or ""
        ).lower()

        project_name = (
            project.project_name or ""
        ).lower()

        project_text = (
            tech + " " +
            description + " " +
            project_name
        )

        # ---------------------------------------------------------
        # MACHINE LEARNING / DATA PROCESSING
        # ---------------------------------------------------------

        is_ml_project = any(
            keyword in project_text
            for keyword in [
                "machine learning",
                "ml",
                "artificial intelligence",
                "ai",
                "prediction",
                "classification",
                "failure detection",
                "failure prediction"
            ]
        )

        if is_ml_project:

            if "pandas" not in tech:
                technologies.append(
                    "Pandas"
                )

            if (
                "scikit" not in tech
                and "sklearn" not in tech
            ):
                technologies.append(
                    "Scikit-learn"
                )

            if "mlflow" not in tech:
                technologies.append(
                    "MLflow"
                )

        # ---------------------------------------------------------
        # DATABASE
        # ---------------------------------------------------------

        if any(
            keyword in project_text
            for keyword in [
                "database",
                "postgresql",
                "sql",
                "data storage"
            ]
        ):

            if "postgresql" not in tech:
                technologies.append(
                    "PostgreSQL"
                )

        # ---------------------------------------------------------
        # PYTHON API / WEB APPLICATION
        # ---------------------------------------------------------

        if (
            "flask" not in tech
            and "fastapi" not in tech
            and "django" not in tech
        ):

            if (
                "web application" in project_text
                or "api" in project_text
                or "backend" in project_text
            ):
                technologies.append(
                    "FastAPI"
                )

        # ---------------------------------------------------------
        # CONTAINERIZATION
        # ---------------------------------------------------------

        if (
            "docker" not in tech
            and (
                is_ml_project
                or "deployment" in project_text
                or "production" in project_text
            )
        ):

            technologies.append(
                "Docker"
            )

        # ---------------------------------------------------------
        # MODEL SERIALIZATION
        # ---------------------------------------------------------

        if (
            is_ml_project
            and "joblib" not in tech
            and "pickle" not in tech
        ):

            technologies.append(
                "Joblib"
            )

        # ---------------------------------------------------------
        # SAFETY FALLBACK
        # ---------------------------------------------------------

        if not technologies:

            technologies = [
                "Git",
                "Docker"
            ]

        # Maximum four technologies for the existing UI
        technologies = technologies[:4]

        # =========================================================
        # RISK MITIGATION
        # =========================================================

        mitigation = []

        # ---------------------------------------------------------
        # 1. Highest contributing risk
        # ---------------------------------------------------------

        highest_risk = max(
            risk_values,
            key=lambda item: item[1]
        )

        factor = highest_risk[0]

        if factor == "budget":

            mitigation.append(
                "Review budget allocation"
            )

        elif factor == "team":

            mitigation.append(
                "Monitor team capacity"
            )

        elif factor == "timeline":

            mitigation.append(
                "Track project milestones"
            )

        else:

            mitigation.append(
                "Validate technology dependencies"
            )

        # ---------------------------------------------------------
        # 2. ML / technology reliability
        # ---------------------------------------------------------

        if is_ml_project:

            mitigation.append(
                "Validate model performance"
            )

        else:

            mitigation.append(
                "Maintain automated testing"
            )

        # ---------------------------------------------------------
        # 3. Delivery monitoring
        # ---------------------------------------------------------

        if timeline_risk >= 40:

            mitigation.append(
                "Review delivery milestones"
            )

        else:

            mitigation.append(
                "Monitor development progress"
            )

        # ---------------------------------------------------------
        # 4. Technical reliability
        # ---------------------------------------------------------

        if technology_risk >= 40:

            mitigation.append(
                "Test technology integration"
            )

        elif is_ml_project:

            mitigation.append(
                "Track model and data changes"
            )

        else:

            mitigation.append(
                "Maintain regular system backups"
            )

        # Exactly four items for the existing UI
        mitigation = mitigation[:4]

        # =========================================================
        # AI SUMMARY
        # =========================================================

        highest_factor_name = highest_risk[0]
        highest_factor_score = highest_risk[1]

        factor_display = {
            "budget": "budget",
            "team": "team capacity",
            "timeline": "timeline",
            "technology": "technology"
        }

        highest_factor_name = factor_display[
            highest_factor_name
        ]

        if health == "Critical":

            summary = (
                f"The project currently has a critical health "
                f"status with an estimated success probability "
                f"of {success_probability}%. The highest "
                f"contributing factor is {highest_factor_name} "
                f"at {highest_factor_score}%. Immediate "
                f"mitigation should focus on this area before "
                f"major execution decisions."
            )

        elif health == "Moderate":

            summary = (
                f"The project currently has a moderate health "
                f"status with an estimated success probability "
                f"of {success_probability}%. The highest "
                f"contributing factor is {highest_factor_name} "
                f"at {highest_factor_score}%. Targeted "
                f"mitigation can improve project readiness "
                f"and reduce execution risk."
            )

        else:

            summary = (
                f"The project currently has a healthy status "
                f"with an estimated success probability of "
                f"{success_probability}%. The highest "
                f"contributing factor is {highest_factor_name} "
                f"at {highest_factor_score}%. The project "
                f"can continue its current direction while "
                f"monitoring the identified risks."
            )

        # =========================================================
        # RETURN
        # =========================================================

        return {

            "health": health,

            "success_probability":
                success_probability,

            "priority_actions":
                priority_actions,

            "technologies":
                technologies,

            "mitigation":
                mitigation,

            "summary":
                summary
        }