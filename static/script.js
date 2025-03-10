$(document).ready(function () {

    // Mapping for Dropdown A (Physics) to Dropdown B (Products)
    const dropdownOptions = {
        "3d-design": ["discovery", "spaceclaim"],  
        "acoustics-analysis": ["sound"],  
        "additive": ["additive print", "additive suite"],  
        "ansys-ai": ["ansys symai"],  
        "autonomous-vehicle-simulation": ["avxcelerate autonomy", "avxcelerate headlamp", "avxcelerate sensors"],  
        "cloud": ["ansys access on microsoft azure", "cloud direct", "gateway powered by aws"],  
        "connect": ["minerva", "modelcenter", "optislang"],  
        "digital-mission-engineering": ["dme component libraries", "odtk", "rf channel modeler", "stk"],  
        "digital-twin": ["twin builder", "twinai"],  
        "electronics": ["aedt mechanical", "charge plus", "circuit", "conceptev", "emc plus", "emit", "hfss", "hfss 3d layout", "hfss ic", "icepak", "maxwell", "maxwell circuit", "motor-cad", "nuhertz filtersolutions", "perceive em", "q2d extractor", "q3d extractor", "rmxprt", "simplorer", "siwave", "synmatrix filter"],  
        "embedded-software": ["request assessment scade one", "scade architect", "scade display", "scade lifecycle", "scade one", "scade solutions for arinc 661 compliant systems", "scade suite", "scade test"],  
        "fluids": ["blademodeler", "cfd-post", "cfx", "chemkin-pro", "fensap-ice", "fluent", "forte", "icem cfd", "model fuel library", "polyflow", "rocky", "thermal desktop", "turbogrid", "vista tf", "ensight"],  
        "ins-lic": ["n/a"],  
        "materials": ["request assessment", "granta collaborations & partnerships", "granta edupack", "granta materials data", "granta mi enterprise", "granta mi pro", "granta selector", "materials data for simulation"],  
        "optics": ["lumerical cml compiler", "lumerical fdtd", "lumerical interconnect", "lumerical mode", "lumerical multiphysics", "speos", "zemax opticstudio"],  
        "optimization": ["n/a"],  
        "platform": ["n/a"],  
        "safety-analysis": ["digital safety manager", "medini analyze", "medini analyze for cybersecurity", "medini analyze for semiconductors"],  
        "semiconductors": ["clock fx", "exalto", "paragonx", "pathfinder", "pathfinder-sc", "powerartist", "raptorh", "raptorqu", "raptorx", "redHawk-sc", "redhawk-sc electrothermal", "redhawk-sc security", "totem", "totem-sc", "velocerf", "voltage-timing flow"],  
        "structures": ["ansys composites preppost", "aqwa", "autodyn", "forming", "ls-dyna", "material designer", "mcalibration", "mechanical", "mechanical apdl", "motion", "ncode designlife", "polyumod", "sherlock"],  
        "na": ["customization suite", "designmodeler", "designxplorer", "meshing", "remote solve manager", "system coupling"]  
    };
    
    // Handle Dropdown A Change
    $("#drop-physics").change(function () {
        let selectedCategory = $(this).val();
        let dropdownB = $("#drop-product");

        dropdownB.empty().append('<option value="">-- Select a Product --</option>').prop("disabled", true);

        if (selectedCategory in dropdownOptions) {
            dropdownOptions[selectedCategory].forEach(function (item) {
                dropdownB.append(`<option value="${item.toLowerCase().replace(/\s+/g, "-")}">${item}</option>`);
            });
            dropdownB.prop("disabled", false);
        }
    });

    let addedFaqs = [];

    // Start Processing Button Click
    $("#processBtn").click(function () {
        let userInput = $("#userInput").val().trim();
    
        if (userInput === "") {
            alert("Please enter text before processing.");
            return;
        }
    
        // Show loader
        $("#loader").show();
    
        $.ajax({
            url: "/process",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ text: userInput }),  // Sending user input to Flask
            success: function (response) {
                $("#loader").hide();
    
                // Display Summary
                $("#summaryText").text(response.summary);
                $("#summaryHeader").removeClass("hidden");
    
                // Display FAQs
                $("#faqContainer").empty();
                $("#faqHeader").removeClass("hidden");
    
                response.faqs.forEach((faq, index) => {
                    let faqHtml = `
                        <div id="faq-${index}" class="faq-item">
                            <p><strong>Q:</strong> ${faq.question}</p>
                            <p><strong>A:</strong> ${faq.answer}</p>
                            <button class="acceptBtn" data-index="${index}">Accept</button>
                            <button class="rejectBtn" data-index="${index}">Reject</button>
                        </div>
                    `;
                    $("#faqContainer").append(faqHtml);
                });
            },
            error: function () {
                $("#loader").hide();
                alert("Error processing request. Please try again.");
            }
        });
    });
    

    // Add Manually Entered FAQ
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

        let index = addedFaqs.length + $(".faq-item").length;
        let faqHtml = `
            <div class="faq-item" id="faq-${index}">
                <p><strong>Q:</strong> ${question}</p>
                <p><strong>A:</strong> ${answer}</p>
                <button class="acceptBtn" data-index="${index}">Accept</button>
                <button class="rejectBtn" data-index="${index}">Reject</button>
            </div>
        `;

        $("#faqContainer").append(faqHtml);
        addedFaqs.push({ question, answer });

        $("#newFaqQuestion").val("");
        $("#newFaqAnswer").val("");

        if (addedFaqs.length >= 3) {
            $("#addFaqBtn").prop("disabled", true).text("Limit Reached");
        }
    });

    // Accept / Reject FAQ
    $(document).on("click", ".acceptBtn", function () {
        $(this).toggleClass("accepted").text($(this).hasClass("accepted") ? "Accepted" : "Accept");
    });

    $(document).on("click", ".rejectBtn", function () {
        let index = $(this).data("index");
        $(`#faq-${index}`).remove();
    });

    // Submit FAQs and Download JSON
    $("#submitFaqsBtn").click(function () {
        let acceptedFaqs = [];
        $(".acceptBtn.accepted").each(function () {
            let index = $(this).data("index");
            let question = $(`#faq-${index} p:first`).text().replace("Q: ", "");
            let answer = $(`#faq-${index} p:last`).text().replace("A: ", "");
            acceptedFaqs.push({ question, answer });
        });

        acceptedFaqs = acceptedFaqs.concat(addedFaqs);

        if (acceptedFaqs.length === 0) {
            alert("No FAQs to download.");
            return;
        }

        let jsonData = JSON.stringify({ faqs: acceptedFaqs }, null, 4);
        let blob = new Blob([jsonData], { type: "application/json" });
        let a = document.createElement("a");
        let timestamp = new Date().toISOString().replace(/[-T:.Z]/g, "");
        a.href = URL.createObjectURL(blob);
        a.download = `FAQs_${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        alert("FAQs JSON file has been downloaded!");
    });

});

