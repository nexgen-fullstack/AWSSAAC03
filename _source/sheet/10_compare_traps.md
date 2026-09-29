## 26. «X чи Y?» — найчастіші плутанини {quick}

### Мережа

- **Security Group vs NACL:** SG — інстанс, stateful, лише Allow, посилання на інші SG. NACL — підмережа, stateless, Allow + Deny, правила за номерами.
- **Gateway vs Interface endpoint:** Gateway — лише S3 і DynamoDB, безкоштовно, запис у route table. Interface — майже всі сервіси, ENI з приватним IP, платно, доступний з on-prem.
- **VPC Peering vs Transit Gateway vs PrivateLink:** Peering — 1:1, нетранзитивно, дешево. TGW — хаб на сотні VPC і on-prem, транзитивно. PrivateLink — доступ до одного конкретного сервісу, односторонній, CIDR можуть перетинатися.
- **Site-to-Site VPN vs Direct Connect:** VPN — через інтернет, шифрування IPsec, налаштування за хвилини, дешево. DX — приватний канал, стабільна швидкість, прокладання тижнями, шифрування окремо (VPN поверх DX або MACsec).
- **CloudFront vs Global Accelerator:** CloudFront — кеш HTTP-контенту на edge. Global Accelerator — без кешу, TCP/UDP, 2 статичні IP, швидкий failover між регіонами.
- **ALB vs NLB vs GWLB:** ALB — рівень 7, роутинг HTTP за шляхом і хостом, Lambda як ціль. NLB — рівень 4, TCP/UDP, статичні IP, мільйони запитів/с. GWLB — рівень 3, прогін трафіку через апарати безпеки.
- **Route 53 Geolocation vs Geoproximity vs Latency:** Geolocation — за країною користувача. Geoproximity — за відстанню з можливістю змістити трафік (bias). Latency — до регіону з найменшою затримкою.

### Обчислення

- **Lambda vs Fargate vs EC2 vs Batch:** Lambda — подієві задачі до 15 хв. Fargate — контейнери без серверів, без ліміту часу. EC2 — повний контроль, особливі вимоги (GPU, ліцензії, ОС). Batch — черги пакетних задач будь-якої тривалості.
- **ECS vs EKS:** ECS — простіше, «рідне» для AWS. EKS — Kubernetes (вже є K8s, портативність).
- **Spot vs Reserved vs Savings Plans vs On-Demand:** Spot — до 90%, може перерватися. RI/SP — 1–3 роки, до ~72%, для постійного навантаження. On-Demand — без зобов'язань, найдорожче.
- **Dedicated Host vs Dedicated Instance:** Host — видно фізичний сервер, сокети і ядра (BYOL). Instance — лише ізоляція обладнання.
- **Scheduled vs Predictive vs Target tracking:** Scheduled — відомий час піку. Predictive — ML за історією циклів. Target tracking — тримати метрику на рівні.
- **Elastic Beanstalk vs CloudFormation:** Beanstalk — PaaS для розгортання застосунку. CloudFormation — IaC для будь-якої інфраструктури.

### Сховище

- **S3 vs EBS vs EFS vs FSx vs Instance store:** S3 — об'єкти, необмежено, доступ по HTTP. EBS — блочний диск, одна AZ. EFS — спільні файли NFS для Linux у кількох AZ. FSx — Windows (SMB) / Lustre (HPC) / ONTAP (NFS + SMB + iSCSI) / OpenZFS. Instance store — ефемерний локальний диск.
- **DataSync vs Storage Gateway vs Transfer Family vs Snowball:** DataSync — перенесення мережею. Storage Gateway — постійний гібридний доступ з кешем. Transfer Family — SFTP/FTP для партнерів. Snowball — фізичне офлайн-перенесення.
- **Volume Gateway Cached vs Stored:** Cached — основні дані в S3, кеш локально. Stored — усе локально, бекап в S3.
- **Object Lock Compliance vs Governance:** Compliance — не обійде ніхто, навіть root. Governance — можуть обійти користувачі з окремим дозволом.
- **CloudFront signed URL vs signed cookies vs S3 presigned URL:** signed URL — один файл через CloudFront. Signed cookies — багато файлів через CloudFront. Presigned URL — напряму до одного об'єкта S3.
- **OAC vs OAI:** OAC — сучасний спосіб закрити S3 за CloudFront (підтримує SSE-KMS). OAI — застарілий.

