// Handle form submission
function handleSubmit(event) {
    event.preventDefault();
    analyzeCategory();
}

// Show message based on type (error or success)
function showMessage(type, message) {
    const noResultsContainer = document.getElementById('noResultsContainer');
    
    if (type === 'error') {
        noResultsContainer.style.display = 'block';
        noResultsContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        noResultsContainer.style.display = 'none';
    }
    
    console.log(`${type}: ${message}`);
}

// Main function to analyze the category
function analyzeCategory() {
    const category = document.getElementById('categoryInput').value.trim();
    if (!category) return;

    const loadingEl = document.querySelector('.loading');
    const resultsEl = document.getElementById('results');
    const noResultsContainer = document.getElementById('noResultsContainer');
    
    loadingEl.style.display = 'block';
    noResultsContainer.style.display = 'none';
    document.getElementById('wordCards').innerHTML = '';
    document.getElementById('wordCloud').innerHTML = '';
    resultsEl.style.display = 'none';

    fetch(`/analyze/${category}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response:', data); 
            loadingEl.style.display = 'none';
            
            showMessage(data.status, data.message);
            
            if (data.words && data.words.length > 0) {
                resultsEl.style.display = 'block';
                displayResults(data.words);
                createWordCloud(data.words);
            } else {
                resultsEl.style.display = 'none';
                noResultsContainer.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingEl.style.display = 'none';
            showMessage('error', 'An error occurred while analyzing the category. Please try again.');
            noResultsContainer.style.display = 'block';
        });
}

// Display word frequency results as cards
function displayResults(words) {
    const container = document.getElementById('wordCards');
    container.innerHTML = '';
    
    words.slice(0, 20).forEach(word => {
        const col = document.createElement('div');
        col.className = 'col-6 col-sm-4 col-md-3 mb-3';
        
        const card = document.createElement('div');
        card.className = 'card h-100 word-card';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body text-center';
        
        const wordEl = document.createElement('h5');
        wordEl.className = 'card-title';
        wordEl.textContent = word.word;
        
        const freqEl = document.createElement('p');
        freqEl.className = 'card-text text-muted';
        freqEl.textContent = `Frequency: ${word.frequency}`;
        
        cardBody.appendChild(wordEl);
        cardBody.appendChild(freqEl);
        card.appendChild(cardBody);
        col.appendChild(card);
        container.appendChild(col);
    });
}

// Create a word cloud visualization using D3.js
function createWordCloud(words) {
    const width = document.getElementById('wordCloud').offsetWidth;
    const height = 400;

    d3.select("#wordCloud").html("");

    const layout = d3.layout.cloud()
        .size([width, height])
        .words(words.map(d => ({
            text: d.word,
            size: 10 + d.frequency * 0.5,
            value: d.frequency
        })))
        .padding(5)
        .rotate(() => ~~(Math.random() * 2) * 90)
        .font("Impact")
        .fontSize(d => d.size)
        .on("end", draw);

    layout.start();

    function draw(words) {
        // Color scale for the words
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        d3.select("#wordCloud")
            .append("svg")
            .attr("width", layout.size()[0])
            .attr("height", layout.size()[1])
            .append("g")
            .attr("transform", `translate(${layout.size()[0] / 2},${layout.size()[1] / 2})`)
            .selectAll("text")
            .data(words)
            .enter()
            .append("text")
            .style("font-size", d => `${d.size}px`)
            .style("font-family", "Impact")
            .style("fill", (d, i) => color(i))
            .attr("text-anchor", "middle")
            .attr("transform", d => `translate(${d.x},${d.y}) rotate(${d.rotate})`)
            .text(d => d.text)
            .append("title")
            .text(d => `${d.text}: ${d.value}`);
    }
}

// Initialize event listeners when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up form submission
    const form = document.getElementById('analysisForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
});
