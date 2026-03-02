from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-development') # Нужно для работы flash-сообщений

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html", error=False)

@app.route("/folder/<folder_name>")
def open_folder(folder_name):
    folder_path = os.path.join("uploads", folder_name)

    if not os.path.exists(folder_path):
        flash("Папка не найдена")
        return redirect(url_for("success"))

    files = os.listdir(folder_path)
    return render_template("folder.html", folder=folder_name, files=files)

@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    correct_password = "8962"

    if password == correct_password:
        return redirect(url_for("success"))
    else:
        return render_template("index.html", error=True)

@app.route("/success")
def success():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("success.html", files=files)

@app.route("/upload", methods=["POST"])
def upload_papk():
    name=request.form.get("name_file", "").strip()
    if name=="":
        flash("Введи название папки")
    folder_path = os.path.join("uploads", name)
    if os.path.exists(folder_path):
        flash("Такая папка уже есть")
    else:
        os.makedirs(folder_path)
        flash("Папка успешно создана")
    return redirect(url_for("success"))

@app.route("/upload_file/<folder_name>", methods=["POST"])
def upload_file(folder_name):
    if "file" not in request.files:
        flash("Файл не выбран")
        return redirect(url_for("open_folder", folder_name=folder_name))

    file = request.files["file"]

    if file.filename == "":
        flash("Файл не выбран")
        return redirect(url_for("open_folder", folder_name=folder_name))

    filename = secure_filename(file.filename)

    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    file_path = os.path.join(folder_path, filename)

    file.save(file_path)

    flash("Файл успешно загружен")
    return redirect(url_for("open_folder", folder_name=folder_name))

@app.route("/download/<folder_name>/<filename>")
def download(folder_name,filename):
    folder_path=os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Папка не найдена')
        return redirect(url_for("success"))
    return send_from_directory(folder_path, filename, as_attachment=True)

@app.route("/delete/<folder_name>/<filename>")
def delete(folder_name,filename):
    folder_path=os.path.join(app.config['UPLOAD_FOLDER'],folder_name)
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(folder_path):
        flash('Папка не найдена')
        return redirect(url_for("success"))
    os.remove(file_path)
    flash("Файл удалён")
    return redirect(url_for("open_folder", folder_name=folder_name))
@app.route("/delete_papk/<folder_name>")
def delete_papk(folder_name):
    folder_path=os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Папка не найдена')
    else:
        shutil.rmtree(folder_path) 
    return redirect(url_for("success"))
if __name__ == "__main__":
    app.run(port=4000)