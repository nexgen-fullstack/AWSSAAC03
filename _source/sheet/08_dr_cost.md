## 23. Висока доступність і Disaster Recovery

- **RPO** (Recovery Point Objective) — скільки даних можна втратити (час від останньої копії до аварії).
- **RTO** (Recovery Time Objective) — за скільки часу система має знову запрацювати.

### Стратегії DR (від найдешевшої до найдорожчої)

| Стратегія | Що є в резервному регіоні | RPO / RTO | Вартість |
|---|---|---|---|
| **Backup & Restore** | Лише бекапи (snapshots, S3, AWS Backup) | Години | Найнижча |
| **Pilot Light** | Ядро: реплікована БД; сервери вимкнені або є лише AMI | Десятки хвилин | Низька |
| **Warm Standby** | Зменшена, але робоча копія всього стеку; при аварії масштабується | Хвилини | Середня |
| **Multi-site Active-Active** | Повна копія, постійно приймає трафік | Майже нуль | Найвища |

<figure class="diagram" id="fig-dr" data-caption="Стратегії DR: від найдешевшої до найшвидшої">
<div class="dr">
<div class="card"><b>💾 Backup & Restore</b>У DR-регіоні лише бекапи<span class="muted">RPO/RTO: години</span><span class="price">💲</span></div>
<div class="card"><b>🔥 Pilot Light</b>Реплікована БД; сервери вимкнені (готові AMI)<span class="muted">RPO/RTO: десятки хвилин</span><span class="price">💲💲</span></div>
<div class="card"><b>🌡️ Warm Standby</b>Зменшена робоча копія всього стеку<span class="muted">RPO/RTO: хвилини</span><span class="price">💲💲💲</span></div>
<div class="card"><b>🌍 Active-Active</b>Повна копія, постійно обслуговує трафік<span class="muted">RPO/RTO: майже нуль</span><span class="price">💲💲💲💲</span></div>
</div>
<div class="dr-bar"></div>
<div class="dr-legend"><span>дешевше, повільніше відновлення</span><span>дорожче, швидше відновлення</span></div>
<figcaption>Обирай найдешевшу стратегію, яка вкладається в RPO і RTO з питання.</figcaption>
</figure>

### Шаблони

<figure class="diagram" id="fig-3tier" data-caption="Високодоступний веб-застосунок у трьох рівнях">
<div class="tiers">
<div class="tier"><span class="tl">Вхід</span><span class="dg-node net">Route 53 (DNS, failover)</span><span class="dg-node net">CloudFront + WAF + Shield</span><span class="dg-node sto">S3: статика (OAC)</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Балансування</span><span class="dg-node net">Application Load Balancer — публічні підмережі у 2+ AZ</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Застосунок</span><span class="dg-node cmp">EC2 в Auto Scaling — AZ a</span><span class="dg-node cmp">EC2 в Auto Scaling — AZ b</span><small>приватні підмережі, без стану (stateless)</small></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Дані</span><span class="dg-node db">Aurora writer (AZ a)</span><span class="dg-node db">Aurora replica (AZ b)</span><span class="dg-node db">ElastiCache: сесії й кеш</span></div>
<div class="down">↓</div>
<div class="tier"><span class="tl">Бекапи і DR</span><span class="dg-node sto">AWS Backup → інший регіон</span><span class="dg-node db">Aurora Global Database (за потреби)</span></div>
</div>
<figcaption>Немає єдиної точки відмови: кожен рівень щонайменше у двох AZ. Сесії зберігаються не на серверах, тому ASG вільно додає й прибирає інстанси.</figcaption>
</figure>

- **HA в одному регіоні:** ALB + ASG у ≥2 AZ + Multi-AZ БД + stateless-сервери (сесії в ElastiCache/DynamoDB) + статика в S3 + CloudFront.
- **Кілька регіонів:** Route 53 (failover/latency) або Global Accelerator; Aurora Global Database або DynamoDB Global Tables; S3 CRR; копії AMI і snapshots; CloudFormation для відтворення інфраструктури; квоти в DR-регіоні — заздалегідь.
- **AWS Backup** — централізовані плани бекапів для EC2, EBS, RDS, Aurora, DynamoDB, EFS, FSx, S3, Storage Gateway, DocumentDB, Neptune та ін.; **копії між регіонами й акаунтами**; **Backup Vault Lock** (WORM — ніхто не видалить бекапи, захист від ransomware); backup policies в Organizations; Backup Audit Manager.
- **Elastic Disaster Recovery** — постійна реплікація серверів, RPO секунди, RTO хвилини (див. розділ 15).
- **Immutable infrastructure** — не латати «живі» сервери, а замінювати новими з нового AMI (instance refresh, blue/green).
- **Legacy-застосунок без змін коду:** ASG (навіть min = max = 1 для автозаміни), ELB health checks, Multi-AZ RDS, RDS Proxy, EFS для спільних файлів, Route 53 health checks.
- **Стійкий код:** слабке зв'язування (SQS між шарами), повтори з exponential backoff і jitter, ідемпотентність обробки.

#### 🎯 Тригери

- RPO/RTO — години, мінімальна вартість → **Backup & Restore**
- RTO — десятки хвилин; БД реплікується, сервери піднімаються під час аварії → **Pilot Light**
- RTO — хвилини; зменшена копія працює постійно → **Warm Standby**
- RPO і RTO майже нуль, трафік в обох регіонах → **Multi-site Active-Active**
- Централізовані бекапи багатьох сервісів з копією в інший акаунт і регіон → **AWS Backup**
- Бекапи не може видалити навіть адміністратор (ransomware) → **AWS Backup Vault Lock**
- Застосунок на одному EC2 має автоматично відновлюватися після збою → **ASG з min = max = 1 (+ ELB health check)**
- Швидко відтворити всю інфраструктуру в іншому регіоні → **CloudFormation (+ копії AMI)**
- Реляційна БД з RPO ~1 с і RTO < 1 хв між регіонами → **Aurora Global Database**
- NoSQL, запис у кількох регіонах одночасно → **DynamoDB Global Tables**
- Копія об'єктів S3 в іншому регіоні з гарантованим часом → **S3 CRR + Replication Time Control**

