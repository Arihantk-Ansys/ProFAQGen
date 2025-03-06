$(document).ready(function () {
    let acceptedFaqs = [];

    // Handle Processing
    $("#processBtn").click(function () {
        let userText = $("#userInput").val();
        $("#loader").show();  // Show loader
        $("#summaryHeader, #faqHeader").addClass("hidden"); // Hide headers

        $.post("/process", JSON.stringify({ text: userText }), "json")
            .done(function (data) {
                $("#loader").hide(); // Hide loader
                $("#summaryText").text(data.summary);
                $("#summaryHeader").removeClass("hidden"); // Show summary header

                $("#faqContainer").empty();
                if (data.faqs.length > 0) {
                    $("#faqHeader").removeClass("hidden"); // Show FAQ header if FAQs exist
                }

                data.faqs.forEach((faq, index) => {
                    let faqHtml = `
                        <div id="faq-${index}">
                            <p><strong>Q:</strong> ${faq.question}</p>
                            <p><strong>A:</strong> ${faq.answer}</p>
                            <button class="acceptBtn" data-index="${index}">Accept</button>
                            <button class="rejectBtn" data-index="${index}">Reject</button>
                        </div>
                    `;
                    $("#faqContainer").append(faqHtml);
                });
            });
    });

    // Handle Accept/Reject
    $(document).on("click", ".acceptBtn", function () {
        let index = $(this).data("index");
        let faqDiv = $(`#faq-${index}`);
        let question = faqDiv.find("p strong").eq(0).text().replace("Q: ", "");
        let answer = faqDiv.find("p strong").eq(1).text().replace("A: ", "");
        acceptedFaqs.push({ question, answer });
        faqDiv.remove();
    });

    $(document).on("click", ".rejectBtn", function () {
        let index = $(this).data("index");
        $(`#faq-${index}`).remove();
    });

    // Handle Adding New FAQ
    $("#addFaqBtn").click(function () {
        let question = $("#newFaqQuestion").val();
        let answer = $("#newFaqAnswer").val();
        if (question && answer) {
            acceptedFaqs.push({ question, answer });
            $("#newFaqQuestion").val("");
            $("#newFaqAnswer").val("");
        }
    });

    // Submit FAQs
    $("#submitFaqsBtn").click(function () {
        $.post("/save_faqs", JSON.stringify({ accepted_faqs: acceptedFaqs }), "json")
            .done(function () {
                alert("FAQs saved successfully!");
            });
    });
});
