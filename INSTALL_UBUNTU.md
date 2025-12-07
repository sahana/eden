# Panduan Instalasi Sahana Eden di Ubuntu 24.04 LTS

Dokumen ini memberikan panduan lengkap untuk menginstal Sahana Eden di server Ubuntu 24.04 LTS menggunakan script instalasi otomatis.

## Persyaratan Sistem

### Minimum Requirements
- Ubuntu 24.04 LTS (fresh install recommended)
- 2 GB RAM minimum (4 GB recommended)
- 10 GB disk space minimum
- Python 3.9 atau lebih baru
- Akses root/sudo
- Koneksi internet

### Recommended Requirements (Production)
- Ubuntu 24.04 LTS
- 4 GB RAM atau lebih
- 20 GB disk space atau lebih
- PostgreSQL database
- Web server (Apache/Nginx) sebagai reverse proxy

## Instalasi Cepat

### 1. Download atau Clone Repository

```bash
git clone https://github.com/sahana/eden.git
cd eden
```

### 2. Jalankan Script Instalasi

```bash
sudo bash install_sahana_ubuntu24.sh
```

### 3. Ikuti Prompt Interaktif

Script akan meminta informasi berikut:

1. **Direktori instalasi** (default: `/opt/sahana`)
2. **Password untuk web2py admin interface**
3. **Jenis database**:
   - SQLite (default, untuk development)
   - PostgreSQL (recommended untuk production)
4. **Jika memilih PostgreSQL**:
   - Nama database (default: `sahana`)
   - Username database (default: `sahana`)
   - Password database

### 4. Tunggu Proses Instalasi

Instalasi akan memakan waktu beberapa menit tergantung kecepatan internet dan spesifikasi server. Script akan:
- Update sistem
- Install dependensi sistem
- Install dependensi Python
- Setup database (SQLite atau PostgreSQL)
- Clone dan konfigurasi web2py
- Clone dan konfigurasi Sahana Eden
- Initialize database
- Membuat systemd service
- Setup helper scripts

## Menjalankan Sahana Eden

### Menggunakan Systemd Service (Recommended)

```bash
# Start service
sudo systemctl start sahana-eden

# Enable on boot
sudo systemctl enable sahana-eden

# Check status
sudo systemctl status sahana-eden

# View logs
sudo journalctl -u sahana-eden -f

# Stop service
sudo systemctl stop sahana-eden
```

### Manual Start

```bash
cd /opt/sahana
sudo ./start_eden.sh
```

## Mengakses Aplikasi

Setelah server berjalan, akses Sahana Eden melalui browser:

- **Local**: http://localhost:8000/eden
- **Remote**: http://YOUR_SERVER_IP:8000/eden

### Login Credentials Default

**Administrator:**
- Email: `admin@example.com`
- Password: `testing`

**Normal User:**
- Email: `normaluser@example.com`
- Password: `testing`

> ⚠️ **PENTING**: Segera ubah password default setelah login pertama kali!

## Konfigurasi Post-Installation

### 1. Ubah Password Default

Login sebagai admin dan ubah password melalui menu user profile.

### 2. Konfigurasi Email (Opsional)

Edit file `/opt/sahana/eden/models/000_config.py`:

```python
settings.mail.server = "smtp.gmail.com:587"
settings.mail.sender = "your-email@gmail.com"
settings.mail.login = "username:password"
```

### 3. Setup Reverse Proxy dengan Nginx (Production)

Install Nginx:

```bash
sudo apt-get install nginx
```

Buat konfigurasi Nginx:

```bash
sudo nano /etc/nginx/sites-available/sahana-eden
```

Contoh konfigurasi:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /eden/static/ {
        alias /opt/sahana/eden/static/;
        expires 24h;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/sahana-eden /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Setup SSL dengan Let's Encrypt (Production)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

### Server tidak bisa diakses

```bash
# Check if service is running
sudo systemctl status sahana-eden

# Check logs
sudo journalctl -u sahana-eden -n 50

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp  # If using UFW
```

### Database Error

**PostgreSQL**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Connect to database
sudo -u postgres psql -d sahana

# Check connection settings in
nano /opt/sahana/eden/models/000_config.py
```

**SQLite**:
```bash
# Check database file permissions
ls -la /opt/sahana/eden/databases/

# Reset database (WARNING: deletes all data)
cd /opt/sahana/web2py
rm -rf applications/eden/databases/*
python3 web2py.py -S eden -M -R applications/eden/static/scripts/tools/noop.py
```

### Python Dependencies Error

```bash
# Reinstall Python packages
pip3 install --upgrade -r /opt/sahana/eden/requirements.txt
pip3 install --upgrade -r /opt/sahana/eden/optional_requirements.txt
```

### Permission Issues

```bash
# Fix ownership (replace 'username' with actual user)
sudo chown -R username:username /opt/sahana

# Fix permissions
chmod +x /opt/sahana/start_eden.sh
chmod +x /opt/sahana/eden_status.sh
```

## Maintenance

### Backup Database

**PostgreSQL**:
```bash
sudo -u postgres pg_dump sahana > sahana_backup_$(date +%Y%m%d).sql
```

**SQLite**:
```bash
cp /opt/sahana/eden/databases/storage.db /backup/storage.db.$(date +%Y%m%d)
```

### Update Sahana Eden

```bash
cd /opt/sahana/eden
git pull origin master
sudo systemctl restart sahana-eden
```

### Update web2py

```bash
cd /opt/sahana/web2py
git pull origin master
sudo systemctl restart sahana-eden
```

## Informasi Tambahan

### Lokasi File Penting

- **Sahana Eden**: `/opt/sahana/eden/`
- **web2py**: `/opt/sahana/web2py/`
- **Konfigurasi**: `/opt/sahana/eden/models/000_config.py`
- **Database (SQLite)**: `/opt/sahana/eden/databases/`
- **Logs**: `sudo journalctl -u sahana-eden`
- **Systemd Service**: `/etc/systemd/system/sahana-eden.service`

### Useful Commands

```bash
# View running processes
ps aux | grep web2py

# Check disk space
df -h

# Check memory usage
free -h

# Monitor system resources
htop

# Test database connection (PostgreSQL)
sudo -u postgres psql -d sahana -c "SELECT version();"
```

## Uninstall

Untuk menghapus Sahana Eden sepenuhnya:

```bash
# Stop service
sudo systemctl stop sahana-eden
sudo systemctl disable sahana-eden

# Remove service file
sudo rm /etc/systemd/system/sahana-eden.service
sudo systemctl daemon-reload

# Remove files
sudo rm -rf /opt/sahana

# Remove PostgreSQL database (if used)
sudo -u postgres psql -c "DROP DATABASE sahana;"
sudo -u postgres psql -c "DROP USER sahana;"

# Remove packages (optional)
# Note: This will remove packages that might be used by other applications
# sudo apt-get remove --purge postgresql postgresql-contrib
```

## Dukungan dan Dokumentasi

- **Developer Handbook**: https://eden-asp.readthedocs.io
- **Project Wiki**: https://eden.sahanafoundation.org
- **Mailing List**: https://groups.google.com/g/eden-asp
- **GitHub Repository**: https://github.com/sahana/eden
- **Issue Tracker**: https://github.com/sahana/eden/issues

## Lisensi

Sahana Eden dilisensikan di bawah MIT License. Lihat file LICENSE untuk detail lebih lanjut.
