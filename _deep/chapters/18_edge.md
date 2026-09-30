---
id: edge
module: Мережа
title: Швидко для всього світу — Amazon CloudFront і AWS Global Accelerator
short: CloudFront і Global Accelerator
emoji: 🚀
domains: secure, performance, cost
svc: cloudfront, ga, oac, s3ta
---
> 🎬 **Історія Хмаринки.** Пам'ятаєш скаргу покупниці з Варшави з [розділу 3](#ch/it-networks)? Кожне фото товару їхало з Франкфурта окремо, а сторінка каталогу має 60 фото. А ще кур'єрська служба, з якою працює Хмаринка, вимагає: «Дайте нам **постійні IP-адреси** вашого API, ми внесемо їх у свій файрвол». Але в балансувальника адреси змінюються. Дві різні задачі — «ближче до людей» і «стабільний вхід у мережу AWS» — і два сервіси на краю мережі: **CloudFront** і **Global Accelerator**.

> 🖼️ **Образ.** **CloudFront** — мережа кіосків з копіями найпопулярніших товарів у кожному районі міста: покупець бере товар за рогом, а не їде на центральний склад. **Global Accelerator** — швидкісна платна автомагістраль із двома постійними в'їздами біля кожного міста світу: товарів на в'їзді немає (нічого не кешує), зате з будь-якого міста ти одразу потрапляєш на рівну приватну трасу без світлофорів аж до потрібного складу — а якщо склад закрито, тебе за секунди розвертають на інший.

## CloudFront: мережа доставки контенту {#cloudfront}

**Amazon CloudFront** — CDN (content delivery network): копії контенту кешуються в **сотнях edge-локацій** по світу. Покупець отримує файл з найближчої точки за мілісекунди, а сервери Хмаринки (**origin** — джерело) отримують у рази менше запитів.

Як працює запит:

<figure class="diagram" data-caption="Шлях запиту через CloudFront">
<div class="flow">
<div class="st"><b>👤 Покупець у Варшаві</b>Запит khmarynka.ua/images/mug.jpg</div>
<span class="ar">→</span>
<div class="st"><b>📍 Edge-локація (Варшава)</b>Є в кеші? → <b>Cache hit</b>: віддає за мілісекунди</div>
<span class="ar">→</span>
<div class="st"><b>🏬 Regional edge cache</b>Більший кеш рівнем вище (якщо в edge немає)</div>
<span class="ar">→</span>
<div class="st"><b>🗄️ Origin (Франкфурт)</b>S3 чи ALB — лише при <b>cache miss</b>; відповідь кешується на TTL</div>
</div>
<figcaption>Навіть некешований (динамічний) контент прискорюється: CloudFront тримає «теплі» з'єднання з origin і везе трафік приватною мережею AWS, а не інтернетом.</figcaption>
</figure>

### Origins: звідки CloudFront бере контент

- **S3 bucket** — статика: фото, відео, CSS, JavaScript, файли для завантаження.
- **Application Load Balancer**, **EC2**, **API Gateway**, функції Lambda (URL) — динамічний контент і API.
- **Будь-який HTTP-сервер**, навіть у власному дата-центрі (custom origin).
- **VPC origins** (з 2024 року) — приватні ALB, NLB чи EC2 **без публічних адрес**: CloudFront звертається до них прямо в приватні підмережі.

### Закрити S3 від усіх, крім CloudFront: OAC {#oac}

Якщо bucket з фото публічний, будь-хто може качати файли в обхід CloudFront (і WAF, і кешу). Правильна схема: bucket **приватний**, а доступ має лише CloudFront через **Origin Access Control (OAC)** — bucket policy дозволяє читання лише цьому конкретному distribution. OAC — сучасна заміна старого **OAI** (Origin Access Identity) і, на відміну від нього, підтримує шифрування **SSE-KMS**, усі регіони й запис (PUT).

### Cache behaviors: різні правила для різних шляхів

Один distribution може мати кілька **behaviors** за шаблоном шляху — кожен зі своїм origin і своїм кешуванням:

| Шлях | Origin | Кешування | Інше |
|---|---|---|---|
| `/images/*`, `/static/*` | S3 (через OAC) | Довго (дні), файли з версією в імені | Стиснення |
| `/api/*` | ALB | **Не кешувати**; передавати заголовки, cookies, query string | Дозволені POST/PUT/DELETE |
| `*` (default) | ALB | Коротко (хвилини) | Переадресація HTTP → HTTPS |

