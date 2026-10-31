-- Run against the NEW database created in the SmarterASP control panel (SSMS).
-- No database creation, destructive migration, sample users or sample events.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF OBJECT_ID(N'dbo.AgroUsers',N'U') IS NULL
 CREATE TABLE dbo.AgroUsers(Uid nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL PRIMARY KEY, CreatedAt datetimeoffset(3) NOT NULL DEFAULT SYSUTCDATETIME());
IF OBJECT_ID(N'dbo.AgroDevices',N'U') IS NULL BEGIN
 CREATE TABLE dbo.AgroDevices(Id uniqueidentifier NOT NULL PRIMARY KEY, OwnerUid nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL REFERENCES dbo.AgroUsers(Uid), Name nvarchar(120) NOT NULL, TokenHash binary(32) NOT NULL UNIQUE, Type nvarchar(80) NOT NULL DEFAULT 'Laptop camera', Online bit NOT NULL DEFAULT 0, LastSeen datetimeoffset(3) NULL, Source nvarchar(200) NULL, Models nvarchar(1000) NOT NULL DEFAULT '[]', Revoked bit NOT NULL DEFAULT 0, CreatedAt datetimeoffset(3) NOT NULL DEFAULT SYSUTCDATETIME());
 CREATE INDEX IX_AgroDevices_Owner ON dbo.AgroDevices(OwnerUid,Revoked);
END;
IF OBJECT_ID(N'dbo.AgroPairings',N'U') IS NULL BEGIN
 CREATE TABLE dbo.AgroPairings(Id uniqueidentifier NOT NULL PRIMARY KEY, CodeHash binary(32) NOT NULL UNIQUE, TokenHash binary(32) NOT NULL UNIQUE, Name nvarchar(120) NOT NULL, ExpiresAt datetimeoffset(3) NOT NULL, DeviceId uniqueidentifier NULL REFERENCES dbo.AgroDevices(Id));
 CREATE INDEX IX_AgroPairings_Expiry ON dbo.AgroPairings(ExpiresAt);
END;
IF OBJECT_ID(N'dbo.AgroEvents',N'U') IS NULL BEGIN
 CREATE TABLE dbo.AgroEvents(Id uniqueidentifier NOT NULL PRIMARY KEY, DeviceId uniqueidentifier NOT NULL REFERENCES dbo.AgroDevices(Id), AnomalyType varchar(12) NOT NULL CHECK(AnomalyType IN ('fire','smoke','disease')), Confidence float NOT NULL CHECK(Confidence>=0 AND Confidence<=1), CapturedAt datetimeoffset(3) NOT NULL, ReceivedAt datetimeoffset(3) NOT NULL DEFAULT SYSUTCDATETIME(), Metadata nvarchar(max) NOT NULL CHECK(ISJSON(Metadata)=1), EvidenceKey nvarchar(240) NOT NULL, ImageHash char(64) NOT NULL, PayloadHash char(64) NOT NULL, DeletedAt datetimeoffset(3) NULL);
 CREATE INDEX IX_AgroEvents_Recent ON dbo.AgroEvents(ReceivedAt DESC,Id) INCLUDE(DeviceId,DeletedAt);
END;
IF OBJECT_ID(N'dbo.AgroSchemaVersion',N'U') IS NULL BEGIN
 CREATE TABLE dbo.AgroSchemaVersion(Version int NOT NULL PRIMARY KEY, AppliedAt datetimeoffset(3) NOT NULL DEFAULT SYSUTCDATETIME());
 INSERT dbo.AgroSchemaVersion(Version) VALUES(1);
END;
COMMIT;
