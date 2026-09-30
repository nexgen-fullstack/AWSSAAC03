---
id: vpc-connect
module: Мережа
title: Як VPC говорить із сервісами й іншими VPC — endpoints, PrivateLink, Peering, Transit Gateway
short: Endpoints, Peering, TGW
emoji: 🔗
domains: secure, performance, cost
svc: endpoints, privatelink, peering, tgw
---
> 🎬 **Історія Хмаринки.** Марта принесла рахунок за перший місяць: чималий рядок «NAT Gateway — Data Processing». З'ясувалося, що сервери в приватних підмережах щодня качають гігабайти фото з S3 — **через NAT і інтернет**, хоча і сервери, і S3 знаходяться в тому самому регіоні AWS. А ще платіжний партнер хоче, щоб його сервіс перевірки платежів був доступний Хмаринці **приватно**, без інтернету. І з'явилася друга VPC — для аналітики, яку треба з'єднати з першою. Сьогодні — про всі способи з'єднати мережі й сервіси, **і скільки вони коштують**.

> 🖼️ **Образ.** **Gateway endpoint** — безкоштовний службовий тунель з двору твого комплексу прямо на склад S3, минаючи вулицю. **Interface endpoint** — окрема «віконце-каса» сервісу, встановлена прямо в твоєму будинку: платиш оренду, зате обслуговують усередині. **VPC Peering** — пряма хвіртка між двома сусідніми комплексами (але через сусіда в третій комплекс не пройдеш). **Transit Gateway** — центральний вокзал, від якого йдуть потяги до всіх комплексів і в офіс.

## Навіщо VPC endpoints {#endpoints}

Сервіси AWS на кшталт S3, SQS, DynamoDB мають **публічні** адреси. Без спеціальних налаштувань сервер у приватній підмережі може звернутися до них лише через **NAT Gateway** (тобто через інтернет-вихід), а це:

- **гроші** — NAT бере плату за кожен гігабайт;
- **ризик** — підмережі потрібен вихід в інтернет, навіть якщо іншого інтернету їй не треба;
- **вимоги регуляторів** — «трафік до сховища не повинен виходити в інтернет».

**VPC endpoint** — приватний шлях від VPC до сервісу AWS по мережі AWS, без інтернету, NAT і публічних IP. Два типи:

<figure class="diagram" data-caption="Gateway endpoint і interface endpoint">
<div class="grid2">
<div class="gcard"><b>🚪 Gateway endpoint</b>Запис у <strong>таблиці маршрутів</strong>: «трафік до S3 → vpce-…»<small>✅ Лише <strong>S3 і DynamoDB</strong><br>✅ <strong>Безкоштовний</strong><br>⚠️ Працює лише для ресурсів у цій VPC — не з офісу через VPN/DX і не з іншої VPC</small></div>
<div class="gcard"><b>🪟 Interface endpoint (PrivateLink)</b><strong>Мережевий інтерфейс (ENI)</strong> з приватною IP у твоїй підмережі; до нього прикріплюється Security Group<small>✅ Майже всі сервіси: SQS, SNS, KMS, Secrets Manager, SSM, ECR, CloudWatch, STS, API Gateway, S3…<br>💲 Платний: за годину в кожній AZ + за гігабайт<br>✅ Доступний з офісу (VPN/DX) і з інших VPC</small></div>
</div>
<figcaption>Для S3 існують обидва. Усередині VPC — безкоштовний gateway. Для доступу до S3 приватно з офісу через Direct Connect — interface endpoint.</figcaption>
</figure>

**Private DNS** для interface endpoint: звичайне ім'я сервісу (наприклад, `sqs.eu-central-1.amazonaws.com`) усередині VPC починає вказувати на **приватні** адреси endpoint — код застосунку не змінюється взагалі.

### Політики endpoint і bucket

