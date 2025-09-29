from enum import Enum

css = """
/* Import Custom Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Merriweather+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,300;1,400;1,500;1,600;1,700;1,800&display=swap');

/* Professional Dark Theme */
:root {
    --primary-color: #00d4aa;
    --secondary-color: #1a1a1a;
    --accent-color: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --success-color: #00d4aa;
    --danger-color: #ff6b6b;
    --warning-color: #ffd93d;
    --info-color: #4dabf7;
    --border-color: #404040;
    --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Global Styles */
body {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Custom Font Styles for Headers */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Merriweather Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    font-style: normal !important;
}

/* Block Headers with Professional Styling */
h1 {
    font-family: 'Merriweather Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    font-style: normal !important;
}

h2 {
    font-family: 'Merriweather Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.35px !important;
    font-style: normal !important;
}

h3 {
    font-family: 'Merriweather Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    font-style: normal !important;
}

/* Gradio Container */
.gradio-container {
    background: transparent !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Cards and Panels */
.panel, .block {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow) !important;
    margin: 8px !important;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    margin-bottom: 16px !important;
}

/* Portfolio Value Display */
.portfolio-value {
    background: linear-gradient(135deg, var(--primary-color), #00b894) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    text-align: center !important;
    box-shadow: 0 8px 32px rgba(0, 212, 170, 0.3) !important;
    border: 1px solid rgba(0, 212, 170, 0.2) !important;
}

.portfolio-value h2 {
    color: white !important;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.portfolio-value .subtitle {
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 1.1rem !important;
    margin-top: 8px !important;
}

/* Strategy Info Panel */
.strategy-info {
    background: rgba(45, 45, 45, 0.8) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    border-left: 4px solid var(--primary-color) !important;
}

.strategy-info h3 {
    color: var(--primary-color) !important;
    font-size: 1.3rem !important;
    margin-bottom: 16px !important;
}

.strategy-info .info-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
    gap: 12px !important;
}

.strategy-info .info-item {
    display: flex !important;
    justify-content: space-between !important;
    padding: 8px 0 !important;
    border-bottom: 1px solid var(--border-color) !important;
}

.strategy-info .info-label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

.strategy-info .info-value {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Logs Console */
.logs-console {
    background: #0a0a0a !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 16px !important;
    font-family: 'Fira Code', 'Monaco', 'Consolas', monospace !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    max-height: 300px !important;
    overflow-y: auto !important;
}

.logs-console::-webkit-scrollbar {
    width: 6px !important;
}

.logs-console::-webkit-scrollbar-track {
    background: #1a1a1a !important;
    border-radius: 3px !important;
}

.logs-console::-webkit-scrollbar-thumb {
    background: var(--primary-color) !important;
    border-radius: 3px !important;
}

/* Data Tables */
.dataframe-fix-small .table-wrap,
.dataframe-fix .table-wrap {
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    overflow: hidden !important;
}

.dataframe-fix-small .table-wrap {
    min-height: 150px !important;
    max-height: 300px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

.dataframe-fix-small .table-wrap table {
    width: 100% !important;
    table-layout: fixed !important;
}

.dataframe-fix-small .table-wrap::-webkit-scrollbar {
    width: 8px !important;
}

.dataframe-fix-small .table-wrap::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 4px !important;
}

.dataframe-fix-small .table-wrap::-webkit-scrollbar-thumb {
    background: var(--primary-color) !important;
    border-radius: 4px !important;
}

.dataframe-fix-small .table-wrap::-webkit-scrollbar-thumb:hover {
    background: #00b894 !important;
}

.dataframe-fix .table-wrap {
    min-height: 200px !important;
    max-height: 200px !important;
}

/* Table Headers */
.dataframe-fix-small th,
.dataframe-fix th {
    background: var(--accent-color) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    padding: 12px !important;
    border-bottom: 2px solid var(--primary-color) !important;
}

/* Table Cells */
.dataframe-fix-small td,
.dataframe-fix td {
    color: var(--text-secondary) !important;
    padding: 10px 12px !important;
    border-bottom: 1px solid var(--border-color) !important;
}

/* Hover Effects */
.dataframe-fix-small tr:hover,
.dataframe-fix tr:hover {
    background: rgba(0, 212, 170, 0.1) !important;
}

/* Status Indicators */
.positive-pnl {
    color: var(--success-color) !important;
    font-weight: 600 !important;
}

.negative-pnl {
    color: var(--danger-color) !important;
    font-weight: 600 !important;
}

.positive-bg {
    background: linear-gradient(135deg, var(--success-color), #00b894) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 4px 8px !important;
    border-radius: 4px !important;
}

.negative-bg {
    background: linear-gradient(135deg, var(--danger-color), #ff5252) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 4px 8px !important;
    border-radius: 4px !important;
}

/* Buttons */
button {
    background: linear-gradient(135deg, var(--primary-color), #00b894) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3) !important;
}

button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 212, 170, 0.4) !important;
}

/* Charts */
.plotly {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
}

/* Footer */
footer {
    display: none !important;
}

/* Loading States */
.loading {
    opacity: 0.7 !important;
    pointer-events: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .strategy-info .info-grid {
        grid-template-columns: 1fr !important;
    }
    
    .portfolio-value h2 {
        font-size: 2rem !important;
    }
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 8px !important;
    height: 8px !important;
}

::-webkit-scrollbar-track {
    background: var(--secondary-color) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-color) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb:hover {
    background: #00b894 !important;
}
"""


js = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

class Color(Enum):
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    BLUE = "#0000ee"
    MAGENTA = "#aa00dd"
    CYAN = "#00dddd"
    WHITE = "#87CEEB"
