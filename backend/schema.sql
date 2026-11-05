-- This file covers the Queue table only.
-- The services table must be created first by the teammate implementing Service.
-- Coordinate its id type with that schema; this foreign key expects BIGINT UNSIGNED.
CREATE TABLE IF NOT EXISTS queues (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    service_id BIGINT UNSIGNED NOT NULL,
    status ENUM('open', 'closed') NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_queues_service
        FOREIGN KEY (service_id) REFERENCES services (id),
    INDEX idx_queues_service_status (service_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
