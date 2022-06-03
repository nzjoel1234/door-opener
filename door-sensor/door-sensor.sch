EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Transistor_BJT:BC547 Q?
U 1 1 62837159
P 3650 2950
F 0 "Q?" H 3841 2996 50  0000 L CNN
F 1 "BC547" H 3841 2905 50  0000 L CNN
F 2 "Package_TO_SOT_THT:TO-92_Inline" H 3850 2875 50  0001 L CIN
F 3 "http://www.fairchildsemi.com/ds/BC/BC547.pdf" H 3650 2950 50  0001 L CNN
	1    3650 2950
	1    0    0    -1  
$EndComp
$Comp
L Device:Battery 5V
U 1 1 62837C6E
P 1550 2950
F 0 "5V" H 1658 2996 50  0000 L CNN
F 1 "Battery" H 1658 2905 50  0000 L CNN
F 2 "" V 1550 3010 50  0001 C CNN
F 3 "~" V 1550 3010 50  0001 C CNN
	1    1550 2950
	1    0    0    -1  
$EndComp
$Comp
L Device:LED D?
U 1 1 62839F0E
P 3750 3950
F 0 "D?" V 3789 3833 50  0000 R CNN
F 1 "LED" V 3698 3833 50  0000 R CNN
F 2 "" H 3750 3950 50  0001 C CNN
F 3 "~" H 3750 3950 50  0001 C CNN
	1    3750 3950
	0    -1   -1   0   
$EndComp
$Comp
L Device:R_US R?
U 1 1 6283AD29
P 3750 3550
F 0 "R?" H 3818 3596 50  0000 L CNN
F 1 "330R" H 3818 3505 50  0000 L CNN
F 2 "" V 3790 3540 50  0001 C CNN
F 3 "~" H 3750 3550 50  0001 C CNN
	1    3750 3550
	1    0    0    -1  
$EndComp
$Comp
L Sensor_Magnetic:SM351LT U?
U 1 1 6283BD64
P 2750 2950
F 0 "U?" H 2420 2996 50  0000 R CNN
F 1 "SM351LT" H 2420 2905 50  0000 R CNN
F 2 "Package_TO_SOT_SMD:SOT-23" H 2700 2950 50  0001 C CNN
F 3 "https://sensing.honeywell.com/honeywell-sensing-nanopower-series-product-sheet-50095501-a-en.pdf" H 2700 2950 50  0001 C CNN
	1    2750 2950
	1    0    0    -1  
$EndComp
Wire Wire Line
	1550 3150 1550 4400
Wire Wire Line
	1550 4400 2550 4400
Wire Wire Line
	3750 4400 3750 4100
Wire Wire Line
	2550 3250 2550 4400
Connection ~ 2550 4400
Wire Wire Line
	2550 4400 3750 4400
Wire Wire Line
	1550 2750 1550 1800
Wire Wire Line
	1550 1800 2550 1800
Wire Wire Line
	2550 1800 2550 2650
Wire Wire Line
	2550 1800 3350 1800
Wire Wire Line
	3750 1800 3750 2750
Connection ~ 2550 1800
Wire Wire Line
	3750 3150 3750 3400
Wire Wire Line
	3750 3700 3750 3800
Wire Wire Line
	3150 2950 3350 2950
$Comp
L Device:R_US R?
U 1 1 62840847
P 3350 2250
F 0 "R?" H 3418 2296 50  0000 L CNN
F 1 "270R" H 3418 2205 50  0000 L CNN
F 2 "" V 3390 2240 50  0001 C CNN
F 3 "~" H 3350 2250 50  0001 C CNN
	1    3350 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	3350 2100 3350 1800
Connection ~ 3350 1800
Wire Wire Line
	3350 1800 3750 1800
Wire Wire Line
	3350 2400 3350 2950
Connection ~ 3350 2950
Wire Wire Line
	3350 2950 3450 2950
$EndSCHEMATC
