import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="LABCOST – Learning and Business Cost Simulator",
    layout="centered"
)

st.title("LABCOST – Learning and Business Cost Simulator")

st.write("""
**LABCOST** is an educational tool to help students and managers understand  
**cost behavior, contribution margin, break-even analysis, and operating leverage.**
Use the sidebar inputs to simulate different scenarios.
""")

# SIDEBAR INPUTS
st.sidebar.header("Simulation Settings")

price = st.sidebar.number_input("Selling price per unit (R$)", 0.0, 10000.0, 100.0)
variable_cost = st.sidebar.number_input("Variable cost per unit (R$)", 0.0, 10000.0, 30.0)
fixed_costs = st.sidebar.number_input("Total fixed costs (R$)", 0.0, 1000000.0, 25000.0)
quantity = st.sidebar.number_input("Expected sales volume (units)", 0, 1000000, 1000)

q_min = st.sidebar.number_input("Min volume (chart)", 0, 1000000, 0)
q_max = st.sidebar.number_input("Max volume (chart)", 0, 1000000, 2000)
q_step = st.sidebar.number_input("Step", 1, 1000000, 100)

# BASIC CALCULATIONS
cm_unit = price - variable_cost
total_cm = cm_unit * quantity
total_revenue = price * quantity
total_var_cost = variable_cost * quantity
profit = total_cm - fixed_costs

# BREAK-EVEN
if cm_unit != 0:
    break_even_units = fixed_costs / cm_unit
    break_even_revenue = break_even_units * price
else:
    break_even_units = 0
    break_even_revenue = 0

# DOL
if total_cm - fixed_costs != 0:
    dol = total_cm / (total_cm - fixed_costs)
else:
    dol = 0

# RESULTS
st.header("Key Results")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Contribution Margin")
    st.write(f"Unit CM: **R$ {cm_unit:,.2f}**")
    st.write(f"Total CM: **R$ {total_cm:,.2f}**")

with col2:
    st.subheader("Break-even Point")
    st.write(f"Units: **{break_even_units:,.0f}**")
    st.write(f"Revenue: **R$ {break_even_revenue:,.2f}**")

st.subheader("Profitability")
st.write(f"Total revenue: **R$ {total_revenue:,.2f}**")
st.write(f"Total variable costs: **R$ {total_var_cost:,.2f}**")
st.write(f"Profit (Operating income): **R$ {profit:,.2f}**")

st.subheader("Degree of Operating Leverage (DOL)")
st.write(f"DOL: **{dol:,.2f}**")

# CHART
if q_max > q_min:
    volumes = list(range(q_min, q_max + 1, q_step))
    df = pd.DataFrame({
        "Volume": volumes,
        "Revenue": [price * q for q in volumes],
        "Variable Cost": [variable_cost * q for q in volumes],
        "Profit": [(price - variable_cost) * q - fixed_costs for q in volumes]
    }).set_index("Volume")

    st.subheader("Profit by Sales Volume")
    st.line_chart(df)

st.caption("LABCOST – Educational use only.")
