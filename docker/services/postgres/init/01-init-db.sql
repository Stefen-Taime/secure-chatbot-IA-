-- Création des tables pour les clients
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    adresse TEXT,
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    numero_securite_sociale VARCHAR(20) UNIQUE NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création des tables pour les contrats d'assurance
CREATE TABLE contrats (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    numero_contrat VARCHAR(20) UNIQUE NOT NULL,
    type_contrat VARCHAR(50) NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE,
    montant_cotisation DECIMAL(10, 2) NOT NULL,
    niveau_couverture VARCHAR(20) NOT NULL,
    statut VARCHAR(20) NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création des tables pour les réclamations
CREATE TABLE reclamations (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    contrat_id INTEGER REFERENCES contrats(id),
    numero_reclamation VARCHAR(20) UNIQUE NOT NULL,
    date_reclamation DATE NOT NULL,
    type_reclamation VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    montant_demande DECIMAL(10, 2),
    statut VARCHAR(20) NOT NULL,
    date_traitement DATE,
    agent_traitement VARCHAR(100),
    commentaires TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création des tables pour les documents
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    contrat_id INTEGER REFERENCES contrats(id),
    reclamation_id INTEGER REFERENCES reclamations(id),
    nom_fichier VARCHAR(255) NOT NULL,
    type_document VARCHAR(50) NOT NULL,
    chemin_stockage TEXT NOT NULL,
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    taille_fichier INTEGER NOT NULL
);

-- Création des tables pour les tickets de support
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    numero_ticket VARCHAR(20) UNIQUE NOT NULL,
    sujet VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priorite VARCHAR(20) NOT NULL,
    statut VARCHAR(20) NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_resolution TIMESTAMP,
    agent_assignation VARCHAR(100),
    canal_communication VARCHAR(50) NOT NULL
);

-- Création des tables pour les communications
CREATE TABLE communications (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    client_id INTEGER REFERENCES clients(id),
    type_communication VARCHAR(50) NOT NULL,
    contenu TEXT NOT NULL,
    date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expediteur VARCHAR(100) NOT NULL,
    destinataire VARCHAR(100) NOT NULL
);

-- Création des tables pour les logs d'audit
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    utilisateur VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entite_affectee VARCHAR(50) NOT NULL,
    identifiant_entite INTEGER NOT NULL,
    details TEXT,
    adresse_ip VARCHAR(45) NOT NULL,
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertion de quelques données de test pour les clients
INSERT INTO clients (nom, prenom, date_naissance, email, telephone, adresse, code_postal, ville, numero_securite_sociale)
VALUES 
('Dubois', 'Marie', '1985-04-12', 'marie.dubois@example.com', '0612345678', '15 rue des Lilas', '75001', 'Paris', '185047512345678'),
('Martin', 'Jean', '1972-09-23', 'jean.martin@example.com', '0698765432', '8 avenue Victor Hugo', '69002', 'Lyon', '172097612345678'),
('Bernard', 'Sophie', '1990-11-05', 'sophie.bernard@example.com', '0723456789', '42 boulevard Gambetta', '33000', 'Bordeaux', '290115712345678');

-- Insertion de quelques données de test pour les contrats
INSERT INTO contrats (client_id, numero_contrat, type_contrat, date_debut, date_fin, montant_cotisation, niveau_couverture, statut)
VALUES 
(1, 'CONT-2023-001', 'Santé Individuelle', '2023-01-01', '2024-01-01', 120.50, 'Premium', 'Actif'),
(1, 'CONT-2023-002', 'Prévoyance', '2023-01-01', '2024-01-01', 45.75, 'Standard', 'Actif'),
(2, 'CONT-2023-003', 'Santé Famille', '2023-03-15', '2024-03-15', 210.00, 'Premium', 'Actif'),
(3, 'CONT-2023-004', 'Santé Individuelle', '2023-05-10', '2024-05-10', 95.25, 'Économique', 'Actif');

-- Insertion de quelques données de test pour les réclamations
INSERT INTO reclamations (client_id, contrat_id, numero_reclamation, date_reclamation, type_reclamation, description, montant_demande, statut, date_traitement, agent_traitement)
VALUES 
(1, 1, 'REC-2023-001', '2023-04-15', 'Remboursement', 'Consultation spécialiste non remboursée', 75.00, 'Traitée', '2023-04-20', 'Jean Dupont'),
(2, 3, 'REC-2023-002', '2023-06-10', 'Contestation', 'Montant remboursé inférieur au contrat', 120.50, 'En cours', NULL, 'Marie Martin'),
(3, 4, 'REC-2023-003', '2023-07-05', 'Information', 'Demande de détail sur les garanties', NULL, 'Traitée', '2023-07-06', 'Philippe Dubois');

-- Insertion de quelques données de test pour les tickets
INSERT INTO tickets (client_id, numero_ticket, sujet, description, priorite, statut, agent_assignation, canal_communication)
VALUES 
(1, 'TIC-2023-001', 'Problème de connexion', 'Impossible de se connecter à l''espace client', 'Haute', 'Résolu', 'Jean Dupont', 'Email'),
(2, 'TIC-2023-002', 'Question sur remboursement', 'Délai de remboursement trop long', 'Moyenne', 'En cours', 'Marie Martin', 'Téléphone'),
(3, 'TIC-2023-003', 'Modification coordonnées', 'Changement d''adresse et téléphone', 'Basse', 'Nouveau', NULL, 'Formulaire web');


-- Create keycloak user and database
CREATE USER keycloak WITH PASSWORD 'keycloak_password_123';
CREATE DATABASE keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;