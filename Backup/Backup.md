
# 📦 PostgreSQL Backup-System mit GPG-Verschlüsselung und automatisierter Übertragung

## 🔧 Systemübersicht

- **Quell-VM (VM1)**: 193.196.53.144 – enthält PostgreSQL und das Backup-Skript
- **Ziel-VM (VM2)**: 193.196.52.126 – empfängt verschlüsselte Backups
- **Nutzer**: `jukrauss`
- **Datenbankname**: `db_sswem`
- **Backup-Zeitpunkt**: täglich um 02:00 Uhr automatisiert per `cron`

---

## 🔁 Backup-Ablauf

### 1. PostgreSQL Dump mit `pg_dump`

Dump der Datenbank `db_sswem` erfolgt lokal auf VM1 unter Benutzer `jukrauss`.  
Das Passwort wird sicher über `.pgpass` bezogen (nicht im Skript gespeichert).

### 2. Verschlüsselung mit GPG (AES256, symmetrisch)

Die SQL-Dump-Datei wird mit einer fest definierten Passphrase verschlüsselt.

### 3. Sicherer Transfer via `rsync` über SSH

Die `.sql.gpg`-Datei wird per `rsync` über SSH-Schlüssel auf VM2 unter  
`/home/jukrauss/backups/pgsql/` übertragen.

### 4. Aufbewahrung und Löschung alter Backups

Lokal werden alle `.gpg`-Backups gelöscht, die älter als 7 Tage sind.

### 5. Logging

Ausgaben und Fehler werden nach `/home/jukrauss/pgsql_backup.log` geschrieben.

---

## 🗓 Automatisierung mit Cron

Auf VM1 eingerichtet via:

```cron
0 2 * * * /home/jukrauss/backup_pgsql.sh >> /home/jukrauss/pgsql_backup_cron.log 2>&1
```

→ Führt das Backup täglich um 02:00 Uhr aus und protokolliert das Ergebnis in eine Log-Datei.

---

## 🔐 Sicherheit

| Maßnahme             | Beschreibung |
|----------------------|--------------|
| Passwortschutz       | `.pgpass` mit chmod 600, Passwort nicht im Klartext im Skript |
| Verschlüsselung      | `gpg --symmetric --cipher-algo AES256` |
| Transportschutz      | `rsync -e ssh` mit hinterlegtem SSH-Key |
| Zugriffsschutz       | Backup-Verzeichnis mit Benutzerrechten eingeschränkt |
| Fallback bei Fehler  | Skript bricht kontrolliert ab, Speicherplatz wird geprüft |

---

## 🛠 Fallback-Strategien

| Fehlerfall                     | Verhalten                       |
|--------------------------------|----------------------------------|
| PostgreSQL-Dienst gestoppt     | `pg_dump` schlägt fehl, Skript bricht ab |
| Passwort ungültig              | `pg_dump` schlägt fehl, keine Datei entsteht |
| Nicht genug Speicherplatz      | Backup wird nicht ausgeführt, Log enthält Fehler |
| SSH fehlgeschlagen             | Datei bleibt lokal erhalten     |
| GPG-Verschlüsselung fehlgeschlagen | Keine Dateiübertragung erfolgt |

---

## 📄 Beispiel `.pgpass`

Pfad: `/home/jukrauss/.pgpass`  
Inhalt (eine Zeile):

```
localhost:5432:db_sswem:jukrauss:52IXgFPpj8EPoXuuofIqkdZY68UmjH3hatdExygU1ytIH4PKYY8bJtFLZkN2Q7Jg
```

Rechte setzen:

```bash
chmod 600 ~/.pgpass
```

---

## 🔁 Wiederherstellung eines Backups

1. Datei auf VM2 entschlüsseln:

```bash
gpg -d db_sswem_backup_<DATUM>.sql.gpg > restore.sql
```

2. In PostgreSQL importieren:

```bash
psql -U jukrauss -d db_sswem -f restore.sql
```

---

## 🧪 Speicherplatzprüfung im Skript

Vor dem Dump prüft das Skript, ob mindestens 50 MB verfügbar sind:

```bash
REQUIRED_MB=50
AVAILABLE_MB=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
if (( AVAILABLE_MB < REQUIRED_MB * 1024 )); then
  echo "$(date): Fehler – nicht genug Speicherplatz für Backup (${AVAILABLE_MB} kB verfügbar)" >> "$LOGFILE"
  exit 1
fi
```

---

## ✅ Status der Umsetzung (nach Aufgabenstellung)

| Anforderung                        | Erfüllt |
|-----------------------------------|---------|
| Vollständige Automatisierung      | ✅      |
| GPG-verschlüsselte Speicherung    | ✅      |
| Verschlüsselter Transport (SSH)   | ✅      |
| Zwei VMs getrennt genutzt         | ✅      |
| Fehlerbehandlung und Logging      | ✅      |
| Speicherplatz-Fallback            | ✅      |

## 📜 Vollständiges Backup-Skript (`backup_pgsql.sh`)

