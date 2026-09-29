## 16. Бази даних: Amazon RDS

- Керовані реляційні БД: MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Db2. AWS робить патчі, бекапи, Multi-AZ. Доступу до ОС немає (виняток — **RDS Custom** для Oracle і SQL Server).
- **Multi-AZ (DB instance)** — **синхронна** standby-копія в іншій AZ, **автоматичний failover** (зазвичай 60–120 с, той самий DNS-endpoint). **Standby не обслуговує читання** — це для доступності, а не для масштабування.
- **Multi-AZ DB cluster** (MySQL, PostgreSQL) — 1 writer + **2 standby, з яких можна читати**, у 3 AZ; failover зазвичай до 35 с.
- **Read Replicas** — **асинхронні**, до 15 (MySQL, MariaDB, PostgreSQL), в інших AZ і **регіонах**. Для масштабування читання і звітів. Можна **promote** у самостійну БД (DR). Застосунок сам спрямовує читання на endpoint репліки. **Автоскейлінгу реплік у RDS немає** (в Aurora є).
- **Бекапи:** автоматичні (зберігання 1–35 днів, **point-in-time restore** з точністю до секунд, приблизно до останніх 5 хв) і ручні snapshots (живуть, доки не видалиш). Відновлення завжди створює **нову** БД з новим endpoint.
- **RDS Proxy** — пул з'єднань (Lambda, тисячі коротких з'єднань), швидший failover (до 66%), IAM-автентифікація, паролі з Secrets Manager. Код не змінюється — лише endpoint.
- **Storage autoscaling** — диск БД росте автоматично.
- **IAM database authentication** (MySQL, PostgreSQL) — токени замість паролів.
- **RDS Blue/Green Deployments** — безпечне оновлення версії БД з перемиканням менш ніж за хвилину.
- **Enhanced Monitoring** — метрики ОС бази (процеси, пам'ять) з інтервалом до 1 с. **Performance Insights** — які SQL-запити навантажують БД.
- **Зупинка RDS** — інстанс можна зупинити до 7 днів (потім він стартує сам). Економія для dev/test.
- Шифрування — лише при створенні (див. розділ 5).

#### 🎯 Тригери

- Висока доступність БД, автоматичний failover в іншу AZ → **RDS Multi-AZ**
- Багато читань, звіти гальмують основну БД → **Read Replicas** (або кеш ElastiCache)
- Недорогий DR БД в іншому регіоні → **Cross-Region Read Replica (promote при аварії)** або копіювання snapshots
- Lambda вичерпує з'єднання до БД → **RDS Proxy**
- Відновити БД на стан 10 хвилин тому → **Point-in-time restore** (створить нову БД)
- Потрібен доступ до ОС бази (агенти, кастомні патчі) → **RDS Custom** (або БД на EC2)
- Оновити версію БД з мінімальним простоєм і можливістю відкату → **RDS Blue/Green Deployments**
- Не зберігати паролі до БД у коді → **IAM DB authentication або Secrets Manager**
- Потрібні і HA, і читання зі standby → **Multi-AZ DB cluster**
- Потрібні метрики ОС бази (пам'ять процесів) щосекунди → **RDS Enhanced Monitoring**
- Знайти SQL-запити, які найбільше навантажують БД → **Performance Insights**

#### ⚠️ Пастки

- Multi-AZ = доступність (standby не читається). Read replica = масштабування читання (асинхронна, можлива затримка).
- Restore зі snapshot або PITR створює **новий** інстанс з новим endpoint.

## 17. Amazon Aurora

- Сумісна з MySQL і PostgreSQL; за даними AWS — до 5× швидша за MySQL і до 3× за PostgreSQL.
- **6 копій даних у 3 AZ**, сховище росте автоматично до **256 TiB** (з 2025; раніше 128 TiB), самовідновлюється.
- **До 15 Aurora Replicas** на спільному сховищі (затримка реплікації зазвичай < 100 мс). **Автоматичний failover** на репліку (зазвичай до ~30 с), порядок — за failover tiers. **Aurora Auto Scaling** додає і прибирає репліки за навантаженням.

### Endpoints

- **Writer (cluster) endpoint** — на поточний primary для запису (INSERT, UPDATE, DELETE). Після failover перемикається сам.
- **Reader endpoint** — балансує SELECT-запити між репліками.
- **Custom endpoints** — окремі групи реплік під різні навантаження (напр., аналітичні звіти окремо від веб-трафіку, більші інстанси — для звітів).
- **Instance endpoints** — до конкретного інстансу.

### Катастрофостійкість і масштаб

- **Aurora Global Database** — реплікація **на рівні сховища** до **10 вторинних регіонів** (з травня 2025; раніше 5). Затримка зазвичай **< 1 с**, RPO ~1 с, RTO **< 1 хв**. Локальне швидке читання в кожному регіоні; write forwarding.
- **Aurora Cross-Region Read Replica** (Aurora MySQL) — логічна реплікація (binlog) на рівні БД, більша затримка (від секунд до хвилин). Для мінімальних RPO/RTO — Global Database.

### Спеціальні можливості

- **Aurora Serverless v2** — автоматично і миттєво масштабує потужність в **ACU** (1 ACU ≈ 2 GiB RAM + CPU і мережа). З кінця 2024 може опускатися до **0 ACU**: БД «засинає» (auto-pause), платиш лише за сховище, пробудження до ~15 с. Для непередбачуваних або переривчастих навантажень, dev/test. Можна змішувати з provisioned-інстансами в одному кластері.
- **Babelfish for Aurora PostgreSQL** — розуміє **T-SQL** і протокол SQL Server: застосунки з MS SQL Server переходять майже без змін коду.
- **Aurora Machine Learning** — ML-прогнози прямо в SQL-запитах (виклики **SageMaker AI**, **Comprehend**, **Bedrock**) без знань ML.
- **Aurora Backtrack** — «перемотати» кластер назад у часі (до 72 год) без відновлення з бекапу. **Тільки Aurora MySQL.**
- **Aurora Cloning** — швидка copy-on-write копія кластера (тести на свіжих даних без повної копії).
- **Aurora I/O-Optimized** — без плати за I/O; вигідно, коли I/O > ~25% витрат на Aurora.
- **Zero-ETL integration з Redshift** — дані з Aurora майже в реальному часі доступні в Redshift без ETL-пайплайнів.
- **Aurora DSQL** (з 2025) — distributed serverless SQL (PostgreSQL-сумісна), active-active у кількох регіонах.

#### 🎯 Тригери

- Розділити аналітичне навантаження і веб-трафік на різні репліки → **Custom Endpoints**
- Найшвидша реплікація між регіонами, RPO ~1 с, RTO < 1 хв → **Aurora Global Database**
- Міграція з MS SQL Server без переписування T-SQL-коду → **Babelfish for Aurora PostgreSQL**
- ML-прогнози через звичайні SQL-запити без знань ML → **Aurora Machine Learning (SageMaker AI / Comprehend)**
- Непередбачувані сплески навантаження або БД «спить» уночі → **Aurora Serverless v2**
- Випадково видалили дані — швидко повернути стан без відновлення з бекапу → **Aurora Backtrack** (тільки MySQL)
- Швидко створити копію prod-бази для тестів → **Aurora Cloning**
- Автоматично додавати репліки при зростанні читання → **Aurora Auto Scaling**
- Аналітика в Redshift на даних з Aurora без ETL → **Zero-ETL integration**
- Великі витрати на операції I/O в Aurora → **Aurora I/O-Optimized**
- Максимальна доступність реляційної БД з мінімальним адмініструванням → **Amazon Aurora**
- Читання всередині кожного регіону для глобального застосунку → **Aurora Global Database (secondary regions)**

#### ⚠️ Пастки

- Backtrack є лише в Aurora MySQL. Для PostgreSQL — point-in-time restore або клон.
- Global Database — реплікація сховища (швидка). Cross-Region Read Replica — логічна (повільніша).
- Застосунок має писати через writer endpoint, а читати через reader/custom endpoints.

## 18. Amazon DynamoDB

- Serverless NoSQL (key-value і документи): **одноцифрові мілісекунди** на будь-якому масштабі, автоматично в кількох AZ. Елемент — до **400 KB**.
- Ключ: partition key (+ sort key). Індекси: **GSI** — інший partition key, можна додати будь-коли; **LSI** — той самий partition key з іншим sort key, лише під час створення таблиці.
- **Режими ємності:**
  - **On-demand** — плата за запити, без планування (непередбачуваний або новий трафік).
  - **Provisioned** — RCU/WCU + auto scaling (передбачуваний трафік, дешевше; можна reserved capacity).
- Читання: eventually consistent (за замовчуванням, дешевше) або **strongly consistent**. **Transactions** — ACID для кількох елементів.
- **DAX** — кеш у пам'яті перед DynamoDB: **мікросекунди**, сумісний API, код майже не змінюється. Тільки для DynamoDB.
- **Global Tables** — кілька регіонів, **multi-active** (запис у будь-якому регіоні). Eventual consistency або 🆕 (з 2025) **strong consistency між регіонами (RPO = 0)**.
- **DynamoDB Streams** — потік змін (зберігається 24 год) → Lambda: тригери, агрегації, реплікація. Kinesis Data Streams for DynamoDB — довше зберігання і більше споживачів.
- **TTL** — автоматичне безкоштовне видалення застарілих елементів (сесії, тимчасові дані).
- **Бекапи:** **PITR** до 35 днів з точністю до секунди, on-demand backups, AWS Backup. **Export to S3** без навантаження на таблицю → аналітика в Athena.
- Шифрування за замовчуванням. Доступ з VPC — через gateway endpoint.
- **Standard-IA table class** — дешевше зберігання для таблиць, які рідко читають.

### Розрахунок ємності (RCU / WCU)

- **1 RCU** = 1 strongly consistent читання за секунду елемента до 4 KB, або 2 eventually consistent читання. Транзакційне читання — 2 RCU.
- **1 WCU** = 1 запис за секунду елемента до 1 KB. Транзакційний запис — 2 WCU.
- Розмір округлюється вгору: елемент 10 KB = 3 блоки по 4 KB (читання) і 10 блоків по 1 KB (запис).
- **Приклад:** 100 strongly consistent читань/с по 10 KB → 100 × 3 = **300 RCU** (eventually consistent — **150 RCU**). 100 записів/с по 10 KB → **1 000 WCU**.
- **Partition key** обирай з високою кардинальністю (userId, orderId), щоб навантаження розподілялося. Інакше — «гаряча» партиція і throttling.

#### 🎯 Тригери

- Serverless БД з мілісекундною затримкою для мільйонів запитів, гнучка схема → **DynamoDB**
- Мікросекундне читання з DynamoDB без переписування застосунку → **DAX**
- Непередбачуваний трафік, платити лише за запити → **DynamoDB on-demand**
- Стабільний передбачуваний трафік, дешевше → **Provisioned capacity + auto scaling**
- Глобальний застосунок, запис і читання з низькою затримкою в кількох регіонах → **DynamoDB Global Tables**
- Реагувати на кожну зміну в таблиці (надіслати email, оновити пошук) → **DynamoDB Streams + Lambda**
- Автоматично видаляти сесії через 24 години → **TTL**
- Відновити таблицю на будь-яку секунду за останні 35 днів → **Point-in-time recovery (PITR)**
- SQL-аналітика на даних DynamoDB без навантаження на таблицю → **Export to S3 + Athena**
- Кошики, сесії, лідерборди, IoT-дані, профілі гравців → **DynamoDB**
- Потрібні складні JOIN і реляційна модель → **Не DynamoDB → RDS / Aurora**
- Throttling, бо всі запити йдуть в один ключ (напр., поточна дата) → **Partition key з високою кардинальністю (userId) або write sharding**

#### ⚠️ Пастки

- DAX — кеш лише для DynamoDB. Для RDS — ElastiCache.
- LSI створюється тільки разом з таблицею. GSI можна додати будь-коли.
- Елемент DynamoDB — максимум 400 KB. Великі файли → S3, а в таблиці — посилання.

## 19. Кешування та інші бази даних

### Amazon ElastiCache

- Керований кеш у пам'яті: **Redis OSS / Valkey** і **Memcached**. Відповіді за мікросекунди–мілісекунди. Знімає навантаження з БД, зберігає сесії.
- **Redis / Valkey:** реплікація, Multi-AZ з автоматичним failover, persistence і бекапи, складні структури (**sorted sets → лідерборди**), pub/sub. Є serverless-варіант.
- **Memcached:** простий, багатопотоковий, шардування, **без реплікації і без persistence**.
- **Стратегії кешування:**
  - **Lazy loading (cache-aside)** — у кеш потрапляє те, що запитували; дані можуть застаріти → TTL.
  - **Write-through** — запис одночасно в БД і кеш; кеш завжди свіжий, але зберігає й непотрібне.
- Потребує **змін у коді** застосунку (логіка роботи з кешем).

### Інші бази

- **Amazon Redshift** — сховище даних для аналітики (див. розділ 20).
- **Amazon DocumentDB** — документна БД, сумісна з **MongoDB**.
- **Amazon Neptune** — **графова** БД: соцмережі, рекомендації, виявлення шахрайських зв'язків, knowledge graphs.
- **Amazon Keyspaces** — сумісна з **Apache Cassandra** (CQL), serverless.
- **Amazon Timestream** — **часові ряди**: IoT, метрики, телеметрія.
- **Amazon MemoryDB** — Redis/Valkey-сумісна **основна** (не кеш) БД у пам'яті з durability.
- **Amazon QLDB** (ledger) — закритий 31.07.2025, не обирай.

### Яку БД обрати

| Вимога | Сервіс |
|---|---|
| Реляційна, SQL, JOIN, транзакції (OLTP) | RDS / Aurora |
| Максимальна доступність і продуктивність реляційної БД | Aurora |
| Key-value, мілісекунди, будь-який масштаб, serverless | DynamoDB |
| Кеш, сесії, лідерборди | ElastiCache (Redis / Valkey) |
| Аналітика, OLAP, data warehouse, петабайти | Redshift |
| MongoDB-сумісна документна | DocumentDB |
| Графи, зв'язки | Neptune |
| Cassandra | Keyspaces |
| Часові ряди | Timestream |
| Повнотекстовий пошук, аналіз логів | OpenSearch |

#### 🎯 Тригери

- Лідерборд гри в реальному часі → **ElastiCache for Redis/Valkey (sorted sets)**
- Зберігати сесії користувачів для stateless-вебсерверів → **ElastiCache або DynamoDB**
- Зменшити навантаження на RDS для повторюваних запитів → **ElastiCache (lazy loading)**
- Простий багатопотоковий кеш без реплікації → **Memcached**
- Перенести MongoDB-застосунок у керований сервіс → **DocumentDB**
- Соцмережа «друзі друзів» або виявлення шахрайських зв'язків → **Neptune**
- Перенести Cassandra в керований сервіс → **Keyspaces**
- Показники IoT-датчиків з часовими мітками → **Timestream**
- Кеш має пережити збій вузла без втрати даних → **ElastiCache Redis/Valkey з Multi-AZ і реплікацією**

#### ⚠️ Пастки

- ElastiCache потребує змін у коді. Якщо сказано «без змін коду» — дивись на read replicas (RDS) або DAX (DynamoDB).
- Memcached не має реплікації і не зберігає дані на диск.
