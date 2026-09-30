---
id: analytics
module: Дані, аналітика й AI
title: Аналітика — озеро даних, Glue, Athena, Redshift, EMR, Lake Formation, Quick Sight
short: Glue, Athena, Redshift, EMR
emoji: 📊
domains: performance, cost, secure
svc: glue, athena, emr, redshift, quick, lakeformation, dataexchange
---
> 🎬 **Історія Хмаринки.** Марта щомісяця будує звіт «продажі за рік по містах і категоріях» — і щоразу оформлення замовлень на сайті помітно гальмує: важкий запит іде просто в основну базу Aurora. Маркетинг хоче поєднати **події сайту** (їх уже складає в S3 Firehose з [розділу 38](#ch/streaming)) із **замовленнями** і витратами на рекламу. А Олена просить **дашборд на телефоні**: виручка сьогодні, топ-товари, конверсія. Час будувати **аналітику**, окрему від «касового апарата» — OLTP-бази (про OLTP і OLAP — у [розділі 4](#ch/it-data)).

> 🖼️ **Образ.** **Озеро даних (S3)** — величезне дешеве озеро, куди звозять усе як є. **Glue** — бібліотекар: складає каталог «що де лежить» і перепаковує сире в зручні формати. **Athena** — рибалка з вудкою: закидає SQL-запит прямо в озеро і платить за кожен витягнутий кілограм (прочитані байти). **Redshift** — сучасний склад-холодильник: дані заздалегідь розкладені по колонках на полицях, тож важкі щоденні звіти летять. **EMR** — важкий завод, де Spark перемелює терабайти. **Lake Formation** — охорона з перепустками до окремих ділянок озера. **Quick Sight** — вітрина з графіками для керівників.

## Хто що робить в аналітиці {#landscape}

| Роль | Сервіс AWS | Одним рядком |
|---|---|---|
| Озеро даних | **S3** | Дешево, безмежно, будь-які формати; зони raw → clean → curated |
| Каталог і ETL | **AWS Glue** | Опис таблиць (Data Catalog), crawlers, ETL на Spark без серверів |
| SQL по файлах у S3 | **Amazon Athena** | Serverless, платиш за прочитані дані |
| Сховище даних (DWH) | **Amazon Redshift** | Колонкове, MPP, петабайти, BI і важкі регулярні звіти |
| Великі дані на фреймворках | **Amazon EMR** | Spark, Hadoop, Hive, Presto, Flink — кластери або serverless |
| Доступ до даних в озері | **AWS Lake Formation** | Права до баз, таблиць, колонок, рядків; обмін між акаунтами |
| Дашборди | **Amazon Quick Sight** | BI для бізнесу, serverless |
| Пошук і аналіз логів | **OpenSearch** | Повнотекстовий пошук, дашборди — [розділ 37](#ch/cache-special) |
| Потоки | **Kinesis, Firehose, MSK** | Реальний час — [розділ 38](#ch/streaming) |
| Чужі датасети | **AWS Data Exchange** | Купити чи отримати дані постачальників |

## AWS Glue: каталог і ETL без серверів {#glue}

**AWS Glue** — serverless-сервіс інтеграції даних. Три головні частини:

- **Glue Data Catalog** — центральний **каталог метаданих**: бази, таблиці, колонки, типи, партиції, місце в S3. Сумісний з Hive metastore. Його використовують **Athena, Redshift Spectrum, EMR, Lake Formation** — описав таблицю один раз, і всі її бачать.
- **Crawlers** — «павуки», що проходять по S3 (а також по базах через JDBC і DynamoDB), **самі визначають схему** і створюють чи оновлюють таблиці та **нові партиції** в каталозі. Запускаються за розкладом.
- **ETL-задачі (jobs)** — перетворення даних на **Apache Spark** (PySpark, Scala), Python shell або Ray: очистити, об'єднати, **конвертувати CSV/JSON у Parquet**, розкласти по партиціях. Серверів немає — платиш за **DPU-години** роботи. **Glue Studio** — візуальний редактор задач.

Корисні дрібниці, які люблять на іспиті:

- **Job bookmarks** — задача пам'ятає, що вже обробила, і наступного запуску бере **лише нові файли**.
- **Glue Streaming ETL** — безперервна обробка з Kinesis або Kafka.
- **Glue DataBrew** — **візуальна підготовка даних без коду** (понад 250 готових перетворень) для аналітиків.
- **Glue Data Quality** — правила якості даних («сума не від'ємна», «email не порожній»); **виявлення чутливих даних** (PII).
- **Triggers і workflows** — запуск задач за розкладом, подіями або ланцюжком.

## Amazon Athena: SQL прямо по S3 {#athena}

**Amazon Athena** — **serverless інтерактивний SQL** (рушій Trino/Presto) по файлах у S3: CSV, JSON, **Parquet**, **ORC**, Avro, а також таблиці **Apache Iceberg** (з UPDATE, DELETE і «подорожжю в часі»). Таблиці описані в Glue Data Catalog. Нічого не завантажуєш і не запускаєш — пишеш запит і отримуєш відповідь.

- **Ціна:** **$5 за TB прочитаних даних** (мінімум 10 MB на запит), або **provisioned capacity** (оплата за DPU-години) для передбачуваних навантажень.
- **Типові задачі:** разові запити до **журналів у S3** — CloudTrail, VPC Flow Logs, ALB, CloudFront, S3 access logs; дослідження даних в озері.
- **Workgroups** — розділення команд і запитів: окремі налаштування, історія, **ліміти прочитаних даних на запит** для контролю витрат.
- **Federated Query** — SQL до інших джерел через конектори на **Lambda**: DynamoDB, RDS, Redshift, CloudWatch Logs, бази on-premises — і JOIN з даними в S3.
- **Athena for Apache Spark** — інтерактивні Spark-ноутбуки без кластерів.

Оскільки платиш за прочитані байти, головне в Athena — **читати менше**:

<figure class="diagram" data-caption="Чому Parquet і партиції роблять Athena дешевшою">
<svg class="svg-dg" viewBox="0 0 400 400" role="img" aria-label="Запит суми продажів за один день: CSV читає всі клітинки, Parquet з партиціями — лише дві з вісімнадцяти">
<text x="10" y="18" class="h">ЗАПИТ: СУМА ПРОДАЖІВ ЗА 15.09</text>
<rect x="5" y="28" width="390" height="168" rx="12" class="bx"/>
<text x="16" y="50">CSV — по рядках, без партицій</text>
<text x="38" y="72" class="s" text-anchor="middle">id</text>
<text x="86" y="72" class="s" text-anchor="middle">місто</text>
<text x="134" y="72" class="s" text-anchor="middle">день</text>
<text x="182" y="72" class="s" text-anchor="middle">сума</text>
<rect x="16" y="80" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="80" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="80" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="80" width="44" height="13" rx="3" class="f-acc"/>
<rect x="16" y="97" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="97" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="97" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="97" width="44" height="13" rx="3" class="f-acc"/>
<rect x="16" y="114" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="114" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="114" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="114" width="44" height="13" rx="3" class="f-acc"/>
<rect x="16" y="131" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="131" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="131" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="131" width="44" height="13" rx="3" class="f-acc"/>
<rect x="16" y="148" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="148" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="148" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="148" width="44" height="13" rx="3" class="f-acc"/>
<rect x="16" y="165" width="44" height="13" rx="3" class="f-acc"/><rect x="64" y="165" width="44" height="13" rx="3" class="f-acc"/><rect x="112" y="165" width="44" height="13" rx="3" class="f-acc"/><rect x="160" y="165" width="44" height="13" rx="3" class="f-acc"/>
<text x="222" y="100" class="s">Щоб знайти 15.09,</text>
<text x="222" y="118" class="s">читає кожен рядок</text>
<text x="222" y="136" class="s">цілком — усі колонки</text>
<text x="222" y="170">Прочитано: 100%</text>
<rect x="5" y="206" width="390" height="188" rx="12" class="bx"/>
<text x="16" y="228">Parquet — по колонках + партиції</text>
<text x="112" y="250" class="s" text-anchor="middle">id</text>
<text x="160" y="250" class="s" text-anchor="middle">місто</text>
<text x="208" y="250" class="s" text-anchor="middle">сума</text>
<rect x="10" y="256" width="224" height="40" rx="8" class="dash"/>
<text x="18" y="281" class="s">day=14/</text>
<rect x="90" y="262" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="262" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="262" width="44" height="12" rx="3" class="f-mut soft"/>
<rect x="90" y="278" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="278" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="278" width="44" height="12" rx="3" class="f-mut soft"/>
<rect x="10" y="300" width="224" height="40" rx="8" class="dash"/>
<text x="18" y="325" class="s">day=15/</text>
<rect x="90" y="306" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="306" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="306" width="44" height="12" rx="3" class="f-acc"/>
<rect x="90" y="322" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="322" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="322" width="44" height="12" rx="3" class="f-acc"/>
<rect x="10" y="344" width="224" height="40" rx="8" class="dash"/>
<text x="18" y="369" class="s">day=16/</text>
<rect x="90" y="350" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="350" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="350" width="44" height="12" rx="3" class="f-mut soft"/>
<rect x="90" y="366" width="44" height="12" rx="3" class="f-mut soft"/><rect x="138" y="366" width="44" height="12" rx="3" class="f-mut soft"/><rect x="186" y="366" width="44" height="12" rx="3" class="f-mut soft"/>
<text x="248" y="278" class="s">Інші дні — інші</text>
<text x="248" y="296" class="s">папки: пропущено.</text>
<text x="248" y="320" class="s">З потрібної папки —</text>
<text x="248" y="338" class="s">лише колонка «сума»</text>
<text x="248" y="372">Прочитано: ≈ 11%</text>
</svg>
<figcaption>Колонковий формат читає лише потрібні колонки, партиції (папки на кшталт day=15/) відсікають зайві дні, а стиснення зменшує байти ще в кілька разів. На справжніх обсягах різниця — у сотні й тисячі разів.</figcaption>
</figure>

Чотири прийоми, що здешевлюють і пришвидшують Athena:

1. **Колонкові формати Parquet або ORC** — читаються лише потрібні колонки.
2. **Стиснення** (Snappy, ZSTD, GZIP) — менше байтів.
3. **Партиції** (`year=2026/month=09/day=15/`) і фільтр у `WHERE` по них — зайві папки не читаються. Нові партиції додає crawler, команда `MSCK REPAIR TABLE` або **partition projection**.
4. **Менше, але більших файлів** (приблизно від 128 MB) — тисячі дрібних файлів гальмують.

Конвертувати дані можна Glue ETL-задачею, запитом **CTAS** в Athena (`CREATE TABLE AS SELECT` у Parquet), а потоки — одразу в Firehose.

:::calc 🧮 Скільки коштує запит до журналів
Хмаринка тримає **2 TB журналів за рік у CSV**. Запит «помилки за вчора»:
- **CSV без партицій:** Athena читає всі 2 TB → 2 × $5 = **$10 за один запит**.
- **Parquet зі стисненням** (≈ у 4 рази менше): 0,5 TB. **Партиції за днем:** лише 1 день з 365 → ≈ 1,4 GB. **Лише 3 колонки з 20:** ≈ 0,2 GB → **≈ $0,001**.
Та сама відповідь — у **тисячі разів дешевше** і в десятки разів швидше.
:::

:::note 🆕 Новинки, про які варто знати
**Amazon S3 Tables** (з грудня 2024) — таблиці **Apache Iceberg** прямо в S3 (окремий тип — *table buckets*) з автоматичним ущільненням дрібних файлів; запити з Athena, Redshift, EMR. **Zero-ETL** — готові інтеграції, що без власних конвеєрів копіюють дані з **Aurora, RDS і DynamoDB** у **Redshift** майже в реальному часі.
:::

## Amazon Redshift: сховище даних {#redshift}

**Amazon Redshift** — кероване **сховище даних** (data warehouse) для **OLAP**: складні SQL-запити з JOIN і агрегаціями по мільярдах рядків, BI-дашборди, сотні аналітиків. Основа — PostgreSQL-подібний SQL, але всередині все інакше:

- **Колонкове зберігання + стиснення** — запит читає лише потрібні колонки.
- **MPP** (massively parallel processing) — **leader node** приймає запит і складає план, **compute nodes** виконують частини паралельно, кожен над своїм шматком даних.
- **RA3** — вузли з **Redshift Managed Storage**: дані лежать у S3-подібному сховищі, а гарячі — в локальному SSD-кеші, тож **обчислення і сховище масштабуються окремо**.
- **Redshift Serverless** — без кластерів: потужність у **RPU** підлаштовується сама, платиш лише під час роботи запитів. Ідеально для нерегулярних навантажень.

Як дані потрапляють у Redshift:

- **COPY з S3** — найшвидший спосіб: паралельне завантаження з багатьох файлів (а не тисячі окремих INSERT).
- **Amazon Data Firehose** (через S3 + COPY), **streaming ingestion** напряму з Kinesis Data Streams і MSK.
- **Zero-ETL-інтеграції** з Aurora, RDS і DynamoDB — дані з'являються в Redshift за секунди, без власного ETL.
- **AWS DMS** — з інших баз ([розділ 33](#ch/migration)).

Можливості, які впізнаєш у питаннях:

- **Redshift Spectrum** — запити з Redshift **до даних у S3 без завантаження** (зовнішні таблиці з Glue Data Catalog). Гаряче — у Redshift, архів за 5 років — у S3, а JOIN — в одному запиті.
- **Concurrency Scaling** — під час піку одночасних запитів Redshift на льоту додає тимчасову потужність, щоб запити не стояли в черзі.
- **Data sharing** — живий доступ до даних **іншого кластера чи акаунта без копіювання**.
- **Materialized views**, **Redshift ML** (моделі SageMaker AI через SQL), **керування навантаженням (WLM)** — черги й пріоритети запитів.

Надійність і безпека:

- **Знімки (snapshots)** в S3: автоматичні (інкрементальні, приблизно кожні 8 годин або кожні 5 GB змін на вузол; зберігаються від 1 дня до 35 днів) і ручні (до видалення). **Копіювання знімків в інший регіон** автоматично — основа DR. Відновлення — у **новий** кластер.
- **Multi-AZ** для RA3 — кластер у двох AZ з автоматичним перемиканням.
- Шифрування **KMS**, розміщення у **VPC**, **Enhanced VPC Routing** — трафік COPY і UNLOAD іде через твою VPC (VPC endpoints, flow logs), а не через інтернет.

:::deep 🔬 Глибше: чому Redshift швидкий і як не зробити його повільним
Дані таблиці розкладаються по вузлах за **стилем розподілу** (distribution style): **KEY** — рядки з однаковим ключем на одному вузлі (JOIN без пересилання даних), **ALL** — маленький довідник копіюється на кожен вузол, **EVEN** — рівномірно, **AUTO** — Redshift обирає сам. **Sort key** впорядковує дані на диску, і запит «за останній тиждень» пропускає блоки з іншими датами (zone maps). Погано обраний ключ розподілу змушує вузли пересилати дані одне одному — запит гальмує. Для іспиту SAA досить знати, що Redshift — колонковий MPP для OLAP, а не для тисяч дрібних транзакцій.
:::

## Amazon EMR: Spark і Hadoop {#emr}

**Amazon EMR** — керовані кластери фреймворків великих даних: **Apache Spark, Hadoop, Hive, HBase, Presto/Trino, Flink**. Для задач, де потрібен **контроль над фреймворком** і його налаштуваннями, або для **міграції наявного Hadoop** з on-premises.

- **Вузли:** **primary** (керує кластером), **core** (виконують задачі і **зберігають HDFS**), **task** (**лише обчислення, без даних**).
- **Економія:** **task-вузли на Spot** — якщо AWS забере інстанс, дані не втрачаються. Primary і core — On-Demand або Reserved. **Instance fleets** змішують типи і способи оплати.
- **Сховище:** HDFS на дисках вузлів (зникає з кластером) або **EMRFS — дані в S3**. З S3 можна запускати **тимчасові (transient) кластери**: піднявся, обробив, вимкнувся — платиш лише за години роботи.
- **EMR Serverless** — Spark і Hive без керування кластерами. **EMR on EKS** — Spark у твоєму Kubernetes-кластері.

**Glue чи EMR?** Glue — serverless ETL, мінімум налаштувань. EMR — повний контроль, багато фреймворків, великі довгі задачі, наявний код Hadoop.

## AWS Lake Formation: хто що бачить в озері {#lake-formation}

Коли в озері лежать і замовлення, і телефони покупців, і фінанси, постає питання: **хто що бачить**. IAM і політики S3 працюють на рівні **файлів і префіксів** — вони не вміють «показати таблицю, але без колонки phone». **AWS Lake Formation** вміє:

- **централізовані права** на рівні **бази, таблиці, колонки, рядка і навіть клітинки** — видаються як GRANT у базі даних;
- **LF-Tags** — дозволи за тегами (`confidentiality=pii`), щоб не прописувати права до кожної з сотень таблиць;
- **обмін даними між акаунтами** без копіювання;
- права діють однаково для **Athena, Redshift Spectrum, EMR, Glue і Quick Sight**;
- побудований **поверх Glue Data Catalog**; допомагає швидко наповнити озеро (blueprints для завантаження з баз і журналів).

У Хмаринці маркетинг бачить таблицю `orders` **без** колонок `phone` і `address`, Марта бачить усе, а партнерська агенція в іншому акаунті — лише агреговану вітрину.

## Amazon Quick Sight: дашборди {#quick}

**Amazon Quick Sight** (раніше — **Amazon QuickSight**; з жовтня 2025 — частина набору Amazon Quick Suite, а з 2026 — просто **Amazon Quick**) — serverless **BI**: інтерактивні дашборди й звіти для бізнесу. На іспиті він може називатися QuickSight.

- **Джерела:** Athena, Redshift, RDS/Aurora, S3, OpenSearch, Salesforce та інші.
- **SPICE** — вбудований рушій у пам'яті: дані імпортуються, і дашборди відкриваються миттєво, не навантажуючи джерело.
- **Row-level security** — менеджер Львова бачить лише Львів; **вбудовування** дашбордів у сайт чи застосунок; **ML-інсайти** (аномалії, прогнози) і запитання природною мовою.
- Користувачі й групи самого сервісу (з інтеграцією IAM Identity Center); оплата — за користувачів.

## AWS Data Exchange {#data-exchange}

**AWS Data Exchange** — каталог **сторонніх датасетів**: погода, демографія, фінансові ринки, курси валют. Підписуєшся — і файли надходять у твій S3 (або доступні через API чи Redshift data sharing). Хмаринка підписується на прогноз погоди, щоб порівняти продажі свічок із холодними вечорами.

## Архітектура аналітики Хмаринки {#design}

<figure class="diagram" data-caption="Озеро даних Хмаринки: від сирих подій до дашбордів">
<div class="flow">
<div class="st lanes"><b>1. Джерела</b><span class="dg-node ana">Firehose: події сайту</span><span class="dg-node db">Aurora: замовлення (zero-ETL)</span><span class="dg-node int">AppFlow: реклама й CRM</span></div>
<span class="ar">→</span>
<div class="st"><b>2. 🏞️ S3 — озеро даних</b>raw/ (як прийшло) → clean/ (Parquet, партиції) → curated/ (вітрини). Glue: crawlers і ETL-задачі</div>
<span class="ar">→</span>
<div class="st lanes"><b>3. Запити</b><span class="dg-node ana">Athena: разові SQL по озеру</span><span class="dg-node ana">Redshift Serverless: звіти + Spectrum</span></div>
<span class="ar">→</span>
<div class="st"><b>4. 📊 Quick Sight</b>Дашборди для Олени й Марти, row-level security для менеджерів міст</div>
</div>
<figcaption>Над усім — Glue Data Catalog (що де лежить) і Lake Formation (хто що бачить). Звіт Марти більше не торкається основної бази Aurora.</figcaption>
</figure>

## Що обрати {#choose}

| Потреба | Сервіс |
|---|---|
| Разові SQL-запити до файлів і журналів у S3, без серверів | **Athena** |
| Зменшити вартість запитів Athena | **Parquet/ORC + стиснення + партиції** |
| Важкі регулярні звіти, BI, петабайти структурованих даних | **Redshift** (нерегулярно — **Redshift Serverless**) |
| Запити з Redshift до даних у S3 без завантаження | **Redshift Spectrum** |
| Аналітика даних Aurora/DynamoDB майже в реальному часі без ETL | **Zero-ETL-інтеграція з Redshift** |
| Spark/Hadoop, міграція Hadoop, контроль фреймворку | **EMR** (task-вузли на Spot) |
| ETL без серверів, автоматичне визначення схеми | **Glue** (jobs + crawlers) |
| Обробляти лише нові файли в ETL | **Glue job bookmarks** |
| Аналітики готують дані без коду | **Glue DataBrew** |
| Права до колонок і рядків в озері, обмін між акаунтами | **Lake Formation** |
| Дашборди для бізнесу | **Quick Sight** |
| SQL-запит одночасно до DynamoDB, RDS і S3 | **Athena Federated Query** |
| Датасети сторонніх постачальників | **Data Exchange** |

:::lab 🧪 Спробуй у справжньому AWS: Athena, CSV → Parquet і різниця в байтах
**Вартість:** менше цента (Athena бере мінімум 10 MB на запит — це $0,00005). **Час:** 25 хвилин. Регіон — **eu-central-1**.
1. **CloudShell** — згенеруй 5 000 замовлень і поклади в S3:
```bash
B=khmarynka-lake-$RANDOM; echo $B
aws s3 mb s3://$B --region eu-central-1
python3 - <<'PY' > orders.csv
import random
print("order_id,city,category,amount,day")
cities = ["Lviv", "Kyiv", "Odesa", "Kharkiv", "Dnipro"]
cats = ["candles", "mugs", "textile", "toys"]
for i in range(1, 5001):
    print(f"{i},{random.choice(cities)},{random.choice(cats)},{random.randint(100, 3000) / 10},2026-09-{random.randint(1, 30):02d}")
PY
aws s3 cp orders.csv s3://$B/raw/orders/orders.csv
```
2. **Athena → Query editor.** Якщо Athena просить місце для результатів — у налаштуваннях вкажи `s3://<твій bucket>/athena-results/` (або обери керовані результати запитів). Виконай по черзі (заміни `BUCKET`):
```sql
CREATE DATABASE khmarynka;

CREATE EXTERNAL TABLE khmarynka.orders (
  order_id int, city string, category string, amount double, day string)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 's3://BUCKET/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT city, round(sum(amount), 2) AS revenue
FROM khmarynka.orders GROUP BY city ORDER BY revenue DESC;
```
3. Перетвори таблицю в Parquet з партиціями за днем (CTAS):
```sql
CREATE TABLE khmarynka.orders_pq
WITH (format = 'PARQUET', write_compression = 'SNAPPY',
      external_location = 's3://BUCKET/clean/orders/',
      partitioned_by = ARRAY['day'])
AS SELECT order_id, city, category, amount, day FROM khmarynka.orders;
```
4. Порівняй **Data scanned** під результатом двох запитів:
```sql
SELECT sum(amount) FROM khmarynka.orders    WHERE day = '2026-09-15';
SELECT sum(amount) FROM khmarynka.orders_pq WHERE day = '2026-09-15';
```
Відповідь однакова, а прочитано в десятки разів менше. Відкрий bucket: у `clean/orders/` — папки `day=2026-09-01/` … `day=2026-09-30/`.
**Прибери за собою:** `DROP TABLE khmarynka.orders_pq; DROP TABLE khmarynka.orders; DROP DATABASE khmarynka;` і в CloudShell `aws s3 rb s3://$B --force`.
:::

#### 💡 Запам'ятай

- **S3** — озеро даних; **Glue Data Catalog** — спільний каталог для Athena, Redshift Spectrum, EMR, Lake Formation; **crawlers** визначають схему і партиції; **Glue jobs** — serverless ETL на Spark; **job bookmarks** — лише нові дані; **DataBrew** — без коду.
- **Athena** — serverless SQL по S3, **$5 за TB прочитаного**; дешевше — **Parquet/ORC, стиснення, партиції, великі файли**; **workgroups** — ліміти й розділення команд; **Federated Query** — інші джерела через Lambda.
- **Redshift** — колонкове **MPP**-сховище для **OLAP**; **RA3** (сховище окремо від обчислень), **Serverless**; **COPY з S3**, **zero-ETL**, streaming ingestion; **Spectrum** — S3 без завантаження; **Concurrency Scaling**; **data sharing**; знімки з **копією в інший регіон**; **Enhanced VPC Routing**.
- **EMR** — Spark/Hadoop; **task-вузли на Spot**; **EMRFS (S3)** і тимчасові кластери; EMR Serverless, EMR on EKS.
- **Lake Formation** — права до **колонок, рядків, клітинок**, **LF-Tags**, обмін між акаунтами. **Quick Sight** — дашборди, **SPICE**, row-level security. **Data Exchange** — сторонні датасети.

#### 🎯 Як питають на іспиті

- SQL по журналах у S3 без серверів, разово → **Athena**
- Зменшити вартість і пришвидшити запити Athena → **Parquet/ORC + стиснення + партиції**
- Складні аналітичні запити, BI, петабайти, стабільна продуктивність → **Redshift**
- Запити з Redshift до архіву в S3 без завантаження → **Redshift Spectrum**
- Аналітика даних Aurora в Redshift майже в реальному часі з мінімумом зусиль → **Aurora zero-ETL integration**
- Hadoop/Spark з on-premises в AWS, дешевше → **EMR, task-вузли на Spot**
- Serverless ETL і автоматичне визначення схеми даних у S3 → **Glue ETL + crawler + Data Catalog**
- ETL щоночі переробляє всі файли, треба лише нові → **Glue job bookmarks**
- Бізнес-аналітики очищають дані візуально без коду → **Glue DataBrew**
- Права до окремих колонок і рядків в озері, обмін між акаунтами → **Lake Formation**
- Дашборди для керівників, serverless, оплата за користувачів → **Quick Sight**
- SQL-запит, що поєднує DynamoDB, RDS і S3 → **Athena Federated Query**
- DR для Redshift в іншому регіоні → **автоматичне копіювання знімків у інший регіон**
- COPY/UNLOAD має йти через VPC, а не інтернет → **Enhanced VPC Routing**

#### ⚠️ Пастки

- Redshift — для **OLAP**, не для тисяч дрібних транзакцій (це RDS, Aurora, DynamoDB).
- Athena бере гроші за **прочитані** байти, а не за результат: `SELECT *` без фільтра по партиціях — найдорожчий запит.
- На **Spot** — лише **task**-вузли EMR; primary і core на Spot ризикують кластером і даними HDFS.
- IAM і bucket policies не дають прав на рівні **колонок** таблиці — це Lake Formation.
- QuickSight тепер називається **Amazon Quick Sight** (у складі Amazon Quick), але на іспиті можлива стара назва.

## ✅ Перевір себе

:::quiz
? Команді безпеки потрібно час від часу виконувати SQL-запити до журналів CloudTrail, що зберігаються в S3. Потрібне рішення без серверів і з мінімальними витратами. Що обрати?
+ Amazon Athena з таблицею в Glue Data Catalog
- Amazon Redshift з щоденним завантаженням журналів
- Amazon EMR з постійним кластером Hive
- Amazon RDS for PostgreSQL з імпортом журналів
= Athena виконує SQL прямо по файлах у S3 без інфраструктури і бере гроші лише за прочитані дані — ідеально для нерегулярних запитів до журналів.

? Запити Athena до таблиці з журналами (CSV, 3 TB) майже завжди фільтрують за датою, але дорогі й повільні. Що дасть найбільший ефект?
+ Конвертувати дані в Parquet зі стисненням і партиціювати за датою
- Перенести файли в S3 Glacier Flexible Retrieval
- Створити окремий workgroup для кожного аналітика
- Розбити файли на мільйони дрібних файлів
= Колонковий формат читає лише потрібні колонки, стиснення зменшує байти, партиції відсікають непотрібні дати. Glacier не підходить для прямих запитів, а дрібні файли лише гальмують.

? Відділ BI щодня виконує складні запити з JOIN по кількох терабайтах даних продажів для сотень дашбордів і потребує стабільної продуктивності. Що обрати?
- Amazon Athena
+ Amazon Redshift
- Репліку для читання Amazon RDS
- Amazon DynamoDB
= Redshift — колонкове MPP-сховище даних, створене саме для важких регулярних аналітичних запитів і BI.

? Аналітики працюють у Redshift, але хочуть інколи поєднувати поточні дані з архівом за 5 років, що лежить у S3 у форматі Parquet, без завантаження архіву в кластер. Що використати?
+ Amazon Redshift Spectrum
- Redshift Concurrency Scaling
- AWS Glue DataBrew
- Redshift data sharing
= Redshift Spectrum виконує запити до даних у S3 через зовнішні таблиці (Glue Data Catalog) і дозволяє поєднувати їх з таблицями Redshift в одному запиті.

? Компанія переносить кластер Hadoop/Spark з on-premises і хоче мінімізувати вартість, не ризикуючи даними. Як налаштувати Amazon EMR?
+ Primary і core вузли — On-Demand або Reserved, task-вузли — Spot, дані — в S3 (EMRFS)
- Усі вузли, включно з primary, — на Spot
- Core-вузли на Spot, щоб HDFS був дешевшим
- Замінити EMR на Glue DataBrew
= Task-вузли не зберігають дані, тож їх втрата безпечна — ідеальні для Spot. Primary і core на Spot ризикують кластером і даними HDFS; S3 через EMRFS зберігає дані незалежно від кластера.

? Нічна задача AWS Glue щоразу обробляє всі файли в bucket, хоча нові з'являються лише за останню добу. Як обробляти тільки нові дані?
+ Увімкнути job bookmarks
- Запускати crawler частіше
- Перейти на Athena CTAS
- Збільшити кількість DPU
= Job bookmarks зберігають стан обробки, і наступний запуск бере лише нові дані.

? В озері даних на S3 маркетинг має бачити таблицю замовлень без колонок з телефонами й адресами, а фінансовий відділ — усі колонки. Також потрібно надати доступ іншому акаунту. Яке рішення найпростіше?
+ AWS Lake Formation з правами на рівні колонок
- Окремі копії даних для кожного відділу в різних buckets
- Політики S3 bucket з умовами на префікси
- Окремі workgroups Athena для кожного відділу
= Lake Formation надає централізовані права до баз, таблиць, колонок і рядків для Athena, Redshift Spectrum, EMR і дозволяє ділитися даними між акаунтами. Політики S3 працюють лише на рівні об'єктів і префіксів.

? Компанія хоче аналізувати дані зі своєї бази Aurora MySQL у Redshift майже в реальному часі, не будуючи й не підтримуючи ETL-конвеєри. Що обрати?
- Щогодинний експорт знімків Aurora в S3 і COPY
+ Zero-ETL-інтеграцію Aurora з Amazon Redshift
- AWS Glue job щохвилини
- Реплікацію через Kinesis Data Streams з власним кодом
= Zero-ETL-інтеграція автоматично і безперервно реплікує дані з Aurora в Redshift за секунди, без конвеєрів, які треба будувати й обслуговувати.

? Які дії зменшать вартість запитів Amazon Athena? (Оберіть 2)
+ Зберігати дані в колонковому форматі Parquet або ORC
+ Партиціювати дані і фільтрувати по партиціях у WHERE
- Використовувати SELECT * у всіх запитах
- Зберігати дані в тисячах файлів по кілька КБ
- Перейти на S3 Glacier Deep Archive
= Athena бере гроші за прочитані байти: колонковий формат і партиції зменшують обсяг читання. SELECT * і дрібні файли погіршують ситуацію, а Glacier Deep Archive не доступний для прямих запитів.
:::
