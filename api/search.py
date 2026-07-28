from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

import gzip
import shutil

def get_db_connection():
    # Path to the gzipped DB included in the deployment
    gz_path = os.path.join(os.path.dirname(__file__), 'students.db.gz')
    
    # Path to extract the DB to in Vercel's temporary writable storage
    db_path = '/tmp/students.db'
    
    # If it's not extracted yet, extract it
    if not os.path.exists(db_path):
        # Fallback to local path if not on Vercel
        if not os.path.exists('/tmp'):
            db_path = os.path.join(os.path.dirname(__file__), 'students.db')
            if not os.path.exists(db_path):
                with gzip.open(gz_path, 'rb') as f_in:
                    with open(db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
        else:
            with gzip.open(gz_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

    # Connect in read-only mode for performance
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        is_numeric = query.isdigit()
        if is_numeric:
            # Search by seating_no (exact match)
            cursor.execute("SELECT * FROM students WHERE seating_no = ?", (query,))
        else:
            # Search by name (contains)
            cursor.execute("SELECT * FROM students WHERE arabic_name LIKE ?", ('%' + query + '%',))
        
        # Limit to 50 results
        rows = cursor.fetchmany(50)
        conn.close()
        
        results = [dict(row) for row in rows]
        return jsonify(results)
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500

# Vercel needs the 'app' variable, which we defined above.
if __name__ == '__main__':
    app.run(debug=True, port=5000)
