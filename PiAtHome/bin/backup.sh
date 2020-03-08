#!/usr/bin/env bash

BACKUP_FOLDER=/var/backup_piathome
PIATHOME_DATA=/opt/piathome/data
GRAPHITE_DATA=/var/lib/graphite/whisper/servers

if [ ! -d "$BACKUP_FOLDER" ]; then
  mkdir $BACKUP_FOLDER
fi

TODAY=`date +%Y%m%d_%H%M%S`
ARCHIVE_DATA=piathome_data_$TODAY.tar.gz
ARCHIVE_GRAPHITE=piathome_graphite_$TODAY.tar.gz

echo ---- Start $TODAY
#Create archives in backup folder
tar czvf $BACKUP_FOLDER/$ARCHIVE_DATA $PIATHOME_DATA
tar czvf $BACKUP_FOLDER/$ARCHIVE_GRAPHITE $GRAPHITE_DATA

echo Archives done ...

#Clean backup folder
last_month=`date +%Y%m --date='-2 month'`
rm -f $BACKUP_FOLDER/$last_month*

echo Clean up done
echo -- End $TODAY


