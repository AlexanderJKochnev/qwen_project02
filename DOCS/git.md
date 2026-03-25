# DOCS/git.md
##  слияние веток:
git checkout main
git pull origin main
git merge tmp
git push origin main

## удаление ветки после слияния
удаление локальной ветки оставшейся после слияния (еслит слияние не прошло - ничего не удалится)
git branch -d <имя_ветки>
удаление удаленной (remote) ветки после локальной
git push origin --delete <имя_ветки>

## подключение удаленного repo
git remote add qwen https://github.com/AlexanderJKochnev/qwen_project02.git
git push -u qwen main 

TODO.md
migration_volume/
mongodb_data/
pg_data/
upload_volume/

## генерация и привязка нового ssh key
ssh-keygen -t ed25519 -C "akochnev66@gmail.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
copy 
Скопируйте весь текст (начинается с ssh-ed25519 и заканчивается вашей почтой).
Зайдите на GitHub в раздел SSH and GPG keys.
Нажмите New SSH key, вставьте скопированный текст в поле Key и дайте любое название (например, "My Laptop").
Как закончите, попробуйте снова команду ssh -T git@github.com — она должна выдать приветствие.