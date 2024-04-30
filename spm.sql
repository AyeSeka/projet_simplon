CREATE DATABASE spm;

USE spm;

CREATE TABLE users(
    IdUser INT PRIMARY KEY IDENTITY(1,1),
    Email VARCHAR(30) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255),
    Roles VARCHAR(30) NOT NULL,
    path_PhotoProfil VARCHAR(255)
);

CREATE TABLE Admin (
    IdAdmin INT PRIMARY KEY IDENTITY(1,1),
    IdUser INT,  -- Ajout de la colonne IdUser pour la clé étrangère
    NomAdmin VARCHAR(30) NOT NULL,
    PrenomAdmin VARCHAR(55) NOT NULL,
    DateNaissance DATE,
    lieu_hab_rep VARCHAR(55),
    FOREIGN KEY(IdUser) REFERENCES users(IdUser)  -- Référence à la colonne IdUser dans la table users
);

CREATE TABLE Gestionnaire (
    IdGestionnaire INT PRIMARY KEY IDENTITY(1,1),
    IdUser INT,  -- Ajout de la colonne IdUser pour la clé étrangère
    NomGestionnaire VARCHAR(30) NOT NULL,
    PrenomGestionnaire VARCHAR(55) NOT NULL,
    DateNaissance DATE,
    lieu_hab_rep VARCHAR(55),
    FOREIGN KEY(IdUser) REFERENCES users(IdUser),  -- Référence à la colonne IdUser dans la table users
);

CREATE TABLE Vendeur (
    IdVendeur INT PRIMARY KEY IDENTITY(1,1),
    IdUser INT,  -- Ajout de la colonne IdUser pour la clé étrangère
    NomVendeur VARCHAR(30) NOT NULL,
    PrenomVendeur VARCHAR(55) NOT NULL,
    DateNaissance DATE,
    lieu_hab_rep VARCHAR(55),
    FOREIGN KEY(IdUser) REFERENCES users(IdUser),  -- Référence à la colonne IdUser dans la table users
);

CREATE TABLE Client (
    IdClient INT PRIMARY KEY IDENTITY(1,1),
    NomClient VARCHAR(85) NOT NULL,
    GenreClient VARCHAR(10) NOT NULL,
    TelephoneClient VARCHAR(20),
);

CREATE TABLE Categorie (
    IdCategorie INT PRIMARY KEY IDENTITY(1,1),
    NomCategorie VARCHAR(50) NOT NULL,
    DescriptionCategorie TEXT
);

CREATE TABLE Produit (
    IdProduit INT PRIMARY KEY IDENTITY(1,1),
    IdCategorie INT,
    NomProduit VARCHAR(50) NOT NULL,
    DescriptionProduit TEXT,
    Prix DECIMAL(10,2),
    Stock INT DEFAULT 0,
    FOREIGN KEY(IdCategorie) REFERENCES Categorie(IdCategorie)  -- Référence à la table Categorie
);

CREATE TABLE Vente (
    IdVente INT PRIMARY KEY IDENTITY(1,1),
    IdClient INT,
    IdProduit INT,
    Quantite INT,
    DateVente DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(IdProduit) REFERENCES Produit(IdProduit),  -- Référence à la table Produit
    FOREIGN KEY(IdClient) REFERENCES Client(IdClient)     -- Référence à la table Client
);
