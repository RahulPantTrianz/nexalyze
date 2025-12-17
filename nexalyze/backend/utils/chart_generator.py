"""
Chart Generation Utility
Generates charts as base64-encoded images for use in chat and API responses.
"""
import base64
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Configure matplotlib for high-quality output
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


class ChartGenerator:
    """
    Generates charts as base64-encoded PNG images for embedding in API responses.
    """
    
    @staticmethod
    def _fig_to_base64(fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        base64_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        buf.close()
        return base64_str
    
    @classmethod
    def generate_pie_chart(cls, data: Dict[str, int], title: str = "Distribution") -> str:
        """
        Generate a pie chart as base64.
        
        Args:
            data: Dictionary of {label: value}
            title: Chart title
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Limit to top 8 segments, group rest as "Other"
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_items) > 8:
                top_items = dict(sorted_items[:7])
                other_value = sum(v for _, v in sorted_items[7:])
                top_items["Other"] = other_value
                data = top_items
            
            labels = list(data.keys())
            sizes = list(data.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%',
                colors=colors, startangle=90, pctdistance=0.75
            )
            
            plt.setp(autotexts, size=9, weight="bold", color="white")
            plt.setp(texts, size=10)
            
            # Add title
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # Add center circle for donut effect
            centre_circle = plt.Circle((0, 0), 0.50, fc='white')
            ax.add_patch(centre_circle)
            
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Pie chart generation failed: {e}")
            return ""
    
    @classmethod
    def generate_bar_chart(cls, data: Dict[str, int], title: str = "Comparison",
                          xlabel: str = "Category", ylabel: str = "Count",
                          horizontal: bool = False) -> str:
        """
        Generate a bar chart as base64.
        
        Args:
            data: Dictionary of {label: value}
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            horizontal: Whether to create horizontal bars
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Sort and limit data
            sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:12]
            labels = [item[0] for item in sorted_data]
            values = [item[1] for item in sorted_data]
            
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
            
            if horizontal:
                bars = ax.barh(labels, values, color=colors)
                ax.set_xlabel(ylabel, fontsize=12, fontweight='bold')
                ax.set_ylabel(xlabel, fontsize=12, fontweight='bold')
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width * 1.02, bar.get_y() + bar.get_height()/2,
                           f'{int(width):,}', ha='left', va='center', fontweight='bold')
            else:
                bars = ax.bar(labels, values, color=colors)
                ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
                ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height * 1.02,
                           f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.grid(axis='y' if not horizontal else 'x', alpha=0.3)
            
            plt.tight_layout()
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Bar chart generation failed: {e}")
            return ""
    
    @classmethod
    def generate_line_chart(cls, data: Dict[str, float], title: str = "Trend",
                           xlabel: str = "Time", ylabel: str = "Value") -> str:
        """
        Generate a line chart as base64.
        
        Args:
            data: Dictionary of {x_label: y_value}
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x_labels = list(data.keys())
            y_values = list(data.values())
            
            # Plot line with markers
            ax.plot(x_labels, y_values, marker='o', linewidth=2.5, 
                   markersize=8, color='#2E86AB', markerfacecolor='white',
                   markeredgewidth=2)
            
            # Fill area under line
            ax.fill_between(x_labels, y_values, alpha=0.3, color='#2E86AB')
            
            ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Line chart generation failed: {e}")
            return ""
    
    @classmethod
    def generate_comparison_table(cls, data: List[Dict[str, Any]], columns: List[str],
                                  title: str = "Comparison") -> str:
        """
        Generate a styled table as base64 image.
        
        Args:
            data: List of dictionaries with row data
            columns: List of column names to display
            title: Table title
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Filter to specified columns that exist
            available_cols = [c for c in columns if c in df.columns]
            if not available_cols:
                return ""
            
            df = df[available_cols].head(10)  # Limit to 10 rows
            
            # Create figure
            fig, ax = plt.subplots(figsize=(14, max(4, len(df) * 0.6)))
            ax.axis('tight')
            ax.axis('off')
            
            # Create table
            table = ax.table(
                cellText=df.values,
                colLabels=df.columns,
                cellLoc='center',
                loc='center',
                colColours=['#2E86AB'] * len(df.columns)
            )
            
            # Style table
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.8)
            
            # Style header cells
            for i in range(len(df.columns)):
                table[(0, i)].set_text_props(weight='bold', color='white')
                table[(0, i)].set_facecolor('#2E86AB')
            
            # Alternate row colors
            for i in range(1, len(df) + 1):
                for j in range(len(df.columns)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#f0f0f0')
                    else:
                        table[(i, j)].set_facecolor('white')
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Table generation failed: {e}")
            return ""
    
    @classmethod
    def generate_competitive_matrix(cls, companies: List[Dict], dimensions: List[str] = None,
                                    title: str = "Competitive Matrix") -> str:
        """
        Generate a competitive matrix heatmap as base64.
        
        Args:
            companies: List of company data dictionaries
            dimensions: List of dimension names for comparison
            title: Chart title
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            if not dimensions:
                dimensions = ["Innovation", "Market Share", "Growth", "Technology", "Brand"]
            
            # Generate scores for each company on each dimension
            np.random.seed(42)  # For reproducible demo scores
            company_names = [c.get('name', f'Company {i}')[:15] for i, c in enumerate(companies[:8])]
            
            # Create score matrix
            scores = np.random.uniform(4, 10, size=(len(company_names), len(dimensions)))
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            im = ax.imshow(scores, cmap='RdYlGn', aspect='auto', vmin=0, vmax=10)
            
            # Set labels
            ax.set_xticks(np.arange(len(dimensions)))
            ax.set_yticks(np.arange(len(company_names)))
            ax.set_xticklabels(dimensions, fontsize=10)
            ax.set_yticklabels(company_names, fontsize=10)
            
            # Rotate x labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            
            # Add text annotations
            for i in range(len(company_names)):
                for j in range(len(dimensions)):
                    text = ax.text(j, i, f'{scores[i, j]:.1f}',
                                  ha="center", va="center", color="black", fontweight='bold')
            
            # Add colorbar
            cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
            cbar.ax.set_ylabel("Score (0-10)", rotation=-90, va="bottom", fontsize=12)
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Competitive matrix generation failed: {e}")
            return ""
    
    @classmethod
    def generate_funding_chart(cls, companies: List[Dict], title: str = "Funding Overview") -> str:
        """
        Generate a funding analysis chart as base64.
        
        Args:
            companies: List of company dictionaries
            title: Chart title
        
        Returns:
            Base64-encoded PNG string
        """
        try:
            # Parse funding data
            funding_data = []
            for c in companies:
                funding_str = c.get('funding', '0')
                if funding_str:
                    try:
                        # Parse funding amount (handle $10M, $1B format)
                        amount = 0
                        if 'B' in str(funding_str).upper():
                            amount = float(str(funding_str).upper().replace('$', '').replace('B', '')) * 1000
                        elif 'M' in str(funding_str).upper():
                            amount = float(str(funding_str).upper().replace('$', '').replace('M', ''))
                        elif 'K' in str(funding_str).upper():
                            amount = float(str(funding_str).upper().replace('$', '').replace('K', '')) / 1000
                        
                        if amount > 0:
                            funding_data.append({
                                'name': c.get('name', 'Unknown')[:20],
                                'funding': amount,
                                'stage': c.get('stage', 'Unknown')
                            })
                    except:
                        pass
            
            if not funding_data:
                return ""
            
            # Sort by funding and take top 10
            funding_data = sorted(funding_data, key=lambda x: x['funding'], reverse=True)[:10]
            
            fig, ax = plt.subplots(figsize=(12, 7))
            
            names = [d['name'] for d in funding_data]
            amounts = [d['funding'] for d in funding_data]
            stages = [d['stage'] for d in funding_data]
            
            # Color by stage
            stage_colors = {
                'Seed': '#FFC107',
                'Series A': '#4CAF50',
                'Series B': '#2196F3',
                'Series C': '#9C27B0',
                'Series D': '#E91E63',
                'Public': '#F44336',
                'Unknown': '#9E9E9E'
            }
            colors = [stage_colors.get(s, '#9E9E9E') for s in stages]
            
            bars = ax.barh(names, amounts, color=colors)
            
            ax.set_xlabel('Funding ($ Millions)', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width * 1.02, bar.get_y() + bar.get_height()/2,
                       f'${width:.1f}M', ha='left', va='center', fontweight='bold')
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=c, label=s) for s, c in stage_colors.items()
                              if s in stages]
            ax.legend(handles=legend_elements, loc='lower right', title='Stage')
            
            plt.tight_layout()
            return cls._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"Funding chart generation failed: {e}")
            return ""


def generate_chart_for_chat(chart_type: str, data: Any, title: str = "") -> Dict[str, str]:
    """
    Generate a chart for chat interface.
    
    Args:
        chart_type: Type of chart ('pie', 'bar', 'line', 'table', 'matrix', 'funding')
        data: Data for the chart
        title: Chart title
    
    Returns:
        Dictionary with base64 image and metadata
    """
    generator = ChartGenerator()
    base64_img = ""
    
    try:
        if chart_type == "pie":
            base64_img = generator.generate_pie_chart(data, title or "Distribution")
        elif chart_type == "bar":
            base64_img = generator.generate_bar_chart(data, title or "Comparison", horizontal=True)
        elif chart_type == "line":
            base64_img = generator.generate_line_chart(data, title or "Trend")
        elif chart_type == "table":
            columns = data.get('columns', [])
            rows = data.get('rows', [])
            base64_img = generator.generate_comparison_table(rows, columns, title or "Data Table")
        elif chart_type == "matrix":
            base64_img = generator.generate_competitive_matrix(data, title=title or "Competitive Matrix")
        elif chart_type == "funding":
            base64_img = generator.generate_funding_chart(data, title or "Funding Analysis")
        
        return {
            "type": "chart",
            "chart_type": chart_type,
            "title": title,
            "image_base64": base64_img,
            "mime_type": "image/png"
        }
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {"type": "error", "message": str(e)}
