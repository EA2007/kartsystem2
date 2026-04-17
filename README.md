# 🗺 Kartsystem — Driftsättningsguide

Flask + SQLAlchemy backend med Leaflet-karta. Stöd för kunder, ytor, GPS-närvaro och adminpanel.

---

## Snabbstart (lokalt)

```bash
# 1. Klona / packa upp projektet
cd kartsystem

# 2. Skapa virtuell miljö
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Installera beroenden
pip install -r requirements.txt

# 4. Skapa .env-fil
cp .env.example .env
# Redigera .env — byt SECRET_KEY och ADMIN_PASSWORD

# 5. Starta
python app.py
```

Öppna **http://localhost:5000** — logga in med `admin` / lösenordet du satte i `.env`.

---

## Produktionsdriftsättning (Ubuntu/Debian VPS)

### 1. Förbered servern

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx
```

### 2. Ladda upp projektet

```bash
# Från din dator
scp -r kartsystem/ user@DIN-SERVER:/var/www/kartsystem
ssh user@DIN-SERVER
```

### 3. Installera på servern

```bash
cd /var/www/kartsystem
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Konfigurera miljövariabler
cp .env.example .env
nano .env   # Sätt SECRET_KEY, DATABASE_URL och ADMIN_PASSWORD

# Sätt rättigheter
sudo chown -R www-data:www-data /var/www/kartsystem
sudo chmod 750 /var/www/kartsystem
```

### 4. Systemd-tjänst

```bash
sudo cp kartsystem.service /etc/systemd/system/
# Redigera sökvägar om du placerat projektet annorlunda:
sudo nano /etc/systemd/system/kartsystem.service

sudo systemctl daemon-reload
sudo systemctl enable kartsystem
sudo systemctl start kartsystem

# Kontrollera att den körs:
sudo systemctl status kartsystem
```

### 5. Nginx

```bash
# Redigera nginx.conf — byt ut "dittdomän.se" mot ditt riktiga domännamn
nano nginx.conf

sudo cp nginx.conf /etc/nginx/sites-available/kartsystem
sudo ln -s /etc/nginx/sites-available/kartsystem /etc/nginx/sites-enabled/
sudo nginx -t          # Testa konfigurationen
sudo systemctl reload nginx
```

### 6. HTTPS (Let's Encrypt — gratis)

```bash
sudo certbot --nginx -d dittdomän.se -d www.dittdomän.se
# Följ instruktionerna — certbot uppdaterar nginx.conf automatiskt
# Certifikat förnyas automatiskt
```

### 7. Peka domänen

Hos din domänregistrator, lägg till en **A-post**:

| Typ | Namn | Värde           |
|-----|------|-----------------|
| A   | @    | DIN-SERVERS-IP  |
| A   | www  | DIN-SERVERS-IP  |

---

## Byta databas till PostgreSQL

```bash
# Installera PostgreSQL
sudo apt install postgresql postgresql-contrib
pip install psycopg2-binary

# Skapa databas
sudo -u postgres psql
CREATE DATABASE kartsystem_db;
CREATE USER kartsystem_user WITH PASSWORD 'starkt-lösenord';
GRANT ALL PRIVILEGES ON DATABASE kartsystem_db TO kartsystem_user;
\q

# Uppdatera .env
DATABASE_URL=postgresql://kartsystem_user:starkt-lösenord@localhost/kartsystem_db
```

---

## Uppdatera applikationen

```bash
cd /var/www/kartsystem
# Ladda upp nya filer...
source venv/bin/activate
pip install -r requirements.txt   # Om nya paket tillkommit
sudo systemctl restart kartsystem
```

---

## API-översikt

| Metod  | URL                              | Beskrivning               |
|--------|----------------------------------|---------------------------|
| POST   | `/api/auth/login`                | Logga in                  |
| POST   | `/api/auth/logout`               | Logga ut                  |
| GET    | `/api/auth/me`                   | Nuvarande användare       |
| GET    | `/api/customers`                 | Lista kunder              |
| POST   | `/api/customers`                 | Skapa kund (admin)        |
| DELETE | `/api/customers/<id>`            | Ta bort kund (admin)      |
| GET    | `/api/customers/<id>/areas`      | Hämta ytor för kund       |
| PUT    | `/api/customers/<id>/areas`      | Spara alla ytor för kund  |
| PATCH  | `/api/areas/<uid>/status`        | Uppdatera ytstatus        |
| GET    | `/api/users`                     | Lista användare (admin)   |
| POST   | `/api/users`                     | Registrera användare      |
| DELETE | `/api/users/<id>`                | Ta bort användare (admin) |
| POST   | `/api/presence`                  | Publicera GPS-position    |
| DELETE | `/api/presence`                  | Ta bort GPS-position      |
| GET    | `/api/presence`                  | Hämta alla positioner     |
| GET    | `/api/activity`                  | Aktivitetslogg (admin)    |

---

## Säkerhet att tänka på

- Byt `SECRET_KEY` och `ADMIN_PASSWORD` i `.env` omedelbart
- Använd alltid HTTPS i produktion
- Håll Python-paket uppdaterade: `pip install -U -r requirements.txt`
- Ta regelbundna säkerhetskopior av databasen: `cp kartsystem.db kartsystem.db.bak`
