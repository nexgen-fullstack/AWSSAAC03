## 10. EC2: інстанси, тарифи, розміщення

### Типи інстансів

- **T / M** — загального призначення (T — burstable, накопичує CPU-кредити).
- **C** — compute optimized: пакетна обробка, кодування відео, HPC, ігрові сервери, ML-інференс на CPU.
- **R / X / z** — memory optimized: in-memory БД і кеші, SAP HANA, аналітика в пам'яті.
- **I / D / H** — storage optimized: дуже високі IOPS на локальних NVMe (OLTP, NoSQL, data warehouse).
- **P / G / Inf / Trn** — прискорювачі (GPU, ML).
- **Graviton** (літера g у назві, напр. m7g) — процесори ARM, помітно краща ціна/продуктивність.
- **Як читати назву:** `m7g.2xlarge` → сімейство **m**, покоління **7**, **g** = Graviton, розмір **2xlarge**. Інші літери: **a** — AMD, **i** — Intel, **d** — локальні NVMe-диски, **n** — посилена мережа.

### Сховище і стан

- **Instance store** — локальні диски хоста: найвищі IOPS, але дані **зникають** при stop, terminate або збої хоста. Для кешу, буферів і тимчасових даних.
- **EBS root** — зберігається при stop.
- **Hibernate** — зберігає RAM на EBS root (том має бути зашифрований) → швидкий старт з «теплим» станом застосунку.
- **AMI** — регіональний образ. Для іншого регіону — **copy AMI**. «Golden AMI» з готовим ПЗ = швидкий старт при масштабуванні.
- **User data** — скрипт при першому запуску. **Instance metadata** — використовуй **IMDSv2** (токени).
- **Status checks:** *system* (проблема хоста AWS → **stop/start** переносить інстанс на інший хост або CloudWatch alarm з дією **recover**) vs *instance* (проблема в ОС → reboot, виправлення).

### Мережа і розміщення

- **Placement groups:**
  - **Cluster** — одна AZ, інстанси поруч: найменша затримка і найвища пропускна між ними (HPC). Ризик: все поруч.
  - **Spread** — кожен інстанс на окремому обладнанні; максимум **7 інстансів на AZ** у групі. Для кількох критичних інстансів.
  - **Partition** — групи стійок (до 7 partitions на AZ), сотні інстансів. Hadoop, Cassandra, Kafka.
- **EFA (Elastic Fabric Adapter)** — для HPC/MPI, обхід ОС, наднизька затримка між вузлами. **ENA** — розширена мережа (до 100+ Gbps).
- **Elastic IP** — статична публічна IPv4 (з 2024 всі публічні IPv4 платні).
- **ENI** — мережевий інтерфейс; його можна перечепити на інший інстанс (failover з тим самим приватним IP).

### Тарифи (purchasing options)

- **On-Demand** — посекундна/погодинна оплата без зобов'язань. Короткі й непередбачувані навантаження.
- **Reserved Instances (RI)** — 1 або 3 роки, до ~72% знижки. **Standard RI** — більша знижка, сімейство змінювати не можна (можна продати на RI Marketplace). **Convertible RI** — можна міняти сімейство/ОС, знижка менша.
- **Savings Plans** — зобов'язання витрачати $/год протягом 1 або 3 років:
  - **Compute Savings Plan** — до ~66%, будь-яке сімейство, регіон, ОС + **Fargate і Lambda**.
  - **EC2 Instance Savings Plan** — до ~72%, конкретне сімейство в конкретному регіоні.
  - 🆕 **Database Savings Plans** (з грудня 2025) — до 35% на RDS, Aurora, DynamoDB, ElastiCache тощо (1 рік).
