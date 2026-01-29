import mysql.connector
from mysql.connector import Error
import os
import hashlib

def get_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", "3306"))
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verify user credentials and return user data"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        hashed_password = hash_password(password)
        
        cursor.execute("""
            SELECT user_id, username, email, role 
            FROM users 
            WHERE username = %s AND password = %s
        """, (username, hashed_password))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    return None

def create_user(username, email, password, role='user'):
    """Create a new user"""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            hashed_password = hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password, role) 
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_password, role))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True, "User created successfully!"
        except Error as e:
            return False, f"Error creating user: {e}"
    return False, "Database connection failed"

def get_all_resources():
    """Get all resources"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resources ORDER BY resource_type, resource_name")
        resources = cursor.fetchall()
        cursor.close()
        connection.close()
        return resources
    return []

def check_availability(resource_id, event_date, start_time, end_time, exclude_booking_id=None):
    """Check if a resource is available for the given time slot"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor()
        
        query = """
            SELECT COUNT(*) as count FROM bookings 
            WHERE resource_id = %s 
            AND event_date = %s 
            AND status IN ('pending', 'approved')
            AND (
                (start_time < %s AND end_time > %s) OR
                (start_time < %s AND end_time > %s) OR
                (start_time >= %s AND end_time <= %s) OR
                (start_time <= %s AND end_time >= %s)
            )
        """
        params = [resource_id, event_date, end_time, start_time, start_time, start_time, start_time, end_time, start_time, end_time]
        
        if exclude_booking_id:
            query += " AND booking_id != %s"
            params.append(exclude_booking_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        # Return True if no conflicts found (count == 0), False if conflicts exist
        return result[0] == 0
    return False

def create_booking(user_id, resource_id, event_name, event_date, start_time, end_time, description, total_strength):
    """Create a new booking"""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO bookings 
                (user_id, resource_id, event_name, event_date, start_time, end_time, description, total_strength) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, resource_id, event_name, event_date, start_time, end_time, description, total_strength))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True, "Booking request submitted successfully!"
        except Error as e:
            return False, f"Error creating booking: {e}"
    return False, "Database connection failed"

def get_user_bookings(user_id):
    """Get all bookings for a specific user"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, r.resource_name, r.resource_type, u.username 
            FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            JOIN users u ON b.user_id = u.user_id
            WHERE b.user_id = %s
            ORDER BY b.event_date DESC, b.start_time DESC
        """, (user_id,))
        bookings = cursor.fetchall()
        cursor.close()
        connection.close()
        return bookings
    return []

def get_all_bookings():
    """Get all bookings (for admin)"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, r.resource_name, r.resource_type, u.username, u.email 
            FROM bookings b
            JOIN resources r ON b.resource_id = r.resource_id
            JOIN users u ON b.user_id = u.user_id
            ORDER BY b.created_at DESC
        """)
        bookings = cursor.fetchall()
        cursor.close()
        connection.close()
        return bookings
    return []

def update_booking_status(booking_id, status):
    """Update booking status (approve/reject)"""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE bookings 
                SET status = %s 
                WHERE booking_id = %s
            """, (status, booking_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True, f"Booking {status} successfully!"
        except Error as e:
            return False, f"Error updating booking: {e}"
    return False, "Database connection failed"

def get_resource_schedule(resource_id, date):
    """Get all bookings for a resource on a specific date"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, u.username 
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            WHERE b.resource_id = %s 
            AND b.event_date = %s 
            AND b.status = 'approved'
            ORDER BY b.start_time
        """, (resource_id, date))
        bookings = cursor.fetchall()
        cursor.close()
        connection.close()
        return bookings
    return []

def get_all_users():
    """Get all users (for admin)"""
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, username, email, role, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return users
    return []