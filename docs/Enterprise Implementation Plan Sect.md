Enterprise Implementation Plan: Section 1 (IA & Navigation)This guide provides the detailed, production-ready HTML, CSS, and JavaScript required to implement the Information Architecture improvements. The focus is on enterprise-grade UX: smooth transitions, clear state management, accessibility (a11y), and intuitive visual feedback.Phase 1: Progressive Disclosure & Contextual Deep Dive (Section 1.1)Enterprise Objective: Prevent cognitive overload by hiding deep-dive charts until requested. When requested, provide a seamless, animated transition with loading states and clear active-row indicators.Step 1: Accessible & Robust HTML StructureWrap the charts in a dedicated panel with a rich header, action buttons, and ARIA attributes for screen readers. Include placeholder containers for skeleton loaders.<!-- Inside #page-sa, below the main hierarchy table -->
<section id="sa-deep-dive-panel" 
         class="deep-dive-hidden relative mt-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm" 
         aria-hidden="true" 
         aria-live="polite">
    
    <!-- Rich Header -->
    <header class="flex justify-between items-start mb-6 border-b border-gray-100 pb-4">
        <div>
            <p class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Deep Dive Analysis</p>
            <h3 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <span id="sa-deep-dive-node-name">Select a queue...</span>
                <span id="sa-deep-dive-status" class="px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-full hidden">Loading...</span>
            </h3>
        </div>
        <div class="flex gap-3">
            <button class="px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                ⬇ Export PDF
            </button>
            <button id="sa-close-deep-dive" class="px-3 py-1.5 text-sm text-white bg-gray-800 rounded hover:bg-gray-700 transition-colors shadow-sm">
                ✕ Close View
            </button>
        </div>
    </header>
    
    <!-- Chart Grid -->
    <div id="sa-deep-dive-content" class="grid grid-cols-1 lg:grid-cols-2 gap-6 opacity-0 transition-opacity duration-300">
        <div class="chart-container relative h-72 w-full"><canvas id="sa-trend-chart"></canvas></div>
        <div class="chart-container relative h-72 w-full"><canvas id="sa-chart-adherence"></canvas></div>
        <div class="chart-container relative h-72 w-full"><canvas id="sa-chart-forecast"></canvas></div>
        <div class="chart-container relative h-72 w-full"><canvas id="sa-chart-bias"></canvas></div>
    </div>
</section>
Step 2: Enterprise CSS Transitions & State StylingImplement a smooth slide-up and fade-in effect. Add clear visual states for the selected table row to maintain user context./* Panel Animations */
.deep-dive-hidden {
    visibility: hidden;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), 
                transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), 
                visibility 0.4s;
    height: 0;
    overflow: hidden;
    padding: 0;
    margin: 0;
    border: none;
}

.deep-dive-visible {
    visibility: visible;
    opacity: 1;
    transform: translateY(0);
    height: auto; /* Let content dictate height */
}

/* Table Row Interactions */
#sa-hierarchy-body tr {
    cursor: pointer;
    transition: all 0.2s ease;
    border-left: 3px solid transparent;
}

#sa-hierarchy-body tr:hover {
    background-color: #f8fafc; /* Tailwind slate-50 */
    border-left-color: #cbd5e1;
}

#sa-hierarchy-body tr.row-active {
    background-color: #eff6ff; /* Tailwind blue-50 */
    border-left-color: #3b82f6; /* Tailwind blue-500 */
}
Step 3: State-Aware JavaScriptManage the active row state, trigger a mock loading sequence for better UX, and smoothly reveal the data.let activeRowElement = null;

function renderHierarchyTable(data) {
    const tbody = document.getElementById('sa-hierarchy-body');
    tbody.innerHTML = ''; 

    data.forEach(row => {
        const tr = document.createElement('tr');
        // ... populate standard <td> elements ...
        
        tr.addEventListener('click', (e) => {
            // Manage Active State
            if (activeRowElement) activeRowElement.classList.remove('row-active');
            tr.classList.add('row-active');
            activeRowElement = tr;
            
            openDeepDive(row.nodeName, row.data);
        });
        
        tbody.appendChild(tr);
    });
}