- **Spot** — до 90% знижки, але AWS може забрати інстанс з **попередженням за 2 хвилини**. Лише для переривних задач: batch, CI/CD, рендеринг, аналітика, stateless-вебсервери за ASG. Spot Fleet / EC2 Fleet, стратегія **price-capacity-optimized**.
- **Dedicated Hosts** — окремий фізичний сервер: видно сокети і ядра → **BYOL-ліцензії** (Windows Server, SQL Server, Oracle), вимоги комплаєнсу.
- **Dedicated Instances** — обладнання не ділиться з іншими клієнтами, але без контролю над хостом.
- **On-Demand Capacity Reservations** — гарантують ємність у конкретній AZ на будь-який термін, без знижки (знижку дають RI/Savings Plans поверх).

#### 🎯 Тригери

- Пакетні задачі, які можна переривати, мінімальна ціна → **Spot Instances**
- Стабільне навантаження 24/7 на 1–3 роки → **Reserved Instances або Savings Plans**
- Знижка + свобода міняти сімейство, регіон або перейти на Fargate/Lambda → **Compute Savings Plan**
- Ліцензії прив'язані до фізичних ядер/сокетів (BYOL) → **Dedicated Hosts**
- Гарантувати ємність в AZ на важливу подію без довгого зобов'язання → **On-Demand Capacity Reservation**
- HPC, мінімальна затримка між вузлами → **Cluster placement group + EFA**
- Кілька критичних інстансів не повинні відмовити разом → **Spread placement group**
- Hadoop/Cassandra/Kafka на сотнях інстансів з ізоляцією стійок → **Partition placement group**
- Найвищі IOPS для тимчасових даних або кешу → **Instance store**
- Швидко відновити застосунок з «теплою» пам'яттю після зупинки → **EC2 Hibernate**
- Інстанс не проходить system status check → **Stop/Start або CloudWatch alarm → recover**
- In-memory застосунок, потрібно багато RAM → **R-сімейство (memory optimized)**
- Кодування відео, наукові розрахунки → **C-сімейство (compute optimized)**
- Швидкий запуск нових інстансів з готовим ПЗ → **Golden AMI**
- Запустити той самий сервер в іншому регіоні → **Copy AMI в інший регіон**

#### ⚠️ Пастки

- Spot не підходить для основної БД і критичних довгих задач без чекпоінтів.
- Instance store не переживає stop. EBS переживає.
- Вертикальне масштабування (більший тип інстансу) потребує зупинки; горизонтальне — додає інстанси через ASG.

## 11. Serverless і контейнери

### AWS Lambda

- До **15 хвилин** на один виклик. Пам'ять **128 MB–10 240 MB** (CPU росте пропорційно пам'яті). `/tmp` — від 512 MB до 10 GB.
- Payload: **6 MB** синхронно (streamed response — до 200 MB), **1 MB** асинхронно. Пакет коду: 50 MB zip / 250 MB розпакований; container image — до 10 GB; до 5 layers.
- **Concurrency:** за замовчуванням 1 000 одночасних виконань на регіон (можна підняти).
  - **Reserved concurrency** — гарантує функції частку і водночас обмежує її (захист БД від перевантаження).
  - **Provisioned concurrency** — заздалегідь прогріті середовища → **немає cold start**.
  - **SnapStart** — швидкий старт для Java, Python, .NET.
- Тригери: API Gateway, ALB, S3 events, SQS, SNS, EventBridge, DynamoDB Streams, Kinesis, Cognito, CloudFront (Lambda@Edge).
- **Lambda у VPC** — доступ до приватних RDS/ElastiCache. Інтернет — тільки через NAT Gateway. Забагато з'єднань до RDS → **RDS Proxy**.
- Асинхронні виклики: повтори, **DLQ** або **Destinations** (успіх/помилка → SQS, SNS, EventBridge, Lambda).
- **Версії й aliases:** alias може ділити трафік між двома версіями (напр., 90/10) для поступового релізу.
- **Lambda + SQS:** visibility timeout черги ставлять щонайменше в 6 разів більшим за timeout функції; невдалі повідомлення — у DLQ.
- Довше 15 хвилин → розбити через Step Functions, або ECS/Fargate, або AWS Batch.

