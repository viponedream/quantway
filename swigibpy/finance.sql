-- stock_data_1hour
CREATE TABLE `stock_data_1hour` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
    `symbol` varchar(32) NOT NULL DEFAULT '' COMMENT '股票代码',
    `sdate` varchar(64) NOT NULL DEFAULT '' COMMENT '股票开始时间',
    `open` double unsigned NOT NULL DEFAULT '0' COMMENT '开盘价格',
    `high` double unsigned NOT NULL DEFAULT '0' COMMENT '最高价格',
    `low` double unsigned NOT NULL DEFAULT '0' COMMENT '最低价格',
    `close` double unsigned NOT NULL DEFAULT '0' COMMENT '收盘价格',
    `volume` bigint unsigned NOT NULL DEFAULT '0' COMMENT '成交量',
    `barcount` int unsigned NOT NULL DEFAULT '0' COMMENT 'The Bar Count',
    `wap` double unsigned NOT NULL DEFAULT '0' COMMENT '平均价格',
    `hasgaps` int unsigned NOT NULL DEFAULT '0' COMMENT 'Has Gaps',
    `ctime` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `index_symbol_sdata` (`symbol`,`sdate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='股票数据一小时';
