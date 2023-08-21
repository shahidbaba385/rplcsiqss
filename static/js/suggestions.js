function getSuggestions() {
    const input = document.getElementById("searchInput").value;
    const suggestionsDiv = document.getElementById("suggestions");

    suggestionsDiv.innerHTML = "";

    if (input.length >= 2) {
        fetch(`/search?query=${input}`)
            .then(response => response.json())
            .then(suggestions => {
                const uniqueSuggestions = Array.from(new Set(suggestions)); // Convert Set to array
                uniqueSuggestions.forEach(suggestion => {
                    const suggestionTitle = suggestion.replace(".docx", "");
                    const suggestionDiv = createSuggestionDiv(suggestionTitle);
                    suggestionsDiv.appendChild(suggestionDiv);
                });
            });
    }
}

function fetchDocumentText(title) {
    fetch(`/get_text?title=${title}.docx`)
        .then(response => response.json())
        .then(data => {
            const documentTextDiv = document.getElementById("documentText");
            const content = data.content;
            const paragraphs = content.split("\n\n").map(paragraph => `<p>${paragraph}</p>`).join('');
            documentTextDiv.innerHTML = paragraphs;
        });
}


// ... (rest of the code)

function fetchKeywordParagraphs(keyword) {
    if (keyword.length === 0) {
        document.getElementById("documentText").innerHTML = "";
        return;
    }

    fetch(`/search_keywords?keyword=${keyword}`)
        .then(response => response.json())
        .then(data => {
            const keywordParagraphsDiv = document.getElementById("documentText");
            keywordParagraphsDiv.innerHTML = ""; // Clear previous results
            
            if (data.paragraphs.length === 0) {
                keywordParagraphsDiv.innerHTML = "No matching paragraphs found.";
                return;
            }
            
            data.paragraphs.forEach(paragraph => {
                const paragraphDiv = document.createElement("div");
                paragraphDiv.classList.add("text-content");  // Use a different class for text content

                // Highlight the keyword in the paragraph
                const formattedParagraph = paragraph.content.replace(new RegExp(keyword, 'gi'), match => `<span class="highlight">${match}</span>`);
                paragraphDiv.innerHTML = formattedParagraph;

                keywordParagraphsDiv.appendChild(paragraphDiv);
            });
        });
}






function createSuggestionDiv(suggestion) {
    const suggestionDiv = document.createElement("div");
    suggestionDiv.textContent = suggestion;
    suggestionDiv.classList.add("suggestion");
    suggestionDiv.addEventListener("click", () => {
        document.getElementById("searchInput").value = suggestion;
        fetchDocumentText(suggestion);
        document.getElementById("suggestions").innerHTML = "";
    });
    return suggestionDiv;
}