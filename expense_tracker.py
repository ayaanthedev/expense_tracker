import json
from datetime import datetime
from pathlib import Path
import streamlit as st

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Expense Tracker", page_icon="📊", layout="wide")

# Inject original clean styling
st.html(
    """
    <style>
    .stApp { background-color: #f1f5f9; color: #020617; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] { color: #020617 !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #334155 !important; font-weight: bold; }
    h1, h2, h3 { color: #020617 !important; }
    </style>
    """
)

# ---------- DATA STORAGE CONFIGURATION ----------
# Streamlit Cloud utilizes a read-write scratch space directory
DATA_FILE = Path("expenses_state.json")

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Shopping",
    "Entertainment",
    "Health",
    "Education",
    "Travel",
    "Gifts",
    "Subscriptions",
    "Savings",
    "Pets",
    "Other",
]

CATEGORY_COLORS = {
    "Food": "#f97316",
    "Transport": "#0ea5e9",
    "Bills": "#ef4444",
    "Shopping": "#a855f7",
    "Entertainment": "#ec4899",
    "Health": "#22c55e",
    "Education": "#6366f1",
    "Travel": "#14b8a6",
    "Gifts": "#eab308",
    "Subscriptions": "#64748b",
    "Savings": "#10b981",
    "Pets": "#f59e0b",
    "Other": "#94a3b8",
}

# ---------- SCRIPT LOGIC (Your Friend's Original Functions) ----------


def parse_money(raw: str) -> float:
    text = str(raw).strip().lower().replace(",", "")
    text = text.replace("rs", "").replace("inr", "").strip()
    if not text:
        raise ValueError("empty amount")

    multiplier = 1.0
    suffix_map = {
        "crore": 10_000_000.0,
        "cr": 10_000_000.0,
        "lakh": 100_000.0,
        "lac": 100_000.0,
        "l": 100_000.0,
        "m": 1_000_000.0,
        "k": 1_000.0,
    }
    for suffix, factor in suffix_map.items():
        if text.endswith(suffix):
            multiplier = factor
            text = text[: -len(suffix)].strip()
            break

    value = float(text) * multiplier
    if value < 0:
        raise ValueError("negative amount")
    return round(value, 2)


def to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    if isinstance(value, str):
        try:
            return parse_money(value)
        except ValueError:
            return 0.0
    return 0.0


def indian_number(value: float) -> str:
    sign = "-" if value < 0 else ""
    amount = f"{abs(value):.2f}"
    int_part, frac = amount.split(".")
    if len(int_part) <= 3:
        return f"{sign}{int_part}.{frac}"
    last3 = int_part[-3:]
    rest = int_part[:-3]
    chunks = []
    while len(rest) > 2:
        chunks.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        chunks.append(rest)
    grouped = ",".join(reversed(chunks)) + "," + last3
    return f"{sign}{grouped}.{frac}"


def compact(value: float) -> str:
    abs_v = abs(value)
    sign = "-" if value < 0 else ""
    if abs_v >= 10_000_000:
        return f"{sign}{abs_v / 10_000_000:.2f} Cr"
    if abs_v >= 100_000:
        return f"{sign}{abs_v / 100_000:.2f} L"
    if abs_v >= 1_000:
        return f"{sign}{abs_v / 1_000:.2f}k"
    return f"{sign}{abs_v:.2f}"


def money_label(value: float) -> str:
    return f"Rs {indian_number(value)} ({compact(value)})"


# ---------- STATE MANAGEMENT ----------


def load_state():
    if "app_state" not in st.session_state:
        state = {"salary": 0.0, "limit": 0.0, "expenses": []}
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    state["salary"] = to_float(data.get("salary", 0.0))
                    state["limit"] = to_float(data.get("spending_limit", 0.0))
                    expenses_raw = data.get("expenses", [])
                    if isinstance(expenses_raw, list):
                        for item in expenses_raw:
                            if isinstance(item, dict):
                                state["expenses"].append(
                                    {
                                        "title": str(
                                            item.get("title", "Untitled")
                                        ),
                                        "category": str(
                                            item.get("category", "Other")
                                        ),
                                        "amount": to_float(
                                            item.get("amount", 0.0)
                                        ),
                                    }
                                )
            except Exception:
                pass
        st.session_state.app_state = state


