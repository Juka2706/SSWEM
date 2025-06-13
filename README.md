# SSWEM 2FA and Backup

## 2FA
A secure web application that demonstrates user authentication with password validation and two-factor authentication (2FA) using time-based one-time passwords (TOTP). The system emphasizes security best practices, including hashed credentials, QR-based 2FA setup, and basic protection against brute force attacks.

## Backup
Dieses Projekt implementiert ein sicheres und automatisiertes Backup-System für eine PostgreSQL-Datenbank.  
Die Lösung basiert auf einem Shell-Skript, das täglich per Cron ausgeführt wird.  
Das Backup wird verschlüsselt (AES256 via GPG) und per SSH auf eine zweite, unabhängige VM übertragen.  
Alle sicherheitsrelevanten Aspekte wie Passwortschutz, Zugriffskontrolle, Fehlerbehandlung und Speicherplatzprüfung sind berücksichtigt.

Ziel ist ein robuster und wartungsfreier Datensicherungsprozess gemäß den Anforderungen des Moduls.
