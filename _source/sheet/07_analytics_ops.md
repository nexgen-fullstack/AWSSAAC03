## 20. Аналітика і потоки даних

### Kinesis і Kafka

- **Kinesis Data Streams (KDS)** — потік у **реальному часі** (затримка ~70–200 мс), **власні споживачі** (Lambda, KCL-застосунки, Flink), кілька споживачів читають один потік, **replay**, порядок у межах shard.
  - Зберігання: 24 год за замовчуванням, до **365 днів**.
  - Shard: запис 1 MB/s або 1 000 записів/с, читання 2 MB/s (enhanced fan-out — 2 MB/s окремо кожному споживачу).
  - Режими: **on-demand** (масштабується сам) і provisioned (кількість shards).
  - Запис до 1 MiB (🆕 з жовтня 2025 можна налаштувати до 10 MiB).
  - **Partition key** визначає shard. «Гарячий» shard → розділити його (split), обрати кращий ключ або перейти в on-demand.
- **Amazon Data Firehose** (колишній Kinesis Data Firehose) — **near real-time доставка** (з буферизацією) в **S3, Redshift, OpenSearch, Splunk, HTTP endpoints, Snowflake, Iceberg-таблиці**. Повністю керований, масштабується сам, **трансформація через Lambda**, **конвертація в Parquet/ORC**, стиснення. Replay і зберігання даних немає.
- **Managed Service for Apache Flink** (колишній Kinesis Data Analytics) — обробка потоків у реальному часі: агрегації у вікнах часу, виявлення аномалій (SQL, Java, Python).
- **Kinesis Video Streams** — потокове відео з камер для аналітики і ML (напр., Rekognition Video).
- **Amazon MSK** — керований **Apache Kafka** (для наявних Kafka-застосунків), MSK Serverless, MSK Connect.

### ETL, запити, сховища даних

- **AWS Glue** — serverless **ETL** на Spark; **Data Catalog** (центральні метадані таблиць для Athena, Redshift Spectrum, EMR); **crawlers** (самі визначають схему); **job bookmarks** (обробляти лише нові дані); Glue DataBrew (візуальна підготовка даних без коду); конвертація **CSV → Parquet**.
- **Amazon Athena** — **serverless SQL прямо по файлах у S3**, плата за обсяг сканування (~$5 за TB). Дешевше: формат **Parquet/ORC**, стиснення, **партиціювання**. Аналіз логів (CloudTrail, ALB, VPC Flow Logs, CloudFront). **Federated Query** — SQL до RDS, DynamoDB та інших джерел через конектори. **CTAS** (CREATE TABLE AS SELECT) перетворює CSV у Parquet прямо запитом.
- **Amazon EMR** — керований **Hadoop, Spark, Hive, Presto, HBase** для великих даних. Кластер на EC2 (primary / core / **task-вузли на Spot**), EMR Serverless, EMR on EKS. Коли потрібен контроль над фреймворками або вже є Spark/Hadoop-код.
- **Amazon Redshift** — колонкове **сховище даних** (OLAP, MPP): петабайти, складна аналітика SQL.
  - **Redshift Serverless** — без керування кластером.
  - **Redshift Spectrum** — запити до даних у S3 без завантаження.
  - **Concurrency Scaling** — додаткова потужність у пікові години.
  - **Zero-ETL** з Aurora, RDS і DynamoDB; data sharing.
  - DR — **cross-region snapshot copy**.
  - Найшвидше завантаження даних — команда **COPY** з S3 (паралельно з багатьох файлів).
- **Amazon OpenSearch Service** — повнотекстовий пошук і аналіз логів (аналог ELK), дашборди OpenSearch Dashboards, OpenSearch Serverless.
- **Amazon Quick** (колишній QuickSight) — BI-дашборди для бізнесу: serverless, SPICE (in-memory), ML insights, вбудовування в застосунки, row-level security.
- **AWS Lake Formation** — побудова і **безпека data lake** на S3: централізовані дозволи аж до **колонок, рядків і комірок** для Athena, Redshift Spectrum, EMR, Glue; шерінг між акаунтами.
- **AWS Data Exchange** — підписка на сторонні датасети (фінансові, погодні тощо) з доставкою в S3.

