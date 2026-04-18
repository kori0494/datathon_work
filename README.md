# datathon_work
Repo làm việc của nhóm GGB trong datathon
# 📘 Git Workflow Guide for Team Collaboration

## 🎯 Mục tiêu

Tài liệu này hướng dẫn cách sử dụng Git trong project để:

* Làm việc theo **branch riêng**
* Tránh conflict
* Dễ dàng merge code về `main`

---

## 📌 Nguyên tắc chung

* `main` = code ổn định (KHÔNG code trực tiếp vào đây)
* Mỗi người làm việc trên **branch riêng**
* Khi xong → tạo **Pull Request (PR)** để merge

---

## 🚀 1. Setup lần đầu

### Clone repo

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>
```

---

## 🌿 2. Tạo branch để làm việc

Luôn tạo branch từ `main` mới nhất:

```bash
git switch main
git pull
git switch -c feature-ten-cua-ban
```

Ví dụ:

```bash
git switch -c feature-data-cleaning
```

---

## ⬆️ 3. Push branch lên GitHub

```bash
git push -u origin feature-ten-cua-ban
```

---

## 💻 4. Làm việc hằng ngày

Sau khi code:

```bash
git add .
git commit -m "mô tả thay đổi"
git push
```

---

## 🔄 5. Đồng bộ với main (rất quan trọng)

Trước khi tiếp tục làm việc, luôn update branch:

```bash
git switch main
git pull

git switch feature-ten-cua-ban
git merge main
```

👉 Giúp tránh conflict lớn khi merge

---

## 🔀 6. Merge code về main

### Cách chuẩn (khuyên dùng):

* Lên GitHub
* Tạo **Pull Request**
* Review → Merge

---

### Cách bằng terminal:

```bash
git switch main
git pull
git merge feature-ten-cua-ban
git push
```

---

## 👥 7. Làm việc với branch của người khác

```bash
git fetch
git switch -t origin/ten-branch
```

---

## ⚠️ 8. Những lỗi cần tránh

### ❌ Không làm trực tiếp trên main

### ❌ Không pull trước khi code

### ❌ Không push code chưa commit

### ❌ Không đặt tên branch lung tung

---

## 🏷️ 9. Quy ước đặt tên branch

* `feature/...` → tính năng mới
* `bugfix/...` → sửa lỗi
* `experiment/...` → thử nghiệm

Ví dụ:

```
feature/login
feature/data-cleaning
bugfix/missing-value
```

---

## 🔥 10. Flow chuẩn cho team

1. Clone repo
2. Tạo branch riêng
3. Code + commit + push
4. Tạo Pull Request
5. Merge vào `main`

---

## 💡 Tip hữu ích

Xem trạng thái:

```bash
git status
```

Xem branch:

```bash
git branch -a
```

---

## 📌 Tổng kết

👉 Mỗi người = 1 branch
👉 Không đụng vào `main`
👉 Luôn pull trước khi làm
👉 Dùng Pull Request để merge

---

Chúc team làm việc mượt mà 🚀
