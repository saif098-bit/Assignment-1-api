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
    row = conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()
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

@app.put("/tasks/{task_id}", description="Updates the title and/or completion status of a task.")
def update_task(task_id: int, task_data: TaskUpdate):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    update_data = task_data.model_dump(exclude_unset=True)

    if not update_data:
        conn.close()
        return JSONResponse(
            status_code=400,
            content={"error": "Request body cannot be empty"}
        )

    new_title = row["title"]
    if "title" in update_data:
        if not update_data["title"].strip():
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"error": "Title cannot be empty"}
            )
        new_title = update_data["title"].strip()

    new_done = update_data.get("done", bool(row["done"]))

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, int(new_done), task_id)
    )
    conn.commit()
    conn.close()

    return {"id": task_id, "title": new_title, "done": new_done}


@app.delete("/tasks/{task_id}", status_code=204, description="Deletes a task permanently.")
def delete_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"}
        )

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()