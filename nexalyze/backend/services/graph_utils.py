"""
Graph Utilities for Report Visualization
Handles dynamic chart generation from <graph> tags in HTML content
"""
import base64
import io
import re
import logging
import asyncio
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def process_graph_tags_sync(html_content: str, data_context: Dict[str, Any] = None) -> str:
    """
    Synchronous wrapper for process_graph_tags.
    Useful when calling from synchronous code.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Create new event loop in a thread for sync execution
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(process_graph_tags(html_content, data_context)))
            return future.result(timeout=60)
    else:
        return loop.run_until_complete(process_graph_tags(html_content, data_context))


async def process_graph_tags(html_content: str, data_context: Dict[str, Any] = None) -> str:
    """
    Process <graph> tags in HTML content and replace them with embedded base64 images.
    
    Args:
        html_content: HTML string potentially containing <graph> tags with Python code
        data_context: Optional dictionary of data variables to make available during graph execution
        
    Returns:
        Processed HTML with <graph> tags replaced by <img> tags containing base64 images
    """
    if '<graph>' not in html_content:
        return html_content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        graph_tags = soup.find_all('graph')
        
        if not graph_tags:
            return html_content
        
        logger.info(f"Found {len(graph_tags)} graph tags to process")
        
        for graph_tag in graph_tags:
            graph_code = graph_tag.string.strip() if graph_tag.string else ""
            
            if not graph_code:
                logger.warning("Empty graph tag found, removing")
                graph_tag.decompose()
                continue
            
            # Try to execute the graph code and convert to image
            img_base64 = await execute_graph_code(graph_code, data_context)
            
            if img_base64:
                # Create img tag to replace graph tag
                img_tag = soup.new_tag('img')
                img_tag['src'] = f"data:image/png;base64,{img_base64}"
                img_tag['alt'] = "Generated Chart"
                img_tag['class'] = "chart-image"
                img_tag['style'] = "max-width:100%; height:auto; display:block; margin:20px auto;"
                graph_tag.replace_with(img_tag)
                logger.info("Successfully replaced graph tag with embedded image")
            else:
                # Remove failed graph tag
                logger.warning("Failed to generate graph, removing tag")
                graph_tag.decompose()
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error processing graph tags: {e}")
        return html_content


async def execute_graph_code(code: str, data_context: Dict[str, Any] = None, max_retries: int = 2) -> Optional[str]:
    """
    Execute Python graph code and return base64 encoded PNG image.
    
    Args:
        code: Python code that generates a matplotlib figure
        data_context: Optional data variables to inject into execution environment
        max_retries: Number of retry attempts with AI code fixing
        
    Returns:
        Base64 encoded PNG image string, or None if execution fails
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    
    current_code = code
    
    for attempt in range(max_retries + 1):
        try:
            # Close any existing figures
            plt.close('all')
            
            # Build execution environment
            exec_environment = {
                "plt": plt,
                "np": np,
                "pd": pd,
                "__builtins__": __builtins__
            }
            
            # Add any data context
            if data_context:
                exec_environment.update(data_context)
            
            # Try importing seaborn if available
            try:
                import seaborn as sns
                exec_environment["sns"] = sns
            except ImportError:
                pass
            
            logger.info(f"Executing graph code (attempt {attempt + 1}):\n{current_code[:200]}...")
            
            # Execute the code
            exec(current_code, exec_environment, exec_environment)
            
            # Check if a figure was created
            if plt.get_fignums():
                # Capture the figure as base64 PNG
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                buf.seek(0)
                img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                plt.close('all')
                logger.info("Successfully generated graph image")
                return img_base64
            else:
                logger.warning("Graph code executed but no figure was created")
                raise ValueError("No matplotlib figure generated")
                
        except Exception as e:
            logger.error(f"Graph execution failed (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries:
                # Try to fix the code using AI
                fixed_code = await fix_graph_code(current_code, str(e))
                if fixed_code:
                    current_code = fixed_code
                    logger.info("Received fixed code from AI, retrying...")
                else:
                    logger.warning("Could not get fixed code from AI")
                    break
            else:
                logger.error(f"All {max_retries + 1} attempts failed for graph execution")
    
    plt.close('all')
    return None


async def fix_graph_code(failed_code: str, error_message: str) -> Optional[str]:
    """
    Use AI to fix failed graph code.
    
    Args:
        failed_code: The Python code that failed to execute
        error_message: The error message from the failed execution
        
    Returns:
        Fixed Python code, or None if AI call fails
    """
    try:
        from services.bedrock_service import get_bedrock_service
        bedrock_service = get_bedrock_service()
        
        fix_prompt = f"""You are an expert Python data visualization programmer. Fix the following code that failed to generate a matplotlib graph.

**Failed Code:**
```python
{failed_code}
```

**Error Message:**
{error_message}

**Instructions:**
1. Fix the code to run successfully and produce a matplotlib plot
2. Use matplotlib.pyplot as plt
3. Ensure the plot is properly created with plt.figure() or plt.subplots()
4. Only return the corrected Python code, no explanations
5. The code should work standalone with standard imports

**Return only the corrected Python code:**"""

        response = await bedrock_service.generate_text(fix_prompt, temperature=0.2)
        
        # Extract code from response
        if "```python" in response:
            code_match = re.search(r"```python\n(.*?)\n```", response, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
        elif "```" in response:
            code_match = re.search(r"```\n?(.*?)\n?```", response, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
        
        # If no code blocks, assume the whole response is code
        return response.strip()
        
    except Exception as e:
        logger.error(f"Failed to get fixed code from AI: {e}")
        return None


def generate_sample_visualizations(topic: str, data: Dict[str, Any] = None) -> str:
    """
    Generate sample visualization HTML with graph tags based on available data.
    
    Args:
        topic: The report topic
        data: Available data for visualization
        
    Returns:
        HTML string with graph tags for visualizations
    """
    html_parts = []
    
    # Market Distribution Chart
    html_parts.append("""
<div class="chart-section">
    <h3>Market Distribution Analysis</h3>
    <graph>
import matplotlib.pyplot as plt
import numpy as np

# Sample market distribution data
categories = ['Technology', 'Healthcare', 'Finance', 'Retail', 'Other']
values = [35, 25, 20, 12, 8]
colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']

fig, ax = plt.subplots(figsize=(10, 6))
wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%', 
                                   colors=colors, startangle=90)
plt.setp(autotexts, size=10, weight="bold")
ax.set_title('Market Distribution by Sector', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
    </graph>
</div>
""")
    
    # Growth Trend Chart
    html_parts.append("""
<div class="chart-section">
    <h3>Growth Trends</h3>
    <graph>
import matplotlib.pyplot as plt
import numpy as np

# Sample growth data
years = ['2020', '2021', '2022', '2023', '2024']
growth = [15, 22, 35, 48, 62]

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(years, growth, marker='o', linewidth=3, markersize=10, color='#667eea')
ax.fill_between(years, growth, alpha=0.3, color='#667eea')
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Market Size ($ Billions)', fontsize=12, fontweight='bold')
ax.set_title('Market Growth Trend', fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)

for i, v in enumerate(growth):
    ax.annotate(f'${v}B', (years[i], v), textcoords="offset points", 
                xytext=(0,10), ha='center', fontweight='bold')

plt.tight_layout()
    </graph>
</div>
""")
    
    # Competitive Landscape
    html_parts.append("""
<div class="chart-section">
    <h3>Competitive Landscape</h3>
    <graph>
import matplotlib.pyplot as plt
import numpy as np

# Sample company data
companies = ['Company A', 'Company B', 'Company C', 'Company D', 'Company E']
funding = [150, 95, 75, 45, 30]
employees = [500, 350, 250, 150, 80]

fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.viridis(np.linspace(0, 1, len(companies)))

scatter = ax.scatter(funding, employees, s=[f*3 for f in funding], c=colors, alpha=0.7, edgecolors='black', linewidth=1)

for i, company in enumerate(companies):
    ax.annotate(company, (funding[i], employees[i]), textcoords="offset points",
                xytext=(5,5), fontsize=9)

ax.set_xlabel('Funding ($ Millions)', fontsize=12, fontweight='bold')
ax.set_ylabel('Employees', fontsize=12, fontweight='bold')
ax.set_title('Competitive Landscape (Bubble Size = Funding)', fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)
plt.tight_layout()
    </graph>
</div>
""")
    
    return '\n'.join(html_parts)
