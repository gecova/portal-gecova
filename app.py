"""
GECOVA — Portal de Reportes de Generación Solar
Corre con: python app.py
Abre en:   http://localhost:5000
"""

from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for, flash
import os, io, tempfile, json, hashlib, sqlite3
from datetime import datetime
from functools import wraps
import pandas as pd
import pdfplumber

app = Flask(__name__)
app.secret_key = 'gecova-portal-2026-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max

# ── Rutas locales ─────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, 'gecova.db')
LOGO_PATH  = r'C:\Users\SEI\Documents\Gecova\08. Reportes\ás - LOGOTIPOS - GECOVA-02.png'
LOGO_B64   = "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" 
FONT_LOCAL = r'C:\Users\SEI\Documents\Gecova\02.- Imágen\02.- Tipografías\Montserrat'
OUTPUT_DIR = r'C:\Users\SEI\Documents\Gecova\08. Reportes'

# ── Base de datos ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario     TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                nombre      TEXT NOT NULL,
                puesto      TEXT,
                nacimiento  TEXT,
                correo      TEXT,
                telefono    TEXT,
                es_admin    INTEGER DEFAULT 0,
                activo      INTEGER DEFAULT 1,
                creado      TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS reportes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id      INTEGER NOT NULL,
                nombre_sistema  TEXT,
                cliente         TEXT,
                fecha_reporte   TEXT,
                fecha_generado  TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
            CREATE TABLE IF NOT EXISTS ordenes_mantenimiento (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_orden    TEXT NOT NULL,
                usuario_id      INTEGER NOT NULL,
                cliente         TEXT,
                central         TEXT,
                direccion       TEXT,
                tecnico         TEXT,
                supervisor      TEXT,
                fecha_servicio  TEXT,
                tipo_sistema    TEXT,
                potencia        TEXT,
                condicion       TEXT,
                creado          TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
        ''')
        # Crear admin por defecto si no existe
        admin = db.execute("SELECT id FROM usuarios WHERE usuario='admin'").fetchone()
        if not admin:
            db.execute('''INSERT INTO usuarios (usuario, password, nombre, puesto, es_admin)
                          VALUES (?,?,?,?,1)''',
                       ('admin', hash_pw('gecova2026'), 'Alberto Valenzuela', 'Director', ))
            db.commit()
            print("✓ Usuario admin creado: admin / gecova2026")

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('es_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Inicializar DB al arrancar
init_db()


# ── Extraer datos del Excel ───────────────────────────────────────────────────
def leer_excel(file_bytes):
    import io
    df = pd.read_excel(io.BytesIO(file_bytes), header=0)
    df.columns = ['Time','Plant','Weather','Alarm','Capacity_kWp','Hours','Yield_kWh','Total_Yield_kWh']
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    df = df[pd.notna(df['Time']) & pd.notna(df['Yield_kWh'])].copy()

    def month_stats(df, month):
        m = df[df['Time'].dt.month == month]
        if len(m) == 0: return 0, 0, 0, '-', 0
        return (round(m['Yield_kWh'].sum(),1), round(m['Yield_kWh'].mean(),1),
                len(m), m.loc[m['Yield_kWh'].idxmax(),'Time'].strftime('%d/%m'),
                round(m['Yield_kWh'].max(),1))

    meses = {}
    for mes, nombre in [(4,'abril'),(5,'mayo'),(6,'junio')]:
        total,avg,days,max_day,max_val = month_stats(df, mes)
        meses[nombre] = {'total':total,'avg':avg,'days':days,'max_day':max_day,'max_val':max_val}

    wc = df['Weather'].str.strip().value_counts()
    return {
        'total_kwh':   round(df['Yield_kWh'].sum(), 1),
        'total_days':  len(df),
        'avg_daily':   round(df['Yield_kWh'].mean(), 1),
        'avg_hours':   round(df['Hours'].mean(), 2),
        'total_acum':  round(df['Total_Yield_kWh'].iloc[0], 1),
        'periodo':     f"{df['Time'].min().strftime('%d Abr %Y')} — {df['Time'].max().strftime('%d Jun %Y')}",
        'fecha_inicio':df['Time'].min().strftime('%Y%m%d'),
        'meses':       meses,
        'weather': {
            'Clear':      int(wc.get('Clear', 0)),
            'Light Rain': int(wc.get('Light Rain', 0)),
            'Cloudy':     int(wc.get('Cloudy', 0)),
            'Few Clouds': int(wc.get('Few Clouds', 0)),
        },
        'daily_labels': [t.strftime('%d/%m') for t in df['Time']],
        'daily_data':   [round(v,1) for v in df['Yield_kWh']],
        'daily_months': [t.month for t in df['Time']],
    }

# ── Extraer datos del recibo CFE ──────────────────────────────────────────────
def leer_recibo(file_bytes):
    import re
    texto = ''
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ''

    def buscar(patron, texto, default=''):
        m = re.search(patron, texto)
        return m.group(1).strip() if m else default

    def num(s):
        try: return float(s.replace(',',''))
        except: return 0

    # Total a pagar
    total_match = re.search(r'TOTAL A PAGAR[:\s]*\$?([\d,]+)', texto)
    total = f"${total_match.group(1)} MXN" if total_match else ''

    # kWh total facturado (lectura actual - lectura anterior)
    kwh_match = re.search(r'Energía \(kWh\)[^\d]*([\d,]+)\s+([\d,]+)\s+([\d,]+)', texto)
    kwh_facturado = int(num(kwh_match.group(3))) if kwh_match else 0

    # Bloques tarifarios
    basico_match    = re.search(r'Basico\s+([\d,]+)\s+[\d,]+\s+([\d,]+)\s+[\d.]+\s+([\d.]+)\s+([\d,]+)\s+[\d.]+\s+([\d.]+)', texto)
    interm_match    = re.search(r'Intermedio\s+([\d,]+)\s+[\d.]+\s+([\d.]+)\s+([\d,]+)\s+[\d.]+\s+([\d.]+)', texto)
    excedente_match = re.search(r'Excedente\s+([\d,]+)\s+[\d.]+\s+([\d,.]+)\s+([\d,]+)\s+[\d.]+\s+([\d,.]+)', texto)

    kwh_basico     = int(num(basico_match.group(1)))    + int(num(basico_match.group(4)))    if basico_match    else 0
    kwh_intermedio = int(num(interm_match.group(1)))    + int(num(interm_match.group(3)))    if interm_match    else 0
    kwh_excedente  = int(num(excedente_match.group(1))) + int(num(excedente_match.group(3))) if excedente_match else 0

    imp_basico     = round(num(basico_match.group(3))    + num(basico_match.group(5)),2)    if basico_match    else 0
    imp_intermedio = round(num(interm_match.group(2))    + num(interm_match.group(4)),2)    if interm_match    else 0
    imp_excedente  = round(num(excedente_match.group(2)) + num(excedente_match.group(4)),2) if excedente_match else 0

    # Distribución + otros
    dist_match = re.search(r'Distribución\s+[\d.]+\s+[\d.]+\s+([\d,.]+)', texto)
    imp_otros  = int(num(dist_match.group(1))) if dist_match else 0

    # Datos del cliente — nombre está en línea 4 junto con "TOTAL A PAGAR:"
    lines = texto.split('\n')
    cliente_nombre = ''
    for line in lines[:10]:
        if 'TOTAL A PAGAR' in line:
            cliente_nombre = line.replace('TOTAL A PAGAR:', '').strip()
            break
    if not cliente_nombre:
        # fallback: primera línea en mayúsculas que no sea CFE
        for line in lines[:10]:
            if re.match(r'^[A-ZÁÉÍÓÚÑ\s]{5,}$', line.strip()) and 'CFE' not in line and 'REFORMA' not in line:
                cliente_nombre = line.strip()
                break
    servicio_match = re.search(r'NO\. DE SERVICIO[:\s]*([\d]+)', texto)
    tarifa_match   = re.search(r'TARIFA[:\s]*([A-Z0-9]+?)(?:NO\.|$|\s)', texto)
    medidor_match  = re.search(r'NO\. MEDIDOR[:\s]*([^\s]+)', texto)
    periodo_match  = re.search(r'PERIODO FACTURADO[:\s]*([^\n]+)', texto)

    # Historial de consumo
    hist_pattern = re.findall(r'del\s+(\d{2}\s+\w+\s+\d{2})\s+al\s+(\d{2}\s+\w+\s+\d{2})\s+([\d,]+)\s+\$([\d,.]+)', texto)
    historial = []
    meses_abrev = {'ENE':'Ene','FEB':'Feb','MAR':'Mar','ABR':'Abr','MAY':'May','JUN':'Jun',
                   'JUL':'Jul','AGO':'Ago','SEP':'Sep','OCT':'Oct','NOV':'Nov','DIC':'Dic'}
    for desde, hasta, kwh, _ in reversed(hist_pattern):
        parts_d = desde.strip().split(); parts_h = hasta.strip().split()
        mes_d = meses_abrev.get(parts_d[1].upper()[:3], parts_d[1][:3])
        mes_h = meses_abrev.get(parts_h[1].upper()[:3], parts_h[1][:3])
        anio_d = parts_d[2][-2:]; anio_h = parts_h[2][-2:]
        label = f"{mes_d} {anio_d}–{mes_h} {anio_h}"
        historial.append([label, int(kwh.replace(',','')), False])
    if historial:
        historial[-1][2] = False  # el último del historial NO es el actual
    # Agregar período actual con kWh facturado
    if periodo_match:
        p = periodo_match.group(1).strip()  # ej "06 ABR 26-04 JUN 26"
        partes = re.split(r'-', p)
        if len(partes) == 2:
            def fmt_periodo(s):
                s = s.strip().split()
                meses_abrev2 = {'ENE':'Ene','FEB':'Feb','MAR':'Mar','ABR':'Abr','MAY':'May','JUN':'Jun',
                                'JUL':'Jul','AGO':'Ago','SEP':'Sep','OCT':'Oct','NOV':'Nov','DIC':'Dic'}
                if len(s) >= 3:
                    return f"{meses_abrev2.get(s[1].upper()[:3], s[1][:3])} {s[2][-2:]}"
                return s[0] if s else ''
            label_actual = f"{fmt_periodo(partes[0])}–{fmt_periodo(partes[1])}"
            historial.append([label_actual, int(kwh_facturado), True])

    return {
        'total_pagar':     total,
        'kwh_facturado':   kwh_facturado,
        'kwh_basico':      kwh_basico,
        'kwh_intermedio':  kwh_intermedio,
        'kwh_excedente':   kwh_excedente,
        'imp_basico':      imp_basico,
        'imp_intermedio':  imp_intermedio,
        'imp_excedente':   imp_excedente,
        'imp_otros':       imp_otros,
        'cliente_nombre':  cliente_nombre,
        'cliente_servicio':servicio_match.group(1) if servicio_match else '',
        'cliente_tarifa':  tarifa_match.group(1) if tarifa_match else '',
        'cliente_medidor': medidor_match.group(1) if medidor_match else '',
        'periodo_cfe':     periodo_match.group(1).strip() if periodo_match else '',
        'historial':       historial,
    }

# ── Rutas de autenticación ────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario  = request.form.get('usuario','').strip().lower()
        password = request.form.get('password','')
        with get_db() as db:
            u = db.execute('SELECT * FROM usuarios WHERE usuario=? AND activo=1', (usuario,)).fetchone()
        if u and u['password'] == hash_pw(password):
            session['usuario_id']      = u['id']
            session['usuario']         = u['usuario']
            session['nombre_completo'] = u['nombre']
            session['es_admin']        = bool(u['es_admin'])
            return redirect(url_for('index'))
        error = 'Usuario o contraseña incorrectos.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Panel de administración ───────────────────────────────────────────────────
@app.route('/admin')
@login_requerido
@admin_requerido
def admin():
    with get_db() as db:
        usuarios = db.execute('SELECT * FROM usuarios ORDER BY creado DESC').fetchall()
        reportes = db.execute('''
            SELECT r.*, u.nombre, u.puesto FROM reportes r
            JOIN usuarios u ON r.usuario_id = u.id
            ORDER BY r.fecha_generado DESC LIMIT 50
        ''').fetchall()
        ordenes_mto = db.execute('''
            SELECT o.*, u.nombre as elaborado_nombre FROM ordenes_mantenimiento o
            JOIN usuarios u ON o.usuario_id = u.id
            ORDER BY o.creado DESC LIMIT 50
        ''').fetchall()
    return render_template('admin.html',
                           usuarios=usuarios,
                           reportes=reportes,
                           ordenes_mto=ordenes_mto,
                           nombre=session['nombre_completo'],
                           es_admin=session.get('es_admin', False),
                           logo_b64=LOGO_B64,
                           active='admin')

@app.route('/admin/usuario/nuevo', methods=['GET','POST'])
@login_requerido
@admin_requerido
def nuevo_usuario():
    error = None
    if request.method == 'POST':
        usuario    = request.form.get('usuario','').strip().lower()
        password   = request.form.get('password','').strip()
        nombre     = request.form.get('nombre','').strip()
        puesto     = request.form.get('puesto','').strip()
        nacimiento = request.form.get('nacimiento','').strip()
        correo     = request.form.get('correo','').strip()
        telefono   = request.form.get('telefono','').strip()
        es_admin   = 1 if request.form.get('es_admin') else 0
        if not usuario or not password or not nombre:
            error = 'Usuario, contraseña y nombre son obligatorios.'
        else:
            try:
                with get_db() as db:
                    db.execute('''INSERT INTO usuarios
                        (usuario, password, nombre, puesto, nacimiento, correo, telefono, es_admin)
                        VALUES (?,?,?,?,?,?,?,?)''',
                        (usuario, hash_pw(password), nombre, puesto, nacimiento, correo, telefono, es_admin))
                    db.commit()
                return redirect(url_for('admin'))
            except sqlite3.IntegrityError:
                error = f'El usuario "{usuario}" ya existe.'
    return render_template('usuario_form.html', error=error, usuario=None,
                           nombre=session['nombre_completo'], modo='nuevo',
                           es_admin=session.get('es_admin', False), logo_b64=LOGO_B64, active='admin')

@app.route('/admin/usuario/<int:uid>/editar', methods=['GET','POST'])
@login_requerido
@admin_requerido
def editar_usuario(uid):
    error = None
    with get_db() as db:
        u = db.execute('SELECT * FROM usuarios WHERE id=?', (uid,)).fetchone()
    if not u:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        nuevo_usuario = request.form.get('usuario','').strip().lower()
        nombre     = request.form.get('nombre','').strip()
        puesto     = request.form.get('puesto','').strip()
        nacimiento = request.form.get('nacimiento','').strip()
        correo     = request.form.get('correo','').strip()
        telefono   = request.form.get('telefono','').strip()
        es_admin   = 1 if request.form.get('es_admin') else 0
        new_pw     = request.form.get('password','').strip()
        try:
            with get_db() as db:
                if new_pw:
                    db.execute('''UPDATE usuarios SET usuario=?,nombre=?,puesto=?,nacimiento=?,correo=?,
                                  telefono=?,es_admin=?,password=? WHERE id=?''',
                               (nuevo_usuario,nombre,puesto,nacimiento,correo,telefono,es_admin,hash_pw(new_pw),uid))
                else:
                    db.execute('''UPDATE usuarios SET usuario=?,nombre=?,puesto=?,nacimiento=?,correo=?,
                                  telefono=?,es_admin=? WHERE id=?''',
                               (nuevo_usuario,nombre,puesto,nacimiento,correo,telefono,es_admin,uid))
                db.commit()
            # Si editó su propio usuario, actualizar sesión
            if uid == session.get('usuario_id'):
                session['nombre_completo'] = nombre
                session['usuario'] = nuevo_usuario
                session['es_admin'] = bool(es_admin)
        except sqlite3.IntegrityError:
            error = f'El usuario "{nuevo_usuario}" ya existe.'
            with get_db() as db:
                u = db.execute('SELECT * FROM usuarios WHERE id=?', (uid,)).fetchone()
            return render_template('usuario_form.html', error=error, usuario=u,
                                   nombre=session['nombre_completo'], modo='editar',
                                   es_admin=session.get('es_admin', False), logo_b64=LOGO_B64, active='admin')
        return redirect(url_for('admin'))
    return render_template('usuario_form.html', error=error, usuario=u,
                           nombre=session['nombre_completo'], modo='editar',
                           es_admin=session.get('es_admin', False), logo_b64=LOGO_B64, active='admin')

@app.route('/admin/usuario/<int:uid>/toggle', methods=['POST'])
@login_requerido
@admin_requerido
def toggle_usuario(uid):
    with get_db() as db:
        db.execute('UPDATE usuarios SET activo = 1 - activo WHERE id=?', (uid,))
        db.commit()
    return redirect(url_for('admin'))

# ── Rutas principales ─────────────────────────────────────────────────────────
@app.route('/')
@login_requerido
def index():
    return redirect(url_for('generacion'))

@app.route('/generacion')
@login_requerido
def generacion():
    return render_template('generacion.html',
                           nombre=session.get('nombre_completo',''),
                           es_admin=session.get('es_admin', False),
                           logo_b64=LOGO_B64,
                           active='generacion')

@app.route('/extraer', methods=['POST'])
@login_requerido
def extraer():
    try:
        excel_bytes  = request.files['excel'].read()
        recibo_bytes = request.files['recibo'].read()
        datos_excel  = leer_excel(excel_bytes)
        datos_cfe    = leer_recibo(recibo_bytes)
        return jsonify({'ok': True, 'excel': datos_excel, 'cfe': datos_cfe})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/generar', methods=['POST'])
@login_requerido
def generar():
    try:
        datos        = json.loads(request.form['datos'])
        excel_bytes  = request.files['excel'].read()
        recibo_bytes = request.files['recibo'].read()

        datos_excel = leer_excel(excel_bytes)
        datos_cfe   = leer_recibo(recibo_bytes)
        datos['historial']     = datos_cfe.get('historial', [])
        datos['elaborado_por'] = session.get('nombre_completo', '')

        pdf_bytes = generar_pdf(datos, datos_excel)

        nombre = f"{datos['fecha_archivo']} - {datos['nombre_sistema']} - Informe_Generación.pdf"

        # Guardar en carpeta local
        if os.path.exists(OUTPUT_DIR):
            ruta = os.path.join(OUTPUT_DIR, nombre)
            counter = 2
            while os.path.exists(ruta):
                ruta = os.path.join(OUTPUT_DIR, f"{datos['fecha_archivo']} - {datos['nombre_sistema']} - Informe_Generación ({counter}).pdf")
                counter += 1
            with open(ruta, 'wb') as f:
                f.write(pdf_bytes)

        # Registrar en historial
        with get_db() as db:
            db.execute('''INSERT INTO reportes (usuario_id, nombre_sistema, cliente, fecha_reporte)
                          VALUES (?,?,?,?)''',
                       (session['usuario_id'], datos.get('nombre_sistema',''),
                        datos.get('cliente_nombre',''), datos.get('fecha_reporte','')))
            db.commit()

        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                         as_attachment=True, download_name=nombre)
    except Exception as e:
        import traceback
        return jsonify({'ok': False, 'error': str(e), 'trace': traceback.format_exc()})

# ── Generador de PDF (reutiliza lógica del template) ──────────────────────────
def generar_pdf(d, ex):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    import math
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image

    # Fonts
    GF = '/usr/share/fonts/truetype/google-fonts/'
    CA = '/usr/share/fonts/truetype/crosextra/'

    def reg(name, local_file, fallback):
        local = os.path.join(FONT_LOCAL, local_file)
        path  = local if os.path.exists(local) else fallback
        try: pdfmetrics.registerFont(TTFont(name, path))
        except: pass

    reg('Poppins',        'Montserrat-Regular.ttf', GF+'Poppins-Regular.ttf')
    reg('Poppins-Medium', 'Montserrat-Regular.ttf', GF+'Poppins-Medium.ttf')
    reg('Poppins-Bold',   'Montserrat-Bold.ttf',    GF+'Poppins-Bold.ttf')
    reg('Poppins-Light',  'Montserrat-Regular.ttf', GF+'Poppins-Light.ttf')
    reg('Carlito',        'Montserrat-Regular.ttf', CA+'Carlito-Regular.ttf')
    reg('Carlito-Bold',   'Montserrat-Bold.ttf',    CA+'Carlito-Bold.ttf')

    # Logo
    def prepare_logo(path):
        img  = Image.open(path).convert('RGBA')
        arr  = np.array(img)
        mask = (arr[:,:,0]<30)&(arr[:,:,1]<30)&(arr[:,:,2]<30)
        arr[mask,3] = 0
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        Image.fromarray(arr).save(tmp.name)
        return tmp.name

    logo_processed = prepare_logo(LOGO_PATH) if os.path.exists(LOGO_PATH) else None

    W, H = A4
    M = 18*mm; CW = W-2*M; GAP = 5*mm

    C_DARK=colors.HexColor('#094F68'); C_ORANGE=colors.HexColor('#FA6101')
    C_TEAL=colors.HexColor('#79C4DB'); C_LIGHT=colors.HexColor('#EEF6FA')
    C_GRAY=colors.HexColor('#7a8a96'); C_TEXT=colors.HexColor('#1a2530')
    C_WHITE=colors.white; C_LINE=colors.HexColor('#dde6ec'); C_BGCARD=colors.HexColor('#f5f8fa')

    # Chart
    labels     = ex['daily_labels']
    data       = ex['daily_data']
    months     = ex['daily_months']
    bar_colors = ['#FA6101' if m==4 else '#094F68' if m==5 else '#79C4DB' for m in months]

    fig, ax = plt.subplots(figsize=(12,3.0), dpi=150)
    fig.patch.set_facecolor('#ffffff'); ax.set_facecolor('#ffffff')
    ax.bar(np.arange(len(labels)), data, color=bar_colors, width=0.75, zorder=3)
    ax.set_ylim(0,30); ax.set_xlim(-0.8, len(labels)-0.2)
    n = len(labels)
    step = max(1, n//13)
    ticks = list(range(0, n, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([labels[i] for i in ticks], fontsize=7.5, color='#7a8a96', rotation=30, ha='right')
    ax.set_yticks([0,5,10,15,20,25,30])
    ax.set_yticklabels([f'{v} kWh' for v in [0,5,10,15,20,25,30]], fontsize=8, color='#7a8a96')
    ax.yaxis.grid(True,color='#e8edf2',linewidth=0.6,zorder=0); ax.xaxis.grid(False)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color('#e8edf2'); ax.spines['bottom'].set_color('#e8edf2')
    ax.tick_params(axis='both',length=0)
    apr_t = ex['meses']['abril']['total']; may_t = ex['meses']['mayo']['total']; jun_t = ex['meses']['junio']['total']
    patches = [mpatches.Patch(color='#FA6101',label=f'Abril  {apr_t} kWh'),
               mpatches.Patch(color='#094F68',label=f'Mayo  {may_t} kWh'),
               mpatches.Patch(color='#79C4DB',label=f'Junio parcial  {jun_t} kWh')]
    ax.legend(handles=patches,loc='upper right',fontsize=8,frameon=True,framealpha=0.9,
              edgecolor='#e0e8ef',facecolor='white',ncol=3)
    plt.tight_layout(pad=0.3)
    chart_buf = io.BytesIO()
    plt.savefig(chart_buf,format='png',dpi=150,bbox_inches='tight',facecolor='white')
    chart_buf.seek(0); plt.close()

    # Icon helpers
    def draw_sun(c,cx,cy,r=4):
        c.setFillColor(colors.HexColor('#FDAD01')); c.circle(cx,cy,r*0.52,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#FDAD01')); c.setLineWidth(1.1)
        for a in range(0,360,45):
            rad=math.radians(a)
            c.line(cx+math.cos(rad)*r*0.68,cy+math.sin(rad)*r*0.68,cx+math.cos(rad)*r*1.05,cy+math.sin(rad)*r*1.05)

    def draw_cloud(c,cx,cy,r=4,col='#8a9aaa'):
        c.setFillColor(colors.HexColor(col))
        c.circle(cx-r*0.35,cy,r*0.40,fill=1,stroke=0); c.circle(cx+r*0.35,cy,r*0.40,fill=1,stroke=0)
        c.circle(cx,cy+r*0.26,r*0.50,fill=1,stroke=0); c.rect(cx-r*0.73,cy-r*0.36,r*1.46,r*0.38,fill=1,stroke=0)

    def draw_few_clouds(c,cx,cy,r=4):
        c.setFillColor(colors.HexColor('#FDAD01')); c.circle(cx+r*0.28,cy+r*0.22,r*0.36,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#FDAD01')); c.setLineWidth(0.9)
        for a in [30,75,120,160]:
            rad=math.radians(a)
            c.line(cx+r*0.28+math.cos(rad)*r*0.44,cy+r*0.22+math.sin(rad)*r*0.44,
                   cx+r*0.28+math.cos(rad)*r*0.65,cy+r*0.22+math.sin(rad)*r*0.65)
        draw_cloud(c,cx-r*0.08,cy-r*0.08,r*0.82,'#79C4DB')

    def draw_rain(c,cx,cy,r=4):
        draw_cloud(c,cx,cy+r*0.22,r*0.82,'#7a8a96')
        c.setStrokeColor(colors.HexColor('#79C4DB')); c.setLineWidth(1.0)
        for dx in [-r*0.38,0,r*0.38]: c.line(cx+dx,cy-r*0.05,cx+dx-r*0.1,cy-r*0.45)

    def wrap_text(c,text,font,size,max_w):
        words=text.split(); lines,cur=[],''
        for w in words:
            test=cur+(' ' if cur else '')+w
            if c.stringWidth(test,font,size)<=max_w: cur=test
            else: lines.append(cur); cur=w
        if cur: lines.append(cur)
        return lines

    # Layout
    FOOTER_H=11*mm; HEADER_H=46*mm; KPI_H=27*mm; CHART_H=42*mm
    MONTH_H=34*mm; INSIGHT_H=27*mm; WEATHER_H=8*mm

    y=H
    header_bot=y-HEADER_H; y=header_bot
    kpi_top=y; kpi_bot=y-KPI_H; y=kpi_bot-GAP
    chart_lbl_y=y-5*mm; y=chart_lbl_y-2*mm
    chart_bot=y-CHART_H; y=chart_bot-GAP
    month_lbl_y=y-5*mm; y=month_lbl_y-2*mm
    month_bot=y-MONTH_H; y=month_bot-GAP
    insight_top=y; insight_bot=y-INSIGHT_H; y=insight_bot-GAP
    weather_lbl_y=y-5*mm; y=weather_lbl_y-2*mm
    weather_y=y-WEATHER_H; y=weather_y-GAP
    table_lbl_y=y-5*mm; y=table_lbl_y-2*mm
    table_draw_y=y

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Informe de Generación Solar — {d['nombre_sistema']}")
    c.setAuthor('GECOVA Ingeniería')

    # ── HEADER ─────────────────────────────────────────────────────────────────
    c.setFillColor(C_DARK); c.rect(0,header_bot,W,HEADER_H,fill=1,stroke=0)
    if logo_processed:
        lh=24*mm; lw=lh*(4880/2916)
        c.drawImage(logo_processed,M,header_bot+(HEADER_H-lh)/2,width=lw,height=lh,mask='auto')

    RE=W-M; lg=6*mm
    c.setFillColor(C_TEAL); c.setFont('Poppins-Medium',8)
    y1=header_bot+HEADER_H-10*mm; c.drawRightString(RE,y1,'Informe de Generación Solar')
    c.setFillColor(C_WHITE); c.setFont('Poppins-Bold',15)
    y2=y1-lg-2*mm; c.drawRightString(RE,y2,f"Sistema {d['nombre_sistema']}  ({d['capacidad']} kWp)")
    y3=y2-lg-1*mm
    bw,bh=64*mm,6.5*mm; bx=RE-bw
    c.setFillColor(colors.HexColor('#0b5c78')); c.roundRect(bx,y3-1.5*mm,bw,bh,3*mm,fill=1,stroke=0)
    c.setFillColor(C_TEAL); c.setFont('Poppins-Medium',8)
    c.drawCentredString(bx+bw/2,y3-1.5*mm+2*mm,ex['periodo'])
    y4=y3-lg-2*mm
    c.setFillColor(colors.HexColor('#5a8fa3')); c.setFont('Carlito',8)
    c.drawRightString(RE,y4,f"Reporte generado el {d['fecha_reporte']}  |  Baja California, México")

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c.setFillColor(C_BGCARD); c.rect(0,kpi_bot,W,KPI_H,fill=1,stroke=0)
    c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
    c.line(0,kpi_top,W,kpi_top); c.line(0,kpi_bot,W,kpi_bot)

    kpis=[(f"{ex['total_kwh']:,.1f}",'kWh','Energía generada'),
          (str(ex['total_days']),'días','Días monitoreados'),
          (str(ex['avg_daily']),'kWh/día','Promedio diario'),
          (str(ex['avg_hours']),'h/día','Horas sol equiv.')]
    card_gap=3*mm; card_w=(CW-3*card_gap)/4
    for i,(val,unit,label) in enumerate(kpis):
        cx=M+i*(card_w+card_gap); cy=kpi_bot+2*mm; ch=KPI_H-4*mm
        c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.roundRect(cx,cy,card_w,ch,2.5*mm,fill=1,stroke=1)
        c.setFillColor(C_DARK); c.setFont('Poppins-Bold',14)
        vw=c.stringWidth(val,'Poppins-Bold',14); uw=c.stringWidth(' '+unit,'Carlito',8.5)
        sx=cx+(card_w-vw-uw)/2
        c.drawString(sx,cy+ch*0.52,val); c.setFont('Carlito',8.5)
        c.drawString(sx+vw,cy+ch*0.53,' '+unit)
        c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
        lw=c.stringWidth(label.upper(),'Poppins-Medium',6.5)
        c.drawString(cx+(card_w-lw)/2,cy+ch*0.25,label.upper())

    # ── CHART ──────────────────────────────────────────────────────────────────
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M,chart_lbl_y+1*mm,'GENERACIÓN DIARIA (kWh)')
    c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
    c.roundRect(M,chart_bot,CW,CHART_H,2.5*mm,fill=1,stroke=1)
    c.drawImage(ImageReader(chart_buf),M+1*mm,chart_bot+1*mm,width=CW-2*mm,height=CHART_H-2*mm,preserveAspectRatio=False)

    # ── MONTHLY CARDS ──────────────────────────────────────────────────────────
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M,month_lbl_y+1*mm,'RESUMEN MENSUAL')
    mg=4*mm; mw=(CW-2*mg)/3
    meses_cfg = [
        ('ABRIL',          ex['meses']['abril'],  '#FA6101', 'abr'),
        ('MAYO',           ex['meses']['mayo'],   '#094F68', 'may'),
        ('JUNIO (parcial)',ex['meses']['junio'],  '#79C4DB', 'jun'),
    ]
    for i,(name,ms,accent,suf) in enumerate(meses_cfg):
        mx=M+i*(mw+mg)
        c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.roundRect(mx,month_bot,mw,MONTH_H,2.5*mm,fill=1,stroke=1)
        c.setFillColor(colors.HexColor(accent))
        c.roundRect(mx,month_bot+MONTH_H-3*mm,mw,3*mm,1.5*mm,fill=1,stroke=0)
        c.rect(mx,month_bot+MONTH_H-4.5*mm,mw,2*mm,fill=1,stroke=0)
        pad=4*mm
        c.setFillColor(C_GRAY);  c.setFont('Poppins-Medium',6.5); c.drawString(mx+pad,month_bot+MONTH_H-8*mm,name)
        c.setFillColor(C_DARK);  c.setFont('Poppins-Bold',13);    c.drawString(mx+pad,month_bot+MONTH_H-16*mm,f"{ms['total']} kWh")
        c.setFillColor(colors.HexColor(accent)); c.setFont('Poppins-Medium',7); c.drawString(mx+pad,month_bot+MONTH_H-21*mm,f"{ms['days']} días")
        c.setFillColor(C_GRAY);  c.setFont('Carlito',8)
        c.drawString(mx+pad,month_bot+MONTH_H-26.5*mm,f"Prom: {ms['avg']} kWh/día")
        c.drawString(mx+pad,month_bot+MONTH_H-31*mm,  f"Máx: {ms['max_val']} kWh ({ms['max_day']} {suf})")

    # ── INSIGHT ────────────────────────────────────────────────────────────────
    c.setFillColor(C_LIGHT); c.roundRect(M,insight_bot,CW,INSIGHT_H,2.5*mm,fill=1,stroke=0)
    c.setFillColor(C_DARK);  c.roundRect(M,insight_bot,3.5,INSIGHT_H,1.5,fill=1,stroke=0)
    c.setFont('Poppins-Bold',7)
    c.drawString(M+5.5*mm,insight_bot+INSIGHT_H-6.5*mm,'CONTEXTO PARA SU RECIBO DE LUZ')
    insight=(f"Su sistema generó {ex['total_kwh']:,.1f} kWh durante el período, funcionando correctamente "
             f"los {ex['total_days']} días del ciclo. Esta energía fue inyectada a su instalación, reduciendo "
             f"su consumo de la red CFE. Si su recibo refleja un consumo elevado, se debe al consumo total "
             f"del domicilio — el sistema ya realizó su aportación. Reste los kWh generados a su consumo bruto total "
             f"para conocer el ahorro real del período.")
    c.setFillColor(C_TEXT); c.setFont('Carlito',7.5)
    for li,line in enumerate(wrap_text(c,insight,'Carlito',7.5,CW-11*mm)[:4]):
        c.drawString(M+5.5*mm,insight_bot+INSIGHT_H-12*mm-li*3.6*mm,line)

    # ── WEATHER ────────────────────────────────────────────────────────────────
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M,weather_lbl_y+1*mm,'CONDICIONES CLIMÁTICAS DEL PERÍODO')
    wc=ex['weather']; icon_r=3.8; pill_h=8*mm; icon_gap=10*mm
    weather_items=[(draw_sun,f"Despejado — {wc['Clear']} días"),
                   (draw_rain,f"Lluvia ligera — {wc['Light Rain']} días"),
                   (draw_cloud,f"Nublado — {wc['Cloudy']} días"),
                   (draw_few_clouds,f"Pocas nubes — {wc['Few Clouds']} días")]
    px=M
    for draw_fn,text in weather_items:
        pw=c.stringWidth(text,'Carlito',8)+icon_gap+5*mm
        c.setFillColor(C_BGCARD); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.roundRect(px,weather_y,pw,pill_h,3*mm,fill=1,stroke=1)
        draw_fn(c,px+icon_gap/2,weather_y+pill_h/2,icon_r)
        c.setFillColor(C_TEXT); c.setFont('Carlito',8)
        c.drawString(px+icon_gap,weather_y+(pill_h-8)/2,text)
        px+=pw+3*mm

    # ── TABLE ──────────────────────────────────────────────────────────────────
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M,table_lbl_y+1*mm,'RESUMEN DE PRODUCCIÓN ACUMULADA')
    tdata=[['Parámetro','Valor'],
           ['Energía generada en el período',        f"{ex['total_kwh']:,.1f} kWh"],
           ['Producción acumulada total del sistema', f"{ex['total_acum']:,.1f} kWh"],
           ['Capacidad instalada',                    f"{d['capacidad']} kWp"],
           ['Promedio horas sol equivalentes / día',  f"{ex['avg_hours']} h"],
           ['Días con operación registrada',          f"{ex['total_days']} días"]]
    tbl=Table(tdata,colWidths=[CW*0.65,CW*0.35])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),C_DARK),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Poppins-Bold'),('FONTSIZE',(0,0),(-1,0),8),
        ('FONTNAME',(0,1),(-1,-1),'Carlito'),('FONTSIZE',(0,1),(-1,-1),8),
        ('TEXTCOLOR',(0,1),(-1,-1),C_TEXT),('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE,C_BGCARD]),
        ('ALIGN',(1,0),(1,-1),'CENTER'),('FONTNAME',(1,1),(1,-1),'Carlito-Bold'),
        ('TEXTCOLOR',(1,1),(1,-1),C_DARK),('GRID',(0,0),(-1,-1),0.3,C_LINE),
        ('TOPPADDING',(0,0),(-1,-1),4.5),('BOTTOMPADDING',(0,0),(-1,-1),4.5),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
    ]))
    tbl.wrapOn(c,CW,50*mm); tbl.drawOn(c,M,table_draw_y-tbl._height)

    # ── FOOTER P1 ──────────────────────────────────────────────────────────────
    c.setFillColor(C_DARK); c.rect(0,0,W,FOOTER_H,fill=1,stroke=0)
    c.setFillColor(C_WHITE); c.setFont('Poppins-Bold',8.5)
    c.drawString(M,FOOTER_H-4*mm,'GECOVA Ingeniería')
    c.setFillColor(C_TEAL); c.setFont('Carlito',7.5)
    c.drawString(M,FOOTER_H-8*mm,'gecova.mx  ·  gecovamx@gmail.com')
    c.setFillColor(C_WHITE); c.setFont('Carlito',7.5)
    c.drawRightString(W-M,FOOTER_H-4*mm,f"Elaborado por: {d.get('elaborado_por','')}")
    c.setFillColor(C_TEAL); c.setFont('Carlito',7)
    c.drawRightString(W-M,FOOTER_H-8*mm,f"No. Servicio: {d['cliente_servicio']}  ·  Tarifa {d['cliente_tarifa']}  ·  Medidor: {d['cliente_medidor']}")

    # ════════════ PÁGINA 2 ════════════════════════════════════════════════════
    c.showPage()
    c.setFillColor(C_DARK); c.rect(0,H-18*mm,W,18*mm,fill=1,stroke=0)
    if logo_processed:
        lh2=11*mm; lw2=lh2*(4880/2916)
        c.drawImage(logo_processed,M,H-14.5*mm,width=lw2,height=lh2,mask='auto')
    c.setFillColor(C_TEAL); c.setFont('Poppins-Medium',7)
    c.drawRightString(W-M,H-8*mm,'Análisis Cruzado — Recibo CFE vs Generación Solar')
    c.setFillColor(colors.HexColor('#5a8fa3')); c.setFont('Carlito',7)
    c.drawRightString(W-M,H-13*mm,f"Sistema {d['nombre_sistema']}  ·  Período {ex['periodo']}  ·  Cliente: {d['cliente_nombre']}")

    GAP2=4*mm; p2y=H-18*mm
    kpi2_y=p2y-GAP2-24*mm; kpi2_h=22*mm
    consumo_real=round(d['kwh_facturado']+ex['total_kwh'],1)
    cobertura=round(ex['total_kwh']/consumo_real*100,1) if consumo_real>0 else 0
    kpis2=[(f"{d['kwh_facturado']:,}",'kWh','Consumo facturado CFE','#FA6101'),
           (f"{ex['total_kwh']:,.1f}",'kWh','Generación solar GECOVA','#094F68'),
           (f"{consumo_real:,.1f}",'kWh','Consumo real del domicilio','#575756'),
           (str(cobertura),'%','Cobertura solar','#3B6D11')]
    cw4=(CW-3*card_gap)/4
    for i,(val,unit,label,accent) in enumerate(kpis2):
        cx=M+i*(cw4+card_gap)
        c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.roundRect(cx,kpi2_y,cw4,kpi2_h,2.5*mm,fill=1,stroke=1)
        c.setFillColor(colors.HexColor(accent))
        c.roundRect(cx,kpi2_y+kpi2_h-2*mm,cw4,2*mm,1*mm,fill=1,stroke=0)
        c.rect(cx,kpi2_y+kpi2_h-3*mm,cw4,1.5*mm,fill=1,stroke=0)
        c.setFillColor(colors.HexColor(accent)); c.setFont('Poppins-Bold',14)
        vw=c.stringWidth(val,'Poppins-Bold',14); uw=c.stringWidth(' '+unit,'Carlito',8)
        sx=cx+(cw4-vw-uw)/2
        c.drawString(sx,kpi2_y+kpi2_h*0.52,val); c.setFont('Carlito',8); c.drawString(sx+vw,kpi2_y+kpi2_h*0.53,' '+unit)
        c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6)
        lw=c.stringWidth(label.upper(),'Poppins-Medium',6); c.drawString(cx+(cw4-lw)/2,kpi2_y+kpi2_h*0.22,label.upper())

    # Balance + CFE cards
    bal_h=49*mm; bal_y=kpi2_y-GAP2-bal_h; row_h=7*mm; pad=4*mm
    c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
    c.roundRect(M,bal_y,CW/2-2*mm,bal_h,2.5*mm,fill=1,stroke=1)
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M+pad,bal_y+bal_h-6*mm,'BALANCE ENERGÉTICO DEL PERÍODO')
    bars_data=[('Consumo real total',consumo_real,'#094F68'),
               ('Aportación solar',ex['total_kwh'],'#FA6101'),
               ('Facturado por CFE',float(d['kwh_facturado']),'#79C4DB'),
               ('Consumo en excedente',float(d['kwh_excedente']),'#E24B4A')]
    max_val=consumo_real; bar_x=M+pad; bar_lw=38*mm; bar_tw=CW/2-2*mm-bar_lw-22*mm-pad*2
    sby=bal_y+bal_h-13*mm
    for i,(label,val,color_hex) in enumerate(bars_data):
        ry=sby-i*row_h
        c.setFillColor(C_GRAY); c.setFont('Carlito',7.5); c.drawString(bar_x,ry+1.5*mm,label)
        c.setFillColor(C_BGCARD); c.roundRect(bar_x+bar_lw,ry,bar_tw,4.5*mm,1.5*mm,fill=1,stroke=0)
        fw=max(2*mm,bar_tw*(val/max_val)) if max_val>0 else 2*mm
        c.setFillColor(colors.HexColor(color_hex)); c.roundRect(bar_x+bar_lw,ry,fw,4.5*mm,1.5*mm,fill=1,stroke=0)
        c.setFillColor(C_TEXT); c.setFont('Carlito-Bold',7.5); c.drawRightString(bar_x+bar_lw+bar_tw+20*mm,ry+1.5*mm,f'{val:,.1f} kWh')

    rec_x=M+CW/2+2*mm; rec_w=CW/2-2*mm
    c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
    c.roundRect(rec_x,bal_y,rec_w,bal_h,2.5*mm,fill=1,stroke=1)
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(rec_x+pad,bal_y+bal_h-6*mm,'DESGLOSE DEL RECIBO CFE')
    cfe_items=[(f"Básico ({d['kwh_basico']} kWh)",     d['imp_basico'],    '#639922'),
               (f"Intermedio ({d['kwh_intermedio']} kWh)",d['imp_intermedio'],'#BA7517'),
               (f"Excedente ({d['kwh_excedente']} kWh)", d['imp_excedente'], '#E24B4A'),
               ('Distribución + otros',                   d['imp_otros'],     '#7a8a96')]
    max_cfe=d['imp_excedente'] if d['imp_excedente']>0 else 1
    rl_x=rec_x+pad; rl_lw=34*mm; rl_tw=rec_w-rl_lw-22*mm-pad*2
    for i,(label,val,color_hex) in enumerate(cfe_items):
        ry=sby-i*row_h
        c.setFillColor(C_GRAY); c.setFont('Carlito',7.5); c.drawString(rl_x,ry+1.5*mm,label)
        c.setFillColor(C_BGCARD); c.roundRect(rl_x+rl_lw,ry,rl_tw,4.5*mm,1.5*mm,fill=1,stroke=0)
        fw2=max(2*mm,rl_tw*(val/max_cfe))
        c.setFillColor(colors.HexColor(color_hex)); c.roundRect(rl_x+rl_lw,ry,fw2,4.5*mm,1.5*mm,fill=1,stroke=0)
        c.setFillColor(C_TEXT); c.setFont('Carlito-Bold',7.5); c.drawRightString(rl_x+rl_lw+rl_tw+20*mm,ry+1.5*mm,f'${val:,}')
    total_y=bal_y+8*mm
    c.setStrokeColor(C_LINE); c.setLineWidth(0.4); c.line(rec_x+pad,total_y+5*mm,rec_x+rec_w-pad,total_y+5*mm)
    c.setFillColor(C_DARK); c.setFont('Carlito-Bold',8)
    c.drawString(rec_x+pad,total_y,'Total a pagar:'); c.drawRightString(rec_x+rec_w-pad,total_y,d['total_pagar'])

    # Historial
    hist_y=bal_y-GAP2-52*mm; hist_h=50*mm
    c.setFillColor(C_WHITE); c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
    c.roundRect(M,hist_y,CW,hist_h,2.5*mm,fill=1,stroke=1)
    c.setFillColor(C_GRAY); c.setFont('Poppins-Medium',6.5)
    c.drawString(M+pad,hist_y+hist_h-6*mm,'HISTORIAL DE CONSUMO CFE (últimos períodos)')
    hist_data=d.get('historial',[])
    if hist_data:
        max_hist=max(v for _,v,_ in hist_data) or 1
        n2=len(hist_data); cw3=(CW-8*mm)/n2; col_max_h=hist_h-18*mm; base_y2=hist_y+6*mm
        for i2,(period,val,is_current) in enumerate(hist_data):
            cx2=M+4*mm+i2*cw3
            bh_val=(val/max_hist)*col_max_h
            fill_col='#094F68' if is_current else '#B5D4F4'
            c.setFillColor(colors.HexColor(fill_col))
            c.roundRect(cx2+1*mm,base_y2,cw3-2*mm,max(1.5*mm,bh_val),1*mm,fill=1,stroke=0)
            c.setFillColor(C_DARK if is_current else C_GRAY)
            c.setFont('Poppins-Bold' if is_current else 'Carlito',6 if is_current else 5.5)
            vs=str(val); vw2=c.stringWidth(vs,'Poppins-Bold' if is_current else 'Carlito',6 if is_current else 5.5)
            c.drawString(cx2+1*mm+(cw3-2*mm-vw2)/2,base_y2+bh_val+1.5*mm,vs)
            parts=period.split('–') if '–' in period else [period]
            lw3=c.stringWidth(parts[0],'Carlito',5.5)
            c.setFont('Carlito',5.5); c.drawString(cx2+1*mm+(cw3-2*mm-lw3)/2,hist_y+3.5*mm,parts[0])
    c.setFillColor(C_TEAL); c.setFont('Poppins-Medium',6.5)
    c.drawRightString(W-M-4*mm,hist_y+hist_h-6*mm,'★ Período actual')

    # Insights
    ins_available=hist_y-GAP2-(FOOTER_H+GAP2); ins_h=min(ins_available,40*mm)
    ins_w=(CW-2*GAP2)/3; ins_top=hist_y-GAP2; ins_bot=ins_top-ins_h
    ahorro_min=round(ex['total_kwh']*3.98); ahorro_max=round(ex['total_kwh']*4.15)
    consumo_dia=round(consumo_real/ex['total_days'],1) if ex['total_days']>0 else 0
    insights=[
        ('#FA6101','#FFF3EC','Consumo real muy elevado',
         f"El domicilio usó {consumo_real:,.1f} kWh reales en el período (~{consumo_dia} kWh/día promedio). "
         f"El recibo elevado obedece al alto consumo del hogar, no a una falla del sistema solar."),
        ('#094F68','#EEF6FA','Sistema operando correctamente',
         f"El sistema GECOVA funcionó los {ex['total_days']} días sin interrupciones. "
         f"Sin el sistema, el recibo estimado habría sido de $14,000–$16,000 MXN."),
        ('#3B6D11','#EAF3DE',f'Ahorro estimado: ~${ahorro_min:,} MXN',
         f"Los {ex['total_kwh']:,.1f} kWh solares desplazaron consumo en tarifa excedente "
         f"(~$3.99/kWh). El ahorro real del ciclo se estima entre ${ahorro_min:,} y ${ahorro_max:,} MXN."),
    ]
    for i,(accent,bg,title,text) in enumerate(insights):
        ix=M+i*(ins_w+GAP2); iy=ins_bot
        c.setFillColor(colors.HexColor(bg)); c.roundRect(ix,iy,ins_w,ins_h,2.5*mm,fill=1,stroke=0)
        c.setFillColor(colors.HexColor(accent)); c.roundRect(ix,iy,3,ins_h,1.5,fill=1,stroke=0)
        c.setFont('Poppins-Bold',7); c.drawString(ix+5*mm,iy+ins_h-8*mm,title)
        c.setStrokeColor(colors.HexColor(accent)); c.setLineWidth(0.3)
        c.line(ix+5*mm,iy+ins_h-10*mm,ix+ins_w-4*mm,iy+ins_h-10*mm)
        c.setFillColor(C_TEXT); c.setFont('Carlito',7)
        for li,line in enumerate(wrap_text(c,text,'Carlito',7,ins_w-9*mm)[:5]):
            c.drawString(ix+5*mm,iy+ins_h-16*mm-li*3.8*mm,line)

    # Footer p2
    c.setFillColor(C_DARK); c.rect(0,0,W,FOOTER_H,fill=1,stroke=0)
    c.setFillColor(C_WHITE); c.setFont('Poppins-Bold',8.5); c.drawString(M,FOOTER_H-4*mm,'GECOVA Ingeniería')
    c.setFillColor(C_TEAL); c.setFont('Carlito',7.5)
    c.drawString(M,FOOTER_H-8*mm,'gecova.mx  ·  gecovamx@gmail.com')
    c.setFillColor(C_WHITE); c.setFont('Carlito',7.5)
    c.drawRightString(W-M,FOOTER_H-4*mm,f"Elaborado por: {d.get('elaborado_por','')}")
    c.setFillColor(C_TEAL); c.setFont('Carlito',7)
    c.drawRightString(W-M,FOOTER_H-8*mm,f"No. Servicio: {d['cliente_servicio']}  ·  Tarifa {d['cliente_tarifa']}  ·  Medidor: {d['cliente_medidor']}")

    c.save()
    buf.seek(0)
    return buf.read()


# ── Módulo de Mantenimiento ───────────────────────────────────────────────────
@app.route('/mantenimiento')
@login_requerido
def mantenimiento():
    with get_db() as db:
        ordenes = db.execute("""
            SELECT o.*, u.nombre as elaborado_nombre
            FROM ordenes_mantenimiento o
            JOIN usuarios u ON o.usuario_id = u.id
            ORDER BY o.creado DESC LIMIT 50
        """).fetchall()
    return render_template('mantenimiento.html',
                           nombre=session.get('nombre_completo',''),
                           es_admin=session.get('es_admin', False),
                           logo_b64=LOGO_B64,
                           active='mantenimiento',
                           ordenes=ordenes)

@app.route('/mantenimiento/siguiente-orden')
@login_requerido
def siguiente_orden():
    """Devuelve el próximo número de orden sin reservarlo."""
    year = datetime.now().year
    with get_db() as db:
        row = db.execute(
            "SELECT numero_orden FROM ordenes_mantenimiento WHERE numero_orden LIKE ? ORDER BY id DESC LIMIT 1",
            (f"GCV - {year} - MTO - %",)
        ).fetchone()
    if row:
        last_num = int(row['numero_orden'].split(' - ')[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    orden = f"GCV - {year} - MTO - {str(next_num).zfill(3)}"
    return jsonify({'orden': orden})

@app.route('/mantenimiento/guardar', methods=['POST'])
@login_requerido
def guardar_mantenimiento():
    """Guarda la orden en la DB y devuelve el número asignado."""
    try:
        data = request.get_json()
        year = datetime.now().year
        # Get next number atomically
        with get_db() as db:
            row = db.execute(
                "SELECT numero_orden FROM ordenes_mantenimiento WHERE numero_orden LIKE ? ORDER BY id DESC LIMIT 1",
                (f"GCV - {year} - MTO - %",)
            ).fetchone()
            if row:
                last_num = int(row['numero_orden'].split(' - ')[-1])
                next_num = last_num + 1
            else:
                next_num = 1
            orden = f"GCV - {year} - MTO - {str(next_num).zfill(3)}"
            db.execute("""
                INSERT INTO ordenes_mantenimiento
                  (numero_orden, usuario_id, cliente, central, direccion, tecnico, supervisor,
                   fecha_servicio, tipo_sistema, potencia, condicion)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                orden,
                session['usuario_id'],
                data.get('cliente',''),
                data.get('central',''),
                data.get('direccion',''),
                data.get('tecnico',''),
                data.get('supervisor',''),
                data.get('fecha',''),
                data.get('tipo_sistema',''),
                data.get('potencia',''),
                data.get('condicion',''),
            ))
            db.commit()
        return jsonify({'ok': True, 'orden': orden})
    except Exception as e:
        import traceback
        return jsonify({'ok': False, 'error': str(e), 'trace': traceback.format_exc()})

if __name__ == '__main__':
    print("=" * 50)
    print("  GECOVA — Portal de Reportes")
    print("  Abre tu navegador en: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000)
