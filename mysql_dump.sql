-- MySQL dump 10.13  Distrib 5.7.23, for Linux (x86_64)
--
-- Host: localhost    Database: dsa_db
-- ------------------------------------------------------
-- Server version	5.7.23-0ubuntu0.16.04.1

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
-- Table structure for table `errors`
--

DROP TABLE IF EXISTS `errors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `errors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `text_word` int(11) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `transcription` int(11) NOT NULL,
  `err_w` int(11) DEFAULT NULL,
  `time` double DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `autocorrection` tinyint(1) DEFAULT NULL,
  `checked` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `word` (`text_word`),
  KEY `fk_trans` (`transcription`),
  KEY `err_w` (`err_w`),
  CONSTRAINT `errors_ibfk_1` FOREIGN KEY (`text_word`) REFERENCES `text_words` (`id`),
  CONSTRAINT `errors_ibfk_2` FOREIGN KEY (`err_w`) REFERENCES `words` (`id`),
  CONSTRAINT `fk_trans` FOREIGN KEY (`transcription`) REFERENCES `transcriptions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patients`
--

DROP TABLE IF EXISTS `patients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `patients` (
  `cf` varchar(16) NOT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) NOT NULL,
  `birthday` date NOT NULL,
  `gender` varchar(1) DEFAULT NULL,
  PRIMARY KEY (`cf`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sim_words`
--

DROP TABLE IF EXISTS `sim_words`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sim_words` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `word1` int(11) DEFAULT NULL,
  `word2` int(11) DEFAULT NULL,
  `ratio` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `word1` (`word1`),
  KEY `word2` (`word2`),
  CONSTRAINT `sim_words_ibfk_1` FOREIGN KEY (`word1`) REFERENCES `words` (`id`),
  CONSTRAINT `sim_words_ibfk_2` FOREIGN KEY (`word2`) REFERENCES `words` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `spoken_words`
--

DROP TABLE IF EXISTS `spoken_words`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `spoken_words` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `text_word` int(11) DEFAULT NULL,
  `transcription` int(11) DEFAULT NULL,
  `pos` int(11) DEFAULT NULL,
  `time` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `text_word` (`text_word`),
  KEY `transcription` (`transcription`),
  CONSTRAINT `spoken_words_ibfk_1` FOREIGN KEY (`text_word`) REFERENCES `text_words` (`id`),
  CONSTRAINT `spoken_words_ibfk_2` FOREIGN KEY (`transcription`) REFERENCES `transcriptions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `text_words`
--

DROP TABLE IF EXISTS `text_words`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `text_words` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `word` int(11) DEFAULT NULL,
  `position` int(11) NOT NULL,
  `text` int(11) NOT NULL,
  `row` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_text` (`text`),
  KEY `word` (`word`),
  CONSTRAINT `fk_text` FOREIGN KEY (`text`) REFERENCES `texts` (`id`),
  CONSTRAINT `text_words_ibfk_1` FOREIGN KEY (`word`) REFERENCES `words` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `texts`
--

DROP TABLE IF EXISTS `texts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `texts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(50) DEFAULT NULL,
  `font` varchar(30) DEFAULT NULL,
  `body` text NOT NULL,
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `class` varchar(20) DEFAULT NULL,
  `period` varchar(20) DEFAULT NULL,
  `outdated` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transcriptions`
--

DROP TABLE IF EXISTS `transcriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transcriptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `supervisor_id` int(11) DEFAULT NULL,
  `patient_id` varchar(16) DEFAULT NULL,
  `text_id` int(11) DEFAULT NULL,
  `filename` varchar(100) NOT NULL,
  `body` text NOT NULL,
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `supervisor_id` (`supervisor_id`),
  KEY `patient_id` (`patient_id`),
  KEY `textTranscription` (`text_id`),
  CONSTRAINT `textTranscription` FOREIGN KEY (`text_id`) REFERENCES `texts` (`id`),
  CONSTRAINT `transcriptions_ibfk_1` FOREIGN KEY (`supervisor_id`) REFERENCES `users` (`id`),
  CONSTRAINT `transcriptions_ibfk_2` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`cf`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `username` varchar(30) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  `register_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `words`
--

DROP TABLE IF EXISTS `words`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `words` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `word` varchar(30) DEFAULT NULL,
  `type` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-08-05 23:26:09
