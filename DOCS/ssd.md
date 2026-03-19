##  проверка/подготовка дисков
1. sudo apt install nvme-cli smartmontools lshw pciutils hdparm fio
2. nvme list
   1. /dev/ng1n1  #  PHLF730100NN1P0GGN   INTEL SSDPE2KX010T7                      0x1          1.00  TB /   1.00  TB    512   B +  0 B   QDV10170
   2. /dev/ng0n1  #  P320PDBB250718003134 Patriot M.2 P320 256GB                   0x1        256.06  GB / 256.06  GB    512   B +  0 B   GT29c363
3. nvme id-ctrl /dev/ng1n1  # общая информация
4. nvme id-ns /dev/ng1n1  # информация о пространстве имен
5. nvme smart-log /dev/ng1n1  # smart
6. smartctl -a /dev/ng1n1  # smart ext
7. lspci -vvv -s $(lspci | grep "Non-Volatile memory controller" | head -1 | cut -d' ' -f1)  # скорость соедиения
8. watch -n 1 sudo nvme smart-log /dev/ng1n1

## форматирование диска
