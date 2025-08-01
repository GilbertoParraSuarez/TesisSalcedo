db = db.getSiblingDB('mydb');

db.createUser({
  user: "admin",
  pwd: "secreta123",
  roles: [{ role: "readWrite", db: "db" }]
})
