from models import User, Event, Todo, engine, Base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
import json
from sqlalchemy import func

SessionLocal = sessionmaker(bind=engine)

def get_user(db, username):
    return db.query(User).filter(User.username == username).first()

def create_user(db, username, password, department):
    # パスワードハッシュ生成は省略（元の generate_password_hash を使用）
    user = User(username=username, password=password, department=department)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def add_event_to_db(db, title, start_time, end_time, description, owner_id):
    ev = Event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        owner_id=owner_id,
        deleted=False
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

# 他のCRUD関数も同様に記述