**TTL і інвалідація.** Скільки файл живе в кеші, визначає **cache policy** (мінімальний, типовий і максимальний TTL) разом із заголовками `Cache-Control` від origin. Щоб примусово оновити файл — **invalidation** (`/images/mug.jpg` або `/images/*`), але краще **версіонувати імена** файлів (`style.v42.css`): нова версія — нове ім'я, старий кеш не заважає, інвалідації не потрібні.

### Приватний контент: signed URL і signed cookies

Хмаринка продає електронні подарункові сертифікати в PDF — не всім, а лише покупцям:

- **Signed URL** — підписане посилання на **один** файл з терміном дії (і, за бажанням, дозволеною IP).
- **Signed cookies** — доступ до **багатьох** файлів (увесь розділ «для підписників», відеокурс) без зміни URL-адрес.
- Підписує застосунок ключем з **trusted key group** CloudFront.

Не плутай з **S3 presigned URL** — тимчасовим посиланням напряму на об'єкт S3 (з правами того, хто підписав), без CloudFront.

### Безпека й надійність на краю

- **HTTPS**: сертифікат **ACM у us-east-1** ([розділ 11](#ch/encryption/acm)); примусова переадресація HTTP → HTTPS; власні домени (alternate domain names).
- **AWS WAF** на distribution і автоматичний **Shield Standard**; CloudFront поглинає DDoS своєю гігантською пропускною здатністю.
- **Geo restriction** — дозволити або заборонити цілі країни.
- **Origin failover** — **origin group** з основним і резервним origin: якщо основний повертає помилки (наприклад, 500, 502, 503, 504), запит іде на резервний (скажімо, копію bucket в іншому регіоні).
- **Field-level encryption** — шифрує окремі поля форми (номер картки) вже на edge, щоб лише потрібний мікросервіс міг їх розшифрувати.

### Код на краю: CloudFront Functions і Lambda@Edge

| | **CloudFront Functions** | **Lambda@Edge** |
|---|---|---|
| Мова | JavaScript (легкий) | Node.js, Python |
| Де і коли виконується | На кожній edge-локації, **лише** запит глядача і відповідь глядачу | У regional edge caches, на запити й відповіді **глядача і origin** |
| Швидкість і масштаб | Субмілісекунди, мільйони запитів за секунду | Мілісекунди–секунди |
| Мережа і файли | ❌ Без мережевих викликів | ✅ Можна звертатися до інших сервісів |
| Типові задачі | Заголовки безпеки, редиректи, переписування URL, проста перевірка токена, A/B за cookie | Зміна розміру зображень, складна автентифікація, вибір origin за даними з бази |

### Гроші

- Передача даних з origins AWS (S3, ALB, EC2) **до CloudFront — безкоштовна**, а віддача з CloudFront користувачам зазвичай дешевша за прямий вихід з регіону. Тож CloudFront часто **зменшує** рахунок за трафік.
- **Price classes** — обмежити distribution дешевшими регіонами edge-мережі (наприклад, лише Європа й Північна Америка).
- Є постійний безкоштовний рівень (терабайт трафіку і мільйони запитів на місяць) — для навчальних проєктів цього вистачає з головою.

## AWS Global Accelerator {#ga}

**AWS Global Accelerator** дає застосунку **дві статичні anycast IP-адреси**. «Anycast» означає: ті самі дві адреси анонсуються з усіх edge-локацій AWS, і користувач потрапляє в **найближчу**. Далі трафік іде **приватною мережею AWS** до найкращого здорового endpoint у потрібному регіоні.

- **Endpoints:** Application Load Balancer, Network Load Balancer, EC2, Elastic IP — в одному чи кількох регіонах (endpoint groups).
- **Health checks** і **перемикання між регіонами за секунди** — без залежності від DNS-кешу, бо адреси не змінюються.
- **Traffic dials** (відсоток трафіку на регіон) і **ваги** endpoint — для поступових релізів і техобслуговування.
- **TCP і UDP**, будь-які протоколи зверху. **Нічого не кешує.**
- **Статичні IP** — ідеально, коли клієнти вносять адреси в білі списки файрволів.

Для кур'єрської служби Хмаринки: Global Accelerator перед ALB з API → дві постійні адреси для їхнього файрвола, а бонусом — стабільніша затримка з будь-якої країни.

## CloudFront чи Global Accelerator? {#compare}

| | **CloudFront** | **Global Accelerator** |
|---|---|---|
| Кешування | ✅ Так — головна ідея | ❌ Ні |
| Протоколи | HTTP/HTTPS (і WebSocket) | **TCP / UDP** — будь-які застосунки |
| Вхідні адреси | DNS-ім'я, IP змінюються | **2 статичні anycast IP** |
| Перемикання регіонів | Origin failover у межах запиту | **Секунди**, на рівні мережі, без DNS-кешу |
| Типові сценарії | Сайти, фото, відео, API з кешем, статичні сайти з S3 | Ігри, IoT, VoIP, API зі статичними IP, мультирегіональний failover |
| Захист | WAF, Shield | Shield (з Advanced) |

:::mnemo 🧠 Одним реченням
**Є що кешувати і це веб → CloudFront. Потрібні статичні IP, UDP чи швидке перемикання регіонів → Global Accelerator.** І ще сусід: **S3 Transfer Acceleration** — прискорює **завантаження в S3** з далеких країн через edge-мережу.
:::

:::lab 🧪 Спробуй у справжньому AWS: приватний S3 за CloudFront з OAC
**Вартість:** у межах безкоштовного рівня CloudFront і кількох центів S3. **Час:** 25 хвилин (створення distribution займає кілька хвилин).
1. **S3 → Create bucket**: ім'я `khmarynka-edge-<випадкові-цифри>`, регіон eu-central-1, **Block all public access — увімкнено** (залиш як є).
2. Створи на комп'ютері файл `index.html` з текстом `<h1>Привіт з Хмаринки!</h1>` і завантаж у bucket.
3. **CloudFront → Create distribution**: Origin domain — твій bucket; **Origin access — Origin access control settings (recommended)** → Create new OAC. Default root object: `index.html`. WAF — можна не вмикати для тесту. Create.
4. Натисни **Copy policy** у жовтому банері і встав її в **Bucket policy** свого bucket (S3 → Permissions → Bucket policy) — або погодься, щоб консоль оновила її сама. Подивись: дозволено лише `cloudfront.amazonaws.com` з умовою на ARN твого distribution.
5. Коли статус distribution — Enabled, відкрий його адресу `https://dxxxx.cloudfront.net` — сторінка працює (з HTTPS!).
6. Відкрий прямий URL об'єкта S3 (Object URL) — **AccessDenied**: bucket приватний, доступ лише через CloudFront.
7. Зміни `index.html`, завантаж знову — CloudFront ще показує стару версію (кеш). Зроби **Invalidations → Create** з шляхом `/*` — і отримаєш нову.
**Прибери за собою:** CloudFront → distribution → **Disable**, дочекайся і **Delete**; потім очисти й видали bucket.
:::

#### 💡 Запам'ятай

- **CloudFront** — CDN: кеш на сотнях edge-локацій, менша затримка, менше навантаження на origin, часто дешевший трафік.
- Origins: **S3, ALB, EC2, API Gateway, будь-який HTTP-сервер**, **VPC origins** для приватних ресурсів.
- **OAC** — bucket лише для CloudFront (заміна OAI, підтримує SSE-KMS).
- **Cache behaviors** за шляхом: `/static/*` → S3 з довгим кешем, `/api/*` → ALB без кешу.
- **Signed URL** — один файл; **signed cookies** — багато файлів; **S3 presigned URL** — напряму в S3.
- **Geo restriction**, **origin failover** (origin group), **field-level encryption**, **WAF**, сертифікат **ACM у us-east-1**.
- **CloudFront Functions** — легкі й миттєві (заголовки, редиректи); **Lambda@Edge** — важча логіка з мережею.
- **Global Accelerator** — **2 статичні anycast IP**, **TCP/UDP**, **без кешу**, **перемикання регіонів за секунди**.

#### 🎯 Як питають на іспиті

- Прискорити статичний і динамічний контент для користувачів по всьому світу → **Amazon CloudFront**
- Заборонити прямий доступ до S3, лише через CloudFront → **Origin Access Control (OAC)**
- Доступ підписників до багатьох платних відео → **CloudFront signed cookies**
- Тимчасове посилання на один приватний файл → **CloudFront signed URL** (або S3 presigned URL)
- Заблокувати доступ до контенту з певних країн → **CloudFront geo restriction** (або WAF geo match)
- Статика й API на одному домені з різним кешуванням → **cache behaviors за шляхом**
- Легкі зміни заголовків і редиректи на edge з мінімальною затримкою → **CloudFront Functions**
- Змінювати розмір зображень на льоту з викликами інших сервісів → **Lambda@Edge**
- Автоматично віддавати контент з резервного bucket, якщо основний повертає 5xx → **CloudFront origin failover (origin group)**
- Статичні IP для глобального застосунку, клієнти вносять їх у білий список → **AWS Global Accelerator** (або NLB з Elastic IP в одному регіоні)
- Онлайн-гра на UDP, гравці по всьому світу, швидке перемикання регіонів → **Global Accelerator**
- Зменшити витрати на вихідний трафік для популярного статичного контенту → **CloudFront перед S3**
- Користувачі з інших континентів повільно завантажують великі файли в S3 → **S3 Transfer Acceleration** (+ multipart upload)

#### ⚠️ Пастки

- Global Accelerator **не кешує** — для кешу потрібен CloudFront.
- CloudFront — про HTTP(S); для «UDP-гри» це неправильна відповідь.
- Сертифікат ACM для CloudFront — лише з **us-east-1**.
- OAI — застарілий; якщо в питанні є SSE-KMS — лише **OAC**.
- Signed URL ≠ presigned URL: перший — CloudFront, другий — S3.

## ✅ Перевір себе

:::quiz
? Інтернет-магазин зберігає фото товарів у S3 і хоче, щоб їх отримували лише через CloudFront, а прямий доступ до bucket був заборонений. Що налаштувати?
- Зробити bucket публічним і обмежити доступ Security Group
+ Origin Access Control і bucket policy, що дозволяє читання лише цьому distribution
- S3 presigned URL для кожного фото
- Signed cookies для всіх відвідувачів
= OAC дозволяє CloudFront підписувати запити до приватного bucket, а bucket policy пускає лише сервіс CloudFront з умовою на конкретний distribution. У S3 немає Security Groups.

? Відеоплатформа хоче, щоб платні підписники мали доступ до сотень відео без зміни посилань, а інші — ні. Що обрати?
- CloudFront signed URL для кожного відео
+ CloudFront signed cookies
- S3 presigned URL
- CloudFront geo restriction
= Signed cookies дають доступ до багатьох файлів одночасно без зміни URL. Signed URL зручний для одного файлу, geo restriction обмежує за країнами, а не за підпискою.

? Партнер вимагає фіксованих IP-адрес API, щоб додати їх у свій файрвол. API працює за Application Load Balancer у двох регіонах, і потрібне швидке перемикання при збої регіону. Що обрати?
- CloudFront distribution перед ALB
+ AWS Global Accelerator з endpoints — ALB в обох регіонах
- Elastic IP на ALB
- Route 53 latency-based routing
= Global Accelerator дає дві статичні anycast IP і перемикає між регіонами за секунди за health checks. ALB не підтримує Elastic IP, у CloudFront адреси змінюються, а DNS-перемикання залежить від TTL.

? Компанія запускає багатокористувацьку гру на UDP з гравцями на всіх континентах. Потрібна низька затримка і стабільне з'єднання. Що підходить найкраще?
- Amazon CloudFront
+ AWS Global Accelerator
- S3 Transfer Acceleration
- Route 53 geolocation routing
= Global Accelerator працює з TCP і UDP, заводить трафік у приватну мережу AWS у найближчій точці й має статичні адреси. CloudFront призначений для HTTP(S) і кешування.

? Один domain має обслуговувати статичні файли з S3 з довгим кешем і API з ALB без кешування. Як це зробити в одному distribution CloudFront?
+ Два cache behaviors: /static/* → S3 з довгим TTL, /api/* → ALB з вимкненим кешуванням
- Два окремі distribution з однаковим доменом
- Route 53 weighted routing між S3 і ALB
- Lambda@Edge, що копіює файли з ALB у S3
= Cache behaviors за шаблоном шляху дозволяють різні origins і різні правила кешування в межах одного distribution.

? Потрібно додавати заголовки безпеки (HSTS, CSP) до всіх відповідей сайту з мінімальною затримкою і вартістю. Що обрати?
+ CloudFront Functions на подію viewer response
- Lambda@Edge на подію origin request
- EC2 з nginx перед CloudFront
- AWS WAF
= CloudFront Functions — легкий JavaScript, що виконується на кожній edge-локації за субмілісекунди і дешево. Для простих змін заголовків це найкращий вибір; Lambda@Edge — для важчої логіки.

? Сайт зберігає фото в bucket у eu-central-1 і має копію bucket в eu-west-1. Як зробити, щоб CloudFront автоматично віддавав фото з копії, якщо основний bucket повертає помилки 5xx?
- Route 53 failover для bucket
+ Origin group у CloudFront з основним і резервним origin та критеріями failover
- Два distribution з перемиканням вручну
- S3 Transfer Acceleration
= Origin group задає основний і резервний origin; при вказаних кодах помилок CloudFront повторює запит до резервного.
:::
