from flask import Blueprint, request, jsonify, make_response
from app.models.task import Task
from app import db
from datetime import datetime
from app.helper_functions import validate_model, create_model, sort_models, update_model, send_slack_message


tasks_bp = Blueprint("tasks_db", __name__, url_prefix="/tasks")

# Create
@tasks_bp.route("", methods=["POST"])
def post_task():
    request_body = request.get_json()
    new_task = create_model(Task, request_body)
    db.session.add(new_task)
    db.session.commit()
    return make_response({"task": new_task.to_dict()}, 201)


# Read
@tasks_bp.route("", methods=["GET"])
def get_all_tasks():
    sort_query = request.args.get("sort")
    title_query = request.args.get("title")
    tasks_query = Task.query
    if title_query:
        # filter tasks by case-insensitive substring
        tasks_query = tasks_query.filter(Task.title.ilike(f'%{title_query}%'))
    tasks = sort_models(Task, tasks_query, sort_query)
    tasks_response = [task.to_dict() for task in tasks]
    return jsonify(tasks_response)


@tasks_bp.route("/<task_id>", methods=["GET"])
def get_task(task_id):
    task = validate_model(Task, task_id)
    return make_response({"task": task.to_dict()})


# Update
@tasks_bp.route("<task_id>", methods=["PUT"])
def update_task_info(task_id):
    task = validate_model(Task, task_id)
    request_body = request.get_json()
    update_model(task, request_body)
    db.session.commit()
    return make_response({"task": task.to_dict()})


@tasks_bp.route("<task_id>/mark_complete", methods=["PATCH"])
def mark_task_complete(task_id):
    task = validate_model(Task, task_id)
    task.completed_at = datetime.utcnow()
    db.session.commit()
    response = send_slack_message(task)

    # response.ok is a boolean value that is True if the HTTP status code is between 
    # 200 and 299 (indicating a successful request), and False otherwise
    if response.ok:
        return make_response({"task": task.to_dict()})
    else:
        return make_response({"Error message":response.text})


@tasks_bp.route("<task_id>/mark_incomplete", methods=["PATCH"])
def mark_task_incomplete(task_id):
    task = validate_model(Task, task_id)
    task.completed_at = None
    db.session.commit()
    return make_response({"task": task.to_dict()})


# Delete
@tasks_bp.route("<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = validate_model(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    return make_response({"details": f"Task {task_id} \"{task.title}\" successfully deleted"})
