class MarketService:

    @staticmethod
    def generate(project):

        domain = project.domain.lower()

        # ----------------------------
        # Default Values
        # ----------------------------

        industry = "General Software Industry"
        demand = "Medium"
        growth = "Moderate"

        competitors = []

        swot = {
            "strength": "Innovative project idea",
            "weakness": "Limited resources",
            "opportunity": "Growing digital transformation",
            "threat": "Strong market competition"
        }

        insights = (
            "The project has good market potential. "
            "Continuous innovation and customer-focused development "
            "will improve competitiveness."
        )

        # ----------------------------
        # Healthcare
        # ----------------------------

        if "health" in domain:

            industry = "Healthcare Technology"

            demand = "Very High"

            growth = "18% Annual Growth"

            competitors = [

                ("Practo", "92%", "Leader"),

                ("Apollo 24/7", "89%", "Leader"),

                ("Tata 1mg", "85%", "Strong"),

                ("MediBuddy", "81%", "Growing")

            ]

        # ----------------------------
        # Finance
        # ----------------------------

        elif "finance" in domain or "fintech" in domain:

            industry = "Financial Technology"

            demand = "Very High"

            growth = "22% Annual Growth"

            competitors = [

                ("Razorpay", "93%", "Leader"),

                ("PhonePe", "90%", "Leader"),

                ("Paytm", "86%", "Strong"),

                ("CRED", "80%", "Growing")

            ]

        # ----------------------------
        # Education
        # ----------------------------

        elif "education" in domain:

            industry = "EdTech"

            demand = "High"

            growth = "15% Annual Growth"

            competitors = [

                ("Coursera", "91%", "Leader"),

                ("Udemy", "88%", "Leader"),

                ("Unacademy", "84%", "Strong"),

                ("Khan Academy", "80%", "Growing")

            ]

        # ----------------------------
        # Artificial Intelligence
        # ----------------------------

        elif "ai" in domain or "artificial" in domain:

            industry = "Artificial Intelligence"

            demand = "Extremely High"

            growth = "30% Annual Growth"

            competitors = [

                ("OpenAI", "95%", "Leader"),

                ("Google Gemini", "92%", "Leader"),

                ("Anthropic", "88%", "Strong"),

                ("Perplexity", "82%", "Growing")

            ]

        return {

            "industry": industry,

            "demand": demand,

            "growth": growth,

            "competitors": competitors,

            "swot": swot,

            "insights": insights

        }