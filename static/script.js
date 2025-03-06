$(document).ready(function () {
    let addedFaqs = []; // Store manually added FAQs

    // Add manually entered FAQ
    $("#addFaqBtn").click(function () {
        let question = $("#newFaqQuestion").val().trim();
        let answer = $("#newFaqAnswer").val().trim();

        if (question === "" || answer === "") {
            alert("Please enter both a question and an answer.");
            return;
        }

        if (addedFaqs.length >= 3) {
            alert("You can only add up to 3 FAQs manually.");
            return;
        }

        // Add FAQ to UI and storage
        let faqHtml = `<div class="faq-item"><p><strong>Q:</strong> ${question}</p><p><strong>A:</strong> ${answer}</p></div>`;
        $("#faqContainer").append(faqHtml);
        addedFaqs.push({ question, answer });

        // Clear input fields
        $("#newFaqQuestion").val("");
        $("#newFaqAnswer").val("");

        // Disable button after 3 additions
        if (addedFaqs.length >= 3) {
            $("#addFaqBtn").prop("disabled", true).text("Limit Reached");
        }
    });

    // Submit FAQs and download JSON file
    $("#submitFaqsBtn").click(function () {
        let acceptedFaqs = [];

        // Collect accepted FAQs
        $(".acceptBtn.accepted").each(function () {
            let index = $(this).data("index");
            let question = $(`#faq-${index} p:first`).text().replace("Q: ", "");
            let answer = $(`#faq-${index} p:last`).text().replace("A: ", "");
            acceptedFaqs.push({ question, answer });
        });

        // Include manually added FAQs
        acceptedFaqs = acceptedFaqs.concat(addedFaqs);

        if (acceptedFaqs.length === 0) {
            alert("No FAQs to download.");
            return;
        }

        // Convert to JSON and create a downloadable file
        let jsonData = JSON.stringify({ faqs: acceptedFaqs }, null, 4);
        let blob = new Blob([jsonData], { type: "application/json" });
        let a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "FAQs.json"; // Default filename
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        alert("FAQs JSON file has been downloaded!");
    });

    // Accept/Reject FAQ functionality
    $(document).on("click", ".acceptBtn", function () {
        $(this).toggleClass("accepted").text($(this).hasClass("accepted") ? "Accepted" : "Accept");
    });

    $(document).on("click", ".rejectBtn", function () {
        let index = $(this).data("index");
        $(`#faq-${index}`).remove();
    });
});
