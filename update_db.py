import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/device_management.db')
cursor = conn.cursor()

# Add new columns to the device table
try:
    cursor.execute('ALTER TABLE device ADD COLUMN owner TEXT')
    cursor.execute('ALTER TABLE device ADD COLUMN department TEXT')
    cursor.execute('ALTER TABLE device ADD COLUMN warranty_period INTEGER')
    cursor.execute('ALTER TABLE device ADD COLUMN supplier TEXT')
    conn.commit()
    print("Database updated successfully!")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
    conn.rollback()

# Close the connection
conn.close()