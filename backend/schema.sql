-- Login details for each user.
CREATE TABLE IF NOT EXISTS user_credentials (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    PRIMARY KEY (id),
    CONSTRAINT uq_user_credentials_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Personal details for each user.
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(254) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    preferences VARCHAR(500) NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_user_profiles_email UNIQUE (email),
    CONSTRAINT fk_user_profiles_email
        FOREIGN KEY (email) REFERENCES user_credentials (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Starting users. Passwords are admin1234 and user1234.
INSERT IGNORE INTO user_credentials (email, password_hash, role) VALUES
    ('admin@queuesmart.com', '$2b$12$y477B7QBuefNltrQuNQtcet3e4K5d12cLn82uOEXAyBEXNwhexuxe', 'admin'),
    ('user@queuesmart.com', '$2b$12$lkuYWH3uMF8vAOZIVhhffeyEu.POGI3QQe.4O6AxzELG.sh.mehVS', 'user');

INSERT IGNORE INTO user_profiles (email, full_name) VALUES
    ('admin@queuesmart.com', 'Admin User'),
    ('user@queuesmart.com', 'Test User');

-- Services must be created before queues because queues.service_id references it.
CREATE TABLE IF NOT EXISTS services (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    expected_duration INT UNSIGNED NOT NULL,
    priority TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT chk_services_expected_duration
        CHECK (expected_duration > 0),
    CONSTRAINT chk_services_priority
        CHECK (priority BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Starting services.
INSERT IGNORE INTO services (id, name, description, expected_duration, priority) VALUES
    (1, 'Dine In', 'Sit down and enjoy your meal at the restaurant.', 20, 3),
    (2, 'Take Out', 'Pick up your order at the front counter.', 10, 3),
    (3, 'DoorDash', 'Have your order delivered to your door.', 35, 3);

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

-- Messages sent to each user.
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    message VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('sent', 'viewed') NOT NULL DEFAULT 'sent',
    PRIMARY KEY (id),
    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES user_credentials (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Record of each user's queue activity.
CREATE TABLE IF NOT EXISTS queue_history (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    service_id BIGINT UNSIGNED NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    outcome ENUM('Joined Queue', 'Left Queue', 'Served') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_queue_history_user
        FOREIGN KEY (user_id) REFERENCES user_credentials (id),
    CONSTRAINT fk_queue_history_service
        FOREIGN KEY (service_id) REFERENCES services (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Each row is one user waiting in one queue.
-- user_credentials and queues must be created before this table because of the foreign keys.
-- waiting_user_id is filled in by MySQL: it equals user_id while the status is 'waiting' and
-- is NULL otherwise. The unique rule on it means a user can only be waiting once per queue,
-- but can still have many old 'served' or 'canceled' rows and rejoin later.
CREATE TABLE IF NOT EXISTS queue_entries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    queue_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    position INT UNSIGNED NOT NULL,
    priority TINYINT UNSIGNED NOT NULL DEFAULT 1,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) NOT NULL DEFAULT 'waiting',
    waiting_user_id BIGINT UNSIGNED
        GENERATED ALWAYS AS (IF(status = 'waiting', user_id, NULL)) STORED,
    PRIMARY KEY (id),
    CONSTRAINT uq_queue_entries_queue_waiting_user
        UNIQUE (queue_id, waiting_user_id),
    CONSTRAINT fk_queue_entries_queue
        FOREIGN KEY (queue_id) REFERENCES queues (id),
    CONSTRAINT fk_queue_entries_user
        FOREIGN KEY (user_id) REFERENCES user_credentials (id),
    CONSTRAINT chk_queue_entries_position
        CHECK (position > 0),
    CONSTRAINT chk_queue_entries_priority
        CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT chk_queue_entries_status
        CHECK (status IN ('waiting', 'served', 'canceled')),
    INDEX idx_queue_entries_queue_status (queue_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
