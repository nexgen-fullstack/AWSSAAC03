---
id: streaming
module: Дані, аналітика й AI
title: Потоки даних у реальному часі — Kinesis Data Streams, Data Firehose, Flink, MSK
short: Kinesis, Firehose, MSK
emoji: 🌊
domains: performance, resilient, cost
svc: kds, firehose, flink, kvs, msk
---
> 🎬 **Історія Хмаринки.** Маркетинг хоче знати, **що відбувається на сайті прямо зараз**: які товари розглядають, що кладуть у кошик, звідки прийшли покупці. Під час розпродажу це 20 000 подій за секунду. Ще три бажання: показувати «🔥 зараз купують» у реальному часі, ловити ботів, що скуповують товар, за кілька секунд, і складати всі події в сховище для аналітики. Черга SQS тут не підходить: подію має прочитати **кілька** систем, і в **порядку** надходження, а ще — мати змогу **перечитати** вчорашні події після виправлення помилки. Потрібен **потік даних**.

> 🖼️ **Образ.** Черга SQS — стос квитків на кухні: кухар бере квиток, і для інших його вже немає. **Потік (Kinesis)** — стрічка конвеєра з камерою запису: усе, що проїжджає, записується на плівку (зберігається від доби до року), і кожен відділ дивиться запис зі **своєї** позиції — хтось наживо, хтось перемотує на вчора. Стрічка розділена на доріжки (**shards**): що більше доріжок, то більше вантажу за секунду. **Firehose** — автоматичний навантажувач у кінці конвеєра, що складає вантаж у склад пакетами.

## Потік чи черга {#stream-vs-queue}

| | **Черга (SQS)** | **Потік (Kinesis Data Streams, Kafka)** |
|---|---|---|
| Хто отримує повідомлення | **Один** обробник (після обробки — видаляється) | **Багато** споживачів читають ті самі записи незалежно |
| Порядок | Standard — ні, FIFO — в межах групи | **Так**, у межах shard (partition) |
| Зберігання | До 14 днів, до обробки | Від 24 год до **365 днів** (Kinesis), незалежно від читання |
| Повторне читання (replay) | ❌ | ✅ перечитати з будь-якої позиції |
| Типові дані | Задачі: «обробити замовлення» | Події й телеметрія: кліки, журнали, IoT, транзакції |

## Amazon Kinesis Data Streams {#kds}

**Kinesis Data Streams (KDS)** — потік записів у **реальному часі** (затримка — сотні мілісекунд) з власними споживачами.

- **Записи** мають **partition key** — від нього залежить, у який **shard** потрапить запис. Порядок гарантовано **в межах shard**: усі події однієї сесії (однаковий ключ) йдуть по черзі.
- **Shard** — одиниця пропускної здатності: **запис 1 MB/с або 1 000 записів/с**, **читання 2 MB/с** (спільні для всіх споживачів shard).
- **Enhanced fan-out** — кожен споживач отримує **власні 2 MB/с** на shard (push), без конкуренції з іншими.
- **Зберігання:** 24 години за замовчуванням, до **365 днів**.
- **Розмір запису:** до 1 MiB (🆕 з жовтня 2025 можна налаштувати до 10 MiB).
- **Режими ємності:** **on-demand** — потік сам підлаштовується під навантаження (не треба рахувати shards); **provisioned** — задаєш кількість shards (дешевше при стабільному трафіку), збільшуєш **split** (розділити shard), зменшуєш **merge**.
- **Виробники:** SDK (PutRecord/PutRecords), Kinesis Producer Library (пакетування), Kinesis Agent, журнали CloudWatch.
- **Споживачі:** **Lambda**, застосунки на **KCL** (Kinesis Client Library — сама ділить shards між воркерами і зберігає позиції в DynamoDB), **Managed Service for Apache Flink**, **Data Firehose**.

:::calc 🧮 Скільки shards потрібно (provisioned)
Хмаринка пише **6 000 подій/с** по **0,5 KB** = 3 MB/с. І двоє споживачів читають усе.
- Запис за обсягом: 3 MB/с ÷ 1 MB/с = **3 shards**. За кількістю: 6 000 ÷ 1 000 = **6 shards**. Беремо більше — **6**.
- Читання: 2 споживачі × 3 MB/с = 6 MB/с; 6 shards × 2 MB/с = 12 MB/с — вистачає. З enhanced fan-out кожен споживач мав би власні 2 MB/с на shard.
- Не хочеш рахувати і трафік стрибає — **on-demand**.
:::

