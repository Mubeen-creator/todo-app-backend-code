from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from dailydo_todo_app import setting
from typing import Annotated
from contextlib import asynccontextmanager


# Create Model
class Todo (SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(index=True, min_length=3, max_length=54)
    is_completed: bool = Field(default=False)


# engine one for whole application
connection_string: str = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Creating tables")
    create_tables()
    print("Table Created")
    yield


app: FastAPI = FastAPI(lifespan=lifespan, title="dailyDo Todo App", version='1.0.0')

@app.get('/')
async def root():
    return {'message': 'Welocome dailyDo todo app'}

@app.post('/todos/', response_model=Todo)
async def create_todo(todo:Todo, session:Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo
    
@app.get('/todos/', response_model= list[Todo])
async def get_all(session:Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    if todos:
        return todos
    else:
        raise HTTPException(status_code=404, detail=f'No Task found')
    
@app.get('/todos/{id}', response_model=Todo)
async def get_single_todo(id: int, session:Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id==id)).first()
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail=f'Todo with id {id} not found')
    
@app.put('/todos/{id}')
async def edit_todo(id: int, todo:Todo, session:Annotated[Session, Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id==id)).first()
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail=f'Todo with id {id} not found')
    
@app.delete('/todos/{id}')
async def delete_todo(id: int, session:Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if todo:
        session.delete(todo)
        session.commit()
        # session.refresh(todo)
        return {"message": "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail=f'Todo with id {id} not found')
    
    