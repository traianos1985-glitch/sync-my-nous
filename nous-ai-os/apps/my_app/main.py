from flask import Flask, request, jsonify
import subprocess
import sys
import os

app = Flask(__name__)

# Ορίστε το τρέχον directory του script ως βάση
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/upgrade', methods=['POST'])
def upgrade_self():
    """
    Λαμβάνει ένα URL για ένα νέο αρχείο Python, το κατεβάζει και το εκτελεί.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Παρακαλώ παρέχετε ένα URL στο JSON payload.'}), 400

    new_script_url = data['url']
    script_name = new_script_url.split('/')[-1]
    download_path = os.path.join(BASE_DIR, script_name)

    try:
        # Κατεβάστε το νέο script
        import requests
        response = requests.get(new_script_url, stream=True)
        response.raise_for_status() # Ελέγξτε για σφάλματα HTTP

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Εκτελέστε το νέο script
        # Χρησιμοποιούμε sys.executable για να βεβαιωθούμε ότι χρησιμοποιείται ο ίδιος Python interpreter
        # και προσθέτουμε το directory του script στο sys.path για να μπορεί να εισαχθεί
        # Σημείωση: Αυτή η προσέγγιση είναι απλοϊκή και μπορεί να μην είναι ασφαλής για παραγωγικά περιβάλλοντα.
        # Σε ένα πραγματικό σενάριο, θα χρειαζόταν πιο στιβαρός μηχανισμός διαχείρισης εκδόσεων και ασφάλειας.
        
        # Προσθήκη του directory του νέου script στο sys.path
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
            
        # Εκτέλεση του νέου script
        # Για απλότητα, υποθέτουμε ότι το νέο script είναι ένα άλλο Flask app που θα αντικαταστήσει το τρέχον
        # ή θα εκτελεστεί ως ξεχωριστή διεργασία.
        # Εδώ, απλώς εκτελούμε το script ως ξεχωριστή διεργασία.
        # Για να αντικαταστήσουμε το τρέχον app, θα χρειαζόταν επανεκκίνηση της κύριας διεργασίας.
        
        # Δημιουργία ενός νέου αρχείου για την εκτέλεση του νέου script
        # Αυτό είναι ένα παράδειγμα. Σε πραγματικό σενάριο, θα μπορούσατε να χρησιμοποιήσετε
        # ένα εργαλείο διαχείρισης διεργασιών όπως το systemd ή το supervisor.
        
        # Δημιουργούμε ένα απλό script που θα εκτελέσει το νέο αρχείο
        runner_script_content = f'''
import subprocess
import sys
import os

new_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '{script_name}')
print(f"Executing new script: {{new_script_path}}")

try:
    # Χρησιμοποιούμε sys.executable για να βεβαιωθούμε ότι χρησιμοποιείται ο ίδιος Python interpreter
    # και προσθέτουμε το directory του script στο sys.path για να μπορεί να εισαχθεί
    process = subprocess.Popen([sys.executable, new_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print("STDOUT:", stdout.decode())
    print("STDERR:", stderr.decode())
    if process.returncode != 0:
        print(f"Error executing script. Return code: {{process.returncode}}")
        # Εδώ θα μπορούσατε να χειριστείτε το σφάλμα, π.χ. να επαναφέρετε την προηγούμενη έκδοση
except Exception as e:
    print(f"An exception occurred: {{e}}")

'''
        runner_script_path = os.path.join(BASE_DIR, 'run_new_script.py')
        with open(runner_script_path, 'w') as f:
            f.write(runner_script_content)

        # Εκτέλεση του runner script
        subprocess.Popen([sys.executable, runner_script_path])

        return jsonify({'message': f'Το νέο script κατεβάστηκε και εκτελείται σε ξεχωριστή διεργασία: {script_name}'}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Σφάλμα κατά το κατέβασμα του script: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'Σφάλμα κατά την εκτέλεση του script: {e}'}), 500


@app.route('/')
def index():
    return "Καλώς ήρθατε στο εργαλείο αυτο-αναβάθμισης! Χρησιμοποιήστε το endpoint /upgrade με POST request."

if __name__ == '__main__':
    # Για να τρέξει σε όλες τις διαθέσιμες διεπαφές, χρησιμοποιήστε '0.0.0.0'
    app.run(host='0.0.0.0', port=7000, debug=True)
