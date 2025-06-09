from shared.celery_app import app


def send_task_to_parser(categories):
    app.send_task("parser.tasks.parse_category", args=[*categories], queue="parsing_queue")