def save_state():
    if "app_state" in st.session_state:
        payload = {
            "salary": st.session_state.app_state["salary"],
            "spending_limit": st.session_state.app_state["limit"],
            "expenses": st.session_state.app_state["expenses"],
        }
        try:
            DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass


load_state()
state = st.session_state.app_state

# ---------- HEADER SECTION ----------
st.title("📊 Expense Tracker")
st.caption(
    "Supports smart inputs: 1200, 100k, 2 lakh, 1.5 cr. Colorful breakdown included."
)

# ---------- BUDGET SETUP CARD ----------
with st.container(border=True):
    st.subheader("Income & Budget Settings")
    b_col1, b_col2, b_col3, b_col4 = st.columns([2, 2, 1, 1])

    with b_col1:
        salary_input = st.text_input(
            "Salary (Rs)",
            value=indian_number(state["salary"]) if state["salary"] > 0 else "",
            placeholder="e.g., 1.5 lakh",
        )
    with b_col2:
        limit_input = st.text_input(
            "Limit (Rs)",
            value=indian_number(state["limit"]) if state["limit"] > 0 else "",
            placeholder="e.g., 50k",
        )

    with b_col3:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_html=True)
        if st.button("💾 Save Budget", use_container_width=True, type="primary"):
            try:
                state["salary"] = (
                    parse_money(salary_input) if salary_input.strip() else 0.0
                )
                state["limit"] = (
                    parse_money(limit_input) if limit_input.strip() else 0.0
                )
                save_state()
                st.toast("Budget configuration saved!", icon="✅")
                st.rerun()
            except ValueError:
                st.error("Use budget formats like 100000, 100k, 2 lakh, 1.5 cr.")

    with b_col4:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_html=True)
        if st.button(
            "🗑️ Reset System", use_container_width=True, type="secondary"
        ):
            state["salary"] = 0.0
            state["limit"] = 0.0
            state["expenses"].clear()
            save_state()
            st.toast("Everything cleared out!", icon="🔄")
            st.rerun()

# ---------- CALCULATE OVERVIEW METRICS ----------
spent = sum(item["amount"] for item in state["expenses"])
remaining = state["salary"] - spent
salary_pct = (spent / state["salary"] * 100) if state["salary"] > 0 else 0.0
limit_pct = (spent / state["limit"] * 100) if state["limit"] > 0 else 0.0

# Dynamic status message matching original budget alerts
if state["limit"] > 0 and spent > state["limit"]:
    st.error("⚠️ Over limit. You crossed your custom spending limit.")
elif state["salary"] > 0 and spent > state["salary"]:
    st.error("⚠️ Over salary. You spent more than your salary.")
elif state["salary"] > 0 or state["limit"] > 0:
    st.success("🟢 Within range. Tracking looks good.")
else:
    st.info("💡 Ready. Add salary/limit and start tracking your expenses.")

# Scoreboard Metrics Grid
m_cols = st.columns(6)
m_cols[0].metric("Total Salary", money_label(state["salary"]))
m_cols[1].metric("Spending Limit", money_label(state["limit"]))
m_cols[2].metric("Total Spent", money_label(spent))
m_cols[3].metric("Remaining Cash", money_label(remaining))
m_cols[4].metric("Spent % Salary", f"{salary_pct:.2f}%")
m_cols[5].metric("Spent % Limit", f"{limit_pct:.2f}%")

