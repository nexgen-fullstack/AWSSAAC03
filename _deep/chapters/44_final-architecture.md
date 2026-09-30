---
id: final-architecture
module: Фінал
title: Велика архітектура Хмаринки — усе разом
short: Велика архітектура
emoji: 🏙️
domains: secure, resilient, performance, cost
---
> 🎬 **Історія Хмаринки.** Минув рік. Від сервера в підсобці не лишилося й сліду. Хмаринка продає в Україні, Польщі й Німеччині, у «чорну п'ятницю» приймає **50 000 відвідувачів за годину**, а платіжний партнер проводить аудит безпеки. Олена просить Тараса: «Покажи інвесторам **усю** нашу архітектуру — на одній сторінці, і поясни, чому кожна деталь саме така». Цей розділ — та сама сторінка. Тут немає нових сервісів: лише **зв'язки** між тими, які ти вже знаєш. Саме так мислить архітектор — і саме так побудовані питання іспиту.

> 🖼️ **Образ.** Хмаринка тепер — не підсобка, а **місто**. Регіон — місто, зони доступності — райони з окремими електростанціями. Акаунти — окремі квартали з власною охороною. VPC — огороджені житлові комплекси, CloudFront — мережа кіосків у кожному місті Європи, черги — пошта між відомствами, бази — архіви, CloudWatch — диспетчерська, а резервний регіон — запасне місто, де вже горить світло в ратуші.

## Уся архітектура на одній сторінці {#big-picture}

<figure class="diagram" data-caption="Хмаринка: від покупця до даних — сім шарів">
<div class="tiers">
<div class="tier"><span class="tl">1. Вхід</span><span class="dg-node net">Route 53: khmarynka.ua, failover + health checks</span><span class="dg-node net">CloudFront + OAC</span><span class="dg-node sec">WAF + Shield</span><span class="dg-node sec">Cognito: вхід покупців</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">2. Застосунок</span><span class="dg-node net">ALB у 3 AZ</span><span class="dg-node cmp">ECS на Fargate: web, API, кошик</span><span class="dg-node cmp">Auto Scaling: target tracking</span><span class="dg-node cmp">Lambda: мініатюри фото</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">3. Інтеграція</span><span class="dg-node int">EventBridge: OrderPlaced</span><span class="dg-node int">Step Functions: оплата → склад → рахунок</span><span class="dg-node int">SQS + DLQ</span><span class="dg-node int">SNS: SMS і листи</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">4. Дані</span><span class="dg-node db">Aurora MySQL: Multi-AZ + репліки</span><span class="dg-node db">DynamoDB: кошики</span><span class="dg-node db">ElastiCache: каталог</span><span class="dg-node db">OpenSearch: пошук</span><span class="dg-node sto">S3: фото, Intelligent-Tiering</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">5. Аналітика й AI</span><span class="dg-node ana">Kinesis → Firehose → S3</span><span class="dg-node ana">Glue + Athena</span><span class="dg-node ana">Redshift Serverless</span><span class="dg-node ana">Quick Sight</span><span class="dg-node ana">Rekognition: модерація</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">6. Безпека й керування</span><span class="dg-node sec">Organizations + Control Tower, SCP</span><span class="dg-node sec">Identity Center + MFA</span><span class="dg-node sec">KMS, Secrets Manager, ACM</span><span class="dg-node sec">GuardDuty, Security Hub, Macie</span><span class="dg-node sec">CloudTrail, Config</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">7. Надійність і гроші</span><span class="dg-node cmp">CloudWatch + X-Ray</span><span class="dg-node db">Pilot light в eu-west-1</span><span class="dg-node sto">AWS Backup + Vault Lock</span><span class="dg-node cmp">Savings Plans, Graviton, Fargate Spot</span></div>
</div>
<figcaption>Шари 1–5 — шлях запиту і даних; шари 6–7 пронизують усі інші. Кожен вузол — розділ курсу, і кожен можна пояснити одним реченням «чому саме так».</figcaption>
</figure>

## Мережа й акаунти {#network}

