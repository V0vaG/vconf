from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Directory for storing configuration and data
FILES_PATH = os.path.expanduser("~/script_files")
DATA_DIR = f"/home/{os.environ.get('USER')}/my_scripts/vconf"
os.makedirs(DATA_DIR, exist_ok=True)


# Helper function to generate topic ID
def generate_topic_id():
    existing_ids = []
    for file in os.listdir(DATA_DIR):
        if file.endswith('.json'):
            with open(os.path.join(DATA_DIR, file), 'r') as f:
                data = json.load(f)
                existing_ids.extend([int(topic["topic_id"]) for topic in data])

    next_topic_id = 1
    for topic_id in sorted(existing_ids):
        if topic_id == next_topic_id:
            next_topic_id += 1
        else:
            break
    return f"{next_topic_id:05d}"


# Route for home page
@app.route('/')
def home():
    return render_template('index.html')


# Route to list all topics (with clickable links)
@app.route('/list')
def list_topics():
    all_topics = []
    for file in os.listdir(DATA_DIR):
        if file.endswith('.json'):
            with open(os.path.join(DATA_DIR, file), 'r') as f:
                data = json.load(f)
                for topic in data:
                    topic_id = topic.get("topic_id", "Unknown ID")
                    creation_date = topic.get("creation_date", "Unknown Date")
                    edition_date = topic.get("edition_date", "Never Edited")
                    topic_name = topic.get("topic", "Unnamed Topic")
                    all_topics.append(
                        {'id': topic_id, 'date': creation_date, 'edit_date': edition_date, 'name': topic_name,
                         'file': file})

    all_topics.sort(key=lambda x: x['name'].lower())
    return render_template('list.html', topics=all_topics)


# Route to display the content of a selected topic
@app.route('/topic/<file>/<id>')
def show_topic(file, id):
    file_path = os.path.join(DATA_DIR, file)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            for topic in data:
                if topic["topic_id"] == id:
                    return render_template('topic.html', topic=topic, file=file)

    flash(f"Topic with ID {id} not found.", "danger")
    return redirect(url_for('list_topics'))


# Route to edit a topic
@app.route('/topic/<file>/<id>/edit', methods=['GET', 'POST'])
def edit_topic(file, id):
    file_path = os.path.join(DATA_DIR, file)

    if request.method == 'POST':
        updated_topic = request.form.get('topic')
        updated_data = request.form.get('data')
        edition_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store the edition date

        # Update the topic in the JSON file
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)

            for topic in data:
                if topic["topic_id"] == id:
                    topic["topic"] = updated_topic
                    topic["data"] = updated_data
                    topic["edition_date"] = edition_date  # Update the edition date

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)

            flash(f"Topic with ID {id} has been updated.", "success")
            return redirect(url_for('show_topic', file=file, id=id))

    # Preload the topic for the GET request
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            for topic in data:
                if topic["topic_id"] == id:
                    return render_template('edit.html', topic=topic, file=file)

    flash(f"Topic with ID {id} not found.", "danger")
    return redirect(url_for('list_topics'))


# Route to create a new topic
@app.route('/create', methods=['GET', 'POST'])
def create_topic():
    if request.method == 'POST':
        file_name = request.form.get('file_name', 'data')
        new_topic = request.form.get('new_topic')
        new_data = request.form.get('new_data')

        full_path = os.path.join(DATA_DIR, f"{file_name}.json")

        # Initialize the file if it doesn't exist
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                json.dump([], f)

        # Generate unique topic ID
        topic_id = generate_topic_id()

        # Append new topic to the JSON file
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "topic_id": topic_id,
            "creation_date": creation_date,
            "edition_date": "Never Edited",  # Default value for newly created topics
            "topic": new_topic,
            "data": new_data
        }

        with open(full_path, 'r') as f:
            data = json.load(f)
        data.append(new_entry)
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=4)

        flash(f"New topic '{new_topic}' added successfully!", "success")
        return redirect(url_for('list_topics'))

    return render_template('create.html')


# Route to search and edit a topic
@app.route('/search', methods=['GET', 'POST'])
def search_topic():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        found_topics = []

        # Search by keyword
        for file in os.listdir(DATA_DIR):
            if file.endswith('.json'):
                with open(os.path.join(DATA_DIR, file), 'r') as f:
                    data = json.load(f)
                    for topic in data:
                        if search_term.lower() in topic["topic"].lower():
                            found_topics.append({'id': topic["topic_id"], 'name': topic["topic"], 'file': file})

        if not found_topics:
            flash("No topics found with that term.", "danger")
        return render_template('search_results.html', topics=found_topics, search_term=search_term)

    return render_template('search.html')


# Route to delete a topic
@app.route('/delete/<file>/<id>', methods=['POST'])
def delete_topic(file, id):
    file_path = os.path.join(DATA_DIR, file)

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Filter out the topic with the matching ID
        data = [topic for topic in data if topic["topic_id"] != id]

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        flash(f"Topic with ID {id} has been deleted.", "success")
    else:
        flash(f"File not found: {file}", "danger")

    return redirect(url_for('list_topics'))


if __name__ == '__main__':
    app.run(debug=True)
