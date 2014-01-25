SELECT kills.characterID,
	SUM(IF(kills.isVictim=1,1,0)) as `losses`,
	SUM(IF(kills.isVictim=0,1,0)) as `kills`,
	MAX(kills.kill_time) as `latestActivity`
FROM kill_participants kills
JOIN invTypes typ on (kills.shipTypeID = typ.typeID)
JOIN invGroups grp on (typ.groupID = grp.groupID)
WHERE grp.categoryID <> 350001
AND ((TIME(kills.kill_time) > '01:00' AND TIME(kills.kill_time) < '05:00')
	OR (WEEKDAY(kills.kill_time) = 5 AND (TIME(kills.kill_time) > '18:00'))
	OR (WEEKDAY(kills.kill_time) = 6 AND (TIME(kills.kill_time) < '05:00'
		AND TIME(kills.kill_time) > '18:00'))
	OR (WEEKDAY(kills.kill_time) = 0 AND (TIME(kills.kill_time) < '05:00')))
AND kills.corporationID = 1000181
AND kills.kill_time > NOW() - INTERVAL 30 DAY
GROUP BY kills.characterID
HAVING (losses + kills) > 5
AND latestActivity > NOW() - INTERVAL 14 DAY
ORDER BY losses DESC 