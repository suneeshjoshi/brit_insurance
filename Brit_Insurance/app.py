import uuid

import uvicorn
from fastapi import FastAPI, Depends, Request, Form, status
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import models
from database import engine, SessionLocal
from utils import get_config, get_token

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create FastAPI instance
app = FastAPI()

# Mount the 'static' directory as '/static' URL prefix
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    """
    Returns a database session handle.

    This function yields a session to the caller, allowing database operations
    to be performed within a context managed by FastAPI's dependency system.
    The session is automatically closed after its use to prevent resource leaks.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoint for displaying result
@app.get("/result/{total}/{number_of_items}/{token}")
def result(request: Request,
           total: float | int,
           number_of_items: int,
           token: str):
    """
    Display the result page with the total value and number of items.
    """
    return templates.TemplateResponse("result.html",
                                      {"request": request,
                                       "total": total,
                                       "number_of_items": number_of_items,
                                       "token": get_token(token)
                                       })


# Endpoint for displaying items
@app.get("/display/{token}")
def home(request: Request,
         token: str,
         db: Session = Depends(get_db)
         ):
    """
    Display the home page with the list of items.
    """
    token = get_token(token)
    check_valid_user_session(token, db)

    items = db.query(models.Item).all()
    return templates.TemplateResponse("base.html",
                                      {"request": request,
                                       "item_list": items,
                                       "token": token
                                       })


# Check if user session is valid
def check_valid_user_session(token: str,
                             db: Session = Depends(get_db)):
    """
    Check if the user session is valid.
    """
    active_session = (db.query(models.UserSession)
                      .filter(models.UserSession.token == token)
                      .filter(models.UserSession.state == True)
                      .first())

    # Check for valid User Session
    if not active_session:
        raise HTTPException(status_code=401, detail="Invalid token")


# Endpoint for adding a new item
@app.post("/add")
def add(request: Request,
        item_name: str = Form(...),
        value_amount: float | int = Form(...),
        token: str = Form(...),
        db: Session = Depends(get_db)):
    """
    Add a new item.
    """
    token = get_token(token)

    check_valid_user_session(token, db)

    new_item = models.Item(name=item_name, value=value_amount, token=token)
    db.add(new_item)
    db.commit()

    url = app.url_path_for("home", token=token)
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


# Endpoint for displaying summary
@app.post("/summary")
def summary(request: Request,
            token: str = Form(...),
            db: Session = Depends(get_db)):
    """
    Display summary of items.
    """
    token = get_token(token)
    check_valid_user_session(token, db)

    total = 0.0
    number_of_items = (db.query(models.Item).filter(models.Item.token == token)
                       .count())

    if number_of_items > 0:
        items = db.query(models.Item).filter(models.Item.token == token).all()

        # Compute the total value
        total = sum(item.value for item in items)

        print("Sum of prices where token = {}: {}".format(total, token))
        print("Number of prices where token = {}: {}".format(number_of_items, token))

    url = app.url_path_for("result", total=total, number_of_items=number_of_items, token=token)
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


# Endpoint for deleting an item
@app.get("/delete/{item_id}/{token}")
def delete(request: Request, item_id: int, token: str, db: Session = Depends(get_db)):
    """
    Delete an item.
    """
    token = get_token(token)
    check_valid_user_session(token, db)

    item = (db.query(models.Item)
            .filter(models.Item.id == item_id).first())
    db.delete(item)
    db.commit()

    url = app.url_path_for("home", token=token)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


# LOGIN LOGIC

# Display login page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Display login page.
    """
    return templates.TemplateResponse("login.html", {"request": request})


# Handle login
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...),
                db: Session = Depends(get_db)):
    """
    Handle user login.
    """
    user = (db.query(models.User)
            .filter(models.User.username == username)
            .filter(models.User.password == password)
            .first())

    if user:
        new_session = models.UserSession(user_id=user.id, token=str(uuid.uuid4()))
        db.add(new_session)
        db.commit()

        return templates.TemplateResponse("login_success.html", {"request": request,
                                                                 "username": user.username,
                                                                 "token": new_session.token
                                                                 })

    return templates.TemplateResponse("login_failure.html", {"request": request, "username": username})


# Handle logout
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request,
                 token: str = Form(...),
                 db: Session = Depends(get_db)):
    """
    Handle user logout.
    """
    session = (db.query(models.UserSession)
               .filter(models.UserSession.token == token)
               .first())

    if session:
        session.state = False
        db.commit()

    return templates.TemplateResponse("logout.html", {"request": request})


# Display signup page
@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    """
    Display signup page.
    """
    return templates.TemplateResponse("signup.html", {"request": request})


# Handle user registration
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request,
                   username: str = Form(...),
                   password: str = Form(...),
                   db: Session = Depends(get_db)):
    """
    Handle user registration.
    """
    try:
        new_user = models.User(username=username, password=password)
        db.add(new_user)
        db.commit()
        return templates.TemplateResponse("user_creation_success.html", {"request": request, "username": username})
    except Exception:
        url = app.url_path_for("login")
        return templates.TemplateResponse("user_creation_failure.html", {"request": request, "username": username})


if __name__ == "__main__":
    # Read config values
    config = get_config()

    # Run the server
    uvicorn.run(app, host=config['Server']['host'], port=int(config['Server']['port']))
