from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse,JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import shutil
from pathlib import Path
import json
import sqlite3
from werkzeug.utils import secure_filename

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SECRET_KEY', 'fallback-secret-key-for-development'))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_flash_messages(request: Request):
    """Получить flash-сообщения из сессии"""
    messages = request.session.get('flash_messages', [])
    request.session['flash_messages'] = []
    return messages


def flash(request: Request, message: str):
    """Добавить flash-сообщение в сессию"""
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append(message)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    conn = sqlite3.connect("baza_user.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT UNIQUE,
            Passw TEXT
        )
    ''')
    conn.commit()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "error": False})


@app.get("/folder/{user}/{folder_name}", response_class=HTMLResponse)
async def open_folder(request: Request,user:str, folder_name: str):
    folder_path = os.path.join("uploads",user, folder_name)

    if not os.path.exists(folder_path):
        flash(request, "Папка не найдена")
        return RedirectResponse(url="/success", status_code=303)

    files = os.listdir(folder_path)
    messages = get_flash_messages(request)
    
    return templates.TemplateResponse(
        "folder.html",
        {"request": request, "username": user, "folder": folder_name, "files": files, "get_flashed_messages": lambda: messages}
    )


@app.post("/login")
async def log(request: Request,password: str = Form(...),user: str = Form(...)):
    us=user.strip()
    ps=password.strip()
    conn=sqlite3.connect("baza_user.db")
    cur=conn.cursor()
    cur.execute('''
                    SELECT Passw
                    FROM Users
                    WHERE Name = ?
                    ''',(us,))
    ril_psw=cur.fetchone()
    conn.commit()
    conn.close()
    if ril_psw is None:
        return JSONResponse(content={
            "status": "Not_user",
            "notification": f"Такого пользователья нет. Создать новый аккаунт?",
        })
    db_password = ril_psw[0]
    if ps == db_password:
        request.session["user"]=user
        return RedirectResponse(url="/success", status_code=303)
    else:
        return JSONResponse(content={
            "status": "error",
            "notification": f"Неверный пароль!",
        })

@app.post("/add_user")
async def log(password: str = Form(...),user: str = Form(...)):
    us=user.strip()
    ps=password.strip()
    folder_path = os.path.join(UPLOAD_FOLDER, us)
    os.makedirs(folder_path, exist_ok=True)
    conn=sqlite3.connect("baza_user.db")
    cur=conn.cursor()
    cur.execute('''
                    INSERT INTO Users
                    (Name, Passw)
                    VALUES (?, ?);
                    ''',(us,ps))
    conn.commit()
    conn.close()
    return JSONResponse(content={
        "status": "good"
    })


@app.get("/success", response_class=HTMLResponse)
async def success(request: Request):
    user=request.session.get("user")
    if user!=None:
        folder_path = os.path.join(UPLOAD_FOLDER, user)
        files = os.listdir(folder_path)
        return templates.TemplateResponse(
            "success.html",
            {"request": request,"username":user, "files": files}
        )
    else:
        return RedirectResponse(url="/", status_code=303)



@app.post("/upload")
async def upload_papk(request: Request, name_file: str = Form("")):
    name = name_file.strip()
    user=request.session.get("user")

    if name == "":
        return JSONResponse(content={
            "status": "Not_inp"
        })
    else:
        folder_path = os.path.join("uploads",user,name)
        if os.path.exists(folder_path):
            return JSONResponse(content={
                "status": "pov"
            })
        else:
            os.makedirs(folder_path)
            return JSONResponse(content={
                "status": "good"
            })


@app.post("/upload_file/{user}/{folder_name}")
async def upload_file(request: Request,user:str, folder_name: str, file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(content={
            "status": "error",
            "message": "Файл не выбран"
        })

    filename = secure_filename(file.filename)
    folder_path = os.path.join(UPLOAD_FOLDER, user, folder_name)
    file_path = os.path.join(folder_path, filename)

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return JSONResponse(content={
        "status": "success",
        "message": "Файл успешно загружен",
        "filename": filename
    })


@app.get("/download/{user}/{folder_name}/{filename}")
async def download(request: Request, user: str, folder_name: str, filename: str):
    folder_path = os.path.join(UPLOAD_FOLDER, user, folder_name)
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(folder_path):
        flash(request, 'Папка не найдена')
        return RedirectResponse(url="/success", status_code=303)
    
    if not os.path.exists(file_path):
        flash(request, 'Файл не найден')
        return RedirectResponse(url=f"/folder/{user}/{folder_name}", status_code=303)
    
    return FileResponse(file_path, filename=filename, media_type='application/octet-stream')


@app.post("/delete/{user}/{folder_name}/{filename}")
async def delete(request: Request, user: str, folder_name: str, filename: str):
    folder_path = os.path.join(UPLOAD_FOLDER, user, folder_name)
    file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(folder_path):
        return JSONResponse(content={
            "status": "error",
            "message": "Папка не найдена"
        })
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return JSONResponse(content={
            "status": "success",
            "message": "Файл удалён"
        })
    else:
        return JSONResponse(content={
            "status": "error",
            "message": "Файл не найден"
        })


@app.post("/delete_papk/{user}/{folder_name}")
async def delete_papk(request: Request, user: str, folder_name: str):
    folder_path = os.path.join(UPLOAD_FOLDER, user, folder_name)
    
    if not os.path.exists(folder_path):
        return JSONResponse(content={
            "status": "error",
            "message": "Папка не найдена"
        })
    else:
        shutil.rmtree(folder_path)
        return JSONResponse(content={
            "status": "success",
            "message": "Папка удалена"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=6767)
