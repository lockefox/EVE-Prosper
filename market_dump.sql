CREATE DATABASE  IF NOT EXISTS `eve_marketdata` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `eve_marketdata`;
-- MySQL dump 10.13  Distrib 5.5.16, for Win32 (x86)
--
-- Host: localhost    Database: eve_marketdata
-- ------------------------------------------------------
-- Server version	5.5.25a

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `rawdata`
--

DROP TABLE IF EXISTS `rawdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rawdata` (
  `itemid` int(8) NOT NULL,
  `order_date` date NOT NULL,
  `regionID` int(8) NOT NULL,
  `systemID` int(8) NOT NULL,
  `order_type` varchar(20) NOT NULL,
  `price_max` decimal(12,2) DEFAULT '0.00',
  `price_min` decimal(12,2) DEFAULT '0.00',
  `price_avg` decimal(12,2) DEFAULT '0.00',
  `price_stdev` decimal(8,4) DEFAULT '0.0000',
  `other` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`itemid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Takes raw output from central_dumpcrunch.py.  Will clean up ';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rawdata`
--

LOCK TABLES `rawdata` WRITE;
/*!40000 ALTER TABLE `rawdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `rawdata` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-02-02 16:13:34
