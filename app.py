from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = "sqlite:///./example.db"

# SQLAlchemy ayarları
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Kullanıcı Modeli
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

# Veritabanını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Veritabanı bağlantısı
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    query = "SELECT * FROM users"
    users = await database.fetch_all(query)
    return templates.TemplateResponse("index.html", {"request": request, "users": users})

@app.post("/add")
async def add_user(name: str = Form(...), email: str = Form(...), age: int = Form(...)):
    query = "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)"
    values = {"name": name, "email": email, "age": age}
    await database.execute(query, values)
    return RedirectResponse(url="/", status_code=303)

@app.post("/update/{user_id}")
async def update_user(user_id: int):
    query = "UPDATE users SET age = age + 1 WHERE id = :id"
    values = {"id": user_id}
    await database.execute(query, values)
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{user_id}")
async def delete_user(user_id: int):
    query = "DELETE FROM users WHERE id = :id"
    values = {"id": user_id}
    await database.execute(query, values)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
