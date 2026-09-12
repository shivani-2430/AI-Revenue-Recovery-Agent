document.addEventListener("DOMContentLoaded", () => {

    const budgetButtons = document.querySelectorAll("[data-budget]");
    const timelineButtons = document.querySelectorAll("[data-time]");

    const runButton = document.getElementById("runSimulation");

    const waitingPanel = document.getElementById("simulation-result");

    const resultSection = document.getElementById("simulation-template");


    let selectedBudget = 20;
    let selectedTimeline = 2;


    /* ----------------------------
       Budget Selection
    -----------------------------*/

    budgetButtons.forEach(button => {

        button.addEventListener("click", () => {

            budgetButtons.forEach(btn =>
                btn.classList.remove("active-option")
            );

            button.classList.add("active-option");

            selectedBudget = parseInt(
                button.dataset.budget
            );

        });

    });


    /* ----------------------------
       Timeline Selection
    -----------------------------*/

    timelineButtons.forEach(button => {

        button.addEventListener("click", () => {

            timelineButtons.forEach(btn =>
                btn.classList.remove("active-option")
            );

            button.classList.add("active-option");

            selectedTimeline = parseInt(
                button.dataset.time
            );

        });

    });


    /* ----------------------------
       Run Simulation
    -----------------------------*/

    runButton.addEventListener("click", () => {

        let currentBudget = getBudget();

        let currentTimeline = getTimeline();

        let newBudget =
            currentBudget +
            (currentBudget * selectedBudget / 100);

        let newTimeline =
            Math.max(
                1,
                currentTimeline - Math.floor(selectedTimeline / 2)
            );


        let success = calculateSuccess(
            selectedBudget,
            selectedTimeline
        );

        let risk = calculateRisk(success);

        updateSimulation(

            currentBudget,
            newBudget,

            currentTimeline,
            newTimeline,

            success,
            risk

        );

    });



    /* ----------------------------
       Read Budget
    -----------------------------*/

    function getBudget(){

        let text =
            document.querySelectorAll(".current-value strong")[0]
            .innerText;

        text =
            text.replace(/[₹,]/g,'');

        return parseFloat(text);

    }



    /* ----------------------------
       Read Timeline
    -----------------------------*/

    function getTimeline(){

        let text =
            document.querySelectorAll(".current-value strong")[1]
            .innerText;

        return parseInt(text);

    }



    /* ----------------------------
       Success Formula
    -----------------------------*/

    function calculateSuccess(

        budgetIncrease,
        timelineIncrease

    ){

        let success = 70;

        success += budgetIncrease * 0.45;

        success += timelineIncrease * 2;

        if(success>95){

            success=95;

        }

        return Math.round(success);

    }



    /* ----------------------------
       Risk Formula
    -----------------------------*/

    function calculateRisk(success){

        if(success>=88){

            return "Low";

        }

        if(success>=78){

            return "Medium";

        }

        return "High";

    }
        /* ----------------------------
       Update UI
    -----------------------------*/

    function updateSimulation(

        currentBudget,
        newBudget,

        currentTimeline,
        newTimeline,

        success,
        risk

    ){

        waitingPanel.style.display="none";

        resultSection.style.display="block";


        /* Before */

        document.getElementById("beforeBudget").innerText =
            "₹" + currentBudget.toLocaleString();

        document.getElementById("beforeTimeline").innerText =
            currentTimeline + " Months";

        document.getElementById("beforeRisk").innerText =
            "Medium";

        document.getElementById("beforeSuccess").innerText =
            "70%";


        /* After */

        document.getElementById("afterBudget").innerText =
            "₹" + Math.round(newBudget).toLocaleString();

        document.getElementById("afterTimeline").innerText =
            newTimeline + " Months";

        document.getElementById("afterRisk").innerText =
            risk;

        document.getElementById("afterSuccess").innerText =
            success + "%";


        /* AI Analysis */

        document.getElementById("aiExplanation").innerText =

            "The simulation predicts that increasing the project budget by "
            + selectedBudget +
            "% and extending the project planning by "
            + selectedTimeline +
            " month(s) improves delivery efficiency, enhances testing coverage, reduces implementation risk, and increases the overall probability of successful project completion.";



        /* Impact Cards */

        document.getElementById("budgetEfficiency").innerText =
            "+" + Math.round(selectedBudget * 0.9) + "%";

        document.getElementById("timelineImprovement").innerText =
            (currentTimeline-newTimeline) +
            " Month Faster";

        document.getElementById("riskReduction").innerText =
            "-" + Math.round(success-70) + "%";

        document.getElementById("successIncrease").innerText =
            "+" + Math.round(success-70) + "%";


        resultSection.scrollIntoView({

            behavior:"smooth",

            block:"start"

        });

    }



    /* ----------------------------
       Reset
    -----------------------------*/

    document
        .getElementById("resetSimulation")
        .addEventListener(

            "click",

            function(){

                resultSection.style.display="none";

                waitingPanel.style.display="block";

            }

        );



    /* ----------------------------
       Apply Scenario
    -----------------------------*/

    document
        .getElementById("applySimulation")
        .addEventListener(

            "click",

            function(){

                alert(
                    "Simulation applied successfully."
                );

            }

        );

});