**«Гарячий» shard** (помилка `ProvisionedThroughputExceededException`, хоча загальне навантаження невелике): partition key з малою кількістю значень гонить усе в один shard. Лікування: **кращий partition key** (з високою кардинальністю), **split** гарячого shard, або **on-demand**.

## Amazon Data Firehose {#firehose}

**Amazon Data Firehose** (колишня назва — Kinesis Data Firehose) — повністю керована **доставка** потокових даних у сховища:

- **куди:** **S3**, **Redshift** (через S3 і команду COPY), **OpenSearch**, **Splunk**, **HTTP-endpoints** (Datadog, New Relic, власні), Snowflake, **таблиці Apache Iceberg**;
- **звідки:** напряму від застосунків (Direct PUT), з **Kinesis Data Streams**, **MSK**, журналів CloudWatch, журналів WAF, EventBridge;
- **буферизація** за розміром (МБ) або часом (секунди) → **near real-time** (секунди–хвилини), а не миттєво;
- **без коду і без серверів**, масштабується сама; платиш за обсяг даних;
- **перетворення** на льоту: функція **Lambda** для кожного запису; **конвертація JSON → Parquet/ORC** (за схемою з Glue Data Catalog); стиснення; **динамічне партиціювання** в S3 (`year=2026/month=09/day=30/`);
- невдалі записи — окремо в S3.

Чого у Firehose **немає**: зберігання для повторного читання (**replay**) і власних споживачів у реальному часі. Для цього — Kinesis Data Streams.

:::mnemo 🧠 Streams чи Firehose?
**Data Streams** — «**реальний час, свої споживачі, replay**» (мілісекунди, код потрібен). **Firehose** — «**просто поклади потік у S3 / Redshift / OpenSearch**, без коду» (секунди–хвилини). Часто їх поєднують: Streams для реального часу, а Firehose як один зі споживачів складає все в озеро даних.
:::

## Обробка потоків: Managed Service for Apache Flink {#flink}

**Amazon Managed Service for Apache Flink** (колишня назва — Kinesis Data Analytics) — обробка потоків **у реальному часі** на Apache Flink (Java, Python, Scala, SQL): агрегації у **вікнах часу** («покупки за останні 5 хвилин за категоріями»), з'єднання потоків, **виявлення аномалій**, збагачення. Джерела — Kinesis і MSK; результати — в інший потік, S3, базу, OpenSearch. Серверів немає — AWS запускає і масштабує Flink.

## Відео й Kafka {#video-kafka}

