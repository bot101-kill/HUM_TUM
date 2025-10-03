from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests 
import os
import dotenv
import uuid
import csv
import random
from flask_cors import CORS

dotenv.load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
app.secret_key = os.urandom(24)  # Secret key for session management

store_email = 'b23371@students.iitmandi.ac.in' # Replace with your email for logging
#new
def send_brevo_email(recipient_email, subject, html_content):
    """Helper function to send an email using the Brevo API."""
    api_key = os.getenv('BREVO_API_KEY')
    verified_sender_email = os.getenv('BREVO_MAIL')  # <-- IMPORTANT: Use your verified Brevo sender email
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    payload = {
        "sender": {"name": "Prom Night App", "email": verified_sender_email},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        print(f"Email to {recipient_email} sent successfully!")
        return True
    else:
        print(f"Failed to send email: {response.status_code} - {response.text}")
        return False
# # Mail configuration
# app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
# app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
# app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
# app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
# app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
# app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')

# mail = Mail(app)
invitations = {}

# Load student list from CSV
STUDENT_LIST_PATH = "./data.csv"
students = []

# DISABLED ROLL NUMBERS ----->
disabledRollNumber = []

with open(STUDENT_LIST_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    reader.fieldnames = [field.strip() for field in reader.fieldnames]
    for row in reader:
        row = {k.strip(): v.strip() for k, v in row.items()}
        students.append({
            'name': row['Name'].upper(),
            'roll': row['Roll No.'].strip().lower(),
            'gender': row.get('Gender', '').strip().lower()
        })

@app.route("/")
def index():
    return render_template('index.html') 

@app.route('/disableEmail')
def disableEmail():
    d = request.args.get('roll_no').strip().lower()
    disabledRollNumber.append(d)
    return render_template('disableEmail.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/resubscribe')
def resubscribe():
    d = request.args.get('roll_no').strip().lower()
    if d in disabledRollNumber:
        disabledRollNumber.remove(d)
    return "<h1>Resubscribe</h1><p>You have successfully resubscribed to the email list.</p>"




@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    roll_no = request.form['roll_no'].strip().lower()
    rec_roll = request.form["prom's_roll_no"].strip().lower()
    subject = "PROM INVITATION"
    REC_EMAIL = rec_roll + '@students.iitmandi.ac.in'
    
    token = str(uuid.uuid4())


    invitations[token] = {
        'sender_roll': roll_no,
        'sender_name': name,
        'recipient_roll': rec_roll
    }

    viewer_link = url_for('viewer', token=token, _external=True)
    disable_Link = url_for('disableEmail', roll_no=roll_no, _external=True)
    # Check if the sender's roll number is in the disabled list
    if rec_roll in disabledRollNumber:
        return redirect(url_for('privacy'))
         

    msgtmp2 = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Prom Night Invitation</title>
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr>
      <td align="center">
        <table width="600" border="0" cellspacing="0" cellpadding="20" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #ddd;">
          <tr>
            <td align="center" style="padding: 20px 0;">
              <h1 style="font-size: 24px; margin: 0;">You have a secret Prom invitation! 💌</h1>
            </td>
          </tr>
          <tr>
            <td align="center" style="font-size: 16px; line-height: 1.5;">
              <p>Hi there,</p>
              <p>Someone you know from IIT Mandi would like you to be their date for Prom Night.</p>
              <p>Click the button below to see your options and guess who it is!</p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 20px 0;">
              <a href="{viewer_link}" style="background-color: #28a745; color: #ffffff; text-decoration: none; padding: 15px 30px; border-radius: 5px; font-weight: bold; font-size: 16px;">
                Reveal Your Invitation
              </a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-top: 20px; font-size: 12px; color: #777;">
              <p>This email was sent because a user invited you via the Prom Night App.</p>
              <p>Not interested? You can <a href="{disable_Link}" style="color: #777;">unsubscribe here</a>.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    # Send the main invitation email
    send_brevo_email(REC_EMAIL, subject, msgtmp2.format(viewer_link=viewer_link, disable_Link=disable_Link))
    
    # Send the log email
    log_body = f"""A new prom invitation was sent.
        Sender: {roll_no} ({name})
        Recipient: {rec_roll}
        Token: {token}
        viewer_link={viewer_link}"""
    send_brevo_email(store_email, "📩 New Prom Invitation Logged", f"<pre>{log_body}</pre>")

    return redirect(url_for('success'))


@app.route('/viewer')
def viewer():
    token = request.args.get('token')
    if not token or token not in invitations:
        return "Invalid or expired invitation.", 400

    sender_roll = invitations[token]['sender_roll'].strip().lower()
    sender_info = next((s for s in students if s['roll'] == sender_roll), None)

    if not sender_info:
        return "Sender not found", 404

    sender_gender = sender_info['gender'].strip().lower()

    if token not in session:
                # Extract prefix like 'b23' from sender's roll
        sender_prefix = sender_roll[:3]

        # Filter by same gender and same roll prefix
        same_batch_gender_choices = [
            s for s in students
            if s['roll'] != sender_roll
            and s['gender'] == sender_gender
            and s['roll'][:3] == sender_prefix
        ]

        # Randomly select 3 options from the filtered list
        dummy_choices = random.sample(same_batch_gender_choices, k=min(4, len(same_batch_gender_choices)))

        # Final options list
        options = dummy_choices + [sender_info, {"name": "DON'T WANNA GO", "roll": "😭"}]
        random.shuffle(options)

        # Store in session
        session[token] = options


    else:
        options = session[token]

    return render_template('viewer.html', token=token, options=options, correct_roll=sender_info['roll'])

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    token = data.get('token')
    selected_roll = data.get('selected_roll')

    if token not in invitations:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 400

    invitation = invitations[token]
    sender_roll = invitation['sender_roll']
    sender_name = invitation['sender_name']
    recipient_roll = invitation['recipient_roll']

    sender_email = sender_roll + '@students.iitmandi.ac.in'

    if selected_roll == sender_roll:
        subject = "🎉 It's a PROM MATCH!"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background: linear-gradient(to right, #43e97b, #38f9d7); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <h2 style="color: #fff; text-align: center;">💃🕺 It's a Match!</h2>
                <p style="color: #fff; font-size: 16px; text-align: center;">
                    Hi <strong>{sender_name}</strong>,<br><br>
                    Your prom invitation was accepted by <strong>{recipient_roll}</strong> 🎉<br>
                    Looks like it’s time to prepare your moves for the dance floor!<br><br>
                    <strong>See you at the PROM NIGHT!</strong> 💌✨
                </p>
            </div>
        </body>
        </html>
        """
        send_brevo_email(sender_email, subject, html_body)
        send_brevo_email(store_email, "📩 Prom Match Alert", f"<pre>Sender: {sender_roll} ({sender_name})\nRecipient: {recipient_roll}\nToken: {token}</pre>")
        
        session.pop(token, None)
        del invitations[token]
        return jsonify({"success": True, "match": True})

    else:
        subject = "😢 Better Luck Next Time"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #fff3f3; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background: linear-gradient(to right, #ff758c, #ff7eb3); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <h2 style="color: #fff; text-align: center;">Oops! Not This Time 😢</h2>
                <p style="color: #fff; font-size: 16px; text-align: center;">
                    Hey <strong>{sender_name}</strong>,<br><br>
                    Sadly, <strong>{recipient_roll}</strong> didn’t guess you correctly 😔<br>
                    But don’t lose heart — there’s always another dance and another chance!<br><br>
                    You tried and that’s what matters ❤️
                </p>
            </div>
        </body>
        </html>
        """
        send_brevo_email(sender_email, subject, html_body)
        
        session.pop(token, None)
        del invitations[token]
        return jsonify({"success": True, "match": False})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
