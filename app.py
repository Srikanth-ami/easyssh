from flask import Flask, render_template, request, jsonify
import pty
import os
import termios
import threading

app = Flask(__name__)

def create_pseudo_terminal():
    master_fd, slave_fd = pty.openpty()
    return os.fdopen(master_fd, 'wb'), os.fdopen(slave_fd, 'rb')

def ssh_session(client_socket, ip_address, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Implement proper authentication and authorization checks (replace with your logic)
        if not is_valid_user(ip_address, username, password):
            client_socket.sendall(f"Error: Invalid credentials or access denied\n".encode())
            return

        ssh.connect(ip_address, username=username, password=password)

        master_pty, slave_pty = create_pseudo_terminal()

        # Set up terminal attributes for interactive communication
        pty_settings = termios.tcgetattr(slave_pty.fileno())
        termios.tcsetattr(slave_pty.fileno(), termios.TCSANOW, pty_settings)

        ssh_channel = ssh.invoke_shell()
        ssh_channel.setpty(term=os.ctermid())  # Set controlling terminal for interactive session

        def read_from_client():
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                ssh_channel.sendall(data)

        def read_from_ssh():
            while True:
                data = ssh_channel.recv(1024)
                if not data:
                    break
                client_socket.sendall(data)

        # Create threads for bidirectional communication
        client_thread = threading.Thread(target=read_from_client)
        client_thread.start()

        ssh_thread = threading.Thread(target=read_from_ssh)
        ssh_thread.start()

        # Wait for threads to finish
        client_thread.join()
        ssh_thread.join()

    except Exception as e:
        client_socket.sendall(f"Error: {str(e)}\n".encode())

    finally:
        if ssh:
            ssh.close()

@app.route('/terminal', methods=['GET', 'POST'])
def terminal():
    if request.method == 'POST':
        ip_address = request.form['ip_address']
        username = request.form['username']
        password = request.form['password']  # Securely handle password (refer to security note)

        # Handle security aspects (see discussion below)
        if not is_valid_user(ip_address, username, password):  # Implement security checks
            return jsonify({'error': 'Invalid credentials or access denied'}), 401

        ws = request.environ.get('wsgi.websocket')
        if not ws:
            return jsonify({'error': 'WebSockets not supported'}), 400

        # Create a new thread to handle the SSH session
        session_thread = threading.Thread(target=ssh_session, args=(ws, ip_address, username, password))
        session_thread.start()

        return jsonify({'message': 'SSH session started'}), 200

    return render_template('terminal.html')  # Replace with your terminal template

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=6000)

# Implement a secure `is_valid_user` function using a database or other authentication mechanisms
# to validate user credentials and access permissions. Avoid storing passwords in plain text.
# Promraging by @sumonpaul
# This is a Web Based SSH Terminal Application for Easy to Manage Linux
