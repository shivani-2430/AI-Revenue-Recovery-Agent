class ReportService:

    @staticmethod
    def generate(project, risk, recommendation, market):

        score = recommendation["success_probability"]

        # -----------------------------
        # Overall Rating
        # -----------------------------

        if score >= 85:
            rating = "★★★★★"
            verdict = "Excellent Project Potential"

        elif score >= 70:
            rating = "★★★★☆"
            verdict = "Very Good Project Potential"

        elif score >= 55:
            rating = "★★★☆☆"
            verdict = "Good Project Potential"

        elif score >= 40:
            rating = "★★☆☆☆"
            verdict = "Average Project Potential"

        else:
            rating = "★☆☆☆☆"
            verdict = "High Risk Project"

        # -----------------------------
        # Overall Summary
        # -----------------------------

        summary = (
            f"The project belongs to the {market['industry']} industry. "
            f"It has a {recommendation['health'].lower()} health status "
            f"with a success probability of "
            f"{recommendation['success_probability']}%. "
            f"The current risk level is {risk['level']}. "
            f"The overall outlook indicates {verdict.lower()}."
        )

        return {

            "rating": rating,

            "verdict": verdict,

            "summary": summary

        }