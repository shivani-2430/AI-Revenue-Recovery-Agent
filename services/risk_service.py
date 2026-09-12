class RiskService:

    @staticmethod
    def calculate_risk(project):

        score = 0

        # Team Size
        if project.team_size <= 3:
            score += 30
        elif project.team_size <= 6:
            score += 15
        else:
            score += 5

        # Budget
        if project.budget < 500000:
            score += 30
        elif project.budget < 2500000:
            score += 15
        else:
            score += 5

        # Timeline
        if project.timeline <= 3:
            score += 25
        elif project.timeline <= 6:
            score += 15
        else:
            score += 5

        # Technology Stack
        tech = project.tech_stack.lower()

        if (
        "ai" in tech
        or "machine learning" in tech
        or "ml" in tech
        ):
            score += 15
        elif (
            "flask" in tech
            or "spring" in tech
        ):
            score += 8
        else:
            score += 5

        score = min(score, 100)

        if score >= 70:
            level = "HIGH"
            summary = (
                "This project has a high probability of failure due to limited "
                "resources and constraints. Consider increasing the budget, "
                "timeline, or team size."
            )

        elif score >= 40:
            level = "MEDIUM "
            summary = (
                "This project has a moderate level of risk. Proper planning and "
                "resource allocation can improve success."
            )

        else:
            level = "LOW"
            summary = (
                "This project has a low probability of failure and appears well "
                "planned."
            )

        return {
            "score": score,
            "level": level,
            "summary": summary,

            "team_level": "HIGH" if project.team_size <= 3 else "MEDIUM" if project.team_size <= 6 else "LOW",
            
            "timeline_level": "HIGH" if project.timeline <= 3 else "MEDIUM" if project.timeline <= 6 else "LOW",

            "team_percent": 90 if project.team_size <= 3 else 60 if project.team_size <= 6 else 30,
            "budget_level": (
                "HIGH"
                if project.budget < 500000
                else "MEDIUM"
                if project.budget < 2500000
                else "LOW"
            ),

            "budget_percent": (
                90
                if project.budget < 500000
                else 60
                if project.budget < 2500000
                else 30
            ),
            "timeline_percent": 90 if project.timeline <= 3 else 60 if project.timeline <= 6 else 30,
            "technology_level": (
                "MEDIUM"
                if (
                    "ai" in tech
                    or "machine learning" in tech
                    or "ml" in tech
                )
                else "LOW"
            ),

            "technology_percent": (
                60
                if (
                    "ai" in tech
                    or "machine learning" in tech
                    or "ml" in tech
                )
                else 30
            )
        }