### Amazon API Gateway

- **REST API** — повний функціонал: кешування, API keys + **usage plans**, WAF, валідація запитів. **HTTP API** — дешевше і простіше (JWT-авторизація). **WebSocket API** — двосторонній зв'язок (чати, реальний час).
- Типи endpoint: Edge-optimized (через CloudFront), Regional, **Private** (лише з VPC через interface endpoint).
- **Throttling:** за замовчуванням 10 000 запитів/с на акаунт у регіоні (burst 5 000); usage plans — окремі ліміти для клієнтів; при перевищенні — помилка 429.
- Таймаут інтеграції за замовчуванням **29 с** (для Regional і Private REST API можна збільшити). Payload до 10 MB.
- Авторизація: IAM, **Cognito User Pools**, **Lambda authorizer** (власна логіка перевірки токенів).
- **Stages** (dev, prod) і **canary deployment** — частина трафіку йде на нову версію API.

### Контейнери та інша обчислювальна платформа

- **Amazon ECS** — оркестрація контейнерів від AWS (простіше за Kubernetes).
  - Launch type **EC2** — сам керуєш інстансами (дешевше при стабільному навантаженні, GPU, особливі вимоги).
  - Launch type **Fargate** — serverless, без серверів.
  - Task definition, service, **task IAM role** (права саме для контейнера), ALB з dynamic port mapping.
- **Amazon EKS** — керований **Kubernetes**: коли вже використовують K8s, потрібна портативність або open-source інструменти. Managed node groups, Fargate profiles, EKS Auto Mode.
- **ECS Anywhere / EKS Anywhere / EKS Distro** — запуск на власних серверах on-prem.
- **AWS Fargate** — serverless для контейнерів (ECS і EKS): платиш за vCPU і пам'ять задачі, EC2 не керуєш.
- **Amazon ECR** — приватний реєстр образів: сканування вразливостей, реплікація між регіонами.
- **Elastic Beanstalk** — PaaS: завантажуєш код (Java, .NET, Node.js, Python, PHP, Go, Docker), Beanstalk сам створює EC2, ASG, ELB і моніторинг. Політики розгортання: all at once, rolling, rolling with additional batch, **immutable**, traffic splitting, **blue/green** (swap URL).
- **AWS Batch** — пакетні задачі будь-якої тривалості на EC2, Spot або Fargate; черги й планувальник задач.
- **Serverless Application Repository** — готові serverless-застосунки для швидкого розгортання.

#### 🎯 Тригери

- Задача виконується 40 хвилин → **Не Lambda: AWS Batch, ECS/Fargate або розбити через Step Functions**
- Cold start критичний для API на Lambda → **Provisioned concurrency** (для Java — SnapStart)
- Lambda вичерпує з'єднання до RDS → **RDS Proxy**
- Обмежити кількість одночасних виконань функції → **Reserved concurrency**
- Обробити зображення одразу після завантаження в S3 → **S3 event → Lambda**
- Serverless REST API → **API Gateway + Lambda (+ DynamoDB)**
- Різні ліміти запитів для різних клієнтів API, API keys → **API Gateway usage plans + throttling**
- Двосторонній чат у реальному часі → **API Gateway WebSocket API**
- Власна перевірка токенів доступу до API → **Lambda authorizer**
- Контейнери без керування серверами → **Fargate (ECS або EKS)**
- Компанія вже використовує Kubernetes → **Amazon EKS** (on-prem — EKS Anywhere)
- Розробники хочуть просто задеплоїти веб-застосунок без роботи з інфраструктурою → **Elastic Beanstalk**
- Нова версія з мінімальним ризиком і швидким відкатом → **Blue/green** (Beanstalk swap URL або Route 53 weighted)
- Тисячі пакетних задач з чергами і Spot → **AWS Batch**
- Контейнеру потрібен доступ до S3 → **ECS task IAM role**
- Перенести застосунок у контейнери без переписування коду → **Образ у ECR + ECS/EKS на Fargate**
- Функція має реагувати на нові записи в DynamoDB → **DynamoDB Streams → Lambda**
- Поступово випустити нову версію Lambda на 10% трафіку → **Lambda alias з вагами (weighted alias)**
- Lambda читає SQS, і повідомлення обробляються повторно → **Visibility timeout черги ≥ 6 × timeout функції**

#### ⚠️ Пастки

- Lambda — максимум 15 хвилин. Усе довше — не Lambda.
- Beanstalk не «serverless»: він створює EC2, просто керує ними за тебе.
- Лише зміна пам'яті Lambda збільшує і CPU (окремо CPU не налаштовується).

## 12. Інтеграція і повідомлення: SQS, SNS, EventBridge, Step Functions, MQ

### Amazon SQS

- Керована черга, **pull**-модель: споживачі самі забирають повідомлення. Розв'язує компоненти (decoupling) і згладжує піки (buffer).
- **Standard:** майже необмежена пропускна здатність, **at-least-once** (можливі дублікати), порядок не гарантується.
- **FIFO:** суворий порядок у межах **MessageGroupId**, **exactly-once processing** (дедуплікація за 5 хв), 300 викликів/с (3 000 повідомлень/с з батчами по 10), high-throughput режим — у рази більше. Назва черги закінчується на `.fifo`.
- Повідомлення до **1 MiB** (з серпня 2025; раніше 256 KB). Більші — **Extended Client Library** (до 2 GB через S3).
- Зберігання: від 1 хв до **14 днів** (за замовчуванням 4 дні).
- **Visibility timeout** — поки один споживач обробляє повідомлення, інші його не бачать (30 с за замовчуванням, максимум 12 год). Обробка довша за timeout → повідомлення оброблять двічі → **збільш visibility timeout**.
- **Long polling** (`WaitTimeSeconds` до 20 с) — менше порожніх відповідей, дешевше.
- **Delay queue** — затримати доставку до 15 хв.
- **Dead-letter queue (DLQ)** — «отруйні» повідомлення після N невдалих спроб (`maxReceiveCount`) для аналізу.
- Споживач сам видаляє повідомлення (`DeleteMessage`) після успішної обробки.

### Amazon SNS

- Pub/sub, **push**: одне повідомлення → багато підписників (SQS, Lambda, HTTP/S, email, SMS, мобільні push, Firehose).
- **Fan-out:** SNS topic → кілька SQS-черг, кожна система обробляє незалежно.
- **Message filtering** — підписник отримує лише потрібні повідомлення (filter policy).
- SNS FIFO topic → SQS FIFO (порядок + без дублікатів).
- Повідомлення до 256 KB (🆕 з вересня 2026 можна до 1 MiB через налаштування `MaximumMessageSize`).
- Щоб SNS або S3 могли писати в SQS, потрібна **queue policy** (resource-based), що дозволяє їм `sqs:SendMessage`.

### Схема: подієва архітектура

<figure class="diagram" id="fig-fanout" data-caption="Подієва архітектура: fan-out SNS → SQS з DLQ">
<div class="flow">
<div class="st"><b>📤 Подія</b>Новий файл у S3, замовлення з API, подія EventBridge</div>
<span class="ar">→</span>
<div class="st"><b>📣 SNS topic</b>Fan-out: копія повідомлення кожному підписнику (з фільтрами)</div>
<span class="ar">→</span>
<div class="st lanes"><b>📥 Окрема SQS-черга на кожну задачу</b><span class="dg-node int">SQS «мініатюри» → Lambda</span><span class="dg-node int">SQS «метадані» → Lambda</span><span class="dg-node int">SQS «антивірус» → EC2 в ASG</span><small>Помилки після N спроб → DLQ</small></div>
<span class="ar">→</span>
<div class="st"><b>💾 Результат</b>DynamoDB, S3 або інший сервіс</div>
</div>
<figcaption>Кожен обробник працює у своєму темпі й не заважає іншим. Якщо обробник впав, повідомлення чекають у черзі (до 14 днів), а не губляться. ASG масштабує воркерів за довжиною черги.</figcaption>
</figure>

