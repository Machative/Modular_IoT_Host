#!/bin/bash
mosquitto_sub -h datalog.local -p 1883 -t "7021132a03a8/data" | while read -r line
do
    echo "$(date + '%Y-%m-%d %H:%M:%S'),$line" >> C:\Users\Aidan\Documents\Modular_IoT\Host/res/7021132a03a8_log.csv
done
