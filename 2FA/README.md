# 2FA-geschützte Login-Webanwendung

Dieses Projekt ist eine einfache, aber sichere Webanwendung mit Benutzerregistrierung, Login-Funktionalität und Zwei-Faktor-Authentifizierung (2FA) über TOTP (z. B. Google Authenticator).

---

## Projektbeschreibung

Ziel des Projekts ist es, eine webbasierte Benutzerverwaltung mit erhöhter Sicherheit bereitzustellen. Die Anwendung unterstützt:

- Benutzerregistrierung mit Passwortvalidierung
- Login mit Rate-Limiting (Schutz gegen Brute-Force)
- Zwei-Faktor-Authentifizierung mit TOTP (QR-Code + Smartphone-App)
- Schutz vor CSRF durch Flask-WTF
- Passwort-Hashing via bcrypt
- Speicherung der Benutzerinformationen in einer SQLite-Datenbank

Nach erfolgreicher Anmeldung wird der Nutzer auf eine Bestätigungsseite weitergeleitet.

---

## Projektstruktur

| Datei / Ordner     | Beschreibung                                      |
|---------------------|--------------------------------------------------|
| `app.py`            | Flask-Hauptanwendung mit Routing und Logik       |
| `db.py`             | Datenbankfunktionen (User speichern/laden)       |
| `users.db`          | SQLite-Datenbank mit Nutzerdaten                 |
| `templates/`        | HTML-Templates (`login.html`, `register.html` …) |
| `requirements.txt`  | Abhängigkeiten (Flask, pyotp, bcrypt, etc.)      |

---

## Voraussetzungen

- Python 3.10 oder höher
- `pip` (Python-Paketmanager)
- Internetverbindung für Erstinstallation
- Smartphone mit Authenticator-App (z. B. Google Authenticator)

---

## Installation

```bash
# Projektverzeichnis betreten
cd projektverzeichnis

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

---

## Anwendung starten

```bash
python app.py
```

Die Anwendung ist anschließend erreichbar unter:

```
http://127.0.0.1:5000
```

---

## Funktionen im Ablauf

1. **Registrierung**: Benutzer gibt Benutzernamen und Passwort an. Das Passwort wird sicher gehasht und in der Datenbank gespeichert.
2. **Login**: Benutzername + Passwort werden abgefragt. Bei Erfolg: Weiterleitung zu 2FA.
3. **2FA-Verifizierung**: Nutzer scannt QR-Code mit App. Danach Eingabe des TOTP-Codes.
4. **Erfolg**: Nutzer wird zur `success.html` weitergeleitet.

---

## Sicherheitstechniken

- TOTP-basierte Authentifizierung über `pyotp`
- Passworthashing mit `bcrypt`
- Rate-Limiting über Session-Counter
- CSRF-Schutz durch `Flask-WTF`
- Kein Klartext-Passwort gespeichert
- Kein QR-Code gespeichert (nur Secret beim Nutzer)

---