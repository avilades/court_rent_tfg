-- Crea un índice único parcial para evitar reservas duplicadas
-- Solo afecta a registros activos (is_cancelled = False)

CREATE UNIQUE INDEX IF NOT EXISTS ix_active_booking 
ON bookings (court_id, start_time) 
WHERE is_cancelled = false;