#### ⚠️ Пастки

- Multi-AZ захищає від збою AZ, але не від збою всього регіону — для цього потрібен інший регіон.
- Read replica в іншому регіоні — це DR, але failover потребує promote (з можливою втратою останніх змін через асинхронність).

## 24. Оптимізація витрат

### Обчислення

- Правильний розмір (Compute Optimizer), Spot для переривних задач, Savings Plans/RI для постійних, Graviton, serverless для переривчастих навантажень.
- Вимикати dev/test поза робочим часом (EventBridge Scheduler + Lambda або Instance Scheduler).
- ASG замість постійного запасу потужності.

### Сховище

- Lifecycle у S3 (→ IA → Glacier), Intelligent-Tiering для невідомого патерну.
- gp3 замість gp2; видаляти старі snapshots і непідключені EBS-томи.
- EFS Infrequent Access / Archive; стиснення і формат Parquet для аналітики.

### Бази даних

- Aurora Serverless v2 або DynamoDB on-demand — для нерівномірного навантаження; provisioned + резервування — для стабільного.
- Кеш (ElastiCache, DAX) замість дорожчого інстансу; read replicas замість вертикального масштабування.
- 🆕 **Database Savings Plans** — до 35% на RDS, Aurora, DynamoDB та ін.

### Мережа (передача даних)

- Вхідний трафік в AWS — **безкоштовний**.
- Усередині однієї AZ по приватних IP — безкоштовно; **між AZ — платно**; між регіонами — платно; в інтернет — найдорожче.
- **Gateway endpoints** до S3/DynamoDB замість NAT Gateway (NAT бере плату за кожен ГБ).
- **CloudFront** зменшує витрати на вихідний трафік і навантаження на origin.
- NAT Gateway у кожній AZ — дорожче, але HA і без трафіку між AZ; одна NAT на всю VPC — дешевше, але єдина точка відмови (підходить для dev/test).
- Direct Connect — дешевший вихідний трафік для великих обсягів.
- Компоненти, що багато спілкуються, тримай в одній AZ або регіоні (якщо вимоги до HA дозволяють).
- **Transit Gateway vs VPC Peering:** TGW бере плату за кожне вкладення (attachment) і за кожен ГБ обробленого трафіку; peering — лише за трафік між AZ/регіонами. Для кількох VPC з великим трафіком peering дешевший.

### Обчислення: що дешевше

- **Lambda vs EC2:** переривчасте або невелике навантаження — Lambda дешевша; постійне високе 24/7 — EC2 або Fargate із Savings Plans зазвичай дешевші.
- **RDS для dev/test** можна зупиняти до 7 днів (потім інстанс стартує сам) або перейти на Aurora Serverless v2.

### Інструменти

- **AWS Cost Explorer** — аналіз і прогноз витрат, рекомендації RI і Savings Plans.
- **AWS Budgets** — сповіщення при перевищенні бюджету або прогнозу; **Budget Actions** — автоматичні дії (напр., обмежити запуск ресурсів).
- **AWS Cost and Usage Report (CUR)** / Data Exports — найдетальніші дані (кожен ресурс, кожна година) в S3 → Athena / Quick.
- **Cost Anomaly Detection** — ML-сповіщення про аномальні витрати.
- **Cost allocation tags** — розподіл витрат за проєктами і відділами (теги треба **активувати** в Billing).
- **Organizations consolidated billing** — один рахунок, об'ємні знижки, спільні RI/SP.
- **Pricing Calculator** — оцінка вартості майбутньої архітектури.

#### 🎯 Тригери

- Сповіщення, коли прогноз витрат перевищить $1000 → **AWS Budgets**
- Проаналізувати витрати за останні місяці і спрогнозувати наступні → **Cost Explorer**
- Найдетальніші дані про витрати по кожному ресурсу для аналізу в Athena → **Cost and Usage Report**
- Розподілити витрати між відділами або проєктами → **Cost allocation tags** (+ окремі акаунти)
- Автоматично помітити раптовий стрибок витрат → **Cost Anomaly Detection**
- Великий рахунок за NAT через трафік до S3 → **Gateway endpoint для S3**
- Великі витрати на вихідний трафік для статичного контенту → **CloudFront**
- Dev/test-сервери потрібні лише в робочі години → **Зупиняти за розкладом (EventBridge Scheduler + Lambda)**
- Постійні інстанси 24/7 → **Savings Plans / Reserved Instances**
- Невідомий патерн доступу до об'єктів S3 → **S3 Intelligent-Tiering**
- Зменшити трафік між AZ для dev-середовища → **Одна NAT Gateway / ресурси в одній AZ**
- Дві VPC обмінюються великим обсягом даних, потрібне найдешевше з'єднання → **VPC Peering** (не Transit Gateway)
- Постійне високе навантаження 24/7 на Lambda, рахунки ростуть → **EC2 або Fargate + Savings Plans**
- Знайти дані, які варто перевести в дешевші класи S3 → **S3 Storage Class Analysis / Storage Lens**

#### ⚠️ Пастки

- «Найдешевше» на іспиті = найдешевше з тих, що **виконують усі вимоги**. Дешевий варіант без HA програє, якщо в питанні потрібна HA.
- Трафік між AZ платний — навіть усередині однієї VPC.
