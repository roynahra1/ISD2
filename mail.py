import mysql.connector
from datetime import datetime, timedelta
import yagmail  # Or use smtplib if preferred

# DB config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'isdb'
}

# Email setup
yag = yagmail.SMTP('roynahra2004@gmail.com', 'vpzi utxt mnie cjni')

def send_reminders():
    target_date = (datetime.now() + timedelta(days=15)).date()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT plate_number, owner_name, model, next_oil_change_due, owner_email
        FROM car_maintenance
        WHERE next_oil_change_due = %s
    ''', (target_date,))
    
    results = cursor.fetchall()
    for row in results:
        body = f"""
    
Dear {row['owner_name']},<br><br>

Your vehicle ({row['model']}, Plate: {row['plate_number']}) is due for an oil change on {row['next_oil_change_due']}.<br>
Please <a href="https/t2/appointment.html?plate={row['plate_number']}">click here to schedule your maintenance</a>.<br><br>

Best regards,<br>
Your Service Team
        
        """
        yag.send(to=row['owner_email'], subject="⏰ Oil Change Reminder", contents=body)
        print(f"✅ Reminder sent to {row['owner_email']}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    send_reminders()    