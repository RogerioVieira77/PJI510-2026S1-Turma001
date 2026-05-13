-- seed_dev.sql — dados de desenvolvimento — Alerta Romano / Piscinão Romano
-- Execute: docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} \
--          -f /docker-entrypoint-initdb.d/seed_dev.sql
--
-- IDEMPOTENTE: usa ON CONFLICT DO NOTHING em todas as inserções.
-- Requer migration 0005_piscinao_romano.py já aplicada (alembic upgrade head).

-- Usuário admin (senha: Admin@123 — altere antes de usar em staging)
INSERT INTO usuario (nome, email, senha_hash, role, ativo)
VALUES (
    'Administrador',
    'admin@unicomunitaria.com.br',
    '$2b$12$92RJg1rD/Im7QuW9fpq5i.6NPLSJrRSmcArZLdtsBLiUAYZvSW8ui',
    'admin',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Usuário operador (senha: Admin@123 — altere antes de usar em staging)
INSERT INTO usuario (nome, email, senha_hash, role, ativo)
VALUES (
    'Técnico',
    'tecnico@unicomunitaria.com.br',
    '$2b$12$92RJg1rD/Im7QuW9fpq5i.6NPLSJrRSmcArZLdtsBLiUAYZvSW8ui',
    'operador',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Reservatório (inserido pela migration 0005 — ON CONFLICT para idempotência)
INSERT INTO reservatorio (nome, codigo, capacidade_m3, latitude, longitude, descricao)
VALUES (
    'Piscinão Romano',
    'RES-ROMANO',
    20000.00,
    -23.4778200,
    -46.3829000,
    'Reservatório de detenção de cheias do Jardim Romano — operado pela PMSP/SIURB'
) ON CONFLICT (codigo) DO NOTHING;

-- Sensores (inseridos pela migration 0005 — ON CONFLICT para idempotência)
INSERT INTO sensor (reservatorio_id, codigo, tipo, unidade, descricao, ativo, latitude, longitude)
SELECT r.id, s.codigo, s.tipo::tipo_sensor_enum, s.unidade, s.descricao, TRUE, s.lat, s.lng
FROM (SELECT id FROM reservatorio WHERE codigo = 'RES-ROMANO') r,
(VALUES
    ('SENSOR-RES-001-nivel_agua',        'nivel_agua',       'm',
     'Sensor de nível — Piscinão Romano Norte',          -23.4774480, -46.3828150),
    ('SENSOR-RES-002-nivel_agua',        'nivel_agua',       'm',
     'Sensor de nível — Piscinão Romano Sul',            -23.4775090, -46.3829760),
    ('ESTACAO-MET-001-temperatura',      'temperatura',      '°C',
     'Temperatura do ar — Estação CEU Três Pontes',      -23.4788700, -46.3812500),
    ('ESTACAO-MET-001-pluviometro',      'pluviometro',      'mm',
     'Chuva acumulada — Estação CEU Três Pontes',        -23.4788700, -46.3812500),
    ('ESTACAO-MET-001-umidade',          'umidade',          '%',
     'Umidade relativa — Estação CEU Três Pontes',       -23.4788700, -46.3812500),
    ('ESTACAO-MET-001-pressao',          'pressao',          'hPa',
     'Pressão atmosférica — Estação CEU Três Pontes',    -23.4788700, -46.3812500),
    ('ESTACAO-MET-001-vento_velocidade', 'vento_velocidade', 'km/h',
     'Velocidade do vento — Estação CEU Três Pontes',    -23.4788700, -46.3812500),
    ('ESTACAO-MET-001-vento_direcao',    'vento_direcao',    'graus',
     'Direção do vento — Estação CEU Três Pontes',       -23.4788700, -46.3812500),
    ('ESTACAO-MET-002-temperatura',      'temperatura',      '°C',
     'Temperatura do ar — Estação Piscinão Romano',      -23.4774720, -46.3829240),
    ('ESTACAO-MET-002-pluviometro',      'pluviometro',      'mm',
     'Chuva acumulada — Estação Piscinão Romano',        -23.4774720, -46.3829240),
    ('ESTACAO-MET-002-umidade',          'umidade',          '%',
     'Umidade relativa — Estação Piscinão Romano',       -23.4774720, -46.3829240),
    ('ESTACAO-MET-002-pressao',          'pressao',          'hPa',
     'Pressão atmosférica — Estação Piscinão Romano',    -23.4774720, -46.3829240),
    ('ESTACAO-MET-002-vento_velocidade', 'vento_velocidade', 'km/h',
     'Velocidade do vento — Estação Piscinão Romano',    -23.4774720, -46.3829240),
    ('ESTACAO-MET-002-vento_direcao',    'vento_direcao',    'graus',
     'Direção do vento — Estação Piscinão Romano',       -23.4774720, -46.3829240)
) AS s(codigo, tipo, unidade, descricao, lat, lng)
ON CONFLICT (codigo) DO NOTHING;

-- Leituras simuladas para sensores de nível (últimas 6 horas, 1 por hora)
INSERT INTO leitura_sensor (sensor_id, timestamp, valor, nivel_percentual)
SELECT
    s.id,
    now() - (i || ' hours')::interval,
    -- Nível simulado entre 0.5m e 1.2m (50cm a 120cm)
    round((0.5 + random() * 0.7)::numeric, 3),
    NULL
FROM
    sensor s,
    generate_series(1, 6) AS i
WHERE
    s.codigo IN ('SENSOR-RES-001-nivel_agua', 'SENSOR-RES-002-nivel_agua')
ON CONFLICT DO NOTHING;


-- 500 leituras históricas simuladas (últimas 48h) para SEN-ARI-N01 (sensor_id=1)
INSERT INTO leitura_sensor (sensor_id, timestamp, valor, nivel_percentual)
SELECT
    (SELECT id FROM sensor WHERE codigo = 'SEN-ARI-N01'),
    NOW() - (gs * INTERVAL '5 minutes 45 seconds'),
    -- nível oscilando entre 200 e 900 cm com ruído
    ROUND((550 + 350 * SIN(gs::float / 50) + (RANDOM() * 60 - 30))::numeric, 3),
    -- percentual baseado em capacidade_m3=1500000, seção=250000 m²
    ROUND(((550 + 350 * SIN(gs::float / 50) + (RANDOM() * 60 - 30)) / 1200.0 * 100)::numeric, 2)
FROM generate_series(1, 500) AS gs;

