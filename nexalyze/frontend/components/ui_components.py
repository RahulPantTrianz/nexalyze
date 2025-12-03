import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional

def create_metric_card(title: str, value: str, subtitle: str, icon: str, color: str = "#667eea"):
    """Create a modern metric card with icon and gradient"""
    st.markdown(f"""
    <div class="metric-card bounce-in">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="width: 50px; height: 50px; background: linear-gradient(135deg, {color} 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                <span style="font-size: 1.5rem;">{icon}</span>
            </div>
            <div>
                <h3 style="margin: 0; color: #2c3e50; font-size: 2rem; font-weight: 700;">{value}</h3>
                <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">{title}</p>
            </div>
        </div>
        <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); color: white; padding: 0.5rem; border-radius: 8px; text-align: center; font-size: 0.8rem;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_page_header(title: str, subtitle: str, icon: str = ""):
    """Create a consistent page header"""
    st.markdown(f"""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">{icon} {title}</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_info_card(title: str, content: str, icon: str, color: str = "#667eea"):
    """Create an information card"""
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 1rem 0;">
        <h4 style="color: {color}; margin-bottom: 1rem;">{icon} {title}</h4>
        <p style="color: #6c757d; margin: 0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_enhanced_button(text: str, icon: str = "", key: str = None, use_container_width: bool = True):
    """Create an enhanced button with consistent styling"""
    return st.button(f"{icon} {text}", key=key, use_container_width=use_container_width)

def create_loading_spinner(text: str = "Loading..."):
    """Create a custom loading spinner"""
    return st.spinner(f"🔄 {text}")

def create_success_message(message: str):
    """Create a success message"""
    st.markdown(f"""
    <div class="success-message">
        ✅ {message}
    </div>
    """, unsafe_allow_html=True)

def create_error_message(message: str):
    """Create an error message"""
    st.markdown(f"""
    <div class="error-message">
        ❌ {message}
    </div>
    """, unsafe_allow_html=True)

def create_enhanced_chart_container(title: str, chart_type: str = "default"):
    """Create a container for enhanced charts"""
    colors = {
        "default": "#667eea",
        "success": "#4ecdc4", 
        "warning": "#ffeaa7",
        "danger": "#fd79a8"
    }
    color = colors.get(chart_type, colors["default"])
    
    return st.markdown(f"""
    <div class="metric-card">
        <h3 style="color: #2c3e50; margin-bottom: 1rem; text-align: center;">{title}</h3>
    """, unsafe_allow_html=True)

def create_insights_section(insights: List[Dict[str, str]]):
    """Create an insights section with multiple cards"""
    st.markdown("""
    <div class="fade-in">
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 2rem; border-radius: 20px; margin: 2rem 0;">
            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 1.5rem;">💡 Key Insights</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
    """, unsafe_allow_html=True)
    
    for insight in insights:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h4 style="color: {insight.get('color', '#667eea')}; margin-bottom: 1rem;">{insight.get('icon', '💡')} {insight.get('title', 'Insight')}</h4>
            <p style="color: #6c757d; margin: 0;">{insight.get('content', 'No content available')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)

def create_quick_actions_section(actions: List[Dict[str, str]]):
    """Create a quick actions section"""
    st.markdown("""
    <div class="slide-in-left">
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem;">
            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 1.5rem;">⚡ Quick Actions</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
    """, unsafe_allow_html=True)
    
    cols = st.columns(len(actions))
    for i, action in enumerate(actions):
        with cols[i]:
            if st.button(f"{action.get('icon', '⚡')} {action.get('text', 'Action')}", 
                        key=f"quick_action_{i}", 
                        use_container_width=True):
                if action.get('callback'):
                    action['callback']()
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)

def create_enhanced_pie_chart(data: pd.DataFrame, values_col: str, names_col: str, title: str = ""):
    """Create an enhanced pie chart"""
    colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4', '#44a08d', '#ffeaa7']
    
    fig = px.pie(data, 
                values=values_col, 
                names=names_col,
                color_discrete_sequence=colors,
                title=title,
                hole=0.4)
    
    fig.update_layout(
        font_family="Inter",
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate=f'<b>%{{label}}</b><br>{values_col}: %{{value}}<br>Percentage: %{{percent}}<extra></extra>'
    )
    
    return fig