- **Amazon Kinesis Video Streams** — приймає **відео** з камер і пристроїв, зберігає, дає відтворення і аналіз машинним навчанням (наприклад, Rekognition Video — розпізнавання облич, об'єктів). Також відеозв'язок WebRTC.
- **Amazon MSK** (Managed Streaming for Apache Kafka) — керований **Apache Kafka**: для компаній, що вже мають Kafka-застосунки, екосистему Kafka (конектори, стрім-процесори), особливі вимоги до зберігання. Варіанти: кластери з брокерами (зокрема **Express brokers** зі швидким масштабуванням), **MSK Serverless**, **MSK Connect** (керовані конектори Kafka Connect).

**Kinesis чи MSK?** Kinesis — «рідний» сервіс AWS, простіше почати, serverless on-demand. MSK — коли потрібна **сумісність з Kafka** (наявний код, інструменти, переносимість).

## Потокова архітектура Хмаринки {#design}

<figure class="diagram" data-caption="Clickstream Хмаринки: реальний час і озеро даних">
<div class="flow">
<div class="st"><b>📱 Сайт і застосунок</b>Події: перегляд, кошик, пошук, оплата (JSON)</div>
<span class="ar">→</span>
<div class="st"><b>🌊 Kinesis Data Streams</b>On-demand; partition key = sessionId (порядок подій сесії); зберігання 7 днів</div>
<span class="ar">→</span>
<div class="st lanes"><b>Споживачі (паралельно)</b><span class="dg-node cmp">Lambda: лічильники «🔥 зараз купують» → DynamoDB</span><span class="dg-node ana">Flink: боти й аномалії за 30 с → SNS</span><span class="dg-node ana">Firehose: Parquet + партиції за датою → S3</span></div>
<span class="ar">→</span>
<div class="st"><b>🏞️ Озеро даних у S3</b>Далі — Glue і Athena (наступний розділ)</div>
</div>
<figcaption>Одна подія — три незалежні споживачі. Знайшли помилку в Lambda? Виправили і перечитали події за останню добу — вони ще в потоці.</figcaption>
</figure>

## Що обрати {#choose}

| Потреба | Сервіс |
|---|---|
| Реальний час, кілька власних споживачів, порядок, replay | **Kinesis Data Streams** |
| Складати потік у S3 / Redshift / OpenSearch / Splunk без коду, near real-time | **Amazon Data Firehose** |
| Перетворити JSON у Parquet перед збереженням у S3 | **Firehose (конвертація формату)** |
| Агрегації у вікнах часу, аномалії в реальному часі | **Managed Service for Apache Flink** |
| Наявні застосунки на Apache Kafka | **Amazon MSK** |
| Відео з камер для відтворення й ML | **Kinesis Video Streams** |
| Задачі, які має обробити один обробник, буфер піків | **SQS** ([розділ 31](#ch/sqs-sns)) |

:::lab 🧪 Спробуй у справжньому AWS: потік, записи і доставка в S3
**Вартість:** 1 shard і Firehose на 30 хвилин з кількома записами — центи. **Час:** 25 хвилин.
1. **Kinesis → Data streams → Create**: назва `clicks`, режим **Provisioned**, **1 shard**. Create.
2. **CloudShell** — запиши кілька подій і прочитай їх:
```bash
for i in 1 2 3; do
  aws kinesis put-record --stream-name clicks --partition-key "session-42" \
    --cli-binary-format raw-in-base64-out --data "{\"event\":\"view\",\"product\":$i}"
done
SHARD=$(aws kinesis list-shards --stream-name clicks --query "Shards[0].ShardId" --output text)
IT=$(aws kinesis get-shard-iterator --stream-name clicks --shard-id $SHARD --shard-iterator-type TRIM_HORIZON --query ShardIterator --output text)
aws kinesis get-records --shard-iterator $IT --query "Records[].Data" --output text | tr '\t' '\n' | base64 -d; echo
```
Ти прочитав записи з початку потоку (TRIM_HORIZON) — і можеш повторити це скільки завгодно разів: це і є replay.
3. Створи bucket `khmarynka-lake-<цифри>`. **Amazon Data Firehose → Create Firehose stream**: Source **Amazon Kinesis Data Streams** → `clicks`; Destination **Amazon S3** → твій bucket; Buffer interval **60 секунд**. Create.
4. Запиши ще кілька подій командою з кроку 2. Через 1–2 хвилини в bucket з'явиться об'єкт у префіксі з датою — Firehose склав потік у файл.
**Прибери за собою:** видали Firehose stream, потім Data stream `clicks`; очисти й видали bucket; видали IAM-роль Firehose.
:::

#### 💡 Запам'ятай

- **Потік** — багато споживачів, порядок у shard, **replay**; **черга** — один обробник, без replay.
- **KDS:** shard = запис **1 MB/с або 1 000 записів/с**, читання **2 MB/с**; **enhanced fan-out** — 2 MB/с кожному споживачу; зберігання **24 год – 365 днів**; **on-demand** або provisioned (split/merge); partition key → shard; гарячий shard → кращий ключ.
- **Firehose:** доставка в **S3, Redshift, OpenSearch, Splunk, HTTP, Iceberg**; буферизація → **near real-time**; Lambda-трансформація, **JSON → Parquet/ORC**, стиснення, динамічне партиціювання; **без replay**.
- **Flink** — вікна часу, аномалії в реальному часі. **Kinesis Video Streams** — відео. **MSK** — керований Kafka (Serverless, Connect).

#### 🎯 Як питають на іспиті

- Потік кліків чи IoT у реальному часі, кілька застосунків-споживачів, повторне читання → **Kinesis Data Streams**
- Складати потокові дані в S3, Redshift або OpenSearch без коду → **Amazon Data Firehose**
- Перетворити потік JSON у Parquet перед збереженням у S3 → **Firehose з конвертацією формату**
- Агрегація у вікнах часу, аномалії в реальному часі → **Managed Service for Apache Flink**
- Наявні Kafka-застосунки, мінімум змін → **Amazon MSK**
- Відео з камер для аналізу ML → **Kinesis Video Streams (+ Rekognition)**
- `ProvisionedThroughputExceededException` на одному shard → **кращий partition key, split shard або on-demand**
- Кілька споживачів конкурують за пропускну здатність shard → **enhanced fan-out**
- Зберігати події потоку рік для перечитування → **KDS з retention до 365 днів**
- Потрібно обробити кожну подію рівно одним воркером і згладити піки → **SQS (не Kinesis)**

#### ⚠️ Пастки

- Firehose — **near real-time** (буферизація) і **без replay**.
- Порядок у Kinesis — лише **в межах shard** (однаковий partition key).
- MSK — не serverless за замовчуванням: є брокери (крім MSK Serverless).
- Kinesis Data Analytics тепер зветься **Managed Service for Apache Flink**, Kinesis Data Firehose — **Amazon Data Firehose**.

## ✅ Перевір себе

:::quiz
? Компанія збирає клікові події сайту. Три різні застосунки мають обробляти ті самі події в реальному часі незалежно, а в разі помилки — перечитувати події за останні 24 години. Що обрати?
+ Amazon Kinesis Data Streams
- Amazon SQS Standard
- Amazon Data Firehose
- Amazon SNS
= Kinesis Data Streams зберігає записи незалежно від читання, дозволяє кільком споживачам читати ті самі дані і перечитувати їх. SQS видає повідомлення одному обробнику, Firehose не має replay, SNS не зберігає повідомлення.

? Потрібно доставляти журнали застосунку в S3 у форматі Parquet з мінімальними операційними зусиллями; затримка в кілька хвилин прийнятна. Що обрати?
- Kinesis Data Streams з власним споживачем на EC2
+ Amazon Data Firehose з конвертацією формату в Parquet
- Amazon SQS з Lambda, що пише файли
- Amazon MSK з Kafka Connect
= Firehose — керована доставка в S3 з буферизацією і вбудованою конвертацією JSON у Parquet/ORC, без коду і серверів.

? Потік Kinesis з 10 shards отримує помилки ProvisionedThroughputExceededException, хоча загальне навантаження вдвічі нижче за ємність. Усі записи мають partition key = назва країни, а 90% трафіку — з однієї країни. Що зробити?
+ Використати partition key з високою кардинальністю (наприклад, sessionId)
- Додати ще 10 shards
- Збільшити retention до 7 днів
- Увімкнути enhanced fan-out
= Нерівномірний ключ заганяє більшість записів в один shard. Ключ з багатьма значеннями розподіляє навантаження. Додаткові shards не допоможуть, поки ключ той самий.

? Банк хоче виявляти підозрілі транзакції за 10 секунд, аналізуючи потік у вікнах часу («понад 5 оплат з однієї картки за хвилину»). Що використати?
+ Amazon Managed Service for Apache Flink, що читає Kinesis Data Streams
- Amazon Athena за розкладом щогодини
- Amazon Data Firehose з доставкою в S3
- AWS Glue ETL щоночі
= Flink обробляє потік у реальному часі з агрегаціями у вікнах часу. Athena і Glue — пакетна аналітика, Firehose — доставка.

? Компанія має десятки мікросервісів на Apache Kafka і хоче перенести кластер в AWS з мінімальними змінами. Що обрати?
- Amazon Kinesis Data Streams
+ Amazon MSK
- Amazon SQS FIFO
- Amazon MQ
= MSK — керований Apache Kafka, сумісний з наявними клієнтами і інструментами. Kinesis вимагав би переписати виробників і споживачів.

? Кілька споживачів читають потік Kinesis, і їм не вистачає пропускної здатності читання. Як дати кожному споживачу власні 2 MB/с на shard?
+ Увімкнути enhanced fan-out для споживачів
- Перейти на Firehose
- Зменшити retention
- Використати SQS замість Kinesis
= Enhanced fan-out надсилає дані кожному зареєстрованому споживачу окремим каналом 2 MB/с на shard, без конкуренції за спільні 2 MB/с.

? Які твердження про Amazon Data Firehose правильні? (Оберіть 2)
+ Може перетворювати записи через Lambda перед доставкою
- Дозволяє споживачам перечитувати дані за останні 7 днів
+ Доставляє дані в S3, Redshift, OpenSearch і HTTP-endpoints
- Гарантує доставку за мілісекунди без буферизації
- Вимагає керувати shards вручну
= Firehose трансформує (Lambda), конвертує формати і доставляє в сховища та сервіси. Він буферизує дані (near real-time), не зберігає їх для replay і не має shards для ручного керування.
:::
