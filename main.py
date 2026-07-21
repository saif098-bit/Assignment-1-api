from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from db import get_connection, init_db, row_to_task

app = FastAPI()
init_db()

class TaskCreate(BaseModel):
    title: str = ""

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Build a CRUD API",
        "done": False
    },
    {
        "id": 3,
        "title": "Test the API with Swagger",
        "done": True
    }
]

@app.get("/", description="Returns basic information about the Task API."
)
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health", description="Checks whether the API server is running.")
def health():
    return {"status": "ok"}


@app.get("/tasks", description="Returns a list of all tasks.")
def get_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", description="Returns a specific task by its ID.")
def get_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    return row_to_task(row)


@app.post("/tasks", status_code=201, description="Creates a new task.")
def create_task(task_data: TaskCreate):
    title = task_data.title.strip()

    if not title:
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (title, 0)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"id": new_id, "title": title, "done": False}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate, description="Updates the title and/or completion status of a task."):
    for task in tasks:
        if task["id"] == task_id:

            update_data = task_data.model_dump(exclude_unset=True)

            if not update_data:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Request body cannot be empty"}
                )

            if "title" in update_data:
                if not update_data["title"].strip():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Title cannot be empty"}
                    )

                task["title"] = update_data["title"].strip()

            if "done" in update_data:
                task["done"] = update_data["done"]

            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )

@app.delete("/tasks/{task_id}", status_code=204,  description="Deletes a task permanently.")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )