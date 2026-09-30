---
id: resilience
module: Моніторинг, надійність і гроші
title: Надійність і відновлення після катастроф — RPO, RTO, стратегії DR, AWS Backup
short: DR, RPO/RTO, AWS Backup
emoji: 🛟
domains: resilient, cost
svc: backup, drs, rpo, rto
---
> 🎬 **Історія Хмаринки.** Олена ставить три незручні запитання. «Що буде, якщо **весь регіон Франкфурт** ляже на кілька годин?» «А якщо хтось **зашифрує наші дані** і вимагатиме викуп?» «А якщо Тарас **випадково видалить** таблицю замовлень?» Тарас чесно відповідає: «Від першого нас рятує лише копія в іншому регіоні, від другого й третього — бекапи, яких ніхто не може видалити». Разом вони записують вимоги: замовлення — втратити **не більше хвилини** даних і запрацювати **за 30 хвилин**; фото — втратити не більше години; аналітика — може почекати добу.

> 🖼️ **Образ.** **RPO** — скільки останніх сторінок щоденника не шкода втратити. **RTO** — за скільки часу ресторан після пожежі знову годує гостей. Чотири стратегії DR — чотири варіанти **запасного будинку**: 🧱 лише **креслення і речі на складі** (будуєш заново) · 🔥 у запасному будинку **горить лише котел** — тепло підтримується, решту вмикаєш за потреби · 🛋️ будинок **з меблями, де живе черговий** — лише покликати родину · 🏘️ **два повноцінні будинки**, і в обох живуть.

## Від чого захищаємося {#threats}

| Що ламається | Чим захищаємося | Де в курсі |
|---|---|---|
| Сервер або контейнер | Кілька екземплярів, **Auto Scaling**, health checks | [розділи 22–23](#ch/elb) |
| Ціла зона доступності (AZ) | **Multi-AZ**: ресурси у 2–3 AZ | [розділ 6](#ch/global), бази — 34–36 |
| Цілий регіон | **Multi-region DR** — копія в іншому регіоні | цей розділ |
| Помилка людини, збій даних, ransomware | **Бекапи** з історією (point-in-time), **незмінні** копії, версіонування | цей розділ, [розділ 28](#ch/s3-deep) |

:::deep 🔬 Глибше: HA, DR і бекап — три різні страховки
**Висока доступність (HA)** — система переживає збій **автоматично і майже непомітно** (Multi-AZ, балансувальник, Auto Scaling). **Відновлення після катастрофи (DR)** — план, як запрацювати в **іншому регіоні**, коли основний недоступний. **Бекап** — копія **в минулому часі**. Реплікація **не замінює** бекап: якщо хтось видалить таблицю чи шифрувальник зіпсує дані, репліка **слухняно повторить** видалення за мілісекунди. Від помилок людей і ransomware рятують лише копії з історією, які неможливо видалити.
:::

## RPO і RTO {#rpo-rto}

- **RPO (Recovery Point Objective)** — **скільки даних** (виміряних у часі) можна **втратити**: відстань від аварії **назад** до останньої доброї копії.
- **RTO (Recovery Time Objective)** — **скільки часу** система може **не працювати**: відстань від аварії **вперед** до відновлення.

<figure class="diagram" data-caption="RPO дивиться назад, RTO — вперед">
<svg class="svg-dg" viewBox="0 0 400 216" role="img" aria-label="Шкала часу: остання копія о 02:00, аварія о 02:40, відновлення о 03:10. RPO — 40 хвилин втрачених даних, RTO — 30 хвилин простою">
<text x="10" y="18" class="h">ПРИКЛАД: БАЗА ЗАМОВЛЕНЬ</text>
<line x1="20" y1="110" x2="385" y2="110" class="ln"/>
<path d="M80 94 V84 H210 V94" class="ln-bad"/>
<path d="M210 94 V84 H340 V94" class="ln-a"/>
<text x="145" y="72" text-anchor="middle">RPO = 40 хв</text>
<text x="275" y="72" text-anchor="middle">RTO = 30 хв</text>
<text x="145" y="54" class="s" text-anchor="middle">дані, яких немає</text>
<text x="275" y="54" class="s" text-anchor="middle">сайт не працює</text>
<circle cx="80" cy="110" r="8" class="f-sto"/>
<circle cx="210" cy="110" r="8" class="f-sec"/>
<circle cx="340" cy="110" r="8" class="f-cmp"/>
<text x="80" y="140" text-anchor="middle">Остання копія</text>
<text x="210" y="140" text-anchor="middle">Аварія</text>
<text x="340" y="140" text-anchor="middle">Знову працює</text>
<text x="80" y="157" class="s" text-anchor="middle">02:00</text>
<text x="210" y="157" class="s" text-anchor="middle">02:40</text>
<text x="340" y="157" class="s" text-anchor="middle">03:10</text>
<text x="10" y="186" class="s">RPO — скільки даних (за часом) можна втратити.</text>
<text x="10" y="205" class="s">RTO — за скільки часу треба знову запрацювати.</text>
</svg>
<figcaption>Менші RPO і RTO — дорожча архітектура. Тому їх визначає бізнес: скільки коштує година простою і година втрачених замовлень.</figcaption>
</figure>

:::mnemo 🧠 P — Point, T — Time
**RP**O — **Point**: до якої **точки** в минулому відкотимося (втрачені дані). **RT**O — **Time**: скільки **часу** на відновлення (простій). «Бекап раз на добу» → RPO до 24 годин. «Відновлення з бекапу триває 4 години» → RTO близько 4 годин.
:::

## Чотири стратегії DR {#strategies}

<figure class="diagram" data-caption="Чотири стратегії DR: що працює в резервному регіоні">
<div class="tiers">
<div class="tier"><span class="tl">Backup &amp; Restore</span><span>У резерві — лише <b>копії</b>: бекапи, знімки, AMI, шаблони IaC. Після аварії все будується заново.<br><small>RPO: години · RTO: години, до доби · 💲</small></span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Pilot Light</span><span><b>Дані реплікуються постійно</b> (база, S3), а сервери вимкнені або ще не створені — готові AMI і шаблони.<br><small>RPO: секунди–хвилини · RTO: десятки хвилин · 💲💲</small></span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Warm Standby</span><span><b>Повна копія, але зменшена</b>: усі частини працюють на мінімумі й уміють обслужити запит; при аварії — масштабування.<br><small>RPO: секунди · RTO: хвилини · 💲💲💲</small></span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Multi-site active/active</span><span><b>Повна потужність у кількох регіонах</b>, трафік іде в усі одночасно; втрата регіону — майже непомітна.<br><small>RPO: майже 0 · RTO: майже 0 · 💲💲💲💲</small></span></div>
</div>
<figcaption>Що нижче — то менші RPO і RTO, але дорожче. Ключова різниця Pilot Light і Warm Standby: у Pilot Light сервери застосунку не працюють, у Warm Standby — працюють, але в мінімальній кількості.</figcaption>
</figure>

Як вони відновлюються:

- **Backup & Restore:** бекапи й знімки **копіюються в інший регіон** (AWS Backup, копії знімків EBS і RDS, S3 CRR), інфраструктура — **кодом** (CloudFormation). При аварії: розгорнути стек, відновити бази з бекапів, перемкнути DNS. Найдешевше, найдовше.
- **Pilot Light:** «ядро» — дані — живе в резервному регіоні: **Aurora Global Database** чи **cross-region read replica**, **DynamoDB global tables**, **S3 CRR**. При аварії: **promote** бази, запустити сервери (AMI, шаблони, Auto Scaling з 0 до потрібного), **Route 53** перемикає трафік.
- **Warm Standby:** те саме, але застосунок уже працює на мінімумі (наприклад, 1 сервер замість 10). При аварії: збільшити Auto Scaling, promote бази, перемкнути трафік. Можна навіть перевіряти резерв справжнім трафіком.
- **Multi-site active/active:** обидва регіони обслуговують користувачів (**Route 53 latency** чи **geolocation**, **Global Accelerator**), дані — **DynamoDB global tables** (запис у будь-якому регіоні) або **Aurora Global Database** з write forwarding. Найскладніше: потрібно продумати конфлікти записів.

:::calc 🧮 Яку стратегію обрати Хмаринці
Вимоги для замовлень: **RPO ≤ 1 хв, RTO ≤ 30 хв**, бюджет обмежений.
- Backup & Restore: RPO — години (між бекапами), RTO — години. ❌ Не проходить.
- **Pilot Light**: Aurora Global Database дає RPO ≈ 1 с; запуск ECS-сервісів з шаблонів і перемикання DNS — 15–25 хв. ✅ Проходить і коштує лише реплікація бази та сховище.
- Warm Standby: RTO — хвилини, але платимо за постійно працюючий мінімальний застосунок. Зайве для цих вимог.
- Active/active: подвійна вартість і складність. Зайве.
Для **аналітики** (RPO 24 год, RTO 1 доба) — **Backup & Restore**.
:::

## Будівельні блоки multi-region {#building-blocks}

| Що | Як мати копію в іншому регіоні | Орієнтовний RPO |
|---|---|---|
| **S3** | **Cross-Region Replication**; з **RTC** — 99,99% об'єктів за 15 хв | хвилини |
| **DynamoDB** | **Global tables** (active-active); режим multi-Region strong consistency | ~1 с (у MRSC — 0) |
| **Aurora** | **Global Database**: репліка до 10 регіонів, switchover і failover | ~1 с, RTO — хвилини |
| **RDS** | **Cross-region read replica** → promote; або копії знімків | секунди / години |
| **EBS, AMI** | Копіювання знімків і AMI (Data Lifecycle Manager, AWS Backup) | години |
| **EFS** | **EFS replication** | хвилини (цільово 15 хв) |
| **ElastiCache** | **Global Datastore** | < 1 с |
| **Секрети, ключі, образи** | Реплікація Secrets Manager, **KMS multi-Region keys**, реплікація ECR | — |
| **Інфраструктура** | **CloudFormation / StackSets**, однакові шаблони | — |
| **Трафік** | **Route 53 failover + health checks**, **Global Accelerator**, **CloudFront origin failover** | — |

**Amazon Application Recovery Controller (ARC)** допомагає перемикатися керовано: **zonal shift** — одним рухом відвести трафік балансувальників від проблемної AZ, **zonal autoshift** — AWS робить це сам, коли бачить збій у зоні, а **Region switch** (з 2025) — готові плани перемикання застосунку між регіонами.

:::deep 🔬 Глибше: статична стабільність
Під час великої аварії найненадійніше — **створювати нове**: API запуску серверів (control plane) перевантажене всіма клієнтами одночасно. Тому надійні системи **статично стабільні**: потрібна потужність **вже працює** до аварії. Приклад: застосунку потрібно 6 серверів; у трьох AZ тримають по 3 (усього 9, тобто 150%). Якщо одна AZ зникне, дві інші вже мають 6 серверів — нічого не потрібно запускати. Так само перемикання трафіку краще робити через **health checks Route 53** (data plane, що працює завжди), а не редагуванням DNS-записів під час аварії.
:::

## AWS Backup: один сейф для всіх копій {#backup}

**AWS Backup** — централізовані бекапи за **політиками** замість десятка окремих налаштувань у кожному сервісі.

- **Backup plan** — розклад (щогодини, щодня), вікно, **життєвий цикл** (перенесення в холодне сховище, термін зберігання); ресурси додаються **за тегами** (`backup=daily`) — новий сервер з тегом автоматично потрапляє в план.
- **Підтримує:** EC2, EBS, **RDS, Aurora, DynamoDB, EFS, FSx**, **S3**, DocumentDB, Neptune, Redshift, Timestream, томи Storage Gateway, VMware on-premises та інші.
- **Point-in-time recovery** (безперервні бекапи) для RDS, Aurora і S3 — відновлення на будь-яку секунду до 35 днів назад.
- **Копії в інший регіон і інший акаунт** — основа Backup & Restore DR і захисту від компрометації акаунта. **Backup policies** в AWS Organizations — однакові плани для всіх акаунтів.
- **Backup Vault Lock** — сховище **WORM**: у режимі **compliance** після короткого пільгового періоду **ніхто**, навіть root, не може видалити копії чи скоротити термін їх зберігання. Захист від ransomware і зловмисного адміністратора.
- **Logically air-gapped vault** — ізольоване сховище, заблоковане за замовчуванням; ним можна поділитися (через RAM) з окремим акаунтом, щоб відновитися, навіть якщо основний акаунт скомпрометовано.
- **Restore testing** — автоматичні регулярні тести відновлення; **Backup Audit Manager** — звіти для аудиторів.

## AWS Elastic Disaster Recovery {#drs}

**AWS Elastic Disaster Recovery (DRS)** захищає **сервери** — фізичні й віртуальні on-premises, в інших хмарах або EC2 в іншому регіоні:

- агент **постійно реплікує диски на рівні блоків** у дешеву **staging-зону** в AWS (маленькі сервери-реплікатори й недорогі диски);
- **RPO — секунди**, **RTO — хвилини**: при аварії DRS запускає повноцінні сервери з актуальних даних;
- **навчальні запуски** (drills) без впливу на основну систему, а після аварії — **failback** назад.

Це правильна відповідь, коли в питанні **сервери з офісу чи дата-центру**, яким потрібен DR в AWS з RPO в секунди. Для міграції є його «брат» — MGN ([розділ 33](#ch/migration)).

## Перевіряй, а не сподівайся {#testing}

«Бекап, який ніколи не відновлювали, — не бекап». Так само і план DR.

- **AWS Fault Injection Service (FIS)** — керовані **хаос-експерименти**: зупинити сервери, додати мережеву затримку, імітувати **втрату AZ** — і подивитися, чи система справді переживе збій.
- **AWS Resilience Hub** — оцінює застосунок щодо твоїх цілей **RPO/RTO** і радить, що покращити.
- **Game days** — регулярні навчання команди: перемкнутися в DR-регіон за інструкцією (runbook) і повернутися.

## DR Хмаринки {#design}

<figure class="diagram" data-caption="Pilot Light для Хмаринки: Франкфурт працює, Ірландія чекає">
<div class="grid2">
<div class="gcard hl"><b>🇩🇪 eu-central-1 — основний</b>ALB + ECS (6 задач у 3 AZ), Aurora (writer + репліки), DynamoDB, S3, ElastiCache<small>Обслуговує 100% трафіку</small></div>
<div class="gcard"><b>🇮🇪 eu-west-1 — резерв (pilot light)</b><strong>Aurora Global Database</strong> (вторинний кластер), <strong>DynamoDB global table</strong>, <strong>S3 CRR</strong> для фото, копії AWS Backup; ECS-сервіс з 0 задач, шаблони CloudFormation готові<small>Платимо переважно за дані</small></div>
</div>
<div class="tiers" style="margin-top:8px">
<div class="tier"><span class="tl">Аварія</span><span>Health check Route 53 фіксує збій → аларм → runbook: <b>failover</b> Aurora Global Database, ECS 0 → 6 задач, Route 53 <b>failover</b> на ALB в Ірландії. Ціль — 30 хв.</span></div>
<div class="tier"><span class="tl">Ransomware</span><span><b>AWS Backup</b>: щоденні копії всього + PITR для Aurora; копії — в окремий акаунт і регіон, <b>Vault Lock (compliance)</b> на 35 днів.</span></div>
<div class="tier"><span class="tl">Перевірка</span><span>Раз на квартал — <b>game day</b> з перемиканням, раз на місяць — <b>restore testing</b>, експерименти <b>FIS</b> з вимкненням AZ.</span></div>
</div>
<figcaption>Замовлення: RPO ≈ 1 с (Aurora Global Database), RTO ≈ 30 хв. Фото: RPO — хвилини (CRR). Аналітика: Backup & Restore.</figcaption>
</figure>

## Що обрати {#choose}

| Вимога | Рішення |
|---|---|
| Найдешевший DR, RTO/RPO — години | **Backup & Restore** (копії в інший регіон + IaC) |
| RTO — десятки хвилин, мінімум витрат, дані актуальні | **Pilot Light** |
| RTO — хвилини, система вже працює в мінімальному розмірі | **Warm Standby** |
| RTO і RPO майже нуль, користувачі по всьому світу | **Multi-site active/active** |
| Реляційна БД між регіонами з RPO ~1 с | **Aurora Global Database** |
| NoSQL з записом у кількох регіонах | **DynamoDB global tables** |
| Централізовані бекапи багатьох сервісів з копією в інший регіон | **AWS Backup** |
| Бекапи не може видалити ніхто, навіть root | **Backup Vault Lock (compliance mode)** |
| DR для серверів з дата-центру, RPO — секунди | **Elastic Disaster Recovery** |
| Перевірити стійкість контрольованим збоєм | **Fault Injection Service** |
| Швидко відвести трафік від проблемної AZ | **ARC zonal shift** |

:::lab 🧪 Спробуй у справжньому AWS: бекап, копія в інший регіон і відновлення
**Вартість:** центи (крихітна таблиця). **Час:** 30–40 хвилин (більшість — очікування).
1. **CloudShell** (eu-central-1) — таблиця з одним замовленням:
```bash
aws dynamodb create-table --table-name khm-orders \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name khm-orders
aws dynamodb put-item --table-name khm-orders \
  --item '{"id":{"S":"A-1001"},"city":{"S":"Lviv"},"total":{"N":"1250"}}'
```
2. Перемкни консоль на **eu-west-1** → **AWS Backup → Backup vaults → Create backup vault**: назва `khm-dr`. Повернись у **eu-central-1**.
3. **AWS Backup → Protected resources → Create on-demand backup**: тип **DynamoDB**, таблиця `khm-orders`, vault **Default**, IAM role **Default role**. Зачекай статусу **Completed** (Jobs).
4. **Backup vaults → Default** → твоя точка відновлення → **Actions → Copy**: регіон **eu-west-1**, vault `khm-dr`. Зачекай завершення копіювання. (Якщо копіювання для DynamoDB недоступне — **Settings → Advanced features for Amazon DynamoDB backups → Enable**.)
5. У **eu-west-1**: **Backup vaults → khm-dr** → точка відновлення → **Restore**: нова таблиця `khm-orders-restored`. Коли відновиться, у DynamoDB (eu-west-1) відкрий таблицю — замовлення **A-1001** на місці. Ти щойно провів **Backup & Restore DR** в іншому регіоні.
**Прибери за собою:** видали таблицю `khm-orders-restored` (eu-west-1) і `khm-orders` (eu-central-1); видали точки відновлення в обох vault (Backup vaults → vault → Delete); видали vault `khm-dr`.
:::

#### 💡 Запам'ятай

- **HA** (Multi-AZ, автоматично) ≠ **DR** (інший регіон, за планом) ≠ **бекап** (копія в минулому часі). Реплікація повторює і помилки — бекап з історією обов'язковий.
- **RPO** — скільки даних втратимо (назад у часі); **RTO** — скільки простоюємо (вперед).
- **Backup & Restore** (години, 💲) → **Pilot Light** (дані живі, сервери вимкнені; десятки хвилин) → **Warm Standby** (зменшена робоча копія; хвилини) → **Active/active** (майже 0, 💲💲💲💲).
- Блоки: **S3 CRR (RTC 15 хв)**, **DynamoDB global tables**, **Aurora Global Database (RPO ~1 с)**, cross-region read replica, копії знімків/AMI, EFS replication, **Route 53 failover**, Global Accelerator, CloudFormation.
- **AWS Backup:** плани за тегами, копії між регіонами й акаунтами, **Vault Lock (compliance)**, air-gapped vault, restore testing, політики Organizations.
- **Elastic Disaster Recovery** — DR серверів з блоковою реплікацією, RPO секунди, RTO хвилини.
- **FIS** — хаос-експерименти; **Resilience Hub** — оцінка RPO/RTO; **ARC** — zonal shift, Region switch.

#### 🎯 Як питають на іспиті

- Мінімальна вартість DR, RTO і RPO — кілька годин → **Backup & Restore** з копіями в інший регіон
- RTO десятки хвилин, мінімум витрат, база реплікується → **Pilot Light**
- Зменшена повна копія, що працює постійно; RTO хвилини → **Warm Standby**
- Майже нульовий простій і втрати даних → **Multi-site active/active**
- Реляційна база, RPO ~1 с і RTO ~1 хв між регіонами → **Aurora Global Database**
- Централізовані бекапи EC2, RDS, DynamoDB, EFS з копією в інший регіон → **AWS Backup**
- Захист бекапів від видалення навіть адміністратором (ransomware) → **Backup Vault Lock у compliance mode**
- DR для серверів у власному дата-центрі з RPO в секунди → **AWS Elastic Disaster Recovery**
- Автоматичне перемикання DNS на резервний регіон → **Route 53 failover routing + health checks**
- Перевірити, як система переживе втрату AZ → **AWS Fault Injection Service**
- Об'єкти S3 мають з'явитися в іншому регіоні за 15 хвилин з SLA → **S3 CRR з Replication Time Control**

#### ⚠️ Пастки

- **Multi-AZ — не DR**: він не рятує від втрати регіону. **Read replica — не бекап**: вона повторює помилки.
- Pilot Light: сервери **не працюють**; Warm Standby: **працюють**, але в мінімальному розмірі.
- Копії бекапів в **тому самому** акаунті не захищають від компрометації акаунта — копіюй в окремий акаунт.
- Vault Lock **compliance** після пільгового періоду **не можна зняти** — налаштовуй терміни уважно.

## ✅ Перевір себе

:::quiz
? Бізнес погоджується втратити дані максимум за 15 хвилин, а система має запрацювати не пізніше ніж за 2 години після аварії. Які це показники?
+ RPO = 15 хвилин, RTO = 2 години
- RPO = 2 години, RTO = 15 хвилин
- RPO і RTO = 15 хвилин
- RTO = 15 хвилин, SLA = 2 години
= RPO — допустима втрата даних (назад у часі від аварії), RTO — допустимий час простою (вперед від аварії).

? Внутрішній застосунок може простоювати до 24 годин, а втрата даних за 12 годин прийнятна. Потрібен найдешевший захист від втрати регіону. Що обрати?
+ Backup & Restore: регулярні бекапи з копіюванням в інший регіон і шаблони CloudFormation
- Pilot Light з Aurora Global Database
- Warm Standby з мінімальною копією застосунку
- Multi-site active/active
= Великі допустимі RPO і RTO дозволяють найдешевшу стратегію — копії в іншому регіоні і відтворення інфраструктури кодом після аварії.

? Компанії потрібне RTO близько 30 хвилин і RPO в секунди для бази даних за мінімальної вартості. Сервери застосунку в резервному регіоні не повинні працювати постійно. Яка стратегія?
- Backup & Restore
+ Pilot Light
- Warm Standby
- Multi-site active/active
= Pilot Light тримає в резервному регіоні лише постійно репліковані дані, а сервери запускаються при аварії. Warm Standby вимагав би постійно працюючої зменшеної копії застосунку.

? Глобальний застосунок має продовжувати працювати без помітного простою і втрати даних навіть при втраті цілого регіону. Користувачі пишуть дані в різних регіонах. Що обрати?
- Pilot Light з cross-region read replica RDS
+ Active/active у кількох регіонах з DynamoDB global tables і маршрутизацією Route 53 за затримкою
- Warm Standby з щоденними бекапами
- Multi-AZ RDS в одному регіоні
= Active/active з global tables дозволяє запис у кожному регіоні і майже нульові RPO/RTO. Multi-AZ не захищає від втрати регіону.

? Компанія хоче централізовано бекапити EC2, RDS, DynamoDB і EFS у 30 акаунтах, копіювати бекапи в інший регіон і гарантувати, що їх не може видалити ніхто, навіть адміністратор. Що обрати?
+ AWS Backup з backup policies в Organizations, cross-region copy і Backup Vault Lock у compliance mode
- Скрипти Lambda, що створюють знімки в кожному акаунті
- Data Lifecycle Manager для EBS і автоматичні бекапи RDS
- S3 Cross-Region Replication для всіх даних
= AWS Backup централізує бекапи багатьох сервісів, копіює їх між регіонами й акаунтами, а Vault Lock у compliance mode робить їх незмінними.

? Компанія має 200 серверів VMware у власному дата-центрі і хоче DR в AWS з RPO в секунди і RTO в хвилини, платячи мінімум, поки аварії немає. Що обрати?
- AWS Application Migration Service
+ AWS Elastic Disaster Recovery
- AWS Backup з щоденними бекапами VMware
- AWS DataSync
= Elastic Disaster Recovery постійно реплікує диски в дешеву staging-зону і при аварії запускає повноцінні сервери за хвилини. MGN — для міграції, а щоденні бекапи дають RPO в годинах.

? Потрібна реляційна база з реплікацією в інший регіон з RPO близько 1 секунди і відновленням за хвилину. Що обрати?
+ Amazon Aurora Global Database
- Amazon RDS Multi-AZ
- Щоденні знімки RDS, скопійовані в інший регіон
- Amazon DynamoDB global tables
= Aurora Global Database реплікує дані в інші регіони із затримкою близько секунди і підтримує швидкий керований failover. Multi-AZ працює в межах одного регіону, а DynamoDB — не реляційна.

? Які твердження правильні? (Оберіть 2)
+ Реплікація не замінює бекап: видалення даних теж реплікується
+ У Warm Standby застосунок у резервному регіоні вже працює, але в мінімальному розмірі
- Multi-AZ захищає від втрати всього регіону
- Pilot Light має менший RTO, ніж Warm Standby
- Backup Vault Lock у compliance mode може зняти root-користувач
= Репліка повторює і помилки, тож бекапи з історією потрібні завжди. Warm Standby — зменшена робоча копія. Multi-AZ діє в межах регіону, Pilot Light повільніший за Warm Standby, а compliance mode не знімає ніхто.
:::
