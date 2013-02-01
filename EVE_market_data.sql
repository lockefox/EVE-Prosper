--TABLE: contains raw output from central_dumpcrunch.py
CREATE TABLE IF NOT EXISTS rawPrice
(itemID INTEGER NOT NULL, 
order_date date NOT NULL,
regionID INTEGER NOT NULL,
systemID INTEGER NOT NULL,
order_type VARCHAR(20) NOT NULL,
price_max DECIMAL(12,2) NULL,
price_min DECIMAL (12,2) NULL,
price_avg DECIMAL (12,2) NULL,
price_stdev DECIMAL (8,4) NULL,
other DECIMAL (12,2) NULL
PRIMARY KEY (order_date)
)

--TABLE: contains cleaned and normalized values for ALL prices in EVEonline
CREATE TABLE IF NOT EXISTS cleanPrice
(itemID INTEGER NOT NULL, 
order_date date NOT NULL,
regionID INTEGER NOT NULL,
systemID INTEGER NOT NULL,
order_type VARCHAR(20) NOT NULL,
price_max DECIMAL(12,2) NULL,
price_min DECIMAL (12,2) NULL,
price_avg DECIMAL (12,2) NULL,
price_stdev DECIMAL (8,4) NULL,
other DECIMAL (12,2) NULL
PRIMARY KEY (order_date)
)