def create_enhanced_line_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str = ""):
    """Create an enhanced line chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data[x_col],
        y=data[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(color='#667eea', width=4),
        marker=dict(size=8, color='#667eea'),
        hovertemplate=f'<b>%{{x}}</b><br>{y_col}: %{{y}}<extra></extra>'
    ))
    
    fig.update_layout(
        font_family="Inter",
        xaxis_title=x_col,
        yaxis_title=y_col,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='x unified'
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig

def create_company_card(company: Dict[str, str]):
    """Create an enhanced company card"""
    industry_colors = {
        'Artificial Intelligence': '#e3f2fd',
        'Education Technology': '#f3e5f5',
        'Financial Technology': '#e8f5e8',
        'Healthcare': '#fff3e0',
        'Software as a Service': '#fce4ec',
        'Consumer': '#f1f8e9',
        'B2B': '#e0f2f1',
        'Fintech': '#e8f5e8'
    }
    
    industry = company.get('industry', 'Unknown')
    card_color = industry_colors.get(industry, '#f5f5f5')
    
    website_link = ""
    if company.get('website') and company['website'] != 'N/A':
        website_link = f'<a href="{company["website"]}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: 500;">🌐 Website</a>'
    
    st.markdown(f"""
    <div style="
        border: 2px solid #e0e0e0; 
        border-radius: 15px; 
        padding: 20px; 
        margin: 10px 0; 
        background: linear-gradient(135deg, {card_color} 0%, #ffffff 100%);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        height: 100%;
        min-height: 350px;
    ">
        <!-- Company Header -->
        <div style="display: flex; align-items: center; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(0,0,0,0.1);">
            <div style="
                width: 50px; 
                height: 50px; 
                background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                margin-right: 15px;
                font-size: 20px;
                color: white;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
            ">
                {company.get('name', 'U')[0].upper()}
            </div>
            <div style="flex: 1;">
                <h3 style="margin: 0; color: #2c3e50; font-size: 20px; font-weight: 700; line-height: 1.2;">
                    {company.get('name', 'Unknown Company')}
                </h3>
                <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 14px; font-weight: 500;">
                    {industry}
                </p>
                <p style="margin: 3px 0 0 0; color: #95a5a6; font-size: 12px;">
                    Founded {company.get('founded_year', 'N/A')} • {company.get('location', 'N/A')}
                </p>
            </div>
        </div>
        
        <!-- Description -->
        <div style="margin-bottom: 15px;">
            <p style="
                color: #5a6c7d; 
                margin: 0; 
                line-height: 1.4;
                font-size: 14px;
                font-style: italic;
                background: rgba(255,255,255,0.7);
                padding: 12px;
                border-radius: 8px;
                border-left: 3px solid #667eea;
                max-height: 60px;
                overflow: hidden;
            ">
                {company.get('description', 'No description available')[:120]}{'...' if len(company.get('description', '')) > 120 else ''}
            </p>
        </div>
        
        <!-- Key Metrics Grid - Only show available YC data -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; text-align: center; border: 1px solid rgba(0,0,0,0.1);">
                <div style="font-size: 18px; margin-bottom: 3px;">📅</div>
                <div style="font-size: 11px; color: #6c757d; margin-bottom: 3px;">Founded</div>
                <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">{company.get('founded_year', 'N/A')}</div>
            </div>
            <div style="background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; text-align: center; border: 1px solid rgba(0,0,0,0.1);">
                <div style="font-size: 18px; margin-bottom: 3px;">🚀</div>
                <div style="font-size: 11px; color: #6c757d; margin-bottom: 3px;">YC Batch</div>
                <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">{company.get('yc_batch', 'N/A')}</div>
            </div>
            <div style="background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; text-align: center; border: 1px solid rgba(0,0,0,0.1);">
                <div style="font-size: 18px; margin-bottom: 3px;">📍</div>
                <div style="font-size: 11px; color: #6c757d; margin-bottom: 3px;">Location</div>
                <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">{company.get('location', 'N/A')[:20]}</div>
            </div>
            <div style="background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; text-align: center; border: 1px solid rgba(0,0,0,0.1);">
                <div style="font-size: 18px; margin-bottom: 3px;">🏷️</div>
                <div style="font-size: 11px; color: #6c757d; margin-bottom: 3px;">Industry</div>
                <div style="font-size: 14px; font-weight: 600; color: #2c3e50;">{company.get('industry', 'N/A')[:20]}</div>
            </div>
        </div>
        
        <!-- Website Link -->
        <div style="text-align: center; margin-bottom: 15px;">
            {website_link}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_progress_bar(current: int, total: int, label: str = ""):
    """Create a custom progress bar"""
    progress = current / total if total > 0 else 0
    percentage = int(progress * 100)
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #2c3e50; font-weight: 600;">{label}</span>
            <span style="color: #7f8c8d;">{current}/{total} ({percentage}%)</span>
        </div>
        <div style="background: #e9ecef; border-radius: 10px; height: 8px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
