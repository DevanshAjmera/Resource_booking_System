import streamlit as st
from datetime import datetime, date, time
import database as db
import os

# Page configuration
st.set_page_config(
    page_title="Resource Booking System",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open('styles.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("⚠️ styles.css file not found! Make sure it's in the same folder as app.py")
        st.info(f"Current directory: {os.getcwd()}")
    except Exception as e:
        st.error(f"Error loading CSS: {e}")

# Initialize database
# db.init_database()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login_page():
    """Display login page"""
    load_css()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h2 class="section-header">Login</h2>', unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("Login as User", use_container_width=True, type="primary"):
                if username and password:
                    user = db.verify_user(username, password)
                    if user and user['role'] == 'user':
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid credentials or not a user account")
                else:
                    st.warning("Please enter username and password")
        
        with col_b:
            if st.button("Login as Admin", use_container_width=True, type="secondary"):
                if username and password:
                    user = db.verify_user(username, password)
                    if user and user['role'] == 'admin':
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid credentials or not an admin account")
                else:
                    st.warning("Please enter username and password")
        
        st.markdown('</div>', unsafe_allow_html=True)

def user_dashboard():
    """Display user dashboard"""
    load_css()
    
    st.markdown(f'<div>Welcome, {st.session_state.user["username"]}! 👋</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<div class="user-info">👤 {st.session_state.user["username"]}<br>📧 {st.session_state.user["email"]}</div>', unsafe_allow_html=True)
        
        menu = st.radio("Navigation", ["New Booking", "My Bookings", "Check Availability"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    # Main content
    if menu == "New Booking":
        new_booking_form()
    elif menu == "My Bookings":
        my_bookings()
    elif menu == "Check Availability":
        check_availability_page()

def new_booking_form():
    """Form to create a new booking"""
    st.markdown('<h2 class="section-header">📝 New Booking Request</h2>', unsafe_allow_html=True)
    
    resources = db.get_all_resources()
    
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name *", placeholder="e.g., Annual Tech Fest")
            
            resource_options = {f"{r['resource_name']} ({r['resource_type'].title()})": r['resource_id'] for r in resources}
            selected_resource = st.selectbox("Select Resource *", options=list(resource_options.keys()))
            resource_id = resource_options[selected_resource]
            
            event_date = st.date_input("Event Date *", min_value=date.today())
            
            total_strength = st.number_input("Total Strength *", min_value=1, max_value=1000, value=50)
        
        with col2:
            start_time = st.time_input("Start Time *", value=time(9, 0))
            end_time = st.time_input("End Time *", value=time(17, 0))
            
            description = st.text_area("Description", placeholder="Provide event details...", height=150)
        
        submitted = st.form_submit_button("Submit Booking Request", use_container_width=True, type="primary")
        
        if submitted:
            if not event_name:
                st.error("Please enter event name")
            elif start_time >= end_time:
                st.error("End time must be after start time")
            else:
                # Check availability
                if db.check_availability(resource_id, event_date, start_time, end_time):
                    success, message = db.create_booking(
                        st.session_state.user['user_id'],
                        resource_id,
                        event_name,
                        event_date,
                        start_time,
                        end_time,
                        description,
                        total_strength
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.error("⚠️ This resource is already booked for the selected time slot. Please choose a different time or resource.")

def my_bookings():
    """Display user's bookings"""
    st.markdown('<h2 class="section-header">📋 My Bookings</h2>', unsafe_allow_html=True)
    
    bookings = db.get_user_bookings(st.session_state.user['user_id'])
    
    if not bookings:
        st.info("You have no bookings yet.")
        return
    
    for booking in bookings:
        status_color = {
            'pending': '🟡',
            'approved': '🟢',
            'rejected': '🔴'
        }
        
        with st.container():
            st.markdown(f"""
                <div class="booking-card">
                    <h3>{booking['event_name']} {status_color.get(booking['status'], '⚪')} {booking['status'].title()}</h3>
                    <p><strong>Resource:</strong> {booking['resource_name']} ({booking['resource_type'].title()})</p>
                    <p><strong>Date:</strong> {booking['event_date'].strftime('%B %d, %Y')}</p>
                    <p><strong>Time:</strong> {booking['start_time']} - {booking['end_time']}</p>
                    <p><strong>Strength:</strong> {booking['total_strength']} people</p>
                    {f"<p><strong>Description:</strong> {booking['description']}</p>" if booking['description'] else ""}
                    <p class="booking-meta">Requested on: {booking['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                </div>
            """, unsafe_allow_html=True)

def check_availability_page():
    """Check resource availability"""
    st.markdown('<h2 class="section-header">🔍 Check Resource Availability</h2>', unsafe_allow_html=True)
    
    resources = db.get_all_resources()
    
    col1, col2 = st.columns(2)
    
    with col1:
        resource_options = {f"{r['resource_name']} ({r['resource_type'].title()})": r['resource_id'] for r in resources}
        selected_resource = st.selectbox("Select Resource", options=list(resource_options.keys()))
        resource_id = resource_options[selected_resource]
    
    with col2:
        check_date = st.date_input("Select Date", value=date.today(), min_value=date.today())
    
    if st.button("Check Schedule", type="primary"):
        schedule = db.get_resource_schedule(resource_id, check_date)
        
        st.markdown(f"### Schedule for {selected_resource} on {check_date.strftime('%B %d, %Y')}")
        
        if not schedule:
            st.success("✅ No bookings found. Resource is available all day!")
        else:
            for booking in schedule:
                st.markdown(f"""
                    <div class="booking-card">
                        <h4>{booking['event_name']}</h4>
                        <p><strong>Time:</strong> {booking['start_time']} - {booking['end_time']}</p>
                        <p><strong>Booked by:</strong> {booking['username']}</p>
                    </div>
                """, unsafe_allow_html=True)

def admin_dashboard():
    """Display admin dashboard"""
    load_css()
    
    st.markdown(f'<div>Admin Dashboard 🛡️</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f'<div class="user-info">👤 {st.session_state.user["username"]} (Admin)<br>📧 {st.session_state.user["email"]}</div>', unsafe_allow_html=True)
        
        menu = st.radio("Navigation", ["All Bookings", "Manage Users"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    # Main content
    if menu == "All Bookings":
        manage_bookings()
    elif menu == "Manage Users":
        manage_users()

def manage_bookings():
    """Manage all bookings (admin)"""
    st.markdown('<h2 class="section-header">📊 All Bookings</h2>', unsafe_allow_html=True)
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
    
    bookings = db.get_all_bookings()
    
    if filter_status != "All":
        bookings = [b for b in bookings if b['status'] == filter_status.lower()]
    
    if not bookings:
        st.info("No bookings found.")
        return
    
    for booking in bookings:
        status_color = {
            'pending': '🟡',
            'approved': '🟢',
            'rejected': '🔴'
        }
        
        with st.container():
            st.markdown(f"""
                <div class="booking-card">
                    <h3>{booking['event_name']} {status_color.get(booking['status'], '⚪')} {booking['status'].title()}</h3>
                    <div class="booking-details">
                        <p><strong>Resource:</strong> {booking['resource_name']} ({booking['resource_type'].title()})</p>
                        <p><strong>Requested by:</strong> {booking['username']} ({booking['email']})</p>
                        <p><strong>Date:</strong> {booking['event_date'].strftime('%B %d, %Y')}</p>
                        <p><strong>Time:</strong> {booking['start_time']} - {booking['end_time']}</p>
                        <p><strong>Strength:</strong> {booking['total_strength']} people</p>
                        {f"<p><strong>Description:</strong> {booking['description']}</p>" if booking['description'] else ""}
                        <p class="booking-meta">Requested on: {booking['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if booking['status'] == 'pending':
                col_a, col_b, col_c = st.columns([1, 1, 4])
                with col_a:
                    if st.button("✅ Approve", key=f"approve_{booking['booking_id']}", use_container_width=True):
                        success, message = db.update_booking_status(booking['booking_id'], 'approved')
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col_b:
                    if st.button("❌ Reject", key=f"reject_{booking['booking_id']}", use_container_width=True):
                        success, message = db.update_booking_status(booking['booking_id'], 'rejected')
                        if success:
                            st.warning(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            st.markdown("---")

def manage_users():
    """Manage users (admin)"""
    st.markdown('<h2 class="section-header">👥 Manage Users</h2>', unsafe_allow_html=True)
    
    # Create new user form
    with st.expander("➕ Create New User", expanded=True):
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username *", placeholder="Enter username")
                new_email = st.text_input("Email *", placeholder="user@example.com")
            
            with col2:
                new_password = st.text_input("Password *", type="password", placeholder="Enter password")
                new_role = st.selectbox("Role *", ["user", "admin"])
            
            submitted = st.form_submit_button("Create User", use_container_width=True, type="primary")
            
            if submitted:
                if not new_username or not new_email or not new_password:
                    st.error("All fields are required")
                else:
                    success, message = db.create_user(new_username, new_email, new_password, new_role)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    # Display all users
    st.markdown("### Existing Users")
    users = db.get_all_users()
    
    if users:
        for user in users:
            role_badge = "🛡️ Admin" if user['role'] == 'admin' else "👤 User"
            st.markdown(f"""
                <div class="booking-card">
                    <h4>{user['username']} - {role_badge}</h4>
                    <p><strong>Email:</strong> {user['email']}</p>
                    <p class="booking-meta">Created: {user['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No users found.")

# Main application logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.user['role'] == 'admin':
            admin_dashboard()
        else:
            user_dashboard()

if __name__ == "__main__":
    main()