### Бази даних

- **RDS Multi-AZ vs Read Replica:** Multi-AZ — синхронна копія, HA, standby не читається. Read replica — асинхронна, масштабування читання, можна в іншому регіоні.
- **Aurora Global Database vs Cross-Region Read Replica:** Global DB — реплікація сховища < 1 с, RTO < 1 хв. Cross-region replica — логічна, від секунд до хвилин.
- **DAX vs ElastiCache:** DAX — лише для DynamoDB, код майже не змінюється. ElastiCache — для будь-якої БД, логіку кешу пише застосунок.
- **Redis/Valkey vs Memcached:** Redis — реплікація, Multi-AZ, persistence, складні структури. Memcached — простий багатопотоковий кеш без реплікації.
- **Athena vs Redshift vs EMR:** Athena — serverless SQL по S3 для разових запитів. Redshift — сховище даних для важкої регулярної BI-аналітики. EMR — кластери Spark/Hadoop.
- **Enhanced Monitoring vs Performance Insights (RDS):** Enhanced Monitoring — метрики ОС (до 1 с). Performance Insights — які SQL-запити навантажують БД.
- **Kinesis Data Streams vs MSK:** KDS — «рідний» сервіс AWS з shards. MSK — керований Apache Kafka для наявних Kafka-застосунків.

### Інтеграція і потоки

- **SQS vs SNS vs EventBridge vs Kinesis:** SQS — черга, споживачі забирають (pull). SNS — pub/sub, розсилка (push). EventBridge — маршрутизація подій за правилами, SaaS, розклад. Kinesis — потоки даних у реальному часі з replay.
- **Kinesis Data Streams vs Firehose:** KDS — реальний час, свої споживачі, replay. Firehose — near real-time доставка в сховища без коду.
- **SQS Standard vs FIFO:** Standard — максимальна швидкість, можливі дублікати і зміна порядку. FIFO — суворий порядок і обробка рівно один раз.
- **Step Functions Standard vs Express:** Standard — до 1 року, exactly-once, історія. Express — до 5 хв, великі обсяги, дешевше.

### Безпека

- **Secrets Manager vs Parameter Store:** Secrets Manager — автоматична ротація, реплікація між регіонами, платно. Parameter Store — без вбудованої ротації, standard tier безкоштовний.
- **KMS vs CloudHSM:** KMS — керований сервіс, інтеграція з усіма сервісами AWS. CloudHSM — виділений апаратний модуль, повний контроль над ключами, FIPS 140 Level 3.
- **Cognito User Pool vs Identity Pool:** User Pool — вхід користувачів (JWT). Identity Pool — тимчасові AWS-credentials.
- **IAM Identity Center vs Cognito:** Identity Center — співробітники в акаунтах AWS і бізнес-застосунках. Cognito — клієнти твого застосунку.
- **Managed Microsoft AD vs AD Connector vs Simple AD:** Managed AD — справжній AD в AWS з trust. AD Connector — проксі до on-prem AD. Simple AD — дешевий базовий, без trust.
- **CloudTrail vs Config vs CloudWatch:** CloudTrail — хто і коли викликав API. Config — яка була конфігурація і чи відповідає вона правилам. CloudWatch — метрики, логи, аларми.
- **GuardDuty vs Inspector vs Macie vs Detective vs Security Hub:** загрози / вразливості / чутливі дані в S3 / розслідування / єдина панель.
- **WAF vs Shield vs Network Firewall vs Firewall Manager:** WAF — рівень 7 (HTTP). Shield — DDoS. Network Firewall — файрвол рівня VPC. Firewall Manager — централізоване керування всім цим в Organizations.
- **SCP vs Permission boundary vs IAM policy:** SCP — стеля для цілих акаунтів/OU. Permission boundary — стеля для конкретного користувача або ролі. IAM policy — власне надає дозволи.

## 27. Пастки, на яких найчастіше ловлять

#### ⚠️ Найчастіші пастки