### Amazon EventBridge

- Шина подій: події від сервісів AWS, власних застосунків і **SaaS-партнерів** (Zendesk, Datadog, Shopify…) → правила з **event pattern** → цілі (Lambda, SQS, Step Functions тощо). Колишні CloudWatch Events.
- **EventBridge Scheduler / cron** — serverless-запуск задач за розкладом.
- Archive & replay, schema registry, cross-account шини, **Pipes** (джерело → фільтр/збагачення → ціль).

### AWS Step Functions

- Оркестрація кроків (state machine): послідовність, розгалуження, паралельність, **retry/catch**, очікування, **людське схвалення** (callback з task token).
- **Standard** — до 1 року, exactly-once, повна історія виконання (довгі бізнес-процеси).
- **Express** — до 5 хвилин, великі обсяги подій, at-least-once, дешевше.
- Прямі інтеграції з сотнями сервісів без Lambda-«клею». Distributed Map — масова паралельна обробка об'єктів S3.

### Amazon MQ і AppFlow

- **Amazon MQ** — керований **ActiveMQ** або **RabbitMQ**. Для міграції наявних застосунків, що використовують стандартні протоколи (**JMS, AMQP, MQTT, STOMP, OpenWire**), без переписування коду. Нові застосунки — SQS/SNS.
- **Amazon AppFlow** — перенесення даних між SaaS (Salesforce, SAP, ServiceNow, Zendesk, Slack) і S3/Redshift без коду, за розкладом або подією.

### Що обрати

| Потреба | Сервіс |
|---|---|
| Черга між компонентами, воркери самі забирають задачі | SQS |
| Одне повідомлення → багато одержувачів (push) | SNS (fan-out → SQS) |
| Маршрутизація подій за вмістом, SaaS-події, розклад | EventBridge |
| Суворий порядок і без дублікатів | SQS FIFO / SNS FIFO |
| Потік даних у реальному часі, кілька споживачів, replay | Kinesis Data Streams |
| Багатокроковий процес з помилками, повторами, схваленням | Step Functions |
| Міграція з on-prem брокера (JMS/AMQP/MQTT) | Amazon MQ |

#### 🎯 Тригери

- Розв'язати компоненти, замовлення не повинні губитися при піках → **SQS**
- Обробка суворо по порядку і без дублікатів (фінансові транзакції) → **SQS FIFO**
- Одне повідомлення мають обробити кілька незалежних систем → **SNS fan-out → кілька SQS**
- Повідомлення обробляються двічі → **Збільшити visibility timeout**
- Повідомлення, які постійно падають з помилкою → **Dead-letter queue**
- Зменшити кількість порожніх ReceiveMessage і витрати → **Long polling**
- Повідомлення більші за 1 MiB → **SQS Extended Client Library + S3**
- Реагувати на подію від SaaS-партнера або маршрутизувати події за правилами → **EventBridge**
- Запускати Lambda щоночі о 2:00 → **EventBridge Scheduler (cron)**
- Багатокроковий процес з повторами і ручним схваленням → **Step Functions (Standard)**
- Мільйони коротких подій на секунду в workflow → **Step Functions Express**
- Мігрувати застосунок на RabbitMQ/ActiveMQ без переписування → **Amazon MQ**
- Регулярно вивантажувати дані з Salesforce у S3 без коду → **Amazon AppFlow**
- Різні підписники мають отримувати лише свої типи повідомлень → **SNS message filtering**

#### ⚠️ Пастки

- SQS не видаляє повідомлення після читання автоматично — споживач викликає `DeleteMessage`.
- SNS не зберігає повідомлення. Для надійної обробки став SQS за SNS.
- SQS Standard може доставити повідомлення двічі і не за порядком.
