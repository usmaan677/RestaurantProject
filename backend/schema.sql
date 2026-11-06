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