### Схема: data lake і потоки даних

<figure class="diagram" id="fig-datalake" data-caption="Data lake і потоки даних на S3">
<div class="flow">
<div class="st"><b>📡 Джерела</b>Веб і мобільні застосунки, IoT, логи, БД (через DMS), SaaS (через AppFlow)</div>
<span class="ar">→</span>
<div class="st"><b>🚰 Приймання</b><span class="dg-node ana">Kinesis Data Streams</span> реальний час<br><span class="dg-node ana">Data Firehose</span> доставка в S3 (+ Parquet)</div>
<span class="ar">→</span>
<div class="st"><b>🪣 S3 raw</b>Сирі дані як є (CSV, JSON)</div>
<span class="ar">→</span>
<div class="st"><b>🧹 AWS Glue</b>Crawler + Data Catalog (схеми); ETL у Parquet з партиціями → S3 curated</div>
<span class="ar">→</span>
<div class="st"><b>🔎 Запити</b><span class="dg-node ana">Athena</span> <span class="dg-node ana">Redshift Spectrum</span> <span class="dg-node ana">EMR</span></div>
<span class="ar">→</span>
<div class="st"><b>📊 Amazon Quick</b>Дашборди для бізнесу</div>
</div>
<div class="dg-govern">🛡️ <b>Lake Formation</b> — єдині дозволи до баз, таблиць, колонок і рядків для Athena, Redshift Spectrum, EMR і Glue</div>
<figcaption>Реальний час з кількома споживачами і replay → Kinesis Data Streams. Просто складати потік у S3 → Firehose. Разові SQL-запити по S3 → Athena; важка регулярна BI-аналітика → Redshift.</figcaption>
</figure>

#### 🎯 Тригери

- Потік кліків або IoT у реальному часі, кілька застосунків-споживачів, replay → **Kinesis Data Streams**
- Складати потокові дані в S3, Redshift або OpenSearch без коду, near real-time → **Amazon Data Firehose**
- Перетворити потік JSON у Parquet перед збереженням у S3 → **Firehose (конвертація формату)**
- Аналіз потоку у вікнах часу, аномалії в реальному часі → **Managed Service for Apache Flink**
- Наявні Kafka-застосунки → **Amazon MSK**
- SQL-запити по логах або CSV у S3 без серверів → **Athena**
- Знизити вартість запитів Athena → **Parquet + стиснення + партиціювання**
- ETL без серверів, CSV → Parquet, каталог даних → **AWS Glue**
- ETL при кожному запуску має обробляти лише нові файли → **Glue job bookmarks**
- Великі задачі Spark/Hadoop, контроль над кластером, дешево → **EMR (task nodes на Spot)**
- Складна BI-аналітика на петабайтах структурованих даних → **Redshift**
- Запитувати дані в S3 з Redshift без завантаження → **Redshift Spectrum**
- Повнотекстовий пошук по каталогу товарів, аналіз логів → **OpenSearch**
- Інтерактивні дашборди для бізнесу → **Amazon Quick (QuickSight)**
- Детальні права до колонок і рядків у data lake → **Lake Formation**
- Отримувати сторонні датасети від постачальників → **AWS Data Exchange**
- Відео з камер для аналізу ML → **Kinesis Video Streams**
- Один shard Kinesis перевантажений (ProvisionedThroughputExceeded) → **Кращий partition key, split shard або on-demand режим**
- Перетворити CSV у Parquet без окремого ETL-сервісу → **Athena CTAS** (або Glue ETL)
- Швидко завантажити великі обсяги з S3 у Redshift → **Команда COPY**

#### ⚠️ Пастки

- Kinesis Data Streams = реальний час + зберігання + replay. Firehose = доставка near real-time, без replay.
- Athena — разові запити по S3; Redshift — постійне сховище для важкої регулярної аналітики.

