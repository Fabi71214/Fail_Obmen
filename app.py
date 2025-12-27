from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-development') # Нужно для работы flash-сообщений

# Конфигурация загрузки файлов
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx',"mp4"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем папку для загрузок, если ее нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Главная страница с формой ввода
@app.route("/")
def index():
    return render_template("index.html", error=False)


# Обработчик формы входа
@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    correct_password = "8962"

    if password == correct_password:
        return redirect(url_for("success"))
    else:
        return render_template("index.html", error=True)


# Страница успешного входа
@app.route("/success")
def success():
    # Получаем список файлов в папке загрузок
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("success.html", files=files)


# Загрузка файлов
@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for("success"))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for("success"))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Файл успешно загружен')
        return redirect(url_for("success"))
    else:
        flash('Файл не подходит')
        return redirect(url_for("success"))


# Скачивание файлов
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


# Удаление файлов
@app.route("/delete/<filename>")
def delete_file(filename):
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Файл успешно удалён')
    except FileNotFoundError:
        flash('File not found')
    return redirect(url_for("success"))


# Проверка разрешенных расширений файлов
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

