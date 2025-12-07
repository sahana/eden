# Quick Start Guide - Sahana Eden Ubuntu 24.04

## 🚀 Instalasi dalam 3 Langkah

### 1. Clone Repository
```bash
git clone https://github.com/sahana/eden.git
cd eden
```

### 2. Jalankan Script Instalasi
```bash
sudo bash install_sahana_ubuntu24.sh
```

### 3. Start Server
```bash
sudo systemctl start sahana-eden
```

Akses di browser: **http://localhost:8000/eden**

---

## 📋 Informasi Login Default

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | testing |
| User | normaluser@example.com | testing |

> ⚠️ **Ubah password setelah login pertama!**

---

## 🛠️ Perintah Berguna

### Mengelola Service

```bash
# Start server
sudo systemctl start sahana-eden

# Stop server
sudo systemctl stop sahana-eden

# Restart server
sudo systemctl restart sahana-eden

# Status server
sudo systemctl status sahana-eden

# Enable auto-start on boot
sudo systemctl enable sahana-eden

# View logs
sudo journalctl -u sahana-eden -f
```

### Manual Start (Alternative)

```bash
cd /opt/sahana
sudo ./start_eden.sh
```

---

## ✅ Verifikasi Instalasi

```bash
bash verify_installation.sh
```

---

## 📊 Informasi Database

### SQLite (Default)
- Location: `/opt/sahana/eden/databases/storage.db`
- No additional configuration needed

### PostgreSQL (Production)
```bash
# Access database
sudo -u postgres psql -d sahana

# Backup database
sudo -u postgres pg_dump sahana > backup.sql

# Restore database
sudo -u postgres psql -d sahana < backup.sql
```

---

## 🔧 Troubleshooting Cepat

### Server tidak bisa diakses?
```bash
# Cek status service
sudo systemctl status sahana-eden

# Cek logs
sudo journalctl -u sahana-eden -n 50

# Cek firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

### Port 8000 sudah digunakan?
```bash
# Cek process yang menggunakan port
sudo lsof -i :8000

# Atau gunakan
sudo netstat -tlnp | grep 8000

# Kill process jika perlu
sudo kill -9 <PID>
```

### Permission errors?
```bash
sudo chown -R $USER:$USER /opt/sahana
chmod +x /opt/sahana/start_eden.sh
```

### Database error?
```bash
# Reset database (WARNING: menghapus semua data!)
cd /opt/sahana/web2py
rm -rf applications/eden/databases/*
python3 web2py.py -S eden -M -R applications/eden/static/scripts/tools/noop.py
```

---

## 📁 Lokasi File Penting

| Item | Lokasi |
|------|--------|
| Eden App | `/opt/sahana/eden/` |
| web2py | `/opt/sahana/web2py/` |
| Config | `/opt/sahana/eden/models/000_config.py` |
| Database | `/opt/sahana/eden/databases/` |
| Service | `/etc/systemd/system/sahana-eden.service` |
| Logs | `journalctl -u sahana-eden` |

---

## 🌐 Setup Production (Nginx + SSL)

### Install Nginx
```bash
sudo apt-get install nginx
```

### Konfigurasi Nginx
```bash
sudo nano /etc/nginx/sites-available/sahana-eden
```

Paste konfigurasi:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /eden/static/ {
        alias /opt/sahana/eden/static/;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/sahana-eden /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Install SSL (Let's Encrypt)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🔄 Update Sahana Eden

```bash
cd /opt/sahana/eden
git pull origin master
sudo systemctl restart sahana-eden
```

---

## 📚 Dokumentasi Lengkap

- **Developer Handbook**: https://eden-asp.readthedocs.io
- **Wiki**: https://eden.sahanafoundation.org
- **Mailing List**: https://groups.google.com/g/eden-asp
- **GitHub**: https://github.com/sahana/eden

---

## 🆘 Bantuan

Jika mengalami masalah:
1. Baca dokumentasi lengkap di `INSTALL_UBUNTU.md`
2. Jalankan verification script: `bash verify_installation.sh`
3. Check logs: `sudo journalctl -u sahana-eden -f`
4. Kunjungi mailing list atau GitHub issues

---

## 📝 Catatan

- Default port: **8000**
- Default database: **SQLite** (file-based)
- Recommended untuk production: **PostgreSQL**
- Ubah configuration di: `/opt/sahana/eden/models/000_config.py`

---

**Happy coding with Sahana Eden! 🎉**