- **Endpoint policy** — політика на самому endpoint: «через цей тунель можна звертатися лише до bucket `khmarynka-*`». Захищає від витоку даних у чужі bucket (ексфільтрації).
- **Bucket policy** з умовою **`aws:SourceVpce`** (конкретний endpoint) або **`aws:SourceVpc`** — «цей bucket доступний лише з нашої VPC». Разом вони будують мережевий периметр даних ([розділ 10](#ch/organizations/rcp)).

:::example 🧩 Рахунок Марти
До: 3 ТБ на місяць з S3 через NAT Gateway — плата за обробку кожного гігабайта в NAT плюс години NAT. Після: **gateway endpoint для S3** — трафік до S3 йде в обхід NAT, а сам endpoint безкоштовний. Рядок «NAT — Data Processing» зменшився в рази. Один рядок у таблиці маршрутів — одна з найвигідніших оптимізацій в AWS.
:::

## PrivateLink: свій сервіс — приватно для інших {#privatelink}

**AWS PrivateLink** — технологія, на якій працюють interface endpoints. І нею можна користуватися для **власних** сервісів:

1. **Провайдер** (платіжний партнер) ставить свій сервіс за **Network Load Balancer** (або Gateway Load Balancer) і створює **endpoint service**.
2. **Споживач** (Хмаринка) створює у своїй VPC **interface endpoint** до цього сервісу. Провайдер схвалює підключення.
3. Трафік іде приватно мережею AWS: Хмаринка бачить **лише цей сервіс**, а не всю мережу партнера.

Переваги: **односторонній** доступ (провайдер не бачить мережу споживача), **діапазони адрес можуть перетинатися** (адреси маршрутизувати не треба), масштабується на **тисячі** споживачів. Так працюють SaaS-сервіси в AWS Marketplace.

## VPC Peering: пряме з'єднання двох VPC {#peering}

**VPC Peering** — приватне з'єднання двох VPC, ніби це одна мережа. Працює між акаунтами і між регіонами.

- Маршрути треба додати **з обох боків** (у таблиці VPC A — діапазон B через `pcx-…`, і навпаки).
- **Діапазони не повинні перетинатися.**
- **Нетранзитивне**: якщо A з'єднана з B, а B — з C, то A **не** бачить C. Потрібне окреме з'єднання A–C.
- Не можна «користуватися» шлюзами сусіда: VPC A не вийде в інтернет через IGW чи NAT VPC B і не дійде до офісу через VPN VPC B.
- Немає окремої плати за з'єднання — лише за передачу даних (у межах однієї AZ безкоштовно, між AZ і регіонами — платно).

Для 2–3 VPC peering — найпростіше і найдешевше. Але для N VPC повна сітка потребує N×(N−1)/2 з'єднань: 10 VPC — 45 peering, 50 VPC — 1225. Тут на сцену виходить Transit Gateway.

## Transit Gateway: мережевий вокзал {#tgw}

**AWS Transit Gateway (TGW)** — регіональний **хаб**, до якого підключаються (attachments) VPC, **Site-to-Site VPN**, **Direct Connect** (через Direct Connect Gateway) і інші Transit Gateway в інших регіонах (peering).

- **Транзитивна маршрутизація**: усе, що підключено до TGW, може спілкуватися через нього (якщо дозволяють таблиці маршрутів).
- **Власні таблиці маршрутів TGW** — сегментація: prod не бачить dev, але обидва бачать спільні сервіси.
- Шариться між акаунтами через **AWS RAM**.
- **ECMP** для VPN — кілька тунелів VPN сумують пропускну здатність.
- **Inter-region peering** між TGW різних регіонів.
- Плата — за кожне підключення на годину **і** за кожен оброблений гігабайт.

<figure class="diagram" data-caption="Peering проти Transit Gateway">
<div class="grid2">
<div class="gcard"><b>🔗 VPC Peering</b>A ⇄ B, B ⇄ C, але <strong>A ✕ C</strong><small>Нетранзитивно. Кожна пара — окреме з'єднання і маршрути. Дешево: лише трафік.</small></div>
<div class="gcard hl"><b>🚉 Transit Gateway</b>A, B, C, D, офіс (VPN/DX) → <strong>один хаб</strong><small>Транзитивно, сегментація таблицями, сотні VPC. Плата за підключення і гігабайти.</small></div>
</div>
<figcaption>Кілька VPC і великий трафік між ними → peering (дешевше). Десятки VPC плюс офіс, централізований контроль → Transit Gateway.</figcaption>
</figure>

:::note 📌 Ще два сервіси, які варто впізнати
- **AWS Cloud WAN** — глобальна мережа з централізованою політикою, що об'єднує VPC і офіси в багатьох регіонах (надбудова над ідеєю Transit Gateway у світовому масштабі).
- **Amazon VPC Lattice** — з'єднання **сервісів** (застосунків) між VPC і акаунтами на рівні застосунку, з політиками автентифікації, без керування маршрутами й перетинами діапазонів.
:::

## Що обрати: таблиця рішень {#choose}

| Задача | Рішення |
|---|---|
| Приватний доступ до S3 або DynamoDB з VPC, найдешевше | **Gateway endpoint** |
| Приватний доступ до SQS, KMS, Secrets Manager, SSM, ECR… | **Interface endpoint** |
| Доступ до S3 приватно з офісу через VPN/DX | **Interface endpoint для S3** |
| Дати свій сервіс сотням клієнтів приватно, діапазони можуть перетинатися | **PrivateLink** (NLB + endpoint service) |
| З'єднати 2–3 VPC просто й дешево | **VPC Peering** |
| З'єднати десятки VPC і офіс, транзитивно, з сегментацією | **Transit Gateway** |
| Кілька акаунтів працюють в одній спільній мережі | **VPC sharing** (AWS RAM) |

:::lab 🧪 Спробуй у справжньому AWS: peering двох VPC
**Вартість:** безкоштовно (створення peering і маршрутів не тарифікується; ми не передаватимемо даних). **Час:** 20 хвилин.
1. Якщо VPC `khmarynka` (10.0.0.0/16) з попередньої практики видалена — створи знову (**VPC and more**, без NAT).
2. Створи другу VPC: **VPC only**, назва `analytics`, CIDR `10.1.0.0/16`.
3. **Peering connections → Create peering connection**: Requester — `khmarynka`, Accepter — `analytics` (цей же акаунт і регіон). Create.
4. Обери peering → Actions → **Accept request**. Статус — Active.
5. **Route tables**: у таблицях підмереж `khmarynka` додай маршрут `10.1.0.0/16 → pcx-…`; у головній таблиці `analytics` — `10.0.0.0/16 → pcx-…`. Без маршрутів з обох боків peering не працює.
6. Подумай: якби була третя VPC `10.2.0.0/16`, з'єднана peering лише з `analytics`, чи могла б `khmarynka` дістатися до неї? (Ні — peering нетранзитивний.)
7. Подивись **Endpoints** своєї VPC: gateway endpoint S3 і його **Policy** (за замовчуванням — повний доступ). Спробуй **Edit policy** і подивись приклад з обмеженням на конкретні bucket.
**Прибери за собою:** видали peering connection, потім VPC `analytics` (і `khmarynka`, якщо більше не потрібна).
:::

#### 💡 Запам'ятай

- **Gateway endpoint** — лише **S3 і DynamoDB**, безкоштовно, через таблицю маршрутів, лише зсередини VPC.
- **Interface endpoint (PrivateLink)** — майже всі сервіси, ENI з приватною IP і Security Group, платний, доступний з офісу й інших VPC.
- **Endpoint policy** + **`aws:SourceVpce` / `aws:SourceVpc`** у bucket policy — приватний периметр.
- **PrivateLink** для власних сервісів: провайдер — **NLB + endpoint service**, споживач — interface endpoint; однобічно, CIDR можуть перетинатися.
- **VPC Peering:** 1:1, **нетранзитивно**, **без перетину CIDR**, маршрути з обох боків, без використання шлюзів сусіда.
- **Transit Gateway:** хаб для сотень VPC, VPN і DX; **транзитивно**; таблиці маршрутів для сегментації; шариться через RAM; платний за підключення і гігабайти.

#### 🎯 Як питають на іспиті

- Приватні сервери звертаються до S3/DynamoDB без інтернету і безкоштовно → **gateway VPC endpoint**
- Великий рахунок за NAT Gateway через трафік до S3 → **gateway endpoint для S3**
- Приватний доступ до SQS, KMS чи Secrets Manager без NAT → **interface VPC endpoint**
- On-prem сервери через Direct Connect мають звертатися до S3 приватно → **interface endpoint для S3** (gateway не працює з on-prem)
- Bucket має бути доступний лише через конкретний VPC endpoint → **bucket policy з умовою aws:SourceVpce**
- Надати свій сервіс сотням клієнтських VPC, діапазони адрес перетинаються → **PrivateLink (NLB + endpoint service)**
- З'єднати дві VPC у різних акаунтах просто і дешево → **VPC Peering**
- VPC A з'єднана з B, B — з C, але A не бачить C → **peering нетранзитивний: додати A–C або Transit Gateway**
- З'єднати 40 VPC і офіс через VPN з транзитивною маршрутизацією → **Transit Gateway**
- Ізолювати prod від dev, але дати обом доступ до спільних сервісів через хаб → **окремі таблиці маршрутів Transit Gateway**
- Дві VPC обмінюються великим обсягом даних, треба найдешевше → **VPC Peering (а не Transit Gateway)**

#### ⚠️ Пастки

- Gateway endpoint для SQS, SNS чи KMS **не існує** — лише S3 і DynamoDB.
- Gateway endpoint не працює для трафіку з офісу (VPN/DX) і з peered VPC.
- Peering не можна створити між VPC з перетинними діапазонами.
- Peering не дає доступу до IGW, NAT, VPN чи DX сусідньої VPC.
- Transit Gateway — не безкоштовний: для великого трафіку між двома VPC він дорожчий за peering.

## ✅ Перевір себе

:::quiz
? Сервери в приватних підмережах завантажують 5 ТБ на місяць з Amazon S3 у тому ж регіоні через NAT Gateway. Як найпростіше зменшити витрати?
+ Створити gateway VPC endpoint для S3 і додати його до таблиць маршрутів приватних підмереж
- Замінити NAT Gateway на NAT instance
- Створити interface endpoint для S3 у кожній AZ
- Перенести сервери в публічні підмережі
= Gateway endpoint для S3 безкоштовний і відправляє трафік до S3 в обхід NAT, тож зникає плата за обробку даних у NAT. Interface endpoint теж працює, але він платний.

? Застосунок у приватній підмережі має читати повідомлення з Amazon SQS без доступу в інтернет. Що створити?
- Gateway endpoint для SQS
+ Interface endpoint для SQS
- VPC peering з SQS
- Internet Gateway з обмежувальною Security Group
= Gateway endpoints існують лише для S3 і DynamoDB. Для SQS — interface endpoint (PrivateLink) з приватною IP у підмережі.

? Компанія підключена до AWS через Direct Connect. Локальні сервери мають приватно звертатися до S3, не через інтернет. Що використати?
- Gateway endpoint для S3
+ Interface endpoint для S3
- NAT Gateway
- VPC peering
= Gateway endpoint працює лише для ресурсів усередині VPC. Трафік з офісу через VPN чи Direct Connect може використати interface endpoint для S3 — він має приватні IP, досяжні з on-prem.

? SaaS-компанія хоче надати свій API сотням клієнтів у їхніх власних VPC, приватно, без peering. У багатьох клієнтів діапазони адрес перетинаються з мережею компанії. Що обрати?
- VPC peering з кожним клієнтом
- Transit Gateway, спільний з усіма клієнтами
+ AWS PrivateLink: Network Load Balancer + endpoint service, клієнти створюють interface endpoints
- Site-to-Site VPN до кожного клієнта
= PrivateLink дає односторонній приватний доступ до конкретного сервісу, масштабується на тисячі споживачів і не залежить від перетину діапазонів. Peering і TGW вимагають непересічних CIDR.

? VPC A з'єднана peering з VPC B, а VPC B — з VPC C. Сервер у VPC A не може звернутися до сервера у VPC C. Чому?
- Бракує маршруту до Internet Gateway
+ VPC Peering нетранзитивний: для A–C потрібне окреме з'єднання або Transit Gateway
- Peering не працює між трьома VPC одного регіону
- Потрібно увімкнути DNS resolution у peering
= Peering з'єднує лише дві VPC. Трафік не проходить «транзитом» через VPC B. Рішення — прямий peering A–C або хаб Transit Gateway.

? Компанія має 60 VPC у кількох акаунтах і два офіси з VPN. Потрібна централізована транзитивна маршрутизація і розділення prod і dev. Що обрати?
- Повна сітка VPC peering
+ AWS Transit Gateway з окремими таблицями маршрутів, шарений через RAM
- PrivateLink між усіма VPC
- Окремий VPN з кожної VPC до кожного офісу
= Transit Gateway — хаб для сотень VPC, VPN і Direct Connect; таблиці маршрутів TGW дають сегментацію, а RAM — спільний доступ для інших акаунтів. Повна сітка peering на 60 VPC — 1770 з'єднань.

? Які твердження про gateway VPC endpoint правильні? (Оберіть 2)
+ Він підтримує лише Amazon S3 і Amazon DynamoDB
- Він створює мережевий інтерфейс з приватною IP-адресою у підмережі
+ За нього немає окремої плати
- До нього прикріплюється Security Group
- Він доступний з офісу через Site-to-Site VPN
= Gateway endpoint — це запис у таблиці маршрутів, лише для S3 і DynamoDB, безкоштовний. ENI, Security Group і доступ з on-prem — властивості interface endpoint.
:::