- У Security Group **немає Deny**. Заблокувати IP → NACL або WAF.
- Standby в RDS Multi-AZ (DB instance) **не обслуговує читання**.
- Read replicas **асинхронні** — остання частина даних може бути ще не скопійована.
- Gateway endpoint — лише **S3 і DynamoDB** і не працює з on-prem.
- **WAF не ставиться на NLB.**
- SCP не надає дозволів і не діє на management account.
- Lambda — максимум **15 хвилин**.
- EBS прив'язаний до AZ; instance store втрачає дані при зупинці.
- EFS — тільки Linux (NFS); для Windows — FSx for Windows File Server.
- Шифрування існуючих RDS/EBS — лише через копію снапшота.
- Сертифікат ACM для CloudFront — тільки в **us-east-1**.
- CloudWatch не бачить **RAM** і місце на диску без агента.
- IA- і Glacier-класи мають **мінімальний термін оплати** (30 / 90 / 180 днів) і мінімальний розмір об'єкта 128 KB (IA, Glacier Instant Retrieval).
- Aurora Backtrack — лише MySQL.
- SQS Standard може доставити повідомлення **двічі і не за порядком**.
- VPC Peering нетранзитивний і не працює з перетином CIDR.
- Route 53 health checks не бачать приватні ресурси напряму — потрібен CloudWatch alarm.
- Direct Connect **не шифрує** трафік сам по собі.
- Spot може бути перерваний з попередженням лише за 2 хвилини.
- Сервіси «One Zone» (S3 One Zone-IA, Express One Zone, EFS One Zone) не переживуть втрату AZ.
- «Свій скрипт на EC2 / cron» майже завжди програє керованому сервісу.
- Presigned URL працює з правами того, хто його підписав, і не довше, ніж діють його облікові дані.
- Класичний NAT Gateway стоїть у **public** subnet, а маршрут `0.0.0.0/0` на нього прописують у route table **private** subnet.
- Cross-zone load balancing у NLB вимкнений за замовчуванням.
- RDS не вміє автоматично додавати read replicas (Aurora вміє).
- LSI у DynamoDB створюється лише разом з таблицею.
- Трафік між AZ платний, навіть в одній VPC.
- Снапшот, зашифрований **AWS managed key**, не можна віддати іншому акаунту — лише з customer managed key.
- Route 53 alias на S3 website працює, лише якщо ім'я bucket збігається з доменом.
- Lambda + SQS: visibility timeout черги має бути щонайменше в 6 разів більшим за timeout функції.
- Restore RDS зі снапшота або PITR дає **новий** endpoint — застосунок треба переналаштувати.

## 28. Що змінилося у 2024–2026 (нові цифри і назви) {quick}

На іспиті можуть траплятися **старі** цифри й назви — відповідай за логікою питання. Але знай актуальні:

- **S3:** об'єкт до **50 TB** (грудень 2025; раніше 5 TB).
- **SQS:** повідомлення до **1 MiB** (серпень 2025; раніше 256 KB).
- **SNS:** повідомлення до **1 MiB** за налаштуванням (вересень 2026; раніше 256 KB).
- **Lambda:** асинхронний payload **1 MB** (раніше 256 KB).
- **EBS gp3:** до **64 TiB, 80 000 IOPS, 2 000 MiB/s** (вересень 2025; раніше 16 TiB / 16 000 / 1 000).
- **Aurora:** сховище до **256 TiB** (2025); Global Database — до **10** вторинних регіонів (травень 2025; раніше 5); Serverless v2 опускається до **0 ACU** (листопад 2024).
- **DynamoDB Global Tables:** strong consistency між регіонами (червень 2025).
- **Kinesis Data Streams:** записи до **10 MiB** (жовтень 2025; раніше 1 MiB).
- **Site-to-Site VPN:** тунелі до **5 Gbps** (листопад 2025; раніше 1,25 Gbps).
- **Regional NAT Gateway** — один NAT на всю VPC (листопад 2025).
- **Database Savings Plans** — до 35% на бази даних (грудень 2025).
- **Закриті для нових клієнтів:** Snowball Edge, старий сервіс Amazon Glacier (vaults), S3 Object Lambda, Migration Hub, Application Discovery Service (з листопада 2025), FSx File Gateway (з жовтня 2024), S3 Select (з липня 2024). Elastic Transcoder закрито 13.11.2025 (заміна — Elemental MediaConvert). QLDB — кінець підтримки 31.07.2025.
- **Перейменування:** QuickSight → **Amazon Quick**; SageMaker → **SageMaker AI**; Kinesis Data Firehose → **Amazon Data Firehose**; Kinesis Data Analytics → **Managed Service for Apache Flink**.