**Акаунти** (Organizations + Control Tower, [розділ 10](#ch/organizations)): `log-archive` і `audit` в OU Security, `network` з Transit Gateway в OU Infrastructure, `shop-prod`, `shop-dev`, `analytics-prod` в OU Workloads, пісочниця Тараса в OU Sandbox. **SCP** забороняють: виходити з організації, вимикати CloudTrail, GuardDuty і Config, працювати поза регіонами `eu-central-1` і `eu-west-1`, користуватися root.

<figure class="diagram" data-caption="VPC shop-prod: три зони, три шари підмереж">
<div class="dg-azs three">
<div class="dg-az"><b>AZ a</b>
<div class="dg-sub pub"><b>Public</b> 10.20.0.0/24<div class="dg-nodes"><span class="dg-node net">ALB</span><span class="dg-node net">NAT GW</span></div></div>
<div class="dg-sub app"><b>Private — застосунок</b> 10.20.10.0/23<div class="dg-nodes"><span class="dg-node cmp">задачі ECS</span></div></div>
<div class="dg-sub db"><b>Private — дані</b> 10.20.20.0/24<div class="dg-nodes"><span class="dg-node db">Aurora writer</span><span class="dg-node db">ElastiCache</span></div></div>
</div>
<div class="dg-az"><b>AZ b</b>
<div class="dg-sub pub"><b>Public</b> 10.20.1.0/24<div class="dg-nodes"><span class="dg-node net">ALB</span><span class="dg-node net">NAT GW</span></div></div>
<div class="dg-sub app"><b>Private — застосунок</b> 10.20.12.0/23<div class="dg-nodes"><span class="dg-node cmp">задачі ECS</span></div></div>
<div class="dg-sub db"><b>Private — дані</b> 10.20.21.0/24<div class="dg-nodes"><span class="dg-node db">Aurora reader</span><span class="dg-node db">репліка кешу</span></div></div>
</div>
<div class="dg-az"><b>AZ c</b>
<div class="dg-sub pub"><b>Public</b> 10.20.2.0/24<div class="dg-nodes"><span class="dg-node net">ALB</span><span class="dg-node net">NAT GW</span></div></div>
<div class="dg-sub app"><b>Private — застосунок</b> 10.20.14.0/23<div class="dg-nodes"><span class="dg-node cmp">задачі ECS</span></div></div>
<div class="dg-sub db"><b>Private — дані</b> 10.20.22.0/24<div class="dg-nodes"><span class="dg-node db">Aurora reader</span><span class="dg-node db">OpenSearch</span></div></div>
</div>
</div>
<figcaption>Security Groups ланцюжком: ALB ← інтернет (443); ECS ← лише SG балансувальника; Aurora і кеш ← лише SG застосунку. Gateway endpoints для S3 і DynamoDB, interface endpoints для ECR, Secrets Manager, CloudWatch. Transit Gateway з'єднує VPC акаунтів і Site-to-Site VPN до складу у Львові.</figcaption>
</figure>

## Шлях одного замовлення {#order-flow}

1. Покупка з Кракова: **Route 53** повертає адресу **CloudFront**; найближча точка присутності віддає з кешу сторінки каталогу й фото (з S3 через **OAC**), а **WAF** відсікає ботів і SQL-ін'єкції.
2. Динамічні запити йдуть на **ALB** → задачі **ECS на Fargate** у трьох AZ. Покупець увійшов через **Cognito** — API перевіряє його токен.
3. Каталог читається з **ElastiCache** (cache-aside); промах — з **репліки Aurora**. Пошук «свічка з корицею» — **OpenSearch**. Кошик — **DynamoDB** (мілісекунди за будь-якого навантаження).
4. «Оформити»: API записує замовлення в **Aurora (writer)** в одній транзакції і публікує подію **OrderPlaced** в **EventBridge**. Покупець одразу бачить «Дякуємо!» — решта відбувається **асинхронно**.
5. **Step Functions** веде процес: оплата через API партнера (вихід через **NAT**) → резерв на складі (повідомлення в **SQS**, яку читає складська програма через **VPN**) → PDF-рахунок (**Lambda** → S3) → **SNS** надсилає SMS. Помилка на будь-якому кроці — повтори, потім компенсація (скасувати резерв, повернути кошти).
6. Кожна подія сайту летить у **Kinesis Data Streams** → **Firehose** → озеро даних у S3 → **Athena** і **Redshift Serverless** → дашборд **Quick Sight** на телефоні Олени оновлюється.
7. Усе це видно в **CloudWatch** (метрики, логи, аларми) і **X-Ray** (траси), а кожен виклик API записано в **CloudTrail**.

## Чому саме так: рішення і альтернативи {#decisions}

| Рішення | Чому | Від чого відмовились і чому |
|---|---|---|
| **ECS на Fargate** | Контейнерний моноліт переїхав без переписування, без серверів для патчів | EC2 — більше адміністрування; EKS — зайва складність для однієї команди; Lambda — довгі запити й сталий трафік |
| **Aurora MySQL** | Сумісність зі старою базою, 6 копій у 3 AZ, репліки, Global Database для DR | RDS MySQL — повільніший failover і менше реплік; DynamoDB — замовленням потрібні транзакції й JOIN |
| **DynamoDB для кошиків** | Мільйони дрібних записів у піки, TTL для старих кошиків | Aurora — саме кошики перевантажували її в «чорну п'ятницю» |
| **EventBridge + Step Functions + SQS** | Сайт не залежить від швидкості складу й оплати; повтори й компенсації без коду | Синхронні виклики — один повільний сервіс валив усе ([розділ 31](#ch/sqs-sns)) |
| **CloudFront + WAF** | Швидкість у Польщі й Німеччині, захист на краю, дешевший трафік | Лише ALB — повільніше для далеких покупців і дорожчий вихід в інтернет |
| **Pilot light в eu-west-1** | RPO ≈ 1 с, RTO ≈ 30 хв за ціною реплікації даних | Active/active — подвійна ціна; Backup & Restore — RTO години |
| **Багато акаунтів** | Ізоляція prod і dev, централізовані журнали, SCP | Один акаунт — стажер у dev міг зачепити prod ([розділ 10](#ch/organizations)) |

## Перевірка за Well-Architected {#wa-review}

| Стовп | Що зроблено в Хмаринці |
|---|---|
| ⚙️ **Операційна досконалість** | Уся інфраструктура — CloudFormation/CDK у git; дашборди й аларми CloudWatch; runbooks для аварій; game days щокварталу |
| 🔐 **Безпека** | Окремі акаунти, SCP, Identity Center з MFA, найменші привілеї; шифрування KMS скрізь, TLS з ACM; секрети в Secrets Manager з ротацією; GuardDuty, Security Hub, Macie, Config; WAF і Shield |
| 🛟 **Надійність** | Три AZ, Auto Scaling, Aurora Multi-AZ; черги між компонентами; AWS Backup з Vault Lock; pilot light в іншому регіоні; FIS-експерименти |
| ⚡ **Ефективність продуктивності** | CloudFront, ElastiCache, DynamoDB для кошиків, OpenSearch для пошуку; Graviton; правильний сервіс під кожен тип даних |
| 💰 **Оптимізація витрат** | Savings Plans на базу, Fargate Spot для фонових задач, gateway endpoints, S3 Intelligent-Tiering, вимкнення dev на ніч, бюджети й Anomaly Detection |
| 🌱 **Сталий розвиток** | Graviton, serverless і автомасштабування (немає простою заліза), життєвий цикл даних, менше зайвих копій |

## Двадцять шаблонів, які варто впізнавати {#patterns}

Більшість питань іспиту — варіації кількох десятків архітектурних шаблонів. Ти вже знаєш їх усі:

| Шаблон | Коли | Сервіси |
|---|---|---|
| Тришаровий вебзастосунок з HA | «Високодоступний сайт з базою» | ALB + ASG у кількох AZ + RDS/Aurora Multi-AZ (+ ElastiCache) |
| Статичний сайт | «Статичний контент по всьому світу, дешево» | S3 + CloudFront (OAC) + Route 53 + ACM |
| Serverless API | «Без серверів, оплата за запити» | API Gateway + Lambda + DynamoDB (+ Cognito) |
| Розв'язування через чергу | «Піки, не втрачати замовлення» | SQS між шарами, Auto Scaling за глибиною черги |
| Fan-out | «Одна подія — кілька незалежних обробників» | SNS → кілька SQS (або EventBridge) |
| Обробка за подією | «Щойно файл завантажено — обробити» | Подія S3 → Lambda / EventBridge |
| Оркестрація процесу | «Кроки, повтори, компенсації, людське схвалення» | Step Functions |
| Сесії без стану | «Сервери масштабуються, користувачі не вилітають» | Сесії в ElastiCache або DynamoDB |
| Кеш для читання | «База перевантажена читанням» | ElastiCache, репліки для читання, DAX для DynamoDB |
| Приватний доступ до сервісів | «Без інтернету, дешевше за NAT» | Gateway / interface endpoints, PrivateLink |
| Мережа багатьох VPC | «Десятки VPC і офіс» | Transit Gateway (+ VPN / Direct Connect) |
| Гібридне сховище | «Офіс працює з файлами, дані в AWS» | Storage Gateway, FSx, DataSync |
| Міграція | «Сервери й бази в AWS з мінімальним простоєм» | MGN, DMS (+ SCT), DataSync |
| Глобальна низька затримка | «Користувачі на всіх континентах» | CloudFront, Global Accelerator, DynamoDB global tables, Aurora Global Database |
| Аналіз логів | «SQL по журналах без серверів» | CloudTrail / Flow Logs → S3 → Athena |
| Потоки в реальному часі | «Кліки, IoT, кілька споживачів» | Kinesis Data Streams → Lambda / Flink; Firehose → S3 |
| Секрети з ротацією | «Не зберігати паролі в коді» | Secrets Manager (+ KMS) |
| Контроль ключів | «Свої ключі, аудит, ротація» | KMS customer managed keys; CloudHSM для окремого HSM |
| DR за RPO/RTO | «Аварія регіону з певними RPO/RTO» | Backup & Restore → Pilot Light → Warm Standby → Active/active |
| Оптимізація витрат | «Найдешевше без втрати надійності» | Правильний розмір, Savings Plans, Spot, lifecycle S3, endpoints |

## Карта курсу для повторення {#map}

| Шар | Розділи |
|---|---|
| Основи й глобальна інфраструктура | [2–6](#ch/it-computers) · [акаунт 7](#ch/account) |
| Безпека й доступ | [IAM 8](#ch/iam) · [ролі 9](#ch/roles) · [організації 10](#ch/organizations) · [шифрування 11](#ch/encryption) · [захист 12](#ch/protection) |
| Мережа | [VPC 13](#ch/vpc) · [безпека VPC 14](#ch/vpc-security) · [зв'язки VPC 15](#ch/vpc-connect) · [гібрид 16](#ch/hybrid-network) · [Route 53 17](#ch/route53) · [край мережі 18](#ch/edge) |
| Обчислення | [EC2 19](#ch/ec2) · [ціни 20](#ch/ec2-pricing) · [диски 21](#ch/ec2-disks) · [ELB 22](#ch/elb) · [Auto Scaling 23](#ch/autoscaling) · [контейнери 24](#ch/containers) · [Lambda 25](#ch/lambda) · [платформи 26](#ch/api-platforms) |
| Сховища | [S3 27](#ch/s3) · [S3 глибше 28](#ch/s3-deep) · [файли 29](#ch/files) · [гібридні сховища 30](#ch/hybrid-storage) |
| Інтеграція й міграція | [SQS/SNS 31](#ch/sqs-sns) · [події 32](#ch/events) · [міграція 33](#ch/migration) |
| Бази даних | [RDS 34](#ch/rds) · [Aurora 35](#ch/aurora) · [DynamoDB 36](#ch/dynamodb) · [кеш і спеціальні 37](#ch/cache-special) |
| Дані й AI | [потоки 38](#ch/streaming) · [аналітика 39](#ch/analytics) · [AI 40](#ch/ai) |
| Експлуатація | [моніторинг 41](#ch/monitoring) · [надійність 42](#ch/resilience) · [гроші 43](#ch/cost) |

:::lab 🧪 Спробуй у справжньому AWS: огляд Well-Architected твоєї архітектури
**Вартість:** безкоштовно. **Час:** 30 хвилин.
1. Спершу **без підглядання**: на аркуші за 10 хвилин намалюй архітектуру Хмаринки — шари, сервіси, стрілки. Порівняй із схемою на початку розділу. Чого не вистачило — туди й повертайся на повторення.
2. **AWS Well-Architected Tool → Define workload**: назва `khmarynka`, регіон eu-central-1, середовище Production.
3. Обери лінзу **AWS Well-Architected Framework** і дай відповіді на перші 3–4 питання стовпа **Reliability** так, ніби це твоя архітектура з цього розділу.
4. Відкрий **Improvement plan**: інструмент покаже ризики (High/Medium risk) і посилання на кращі практики. Саме так проводять огляди архітектури в компаніях.
**Прибери за собою:** можна видалити workload (Workloads → Delete) — він безкоштовний, тож можна й залишити.
:::

#### 💡 Запам'ятай

- Архітектура — це **зв'язки**: вхід (DNS, CDN, WAF) → застосунок (ALB, контейнери, функції) → інтеграція (події, черги, оркестрація) → дані (правильна база під кожен тип даних) → аналітика; безпека, моніторинг, надійність і витрати — наскрізь.
- Кожне рішення має **«чому»** і **відкинуту альтернативу** — так і відповідай на іспиті: спершу вимога, потім сервіс.
- Мережа: **3 AZ × 3 шари підмереж**, SG ланцюжком, endpoints, Transit Gateway.
- Акаунти: окремі prod, dev, log-archive, audit; **SCP** як запобіжники.
- **20 шаблонів** покривають більшість питань — повторюй таблицю, доки не впізнаватимеш шаблон з першого речення питання.

#### 🎯 Як питають на іспиті

- Високодоступний вебзастосунок з базою → **ALB + Auto Scaling у кількох AZ + Aurora/RDS Multi-AZ**
- Користувачі в різних країнах скаржаться на повільне завантаження статичного контенту → **CloudFront**
- Сайт не повинен втрачати замовлення під час піків → **SQS між вебшаром і обробкою**
- Одне замовлення мають обробити кілька незалежних сервісів → **SNS fan-out або EventBridge**
- Багатокроковий процес з повторами й компенсаціями → **Step Functions**
- Сервери масштабуються, а сесії користувачів губляться → **сесії в ElastiCache або DynamoDB**
- Приватний доступ до S3 з приватних підмереж без NAT → **gateway endpoint**
- Централізовані журнали й заборона вимикати аудит у всіх акаунтах → **organization trail + SCP**
- Відновлення після аварії регіону з RTO ~30 хв за мінімальну ціну → **Pilot Light**

#### ⚠️ Пастки

- Не тягни в архітектуру «модні» сервіси без вимоги: якщо питання не просить Kubernetes, EKS рідко найпростіша відповідь.
- «Високодоступний» ≠ «відновлюється після аварії регіону»: Multi-AZ — HA, інший регіон — DR.
- Кожен компонент у **одній** AZ — точка відмови: NAT Gateway, екземпляр бази без Multi-AZ, один сервер.

## ✅ Перевір себе

:::quiz
? Інтернет-магазин працює на одному інстансі EC2 з базою MySQL на тому ж сервері. Потрібно зробити його високодоступним і масштабованим з мінімальними змінами коду. Що обрати?
+ ALB з Auto Scaling group у кількох AZ і Amazon Aurora MySQL (або RDS MySQL Multi-AZ)
- Більший інстанс EC2 з EBS io2
- Два інстанси EC2 в одній AZ з Route 53 simple routing
- Переписати застосунок на Lambda і DynamoDB
= Розділити веб і базу, розмістити вебшар у кількох AZ за балансувальником з автомасштабуванням, а базу — в керованому Multi-AZ сервісі. Більший сервер не прибирає єдину точку відмови, а переписування — не «мінімальні зміни».

? Після переходу на Auto Scaling користувачів інколи «викидає» з облікового запису, коли балансувальник надсилає запит на інший сервер. Як виправити, зберігши масштабованість?
+ Зберігати сесії в Amazon ElastiCache або DynamoDB
- Увімкнути sticky sessions і вимкнути Auto Scaling
- Зберігати сесії на EBS кожного сервера
- Перейти на Network Load Balancer
= Сервери мають бути без стану: сесії в спільному сховищі доступні будь-якому серверу. Sticky sessions лише маскують проблему і ламаються при масштабуванні.

? Під час розпродажів сервіс обробки замовлень не встигає і частина замовлень втрачається. Сайт має приймати замовлення навіть тоді, коли обробка відстає. Що зробити?
+ Додати чергу SQS між сайтом і обробкою, масштабувати обробників за глибиною черги
- Збільшити тип інстансу обробки
- Додати репліки для читання бази
- Використати CloudFront для API замовлень
= Черга приймає замовлення незалежно від швидкості обробки і зберігає їх до обробки; кількість обробників можна масштабувати за кількістю повідомлень.

? Замовлення має незалежно отримати склад, служба листів і аналітика; падіння одного споживача не повинне впливати на інших. Що обрати?
- Один виклик API, що послідовно викликає три сервіси
+ Тему SNS, на яку підписані три окремі черги SQS
- Одну чергу SQS, з якої читають усі три сервіси
- Три записи в DynamoDB
= SNS fan-out доставляє копію кожної події в окрему чергу кожного споживача; вони обробляють незалежно, а черги зберігають повідомлення під час збою споживача. З однієї черги кожне повідомлення отримав би лише один споживач.

? Задачі ECS у приватних підмережах завантажують образи з ECR і читають секрети з Secrets Manager через NAT Gateway. Служба безпеки вимагає, щоб трафік не виходив в інтернет. Що зробити?
+ Створити VPC interface endpoints для ECR, Secrets Manager і CloudWatch Logs та gateway endpoint для S3
- Перемістити задачі в публічні підмережі
- Замінити NAT Gateway на NAT instance
- Додати правило NACL, що забороняє 0.0.0.0/0
= Interface endpoints (PrivateLink) дають приватний доступ до сервісів AWS, а шари образів ECR зберігаються в S3, тому потрібен і gateway endpoint для S3.

? Компанія має 12 акаунтів AWS. Потрібно, щоб журнали API всіх акаунтів збиралися централізовано і жоден адміністратор акаунта не міг вимкнути журналювання. Що зробити?
+ Створити organization trail з доставкою в S3 акаунта log-archive і SCP, що забороняє StopLogging і DeleteTrail
- Увімкнути CloudTrail окремо в кожному акаунті
- Використати AWS Config aggregator
- Налаштувати IAM-політику в management account
= Organization trail збирає події всіх акаунтів, а SCP обмежує навіть адміністраторів акаунтів-учасників. Config фіксує конфігурації, а не виклики API.

? Магазину потрібне відновлення після аварії регіону: втрата даних — не більше кількох секунд, простій — до 30 хвилин, мінімальна вартість. Що обрати?
+ Aurora Global Database і DynamoDB global tables в резервному регіоні, застосунок розгортається з шаблонів при аварії, Route 53 failover
- Щоденні бекапи в інший регіон
- Повноцінна копія всієї системи в другому регіоні з розподілом трафіку 50/50
- Aurora Multi-AZ в основному регіоні
= Це Pilot Light: дані реплікуються постійно (RPO — секунди), а обчислення запускаються лише при аварії (RTO — десятки хвилин). Бекапи дають RPO в годинах, active/active дорожчий, Multi-AZ не захищає від втрати регіону.

? Які рішення зменшать витрати Хмаринки без шкоди для надійності prod? (Оберіть 2)
+ Compute Savings Plan на стабільну базову потужність
+ S3 gateway endpoint замість NAT для трафіку до S3
- Перенести prod-базу з Multi-AZ в одну AZ
- Запускати всі prod-сервіси на Spot без On-Demand
- Вимкнути бекапи Aurora
= Savings Plans знижують ціну стабільного навантаження, а gateway endpoint прибирає плату NAT за трафік до S3. Решта варіантів економить за рахунок надійності.
:::