```bash
#!/bin/bash
set -euo pipefail

# Konfiguration
DB_NAME="db_sswem"
DB_USER="jukrauss"
BACKUP_DIR="/home/jukrauss/backups/pgsql"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql"
ENCRYPTED_FILE="${BACKUP_FILE}.gpg"
REMOTE_USER="jukrauss"
REMOTE_HOST="193.196.52.126"
REMOTE_DIR="/home/jukrauss/backups/pgsql"
SSH_KEY="/home/jukrauss/.ssh/id_rsa_vm1_openssh"
LOGS_DIR="/home/jukrauss/logs"
LOGFILE="${LOGS_DIR}/pgsql_backup.log"
GPG_PASSPHRASE="lusty-skinhead-manhood-steadily-property-spree"

# Vorbereitung
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOGS_DIR"
echo "$(date): Starte Backup für ${DB_NAME}" >> "$LOGFILE"

# Speicherplatzprüfung
REQUIRED_MB=50
AVAILABLE_MB=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
if (( AVAILABLE_MB < REQUIRED_MB * 1024 )); then
  echo "$(date): Fehler – nicht genug Speicherplatz für Backup (${AVAILABLE_MB} kB verfügbar)" >> "$LOGFILE"
  exit 1
fi

# Dump der Datenbank
PGPASSWORD=$(awk -F: -v db="$DB_NAME" -v user="$DB_USER" '$3==db && $4==user {print $5}' ~/.pgpass)
PGPASSWORD="$PGPASSWORD" pg_dump -U "$DB_USER" -d "$DB_NAME" -F p -f "$BACKUP_FILE"

# Verschlüsselung mit GPG
gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase "$GPG_PASSPHRASE" "$BACKUP_FILE"
rm "$BACKUP_FILE"

# Übertragung an Zielserver
rsync -avz -e "ssh -i $SSH_KEY" "$ENCRYPTED_FILE" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

# Alte lokale Backups löschen (älter als 7 Tage)
find "$BACKUP_DIR" -type f -name "*.gpg" -mtime +7 -exec rm {} \;

echo "$(date): Backup erfolgreich abgeschlossen" >> "$LOGFILE"
```

## 🔄 Wiederherstellungsprozess – Automatisiert

Der Wiederherstellungsprozess läuft auf VM1 ab und besteht aus den folgenden Schritten:

### 1. Übergabe des Dateinamens

Der Benutzer gibt den Namen der `.sql.gpg`-Datei als Argument beim Start des Restore-Skripts an.

### 2. Vorbereitende Bereinigung

Falls die Tabelle `testdata` bereits in der Ziel-Datenbank vorhanden ist, wird sie automatisch gelöscht (`DROP TABLE IF EXISTS`), um Konflikte zu vermeiden.

### 3. SCP-Download vom Zielserver (VM2)

Die verschlüsselte Datei wird per `scp` über SSH von VM2 nach VM1 in das Backup-Verzeichnis geladen (`~/backups/pgsql/`).

### 4. Entschlüsselung mit GPG

Die `.sql.gpg`-Datei wird symmetrisch mit dem bekannten Passwort entschlüsselt und als `restore.sql` gespeichert.

### 5. Einspielen in die PostgreSQL-Datenbank

Die SQL-Datei wird mit `psql` in die Datenbank `db_sswem` eingespielt.

### 6. Logging

Alle Aktionen (inkl. Fehler) werden in eine Logdatei geschrieben: `~/logs/restore_<timestamp>.log`

---
### Vollständiges Restore_backup-Skript
´´´
#!/bin/bash
set -euo pipefail

# === Argumentprüfung ===
BACKUP_FILE_REMOTE="${1:-}"
if [[ -z "$BACKUP_FILE_REMOTE" ]]; then
  echo "Error: Bitte den Dateinamen der Backup-Datei als Argument angeben."
  echo "Beispiel: ./restore_pgsql_backup.sh db_sswem_backup_20250615020001.sql.gpg"
  exit 1
fi

# === Konfiguration ===
REMOTE_USER="jukrauss"
REMOTE_HOST="193.196.52.126"
REMOTE_PATH="/home/jukrauss/backups/pgsql"
LOCAL_DIR="/home/jukrauss/backups/pgsql"
SSH_KEY="/home/jukrauss/.ssh/id_rsa_vm1_openssh"
GPG_PASSPHRASE="lusty-skinhead-manhood-steadily-property-spree"

# === Zielordner prüfen/anlegen ===
mkdir -p "$LOCAL_DIR"

# === 0. Vorbereitend: Bestehende Tabelle löschen, falls vorhanden ===
echo "Entferne vorhandene Tabelle testdata (falls vorhanden) ..."
psql -U jukrauss -d db_sswem -c "DROP TABLE IF EXISTS testdata CASCADE;"

# === 1. Datei holen ===
echo "Lade Backup von ${REMOTE_HOST} ..."
scp -i "$SSH_KEY" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/${BACKUP_FILE_REMOTE}" "${LOCAL_DIR}/"

# === 2. Entschlüsseln ===
echo "Entschlüssle Backup ..."
gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -d "${LOCAL_DIR}/${BACKUP_FILE_REMOTE}" > "${LOCAL_DIR}/restore.sql"

# === 3. In Datenbank einspielen ===
echo "Stelle Backup in Datenbank wieder her ..."
psql -U jukrauss -d db_sswem -f "${LOCAL_DIR}/restore.sql"

echo "Wiederherstellung abgeschlossen."

´´´


---

### 📄 Beispielaufruf:

```bash
./restore_pgsql_backup_with_drop.sh db_sswem_backup_20250616144638.sql.gpg
```

Diese Datei muss zuvor via `rsync` oder manuell auf VM2 erzeugt worden sein.
