-- seed_dev.sql — dados de desenvolvimento
-- Execute: docker compose exec postgres psql -U piscinao -d piscinao_db -f /scripts/seed_dev.sql

-- Usuário admin (senha: Admin@123 — troque em produção)
INSERT INTO usuario (nome, email, senha_hash, role)
VALUES (
    'Administrador',
    'admin@piscinao.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUxzAlWq0nDRxD7.N7dQmGCYK',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Reservatórios
INSERT INTO reservatorio (nome, codigo, capacidade_m3, latitude, longitude, descricao) VALUES
('Piscinão do Aricanduva',   'RES-ARI', 1500000, -23.553280, -46.509640, 'Reservatório de detenção na Bacia do Aricanduva'),
('Piscinão do Cabuçu',       'RES-CAB',  250000, -23.521680, -46.625300, 'Reservatório no córrego Cabuçu de Cima'),
('Piscinão do Mirandópolis', 'RES-MIR',   80000, -23.598120, -46.622540, 'Reservatório no Córrego do Mirandópolis'),
('Piscinão do Taboão',       'RES-TAB',  310000, -23.615390, -46.760180, 'Reservatório na bacia do Rio Taboão')
ON CONFLICT (codigo) DO NOTHING;

-- Sensores
INSERT INTO sensor (reservatorio_id, codigo, tipo, unidade, descricao) VALUES
((SELECT id FROM reservatorio WHERE codigo = 'RES-ARI'), 'SEN-ARI-N01', 'nivel', 'cm',   'Sensor de nível principal'),
((SELECT id FROM reservatorio WHERE codigo = 'RES-ARI'), 'SEN-ARI-C01', 'chuva', 'mm',   'Pluviômetro entrada norte'),
((SELECT id FROM reservatorio WHERE codigo = 'RES-CAB'), 'SEN-CAB-N01', 'nivel', 'cm',   'Sensor de nível principal'),
((SELECT id FROM reservatorio WHERE codigo = 'RES-CAB'), 'SEN-CAB-V01', 'vazao', 'm3/s', 'Sensor de vazão saída'),
((SELECT id FROM reservatorio WHERE codigo = 'RES-MIR'), 'SEN-MIR-N01', 'nivel', 'cm',   'Sensor de nível principal'),
((SELECT id FROM reservatorio WHERE codigo = 'RES-TAB'), 'SEN-TAB-N01', 'nivel', 'cm',   'Sensor de nível principal')
ON CONFLICT (codigo) DO NOTHING;

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