## 21. Машинне навчання, AI і фронтенд

- **Amazon Rekognition** — аналіз зображень і відео: об'єкти, обличчя, модерація контенту, текст на фото.
- **Amazon Textract** — витягує текст, **форми і таблиці** зі сканів і PDF (більше, ніж звичайний OCR).
- **Amazon Comprehend** — NLP: тональність (sentiment), сутності, мова, ключові фрази, **PII** в тексті.
- **Amazon Transcribe** — мова → текст (субтитри, записи дзвінків), з приховуванням PII.
- **Amazon Polly** — текст → мова (озвучення).
- **Amazon Translate** — машинний переклад.
- **Amazon Lex** — чат-боти (голос і текст).
- **Amazon SageMaker AI** — побудова, навчання і розгортання **власних** ML-моделей.
- **AWS Amplify** — хостинг і бекенд для веб- і мобільних застосунків (full-stack), CI/CD фронтенду.
- **AWS Device Farm** — тестування застосунків на реальних телефонах, планшетах і браузерах.

#### 🎯 Тригери

- Розпізнати обличчя або об'єкти, модерація фото і відео → **Rekognition**
- Витягнути дані з рахунків, форм і PDF → **Textract**
- Визначити тональність відгуків або знайти PII в тексті → **Comprehend**
- Перетворити записи дзвінків у текст → **Transcribe**
- Озвучити текст → **Polly**
- Перекласти контент на інші мови → **Translate**
- Чат-бот для сайту або кол-центру → **Lex**
- Навчити і розгорнути власну модель → **SageMaker AI**
- Тестувати мобільний застосунок на сотнях реальних пристроїв → **Device Farm**
- Швидко розгорнути фронтенд і бекенд веб/мобільного застосунку → **Amplify**
- Конвеєр «аудіо → текст → переклад → озвучення» → **Transcribe → Translate → Polly**

#### ⚠️ Пастки

- Готові AI-сервіси (Rekognition, Comprehend тощо) не потребують знань ML. SageMaker AI — для **власних** моделей.

## 22. Моніторинг, керування, інфраструктура як код