function openDeepDive(nodeName, nodeData) {
    const panel = document.getElementById('sa-deep-dive-panel');
    const content = document.getElementById('sa-deep-dive-content');
    const status = document.getElementById('sa-deep-dive-status');
    
    // 1. Update UI and Show Panel
    document.getElementById('sa-deep-dive-node-name').textContent = nodeName;
    panel.classList.remove('deep-dive-hidden');
    panel.classList.add('deep-dive-visible');
    panel.setAttribute('aria-hidden', 'false');
    
    // 2. Simulate Loading State (Enterprise UX)
    content.style.opacity = '0.3';
    status.classList.remove('hidden');
    
    // Smooth scroll to panel
    setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);

    // 3. Fetch/Update Data (Simulated Async)
    setTimeout(() => {
        // updateDeepDiveCharts(nodeData); // Your actual Chart.js update logic
        content.style.opacity = '1';
        status.classList.add('hidden');
    }, 600);
}

document.getElementById('sa-close-deep-dive').addEventListener('click', () => {
    const panel = document.getElementById('sa-deep-dive-panel');
    panel.classList.remove('deep-dive-visible');
    panel.classList.add('deep-dive-hidden');
    panel.setAttribute('aria-hidden', 'true');
    if (activeRowElement) {
        activeRowElement.classList.remove('row-active');
        activeRowElement = null;
    }
});
Phase 2: Bi-directional Cross-Filtering (Section 1.2)Enterprise Objective: Visualizations must act as controls. When a user clicks a bar chart, the selected bar should highlight, unselected bars should dim, and a global filter pill should appear.Step 1: Chart.js Visual Feedback LogicModify the Chart.js instances to handle click events and dynamically update bar colors to indicate the active selection.let activeChartFilter = null; // Store the currently selected label

const execPerformersChart = new Chart(ctx, {
    type: 'bar',
    data: chartData, // Your standard data
    options: {
        interaction: { mode: 'index' },
        onClick: (event, elements, chart) => {
            if (elements.length > 0) {
                const clickedIndex = elements[0].index;
                const clickedLabel = chart.data.labels[clickedIndex];
                
                // Toggle logic: If clicking the already active filter, clear it.
                if (activeChartFilter === clickedLabel) {
                    activeChartFilter = null;
                    resetChartColors(chart);
                    removeGlobalFilterPill('Region'); 
                } else {
                    activeChartFilter = clickedLabel;
                    highlightSelectedBar(chart, clickedIndex);
                    addGlobalFilterPill('Region', clickedLabel);
                }
                // Trigger your main data refresh
                filterData(); 
            }
        }
    }
});

// Helper function to dim unselected bars
function highlightSelectedBar(chart, selectedIndex) {
    const dataset = chart.data.datasets[0];
    const defaultColor = '#3b82f6'; // Brand blue
    const dimmedColor = '#e2e8f0';  // Light gray
    
    // Create an array of colors, highlighting only the selected index
    dataset.backgroundColor = dataset.data.map((_, index) => 
        index === selectedIndex ? defaultColor : dimmedColor
    );
    chart.update('none'); // Update without full animation
}

