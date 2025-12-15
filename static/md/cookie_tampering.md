## COOKIE TAMPERING (Подмена cookies)

### Что такое Cookie Tampering?

**Cookie Tampering** — это уязвимость, которая позволяет злоумышленнику изменять значения cookies в своем браузере и отправлять их на сервер. Если сервер хранит критическую информацию в cookies (роль пользователя, ID, права доступа) без проверки целостности (подписания), злоумышленник может легко изменить эту информацию и получить несанкционированный доступ.

### Типы информации в cookies

**Критическая информация, которая часто хранится в cookies:**
- `user_id` — идентификатор пользователя
- `role` или `permission` — роль пользователя (user, admin, moderator)
- `is_premium` — статус подписки
- `access_level` — уровень доступа
- `account_type` — тип аккаунта

### Как ею воспользоваться?

1. **Повышение привилегий:**
   - Сервер устанавливает cookie: `role=user`
   - Злоумышленник изменяет её на: `role=admin`
   - Отправляет модифицированную cookie на сервер
   - Если сервер доверяет cookie, пользователь получает права администратора

2. **Доступ к чужому аккаунту:**
   - Сервер устанавливает cookie: `user_id=5`
   - Злоумышленник изменяет на: `user_id=3`
   - Отправляет запрос на сервер
   - Если нет проверки целостности, сервер думает, что это пользователь с ID 3

3. **Изменение параметров доступа:**
   - Cookie: `account_type=free`
   - Изменяет на: `account_type=premium`
   - Получает доступ к премиум-функциям без оплаты

### Что это дает злоумышленнику?

- ✓ Повышение привилегий (user → admin)
- ✓ Доступ к чужим аккаунтам
- ✓ Доступ к премиум-функциям без оплаты
- ✓ Модификация своих прав и прав других пользователей
- ✓ Обход ограничений на функциональность
- ✓ Несанкционированный доступ к конфиденциальной информации

### Где ошибка разработчика?

Разработчик хранит критическую информацию в cookie без подписания:

```python
# УЯЗВИМО
from flask import Flask, response, request

@app.route('/login', methods=['POST'])
def login():
    user = authenticate(request.form['username'], request.form['password'])
    resp = make_response("Logged in")
    resp.set_cookie('user_id', str(user.id))
    resp.set_cookie('role', user.role)
    return resp

@app.route('/admin')
def admin():
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    if role == 'admin':  # Доверие к cookie без проверки!
        return "Admin Panel"
    return "Access Denied"
```

Сервер **доверяет** значению cookie `role` без проверки целостности. Злоумышленник может легко изменить её в браузере.

### Как это работает на уровне кода?

**Нормальный процесс:**
1. Пользователь логинится с правильными учетными данными
2. Сервер проверяет пароль в БД
3. Сервер устанавливает cookie: `role=user`
4. Браузер отправляет cookie с каждым запросом
5. Сервер проверяет cookie и знает, что это пользователь с ролью `user`

**Атака Cookie Tampering:**
1. Пользователь логинится нормально
2. Сервер устанавливает cookie: `role=user`
3. Злоумышленник открывает DevTools браузера (F12)
4. Во вкладке Application/Cookies находит cookie `role` и изменяет значение на `role=admin`
5. Отправляет запрос на `/admin` с модифицированной cookie
6. Сервер читает cookie и видит `role=admin`, предоставляет доступ

### Как это выглядит в браузере?

**Шаг 1: Нажимаем F12 → Application → Cookies**
```
Домен: example.com
Имя: role
Значение: user  ← Можно отредактировать!
HttpOnly: не отмечено
Secure: не отмечено
```

**Шаг 2: Двойной клик на значение и изменяем на `admin`**

**Шаг 3: Обновляем страницу — теперь у нас права админа!**

### Реальные истории взломов

**Yahoo Mail Cookie Forgery (2013-2014)**
- Обнаружена уязвимость Cookie Tampering в системе управления сеансами Yahoo
- Злоумышленники могли поддельную cookie для входа без пароля
- Компрометированы **450 млн аккаунтов** Yahoo
- Атакующие получали доступ к: личной почте, информации о восстановлении аккаунта, связанным сервисам
- Взлом был одним из крупнейших в истории интернета

**Facebook Session Tokens (2022)**
- Обнаружено, что расширения браузера могут перехватывать и модифицировать cookies
- Третьестороннее расширение сохраняло cookies в открытом виде
- Злоумышленники могли украсть или подделать session tokens
- Компрометированы сотни тысяч аккаунтов
- Дозволил вход в аккаунты, создание постов, рассылку сообщений

**E-commerce Premium Bypass (множественные случаи)**
- Многие интернет-магазины хранили `is_premium=false` в cookie
- Пользователи изменяли значение на `is_premium=true`
- Получали доступ к премиум-товарам без оплаты
- Убыток для компаний: тысячи долларов в непроданных товарах

**Banking Applications**
- Несколько приложений интернет-банкинга хранили `account_type=checking` в cookie
- Пользователи меняли на `account_type=admin`
- Получали доступ к функциям администратора (просмотр чужих счетов, переводы)

### Как защититься?

1. **Подписание cookies (HMAC):**
```python
# БЕЗОПАСНО
import hmac
import hashlib
import base64

SECRET_KEY = 'very-secret-key-stored-on-server'

def sign_cookie(value):
    signature = hmac.new(
        SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256
    ).digest()
    return value + '.' + base64.b64encode(signature).decode()

def verify_cookie(signed_value):
    value, signature = signed_value.rsplit('.', 1)
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256
    ).digest()
    if hmac.compare_digest(base64.b64encode(expected_signature), signature.encode()):
        return value
    return None

@app.route('/login', methods=['POST'])
def login():
    user = authenticate(...)
    signed_role = sign_cookie(user.role)
    resp = make_response("Logged in")
    resp.set_cookie('role', signed_role)
    return resp

@app.route('/admin')
def admin():
    signed_role = request.cookies.get('role')
    role = verify_cookie(signed_role)  # Проверяем подпись!
    if role == 'admin':
        return "Admin Panel"
    return "Access Denied"
```

2. **Шифрование cookies:**
```python
from cryptography.fernet import Fernet

cipher = Fernet(key)
encrypted_role = cipher.encrypt(role.encode())
resp.set_cookie('role', encrypted_role)
```

3. **Использование сеансовых токенов (Session Tokens):**
```python
# Вместо хранения всех данных в cookie, храните только session ID
import uuid
session_id = str(uuid.uuid4())
sessions[session_id] = {'user_id': 5, 'role': 'admin'}  # Данные на сервере!

resp = make_response("Logged in")
resp.set_cookie('session_id', session_id)
return resp

@app.route('/admin')
def admin():
    session_id = request.cookies.get('session_id')
    if session_id in sessions and sessions[session_id]['role'] == 'admin':
        return "Admin Panel"
    return "Access Denied"
```

4. **HttpOnly флаг:**
```python
resp.set_cookie('role', value, httponly=True)  # JavaScript не может читать!
```

5. **Secure флаг:**
```python
resp.set_cookie('role', value, secure=True)  # Отправляется только по HTTPS
```

6. **SameSite атрибут:**
```python
resp.set_cookie('role', value, samesite='Strict')  # Не отправляется при кросс-сайт запросах
```

---