- **CloudWatch Metrics:** EC2 за замовчуванням — CPU, мережа, диск (instance store), status checks; раз на 5 хв (detailed monitoring — раз на хвилину). **RAM і вільне місце на диску — ні!** → **CloudWatch agent**. Можна власні (custom) метрики.
- **CloudWatch Alarms** → SNS, ASG, дії EC2 (stop, terminate, reboot, **recover**), Systems Manager. **Composite alarms** — комбінація умов (менше хибних тривог).
- **CloudWatch Logs:** збір логів агентом і сервісами; retention налаштовується (за замовчуванням — назавжди); **metric filters** (напр., рахувати ERROR і ставити аларм); **Logs Insights** (запити); **subscription filters** → Lambda, Firehose, Kinesis, OpenSearch у реальному часі; експорт в S3.
- **CloudWatch Synthetics** (canaries — імітація користувача), Container Insights. **Amazon Managed Grafana** і **Managed Service for Prometheus** — дашборди і метрики контейнерів.
- **AWS CloudTrail** — журнал API-викликів: хто, що, коли, звідки.
  - Event history — **90 днів** management events безкоштовно.
  - **Trail** → S3 (довге зберігання) + CloudWatch Logs (аларми). **Organization trail** — усі акаунти.
  - **Data events** (об'єкти S3, виклики Lambda) — вимкнені за замовчуванням, платні.
  - **CloudTrail Insights** — незвична активність. **Log file integrity validation** — доказ, що логи не змінювали. **CloudTrail Lake** — SQL-запити по подіях.
- **AWS Config** — інвентар і **історія конфігурацій** ресурсів, **Config rules** (готові і власні) для compliance, **автоматичне виправлення** через SSM Automation, conformance packs, **aggregator** для багатьох акаунтів і регіонів.
- **AWS X-Ray** — трасування запитів через мікросервіси: де затримка або помилка, service map.
- **EventBridge + CloudTrail** — реагувати на конкретний API-виклик (напр., хтось змінив Security Group) → Lambda або SNS.
- **Anomaly detection alarms** у CloudWatch — аларм, коли метрика виходить за звичний коридор, без ручних порогів.
- **AWS Systems Manager (SSM):**
  - **Session Manager** — shell без SSH і бастіону.
  - **Run Command** — команди на всіх серверах одразу.
  - **Patch Manager** + **Maintenance Windows** — патчі ОС за розкладом.
  - **Parameter Store**, **Automation** (runbooks), State Manager, Inventory.
  - Працює і з on-prem серверами (hybrid activations).
- **AWS CloudFormation** — інфраструктура як код (шаблони YAML/JSON): однакові середовища, відтворення в іншому регіоні (DR). **StackSets** — розгортання в багатьох акаунтах і регіонах. **Change sets** — попередній перегляд змін. **Drift detection** — виявлення ручних змін. DeletionPolicy: Retain / Snapshot.
- **AWS Service Catalog** — каталог затверджених продуктів (шаблонів) для самообслуговування користувачів з обмеженими правами.
- **AWS Trusted Advisor** — рекомендації: вартість, продуктивність, безпека, стійкість, **ліміти сервісів**, операційна досконалість. Повний набір перевірок — з планами підтримки Business і вище.
- **AWS Compute Optimizer** — ML-рекомендації правильного розміру для EC2, ASG, EBS, Lambda, ECS на Fargate, RDS.
- **AWS Health Dashboard** — події AWS, що зачіпають твої ресурси (планове обслуговування, збої) → EventBridge.
- **AWS License Manager** — облік і контроль ліцензій (Microsoft, Oracle, SAP), заборона перевищення лімітів.
- **AWS Well-Architected Tool** — самоперевірка архітектури за 6 стовпами.

#### 🎯 Тригери

- Моніторити використання RAM і диска на EC2 → **CloudWatch agent**
- Сповіщення, коли в логах «ERROR» з'являється частіше за N разів → **Metric filter + CloudWatch alarm → SNS**
- Хто змінив або видалив ресурс і коли → **CloudTrail**
- Журнал усіх API-викликів у всіх акаунтах організації → **Organization trail → S3**
- Хто читає об'єкти в S3-bucket → **CloudTrail data events** (або S3 server access logs)
- Автоматично перевіряти й виправляти невідповідні налаштування → **AWS Config rules + remediation (SSM Automation)**
- Знайти, де виникає затримка між мікросервісами → **X-Ray**
- Патчити сотні серверів за розкладом → **SSM Patch Manager + Maintenance Windows**
- Виконати скрипт на всіх інстансах без SSH → **SSM Run Command**
- Однаково розгорнути інфраструктуру в багатьох акаунтах і регіонах → **CloudFormation StackSets**
- Користувачі мають самі запускати лише затверджені шаблони → **Service Catalog**
- Інстанси завеликі, потрібні рекомендації щодо розміру → **Compute Optimizer**
- Перевірити, чи наближаємося до лімітів сервісів → **Trusted Advisor / Service Quotas**
- Сповіщення про планове обслуговування AWS, що зачепить наші інстанси → **AWS Health Dashboard + EventBridge**
- Автоматично відновити EC2 при збої обладнання → **CloudWatch alarm (StatusCheckFailed_System) → recover**
- Довести, що логи CloudTrail ніхто не змінював → **Log file integrity validation**
- Дашборди метрик Prometheus для EKS без власного сервера → **Managed Service for Prometheus + Managed Grafana**
- Миттєве сповіщення, коли хтось змінює Security Group → **EventBridge rule на подію CloudTrail → SNS / Lambda**

#### ⚠️ Пастки

- CloudTrail ≠ CloudWatch: Trail — аудит API-викликів; Watch — метрики, логи і аларми.
- Метрики пам'яті за замовчуванням немає — тільки через агента.