function resetChartColors(chart) {
    const dataset = chart.data.datasets[0];
    dataset.backgroundColor = '#3b82f6'; // Reset all to brand blue
    chart.update('none');
}
Step 2: Global Filter Pill UI ManagementWhen a chart or map is clicked, dynamically render a filter pill so the user knows exactly what global state is active.function addGlobalFilterPill(category, value) {
    const container = document.getElementById('gf-active-pills'); // Ensure this div exists in your header
    
    // Check if pill for this category exists, update it, or create new
    let pill = document.getElementById(`pill-${category}`);
    if (!pill) {
        pill = document.createElement('div');
        pill.id = `pill-${category}`;
        pill.className = 'inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full border border-blue-200';
        container.appendChild(pill);
    }
    
    pill.innerHTML = `
        <span><span class="opacity-70">${category}:</span> ${value}</span>
        <button onclick="clearSpecificFilter('${category}')" class="hover:text-blue-900 focus:outline-none" aria-label="Remove filter">✕</button>
    `;
}
Phase 3: In-line Contextual Indicators (Section 1.3)Enterprise Objective: Replace raw data with immediate, actionable context. Use scalable SVG icons with robust CSS tooltips and subtle animations to draw attention to high-risk areas without breaking the table layout.Step 1: CSS for Enterprise Tooltips and Pulse AnimationAvoid standard browser title attributes. Use a CSS-only tooltip for instant, styled hover states. Add a pulse animation for critical items./* Animated Pulse for Critical Risk */
@keyframes softPulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.15); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
.risk-critical svg {
    animation: softPulse 2s infinite ease-in-out;
    color: #ef4444; /* Tailwind red-500 */
}
.risk-warning svg {
    color: #f59e0b; /* Tailwind amber-500 */
}

/* CSS-Only Tooltip */
.enterprise-tooltip {
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    margin-left: 0.5rem;
}

.enterprise-tooltip::before,
.enterprise-tooltip::after {
    position: absolute;
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    z-index: 50;
    pointer-events: none;
}

/* The Tooltip Bubble */
.enterprise-tooltip::before {
    content: attr(data-tooltip);
    bottom: 150%;
    left: 50%;
    transform: translateX(-50%) translateY(5px);
    width: max-content;
    max-width: 200px;
    padding: 0.4rem 0.75rem;
    background-color: #1e293b; /* slate-800 */
    color: white;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 0.375rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* The Tooltip Arrow */
.enterprise-tooltip::after {
    content: '';
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%) translateY(5px);
    border-width: 5px;
    border-style: solid;
    border-color: #1e293b transparent transparent transparent;
}

.enterprise-tooltip:hover::before,
.enterprise-tooltip:hover::after {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(0);
}
Step 2: Injecting SVG Badges via JavaScriptModify the table rendering loop to inject standard SVG icons (e.g., from Heroicons) rather than emojis.function renderHierarchyTable(data) {
    const tbody = document.getElementById('sa-hierarchy-body');
    // ... loop setup ...

    data.forEach(row => {
        const tr = document.createElement('tr');
        const tdName = document.createElement('td');
        
        // 1. Create a wrapper for flex alignment
        const nameWrapper = document.createElement('div');
        nameWrapper.className = 'flex items-center';
        nameWrapper.textContent = row.offeringName;

        // 2. Evaluate Risk (Example Logic)
        if (row.volatilityScore > 0.15) {
            const isCritical = row.volatilityScore > 0.25;
            
            const badge = document.createElement('div');
            badge.className = `enterprise-tooltip ${isCritical ? 'risk-critical' : 'risk-warning'}`;
            badge.setAttribute('data-tooltip', isCritical ? 'Critical Volatility Shift. Click for Business Context.' : 'Elevated Volatility noted.');
            
            // Inline SVG (Heroicons Exclamation Triangle)
            badge.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
                  <path fill-rule="evenodd" d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" clip-rule="evenodd" />
                </svg>
            `;
            
            badge.addEventListener('click', (e) => {
                e.stopPropagation(); // VERY IMPORTANT: Prevents opening the deep dive panel
                addGlobalFilterPill('Offering', row.offeringName);
                filterData();
                nav('page-bc'); // Navigate to Business Context
            });
            
            nameWrapper.appendChild(badge);
        }
        
        tdName.appendChild(nameWrapper);
        tr.appendChild(tdName);
        // ... append other <td> elements ...
        tbody.appendChild(tr);
    });
}
