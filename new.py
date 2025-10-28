import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import sqlite3
import bcrypt
import jwt
import re
import os
import time
from collections import Counter
from datetime import datetime, timedelta
import missingno

from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import google.oauth2.id_token

# --- CONFIG ---
GOOGLE_CLIENT_SECRETS = "client_secret.json"
JWT_SECRET = "supersecret"
JWT_ALGO = "HS256"

# --- UTILITY FUNCTIONS ---

def create_correlation_chart(corr_df):
    fig = plt.figure(figsize=(15, 15))
    plt.imshow(corr_df.values, cmap="Blues")
    plt.xticks(range(corr_df.shape[0]), corr_df.columns, rotation=90, fontsize=15)
    plt.yticks(range(corr_df.shape[0]), corr_df.columns, fontsize=15)
    plt.colorbar()
    for i in range(corr_df.shape[0]):
        for j in range(corr_df.shape[0]):
            plt.text(i, j, "{:.2f}".format(corr_df.values[i, j]), color="red", ha="center", fontsize=14, fontweight="bold")
    plt.tight_layout()
    return fig

def create_missing_values_bar(df):
    missing_fig = plt.figure(figsize=(10, 5))
    ax = missing_fig.add_subplot(111)
    missingno.bar(df, figsize=(10, 5), fontsize=12, ax=ax)
    return missing_fig

def find_cat_cont_columns(df):
    cont_columns, cat_columns = [], []
    for col in df.columns:
        if len(df[col].unique()) <= 25 or df[col].dtype == object or df[col].dtype == 'O':
            cat_columns.append(col.strip())
        else:
            cont_columns.append(col.strip())
    return cont_columns, cat_columns

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    return sqlite3.connect("users.db")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT,
            is_google_user INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- AUTHENTICATION HELPERS ---
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(password, hashed_password):
    if not hashed_password:
        return False
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def is_strong_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

def create_jwt(user_id):
    expiration = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode({"user_id": user_id, "exp": expiration}, JWT_SECRET, algorithm=JWT_ALGO)

def verify_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_email(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "User"

# --- EMAIL SIGNUP / LOGIN ---
def signup(email, password, confirm_password):
    if password != confirm_password:
        return "Passwords do not match."
    if not is_strong_password(password):
        return "Password must be strong (8+ chars, upper, lower, number, symbol)."
    if not is_valid_email(email):
        return "Invalid email."
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        c.execute(
            "INSERT INTO users (email, password_hash, is_google_user) VALUES (?, ?, 0)",
            (email, hashed_password),
        )
        conn.commit()
        conn.close()
        return "Account created successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return "Email already exists."

def login(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password_hash, is_google_user FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    if not result:
        return None
    if result[2]:
        st.warning("This account is linked with Google. Use Google login instead.")
        return None
    if verify_password(password, result[1]):
        return create_jwt(result[0])
    return None

# --- GOOGLE LOGIN ---
def login_with_google():
    st.write("Or, sign in with Google:")
    redirect_uri = "http://localhost:8501"
    try:
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "openid",
            ],
            redirect_uri=redirect_uri,
        )
        auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
        st.markdown(f"[**Sign in with Google**]({auth_url})")
    except Exception as e:
        st.error(f"OAuth init error: {e}")
        return
    params = st.query_params
    if "code" in params:
        try:
            code = params["code"][0] if isinstance(params["code"], list) else params["code"]
            flow.fetch_token(code=code)
            credentials = flow.credentials
            token_request = google.auth.transport.requests.Request()
            client_info = flow.client_config
            if "web" in client_info:
                client_id = client_info["web"]["client_id"]
            else:
                client_id = client_info.get("client_id")
            id_info = google.oauth2.id_token.verify_oauth2_token(
                credentials.id_token, token_request, client_id
            )
            email = id_info.get("email")
            if not email:
                st.error("No email found in Google token.")
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = c.fetchone()
            if not result:
                c.execute(
                    "INSERT INTO users (email, password_hash, is_google_user) VALUES (?, NULL, 1)",
                    (email,),
                )
                conn.commit()
                c.execute("SELECT id FROM users WHERE email = ?", (email,))
                result = c.fetchone()
            conn.close()
            if not result:
                st.error("Database insert failed for Google user.")
                return
            user_id = result[0]
            st.session_state["jwt_token"] = create_jwt(user_id)
            st.success(f"✅ Logged in successfully as **{email}**")
            st.query_params.clear()
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Google login failed: {e}")