# ---------- ENTRY INPUT FORM ----------
with st.container(border=True):
    st.subheader("➕ Add New Expense Entry")
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 2, 2])

    with f_col1:
        t_input = st.text_input("Expense Title", placeholder="Grocery bill, rent...")
    with f_col2:
        a_input = st.text_input("Amount", placeholder="e.g., 1200, 1.5k, 500")
    with f_col3:
        c_input = st.selectbox("Category", options=CATEGORIES)

    with f_col4:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_html=True)
        if st.button(
            "🚀 Commit Expense", use_container_width=True, type="primary"
        ):
            if not t_input.strip():
                st.warning("Enter an expense title.")
            else:
                try:
                    parsed_amt = parse_money(a_input)
                    if parsed_amt <= 0:
                        st.warning("Amount must be greater than 0.")
                    else:
                        # Append straight to memory state list (mirroring insert at index 0)
                        state["expenses"].insert(
                            0,
                            {
                                "title": t_input.strip(),
                                "category": c_input,
                                "amount": parsed_amt,
                            },
                        )
                        save_state()
                        st.toast(f"Logged: {t_input.strip()}", icon="📝")
                        st.rerun()
                except ValueError:
                    st.error("Enter a valid format like 1200, 100k, 2 lakh.")

# ---------- DATA GRAPHICS & ANALYTICS ----------
if spent > 0:
    st.subheader("📊 Spending Breakdown Visualization")
    g_col1, g_col2 = st.columns([1, 1])

    # Category grouping computations
    by_cat = {}
    for item in state["expenses"]:
        cat = item["category"]
        by_cat[cat] = by_cat.get(cat, 0.0) + item["amount"]

    with g_col1:
        # Build clean progress-bar based chart showing item metrics cleanly
        st.markdown("**Category Split Overview**")
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            cat_pct = amt / spent
            color = CATEGORY_COLORS.get(cat, "#94a3b8")
            st.markdown(
                f"<small style='font-weight:bold;'>{cat} ({cat_pct*100:.1f}%) — {money_label(amt)}</small>",
                unsafe_html=True,
            )
            st.progress(cat_pct)

    with g_col2:
        # Standard relative bar graph comparison matching original script
        st.markdown("**Budget Proportions Compared**")
        max_bar_ref = max(spent, state["salary"], state["limit"], 1.0)

        st.caption(f"Salary: {money_label(state['salary'])}")
        st.progress(state["salary"] / max_bar_ref)

        st.caption(f"Limit: {money_label(state['limit'])}")
        st.progress(state["limit"] / max_bar_ref)

        st.caption(f"Total Spent: {money_label(spent)}")
        st.progress(spent / max_bar_ref)

# ---------- DATA TABLES & MANAGEMENT ----------
st.markdown("---")
t_col1, t_col2 = st.columns([3, 2])

with t_col1:
    st.subheader("📋 Expense History Records")
    if state["expenses"]:
        formatted_table = []
        for i, item in enumerate(state["expenses"]):
            item_sal_pct = (
                (item["amount"] / state["salary"] * 100)
                if state["salary"] > 0
                else 0.0
            )
            formatted_table.append(
                {
                    "Index": i,
                    "Title": item["title"],
                    "Category": item["category"],
                    "Amount": money_label(item["amount"]),
                    "% Salary Contribution": f"{item_sal_pct:.2f}%",
                }
            )

        st.dataframe(formatted_table, use_container_width=True, hide_index=True)

        # Let users drop individual line rows cleanly
        drop_index = st.number_input(
            "Select Record Index to Delete",
            min_value=0,
            max_value=len(state["expenses"]) - 1,
            step=1,
        )
        if st.button("🗑️ Remove Selected Row"):
            removed_item = state["expenses"].pop(drop_index)
            save_state()
            st.toast(f"Removed: {removed_item['title']}", icon="❌")
            st.rerun()
    else:
        st.info("No transaction logs recorded yet.")

with t_col2:
    st.subheader("🎯 Category Matrix Summary")
    if spent > 0:
        split_table = []
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            cat_spent_pct = (amt / spent * 100) if spent > 0 else 0.0
            cat_sal_pct = (
                (amt / state["salary"] * 100) if state["salary"] > 0 else 0.0
            )
            split_table.append(
                {
                    "Category": cat,
                    "Total Value": money_label(amt),
                    "% of Total Spent": f"{cat_spent_pct:.2f}%",
                    "% of Salary": f"{cat_sal_pct:.2f}%",
                }
            )
        st.dataframe(split_table, use_container_width=True, hide_index=True)
    else:
        st.info("Add records to populate metrics chart matrix.")