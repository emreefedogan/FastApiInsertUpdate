# app.py
from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

DATABASE_URL = "sqlite+aiosqlite:///./instance/example2.db"  # Asenkron SQLite bağlantısı için

# SQLAlchemy ayarları
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Kullanıcı Modeli
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

# Veritabanını oluştur
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Veritabanı oturumu
async def get_db():
    async with SessionLocal() as db:
        yield db

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return templates.TemplateResponse("index.html", {"request": request, "users": users})

@app.post("/add")
async def add_user(name: str = Form(...), email: str = Form(...), age: int = Form(...), db: AsyncSession = Depends(get_db)):
    new_user = User(name=name, email=email, age=age)
    db.add(new_user)
    await db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/update/{user_id}")
async def update_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user:
        user.age += 1
        await db.commit()
        return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/delete/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user:
        await db.delete(user)
        await db.commit()
        return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)