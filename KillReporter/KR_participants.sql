DROP TABLE IF EXISTS `KR_participants`;
CREATE TABLE `KR_participants` (
	`killID` int(32) NOT NULL,
	`solarSystemID` int(16) NOT NULL,
	`kill_time` datetime NOT NULL,
	`isVictim` tinyint(1) NOT NULL,
	`shipTypeID` int(8) NOT NULL,
	`damage` int(8) NOT NULL,
	`characterID` int(16) NOT NULL,
	`characterName` tinytext NOT NULL,
	`corporationID` int(16) NOT NULL,
	`corporationName` tinytext NOT NULL,
	`allianceID` int(16) DEFAULT NULL,
	`allianceName` tinytext DEFAULT NULL,
	`factionID` int(16) DEFAULT NULL,
	`factionName` tinytext DEFAULT NULL,
	`finalBlow` tinyint(1) DEFAULT NULL,
	`weaponTypeID` int(8) DEFAULT NULL,
	`points` int(8) DEFAULT NULL,
	`totalValue` decimal(13,2) DEFAULT NULL,
	-- `fit_json` mediumtext DEFAULT NULL,
	PRIMARY KEY(killID,characterID))
ENGINE=InnoDB DEFAULT CHARSET=latin1