# --- DASHBOARD ---
def show_dashboard(user_id):
    email = get_email(user_id)
    st.sidebar.success(f"Logged in as {email}")
    if st.sidebar.button("Logout"):
        st.session_state["jwt_token"] = None
        st.rerun()
    st.title("📊 EDA Dashboard")
    st.caption("Upload CSV file to see various charts related to EDA. Please upload a file that has both continuous and categorical columns. Once you upload a file, various charts, widgets and basic stats will be displayed.")
    upload = st.file_uploader(label="Upload File Here:", type=["csv"])
    if upload:
        try:
            df = pd.read_csv(upload, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(upload, encoding="latin1")
        tab1, tab2, tab3 = st.tabs(["Dataset Overview", "Individual Column Stats", "Relation Between Features"])
        with tab1:
            st.subheader("1. Dataset")
            st.dataframe(df)
            cont_columns, cat_columns = find_cat_cont_columns(df)
            st.subheader("2. Dataset Overview")
            st.markdown("<span style='font-weight:bold;'>Rows</span> : {}".format(df.shape[0]), unsafe_allow_html=True)
            st.markdown("<span style='font-weight:bold;'>Duplicates</span> : {}".format(df.shape[0] - df.drop_duplicates().shape[0]), unsafe_allow_html=True)
            st.markdown("<span style='font-weight:bold;'>Features</span> : {}".format(df.shape[1]), unsafe_allow_html=True)
            st.markdown("<span style='font-weight:bold;'>Categorical Columns</span> : {}".format(len(cat_columns)), unsafe_allow_html=True)
            st.write(cat_columns)
            st.markdown("<span style='font-weight:bold;'>Continuous Columns</span> : {}".format(len(cont_columns)), unsafe_allow_html=True)
            st.write(cont_columns)
            if cont_columns:
                corr_df = df[cont_columns].corr()
                corr_fig = create_correlation_chart(corr_df)
                st.subheader("3. Correlation Chart")
                st.pyplot(corr_fig, use_container_width=True)
            st.subheader("4. Missing Values Distribution")
            missing_fig = create_missing_values_bar(df)
            st.pyplot(missing_fig, use_container_width=True)
        with tab2:
            df_descr = df.describe()
            st.subheader("Analyze Individual Feature Distribution")
            # Continuous features
            if cont_columns:
                st.markdown("#### 1. Understand Continuous Feature")
                feature = st.selectbox(label="Select Continuous Feature", options=cont_columns, key="cont_feature")
                na_cnt = df[feature].isna().sum()
                st.markdown("<span style='font-weight:bold;'>Count</span> : {}".format(df_descr[feature]['count']), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Missing Count</span> : {} / ({:.2f} %)".format(na_cnt, 100 * na_cnt/df.shape[0]), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Mean</span> : {:.2f}".format(df_descr[feature]['mean']), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Standard Deviation</span> : {:.2f}".format(df_descr[feature]['std']), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Minimum</span> : {}".format(df_descr[feature]['min']), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Maximum</span> : {}".format(df_descr[feature]['max']), unsafe_allow_html=True)
                st.markdown("<span style='font-weight:bold;'>Quantiles</span> :", unsafe_allow_html=True)
                st.write(df_descr[[feature]].T[['25%', "50%", "75%"]])
                hist_fig = px.histogram(df, x=feature, nbins=50, title=f"Distribution of {feature}")
                st.plotly_chart(hist_fig, use_container_width=True)
            # Categorical features
            if cat_columns:
                st.markdown("#### 2. Understand Categorical Feature")
                feature = st.selectbox(label="Select Categorical Feature", options=cat_columns, key="cat_feature")
                cnts = Counter(df[feature].values)
                df_cnts = pd.DataFrame({"Type": list(cnts.keys()), "Values": list(cnts.values())})
                bar_fig = px.bar(df_cnts, x="Type", y="Values", title=f"Distribution of {feature}", color="Values")
                st.plotly_chart(bar_fig, use_container_width=True)
        with tab3:
            st.subheader("Explore Relationship Between Features of Dataset")
            chart_type = st.selectbox("Select Chart Type", ["Scatter Plot", "Box Plot", "Bar Plot"])
            col1, col2 = st.columns(2)
            with col1:
                x_axis = st.selectbox(label="X-Axis", options=df.columns, index=0, key="x_axis")
            with col2:
                y_axis = st.selectbox(label="Y-Axis", options=df.columns, index=1, key="y_axis")
            color_encode_opt = [None] + list(df.columns)
            color_encode = st.selectbox(label="Color Encode (Optional)", options=color_encode_opt, key="color_encode")
            if chart_type == "Scatter Plot":
                fig = px.scatter(df, x=x_axis, y=y_axis, color=color_encode,
                                 title=f"{x_axis} vs {y_axis} (Scatter)")
            elif chart_type == "Box Plot":
                fig = px.box(df, x=x_axis, y=y_axis, color=color_encode,
                             title=f"{y_axis} distribution across {x_axis}")
            elif chart_type == "Bar Plot":
                fig = px.bar(df, x=x_axis, y=y_axis, color=color_encode, barmode="group",
                             title=f"{y_axis} vs {x_axis} (Bar)")
            st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="EDA with Login", layout="wide")
    init_db()
    if "jwt_token" not in st.session_state:
        st.session_state["jwt_token"] = None
    if st.session_state["jwt_token"]:
        user_id = verify_jwt(st.session_state["jwt_token"])
        if user_id:
            show_dashboard(user_id)
        else:
            st.session_state["jwt_token"] = None
            st.error("Session expired. Please log in again.")
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Signup"])
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                token = login(email, password)
                if token:
                    st.session_state["jwt_token"] = token
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            st.write("---")
            login_with_google()
        with tab2:
            email = st.text_input("Signup Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", key="signup_conf")
            if st.button("Sign Up"):
                result = signup(email, password, confirm)
                if "successfully" in result:
                    st.success(result)
                else:
                    st.error(result)

if __name__ == "__main__":
    main()
