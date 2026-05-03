# 1. Активируем LVM тома (они могут быть не активны)
sudo vgchange -ay

# 2. Посмотрим, какие LVM тома видны
sudo lvs

# 3. Создадим точку монтирования
sudo mkdir -p /mnt/restore

# 4. Смонтируем корневой том (root)
sudo mount /dev/debby13-vg/root /mnt/restore

# 5. Проверим, что осталось в корне
ls -la /mnt/restore/

# 6. Проверим /bin, /lib, /etc
ls -la /mnt/restore/bin/
ls -la /mnt/restore/lib/
ls -la /mnt/restore/etc/

# 7. Смонтируем /boot (отдельный раздел)
sudo mount /dev/nvme0n1p2 /mnt/restore/boot

# 8. Смонтируем /boot/efi (если еще существует)
sudo mount /dev/nvme0n1p1 /mnt/restore/boot/efi 2>/dev/null || echo "EFI раздел пуст или поврежден"

# 9. Смонтируем /home
sudo mount /dev/debby13-vg/home /mnt/restore/home

# 10. Смонтируем /var
sudo mount /dev/debby13-vg/var /mnt/restore/var

# 11. Смонтируем /tmp
sudo mount /dev/debby13-vg/tmp /mnt/restore/tmp

## Проверка содержимого:
# Проверьте /home/alex - ваши данные должны быть целы
ls -la /mnt/restore/home/alex/

# Проверьте /var - возможно там важное
ls -la /mnt/restore/var/

# Проверьте, есть ли ядра в /boot
ls -la /mnt/restore/boot/

# Проверьте, что осталось в /bin (должно быть пусто или почти пусто)
find /mnt/restore/bin -type f 2>/dev/null | wc -l

## Затем подготовим chroot:
# Монтируем виртуальные ФС
sudo mount --bind /dev /mnt/restore/dev
sudo mount --bind /proc /mnt/restore/proc
sudo mount --bind /sys /mnt/restore/sys
sudo cp /etc/resolv.conf /mnt/restore/etc/resolv.conf

## Вход в систему:
sudo chroot /mnt/restore /bin/bash

## 1. Создаем недостающие файлы в /etc внутри chroot
# Создаем resolv.conf вручную
sudo mkdir -p /mnt/restore/etc
echo "nameserver 8.8.8.8" | sudo tee /mnt/restore/etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee -a /mnt/restore/etc/resolv.conf

# Создаем базовый fstab (если отсутствует)
sudo tee /mnt/restore/etc/fstab << 'EOF'
# /etc/fstab: static file system information.
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
/dev/mapper/debby13--vg-root /               ext4    errors=remount-ro 0       1
/dev/nvme0n1p1       /boot/efi       vfat    umask=0077      0       1
/dev/nvme0n1p2       /boot           ext4    defaults        0       2
/dev/mapper/debby13--vg-home /home           ext4    defaults        0       2
/dev/mapper/debby13--vg-var  /var            ext4    defaults        0       2
/dev/mapper/debby13--vg-tmp  /tmp            ext4    defaults        0       2
/dev/mapper/debby13--vg-swap_1 none            swap    sw              0       0
EOF

## Шаг 4: Проверяем, есть ли в корневой системе bash и базовые утилиты
    нихрена нет
## Шаг 1 — Сохранить важное (прямо сейчас):
# Список пакетов (чтобы знать, что устанавливать)
sudo chroot /mnt/restore /usr/bin/bash -c "dpkg -l" > ~/dpkg_list.txt

# Ваши docker-проекты (docker-compose.yml и т.д.)
sudo cp -r /mnt/restore/home/alex/dockers ~/dockers_backup/

# SSH ключи, если были
sudo cp -r /mnt/restore/home/alex/.ssh ~/.ssh_backup/ 2>/dev/null