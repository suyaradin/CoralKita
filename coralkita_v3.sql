-- ============================================================
--  CoralKita Database Schema
--  Database: coralkita_v3
-- ============================================================

CREATE DATABASE IF NOT EXISTS coralkita_v3;
USE coralkita_v3;

-- ------------------------------------------------------------
--  LOOKUP TABLES
-- ------------------------------------------------------------

CREATE TABLE Role (
    roleID   INT(11)      NOT NULL AUTO_INCREMENT,
    roleName VARCHAR(255) NOT NULL,
    CONSTRAINT Role_roleID_pk PRIMARY KEY (roleID)
);

CREATE TABLE Region (
    regionID   INT(11)      NOT NULL AUTO_INCREMENT,
    regionName VARCHAR(255) NOT NULL,
    latitude   DECIMAL(9,6) NOT NULL,
    longitude  DECIMAL(9,6) NOT NULL,
    CONSTRAINT Region_regionID_pk PRIMARY KEY (regionID)
);

CREATE TABLE GrowthForm (
    growthFormID   INT(11)      NOT NULL AUTO_INCREMENT,
    growthFormName VARCHAR(255) NOT NULL,
    CONSTRAINT GrowthForm_growthFormID_pk PRIMARY KEY (growthFormID)
);

CREATE TABLE HealthStatus (
    healthID   INT(11)      NOT NULL AUTO_INCREMENT,
    healthName VARCHAR(255) NOT NULL,
    CONSTRAINT HealthStatus_healthID_pk PRIMARY KEY (healthID)
);

CREATE TABLE IUCNStatus (
    iucnID   INT(11)      NOT NULL AUTO_INCREMENT,
    iucnName VARCHAR(255) NOT NULL,
    CONSTRAINT IUCNStatus_iucnID_pk PRIMARY KEY (iucnID)
);

-- ------------------------------------------------------------
--  USERS
-- ------------------------------------------------------------

CREATE TABLE Users (
    userID   INT(11)      NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    email    VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    roleID   INT(11)      NOT NULL,
    CONSTRAINT Users_userID_pk PRIMARY KEY (userID),
    CONSTRAINT Users_roleID_fk FOREIGN KEY (roleID) REFERENCES Role (roleID)
);

-- ------------------------------------------------------------
--  CORAL
-- ------------------------------------------------------------

CREATE TABLE Coral (
    coralID      INT(11)      NOT NULL AUTO_INCREMENT,
    genus        VARCHAR(255) NOT NULL,
    species      VARCHAR(255) NOT NULL,
    growthFormID INT(11)      NOT NULL,
    waterTempMin DECIMAL(5,2) NOT NULL,
    waterTempMax DECIMAL(5,2) NOT NULL,
    pHMin        DECIMAL(4,2) NOT NULL,
    pHMax        DECIMAL(4,2) NOT NULL,
    regionID     INT(11)      NOT NULL,
    submittedBy  INT(11)      NOT NULL,
    submittedAt  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT Coral_coralID_pk      PRIMARY KEY (coralID),
    CONSTRAINT Coral_growthFormID_fk FOREIGN KEY (growthFormID) REFERENCES GrowthForm (growthFormID),
    CONSTRAINT Coral_regionID_fk     FOREIGN KEY (regionID)     REFERENCES Region     (regionID),
    CONSTRAINT Coral_submittedBy_fk  FOREIGN KEY (submittedBy)  REFERENCES Users      (userID)
);

-- ------------------------------------------------------------
--  CORAL IMAGE
-- ------------------------------------------------------------

CREATE TABLE CoralImage (
    imageID    INT(11)      NOT NULL AUTO_INCREMENT,
    imagePath  VARCHAR(255) NOT NULL,
    uploadDate DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploadBy   INT(11)      NOT NULL,
    coralID    INT(11)      NOT NULL,
    CONSTRAINT CoralImage_imageID_pk  PRIMARY KEY (imageID),
    CONSTRAINT CoralImage_uploadBy_fk FOREIGN KEY (uploadBy) REFERENCES Users (userID),
    CONSTRAINT CoralImage_coralID_fk  FOREIGN KEY (coralID)  REFERENCES Coral (coralID)
);

-- ------------------------------------------------------------
--  CLASSIFICATION
-- ------------------------------------------------------------

CREATE TABLE Classification (
    classID         INT(11)      NOT NULL AUTO_INCREMENT,
    imageID         INT(11)      NOT NULL,
    healthID        INT(11)      NOT NULL,
    confidenceScore DECIMAL(5,4) NOT NULL,
    CONSTRAINT Classification_classID_pk  PRIMARY KEY (classID),
    CONSTRAINT Classification_imageID_fk  FOREIGN KEY (imageID)  REFERENCES CoralImage   (imageID),
    CONSTRAINT Classification_healthID_fk FOREIGN KEY (healthID) REFERENCES HealthStatus (healthID)
);

-- ------------------------------------------------------------
--  REVIEW
-- ------------------------------------------------------------

CREATE TABLE Review (
    reviewID        INT(11)      NOT NULL AUTO_INCREMENT,
    classID         INT(11)      NOT NULL,
    iucnID          INT(11)      NULL,
    reviewStatus    ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    rejectionReason VARCHAR(500) NULL,
    reviewedBy      INT(11)      NULL,
    reviewedAt      DATETIME     NULL,
    updatedAt       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                          ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT Review_reviewID_pk   PRIMARY KEY (reviewID),
    CONSTRAINT Review_classID_fk    FOREIGN KEY (classID)    REFERENCES Classification (classID),
    CONSTRAINT Review_iucnID_fk     FOREIGN KEY (iucnID)     REFERENCES IUCNStatus     (iucnID),
    CONSTRAINT Review_reviewedBy_fk FOREIGN KEY (reviewedBy) REFERENCES Users          (userID)
);

-- ------------------------------------------------------------
--  SST READING
-- ------------------------------------------------------------

CREATE TABLE SSTReading (
    sstID      INT(11)      NOT NULL AUTO_INCREMENT,
    regionID   INT(11)      NOT NULL,
    sstValue   DECIMAL(5,2) NOT NULL,
    recordedAt DATETIME     NOT NULL,
    CONSTRAINT SSTReading_sstID_pk    PRIMARY KEY (sstID),
    CONSTRAINT SSTReading_regionID_fk FOREIGN KEY (regionID) REFERENCES Region (regionID)
);

-- ------------------------------------------------------------
--  SST ALERT
-- ------------------------------------------------------------

CREATE TABLE SSTAlert (
    alertID    INT(11)      NOT NULL AUTO_INCREMENT,
    regionID   INT(11)      NOT NULL,
    alertLevel VARCHAR(50)  NOT NULL,
    sentAt     DATETIME     NOT NULL,
    CONSTRAINT SSTAlert_alertID_pk  PRIMARY KEY (alertID),
    CONSTRAINT SSTAlert_regionID_fk FOREIGN KEY (regionID) REFERENCES Region (regionID)
);