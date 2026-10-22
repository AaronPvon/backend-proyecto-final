-- =====================================================================
-- A Pachas - Script de creación de la base de datos
-- MySQL 8 · InnoDB · utf8mb4
--
-- ATENCIÓN: este script es para desarrollo. Borra las tablas si ya
-- existen y las vuelve a crear con datos de prueba, así que se pierden
-- los datos anteriores.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS a_pachas_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE a_pachas_db;

-- Se borran en orden inverso a sus dependencias
DROP TABLE IF EXISTS settlements;
DROP TABLE IF EXISTS expense_shares;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS group_members;
DROP TABLE IF EXISTS expense_groups;
DROP TABLE IF EXISTS users;

-- ---------------------------------------------------------------------
-- users: usuarios registrados
-- ---------------------------------------------------------------------
CREATE TABLE users (
  id             INT          NOT NULL AUTO_INCREMENT,
  name           VARCHAR(100) NOT NULL,
  lastname       VARCHAR(150) NOT NULL,
  nickname       VARCHAR(50)  NOT NULL,
  email          VARCHAR(255) NOT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at     DATETIME     NULL,  -- reservado para la futura eliminación de cuenta
  CONSTRAINT pk_users          PRIMARY KEY (id),
  CONSTRAINT uq_users_nickname UNIQUE (nickname),
  CONSTRAINT uq_users_email    UNIQUE (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- expense_groups: grupos de gastos
-- ---------------------------------------------------------------------
CREATE TABLE expense_groups (
  id           INT           NOT NULL AUTO_INCREMENT,
  title        VARCHAR(100)  NOT NULL,
  description  TEXT          NULL,
  budget       DECIMAL(10,2) NULL,  -- presupuesto opcional, solo informativo
  currency     CHAR(3)       NOT NULL DEFAULT 'EUR',
  status       ENUM('active','closed') NOT NULL DEFAULT 'active',
  closed_at    DATETIME      NULL,
  created_by   INT           NOT NULL,  -- creador y único gestor
  created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT pk_expense_groups PRIMARY KEY (id),
  CONSTRAINT fk_expense_groups_created_by
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,
  CONSTRAINT ck_expense_groups_budget
    CHECK (budget IS NULL OR budget > 0),
  -- closed_at tiene valor si y solo si el grupo está cerrado
  CONSTRAINT ck_expense_groups_closed_at
    CHECK ((status = 'active' AND closed_at IS NULL)
        OR (status = 'closed' AND closed_at IS NOT NULL))
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- group_members: relación N:M entre usuarios y grupos
-- ---------------------------------------------------------------------
CREATE TABLE group_members (
  group_id    INT NOT NULL,
  user_id     INT NOT NULL,
  status      ENUM('pending','accepted','left') NOT NULL DEFAULT 'pending',
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT pk_group_members PRIMARY KEY (group_id, user_id),
  CONSTRAINT fk_group_members_group
    FOREIGN KEY (group_id) REFERENCES expense_groups (id) ON DELETE RESTRICT,
  CONSTRAINT fk_group_members_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- expenses: gastos que un miembro pagó en nombre del grupo
-- ---------------------------------------------------------------------
CREATE TABLE expenses (
  id            INT           NOT NULL AUTO_INCREMENT,
  group_id      INT           NOT NULL,
  paid_by       INT           NOT NULL,
  title         VARCHAR(100)  NOT NULL,
  description   TEXT          NULL,
  amount        DECIMAL(10,2) NOT NULL,
  split_type    ENUM('equal','custom') NOT NULL DEFAULT 'equal',
  expense_date  DATE          NOT NULL,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT pk_expenses PRIMARY KEY (id),
  CONSTRAINT fk_expenses_group
    FOREIGN KEY (group_id) REFERENCES expense_groups (id) ON DELETE RESTRICT,
  -- solo un miembro del grupo puede figurar como pagador
  CONSTRAINT fk_expenses_paid_by
    FOREIGN KEY (group_id, paid_by) REFERENCES group_members (group_id, user_id),
  CONSTRAINT ck_expenses_amount CHECK (amount > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- expense_shares: parte de cada gasto que corresponde a cada participante
-- ---------------------------------------------------------------------
CREATE TABLE expense_shares (
  expense_id  INT           NOT NULL,
  user_id     INT           NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  CONSTRAINT pk_expense_shares PRIMARY KEY (expense_id, user_id),
  CONSTRAINT fk_expense_shares_expense
    FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
  CONSTRAINT fk_expense_shares_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
  CONSTRAINT ck_expense_shares_amount CHECK (amount >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- settlements: liquidaciones entre miembros (transferencias externas)
-- ---------------------------------------------------------------------
CREATE TABLE settlements (
  id            INT           NOT NULL AUTO_INCREMENT,
  group_id      INT           NOT NULL,
  from_user_id  INT           NOT NULL,  -- quien paga la deuda
  to_user_id    INT           NOT NULL,  -- quien la cobra
  amount        DECIMAL(10,2) NOT NULL,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT pk_settlements PRIMARY KEY (id),
  CONSTRAINT fk_settlements_group
    FOREIGN KEY (group_id) REFERENCES expense_groups (id) ON DELETE RESTRICT,
  CONSTRAINT fk_settlements_from
    FOREIGN KEY (group_id, from_user_id) REFERENCES group_members (group_id, user_id),
  CONSTRAINT fk_settlements_to
    FOREIGN KEY (group_id, to_user_id) REFERENCES group_members (group_id, user_id),
  CONSTRAINT ck_settlements_amount CHECK (amount > 0),
  CONSTRAINT ck_settlements_users  CHECK (from_user_id <> to_user_id)
) ENGINE=InnoDB;


-- =====================================================================
-- DATOS DE PRUEBA
--
-- Todos los usuarios tienen la contraseña: Pachas123!
-- (hash Argon2id generado con argon2-cffi)
--
-- Grupo 1 "Viaje a Lisboa" (activo, creador Ana):
--   miembros Ana, Luis y Marta; Pablo tiene una invitación pendiente.
--   Incluye los tres modos de reparto y un reparto con céntimo sobrante.
-- Grupo 2 "Piso compartido" (cerrado, creador Luis):
--   Marta saldó su deuda y salió (left); se cerró con Pablo debiendo
--   dinero, el caso que muestra el aviso de saldos pendientes.
-- =====================================================================

INSERT INTO users (id, name, lastname, nickname, email, password_hash) VALUES
  (1, 'Ana',   'García López',   'anag',   'ana@example.com',   '$argon2id$v=19$m=65536,t=3,p=4$oFgm0GNyi3l86y96MP7AVg$9ZD4DV62HS/QoOxecQHBohmiRfzEEABkKsAIz36sh+A'),
  (2, 'Luis',  'Martín Sanz',    'luism',  'luis@example.com',  '$argon2id$v=19$m=65536,t=3,p=4$z+6ttMoptdq4W6MIyLUn0A$ljpXbpSQAu8DvfKTLsJT2pAGp7FQPjAaJarOoXL9gTs'),
  (3, 'Marta', 'Ruiz Fernández', 'martar', 'marta@example.com', '$argon2id$v=19$m=65536,t=3,p=4$+zOBifECiGROIXtg288Xow$7zSl8o51OxJjQtayq4fbfFnVrxhQE3jaC85wEt8hZ/o'),
  (4, 'Pablo', 'Díaz Moreno',    'pablod', 'pablo@example.com', '$argon2id$v=19$m=65536,t=3,p=4$6YeT4sIOY1axeJe58RMgZg$FcN5jHwa9J67NasJMDoGgJQftcrikXKzpOfHxo627t4');

INSERT INTO expense_groups (id, title, description, budget, currency, status, closed_at, created_by) VALUES
  (1, 'Viaje a Lisboa',  'Gastos del viaje de cuatro días a Lisboa.', 1000.00, 'EUR', 'active', NULL,                  1),
  (2, 'Piso compartido', 'Gastos comunes del piso de la calle Mayor.', NULL,   'EUR', 'closed', '2026-09-30 20:00:00', 2);

INSERT INTO group_members (group_id, user_id, status) VALUES
  (1, 1, 'accepted'),  -- Ana (creadora)
  (1, 2, 'accepted'),  -- Luis
  (1, 3, 'accepted'),  -- Marta
  (1, 4, 'pending'),   -- Pablo, invitación sin responder
  (2, 2, 'accepted'),  -- Luis (creador)
  (2, 3, 'left'),      -- Marta, salió con saldo 0
  (2, 4, 'accepted');  -- Pablo

INSERT INTO expenses (id, group_id, paid_by, title, description, amount, split_type, expense_date) VALUES
  -- Grupo 1
  (1, 1, 1, 'Hotel',           'Tres noches en el centro.',  300.00, 'equal',  '2026-08-01'),  -- iguales entre todos
  (2, 1, 2, 'Cena de llegada', NULL,                          40.00, 'equal',  '2026-08-01'),  -- iguales entre todos, con sobrante
  (3, 1, 3, 'Entradas museo',  'Ana no fue.',                 30.00, 'equal',  '2026-08-02'),  -- iguales entre algunos
  (4, 1, 1, 'Gasolina',        'Según los km de cada uno.',   50.00, 'custom', '2026-08-04'),  -- personalizado
  -- Grupo 2
  (5, 2, 2, 'Internet septiembre', NULL,                      30.00, 'equal',  '2026-09-01');

INSERT INTO expense_shares (expense_id, user_id, amount) VALUES
  (1, 1, 100.00), (1, 2, 100.00), (1, 3, 100.00),
  (2, 1,  13.34), (2, 2,  13.33), (2, 3,  13.33),  -- 40 / 3: el céntimo sobrante va al menor user_id (Ana)
  (3, 2,  15.00), (3, 3,  15.00),
  (4, 1,  10.00), (4, 2,  20.00), (4, 3,  20.00),
  (5, 2,  10.00), (5, 3,  10.00), (5, 4,  10.00);

INSERT INTO settlements (id, group_id, from_user_id, to_user_id, amount) VALUES
  (1, 1, 3, 1, 50.00),  -- Marta le hace un Bizum de 50 € a Ana
  (2, 2, 3, 2, 10.00);  -- Marta salda su parte con Luis antes de salir del piso


-- =====================================================================
-- CONSULTA DE COMPROBACIÓN: saldo de cada miembro por grupo
--   saldo = pagado − su parte + liquidaciones enviadas − recibidas
--   positivo: le deben · negativo: debe
-- Los saldos de cada grupo deben sumar exactamente 0.
-- =====================================================================
SELECT
  g.title     AS grupo,
  u.nickname  AS miembro,
  gm.status   AS estado,
    COALESCE((SELECT SUM(e.amount) FROM expenses e
              WHERE e.group_id = gm.group_id AND e.paid_by = gm.user_id), 0)
  - COALESCE((SELECT SUM(es.amount) FROM expense_shares es
              JOIN expenses e ON e.id = es.expense_id
              WHERE e.group_id = gm.group_id AND es.user_id = gm.user_id), 0)
  + COALESCE((SELECT SUM(s.amount) FROM settlements s
              WHERE s.group_id = gm.group_id AND s.from_user_id = gm.user_id), 0)
  - COALESCE((SELECT SUM(s.amount) FROM settlements s
              WHERE s.group_id = gm.group_id AND s.to_user_id = gm.user_id), 0)
    AS saldo
FROM group_members gm
JOIN users u          ON u.id = gm.user_id
JOIN expense_groups g ON g.id = gm.group_id
WHERE gm.status IN ('accepted', 'left')
ORDER BY gm.group_id, gm.user_id;
