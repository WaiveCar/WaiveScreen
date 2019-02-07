[ -e main.db ] && rm main.db
sqlite3 main.db < schema.sql
chmod 0666 main.db
