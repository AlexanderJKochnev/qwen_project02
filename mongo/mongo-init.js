// mongo-init.js
// Создаем пользователя только если он не существует
db = db.getSiblingDB('admin');

// Проверяем, существует ли уже пользователь admin
var user = db.getUser('admin');
if (!user) {
    db.createUser({
        user: "admin",
        pwd: "admin",
        roles: [{ role: "root", db: "admin" }]
    });
    print('User admin created successfully');
} else {
    print('User admin already exists, skipping creation');
}

print("MongoDB initialization completed");
