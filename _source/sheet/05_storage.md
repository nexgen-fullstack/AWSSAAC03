## 13. Amazon S3 і Glacier

### Основне

- Об'єктне сховище, durability **11 дев'яток** (99,999999999%). Bucket — регіональний, але ім'я глобально унікальне.
- Об'єкт до **50 TB** (🆕 з грудня 2025; раніше 5 TB — на іспиті може трапитися стара цифра).
- Один PUT — до 5 GB. **Multipart upload** рекомендований від 100 MB і обов'язковий понад 5 GB: частини вантажаться паралельно, збійні частини — повторно.
- **Strong read-after-write consistency** для всіх операцій.
- **Продуктивність:** 3 500 PUT/COPY/POST/DELETE і 5 500 GET/HEAD запитів/с **на кожен префікс** → більше префіксів = більше швидкість.
- **Transfer Acceleration** — швидке завантаження з далеких країн через edge-локації. **Byte-range fetches** — паралельне читання частин файлу.

### Класи зберігання

| Клас | Для чого | Мін. термін оплати | Доступ |
|---|---|---|---|
| **Standard** | Часті звернення | — | мс |
| **Intelligent-Tiering** | Невідомий або змінний патерн доступу | — | мс (архівні рівні — години); плата за моніторинг, без плати за отримання |
| **Express One Zone** | Найшвидший, 1 AZ, одноцифрові мс, directory buckets | 1 година | мс |
| **Standard-IA** | Рідко, але потрібні миттєво | 30 днів | мс, плата за ГБ отримання |
| **One Zone-IA** | Рідко, дані можна відтворити, 1 AZ | 30 днів | мс, плата за ГБ отримання |
| **Glacier Instant Retrieval** | Архів, доступ ~раз на квартал, але миттєво | 90 днів | мс |
| **Glacier Flexible Retrieval** | Архів і бекапи | 90 днів | Expedited 1–5 хв, Standard 3–5 год, Bulk 5–12 год (безкоштовно) |
| **Glacier Deep Archive** | Найдешевше, зберігання 7–10+ років | 180 днів | Standard до 12 год, Bulk до 48 год |

- Мінімальний розмір об'єкта для оплати в Standard-IA, One Zone-IA і Glacier Instant Retrieval — 128 KB.
- Intelligent-Tiering сам переносить об'єкти: 30 днів без доступу → Infrequent, 90 днів → Archive Instant; опційно — Archive Access і Deep Archive Access.
- **Provisioned capacity** для Glacier Flexible Retrieval гарантує, що Expedited-відновлення (1–5 хв) спрацює навіть у пікові періоди.

<figure class="diagram" id="fig-lifecycle" data-caption="S3 Lifecycle: дані дешевшають з віком">
<div class="flow">
<div class="st"><b>S3 Standard</b>0–30 днів: часті звернення</div>
<span class="ar">→</span>
<div class="st"><b>Standard-IA</b>після 30 днів: рідко, але миттєво</div>
<span class="ar">→</span>
<div class="st"><b>Glacier Instant / Flexible</b>після 90 днів: архів (мс або хвилини–години)</div>
<span class="ar">→</span>
<div class="st"><b>Glacier Deep Archive</b>після 180 днів: найдешевше, відновлення до 12–48 год</div>
<span class="ar">→</span>
<div class="st"><b>🗑️ Expiration</b>видалення через N років</div>
</div>
<figcaption>Строки — лише приклад. У Standard-IA можна перевести не раніше ніж через 30 днів; кожен клас має мінімальний строк оплати (30 / 90 / 180 днів). Невідомий патерн доступу — просто Intelligent-Tiering.</figcaption>
</figure>

### Керування даними

- **Lifecycle rules** — автоматичні переходи між класами (transition) і видалення (expiration), зокрема для старих версій і незавершених multipart-завантажень. У Standard-IA/One Zone-IA можна перевести не раніше ніж через 30 днів після створення.
- **Versioning** — захист від перезапису і видалення (видалення = delete marker, стару версію можна повернути). **MFA Delete** — для остаточного видалення версій потрібен MFA (вмикає тільки root).
- **Replication:** **CRR** (в інший регіон: DR, менша затримка, комплаєнс) і **SRR** (в тому ж регіоні: збір логів, prod → test). Потрібен versioning з обох боків. Реплікуються лише нові об'єкти; наявні — через **S3 Batch Replication**. **RTC** — 99,99% об'єктів за 15 хв (SLA).
- **Object Lock (WORM):**
  - **Compliance mode** — ніхто, навіть root, не видалить і не змінить до кінця терміну.
  - **Governance mode** — можуть обійти користувачі з окремим дозволом.
  - **Legal hold** — без терміну, доки не знімуть.
- **S3 Glacier Vault Lock** — WORM-політика для vault. (Окремий старий сервіс «Amazon Glacier» з vaults з листопада 2025 закритий для нових клієнтів; класи S3 Glacier працюють як завжди.)

### Безпека і доступ

- **Block Public Access** увімкнено за замовчуванням. ACL вимкнені за замовчуванням (Object Ownership = *Bucket owner enforced*). Доступ — через **bucket policy** та IAM.
- **Presigned URL** — тимчасовий доступ до приватного об'єкта (завантажити або скачати) з правами того, хто підписав.
- **Access Points** — окремі точки доступу зі своїми політиками для різних команд і застосунків (можна «тільки з VPC»).
- **Multi-Region Access Points** — один глобальний endpoint до bucket у кількох регіонах з маршрутизацією і failover.
- **CORS** — дозволити браузеру з іншого домену звертатися до bucket.
- **aws:SourceVpce / aws:SourceVpc** в bucket policy — доступ лише через конкретний VPC endpoint або з конкретної VPC.

Приклад bucket policy: заборонити HTTP і будь-який доступ не через свій VPC endpoint (обережно: друге правило закриє доступ навіть з консолі):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyHTTP", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
      "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"],
      "Condition": { "Bool": { "aws:SecureTransport": "false" } }
    },
    {
      "Sid": "OnlyMyEndpoint", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
      "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"],
      "Condition": { "StringNotEquals": { "aws:SourceVpce": "vpce-1a2b3c4d" } }
    }
  ]
}
```

### Інші можливості

- **Event notifications** — при створенні або видаленні об'єктів → SNS, SQS, Lambda, **EventBridge** (більше цілей і фільтрів).
- **Static website hosting** — лише HTTP. Для HTTPS і власного домену → **CloudFront + OAC** (bucket лишається приватним).
- **Requester Pays** — за завантаження даних платить той, хто завантажує.
- **S3 Batch Operations** — одна дія над мільярдами об'єктів (копіювання, теги, restore, виклик Lambda).
- **S3 Inventory** і **Storage Lens** — звіти про об'єкти та аналітика використання і витрат.
- **Storage Class Analysis** — аналізує, як часто читають дані, і підказує, коли переводити їх у Standard-IA (основа для lifecycle-правил).
- S3 Select і S3 Object Lambda закриті для нових клієнтів (замість Select використовуй Athena).

#### 🎯 Тригери

- Невідомий або змінний патерн доступу, без ручного керування → **S3 Intelligent-Tiering**
- Дані читають рідко, але потрібні миттєво → **S3 Standard-IA** (раз на квартал — Glacier Instant Retrieval)
- Відтворювані дані (мініатюри, копії), рідко, найдешевше з мс-доступом → **S3 One Zone-IA**
- Архів, іноді потрібен доступ за кілька хвилин → **Glacier Flexible Retrieval (Expedited)**
- Зберігати 7–10 років для регулятора, доступ до 48 год прийнятний, найдешевше → **Glacier Deep Archive**
- Автоматично перенести в Glacier через 90 днів і видалити через 5 років → **Lifecycle rule**
- Захист від випадкового видалення або перезапису → **Versioning (+ MFA Delete)**
- Ніхто не може видалити або змінити дані N років (WORM, регулятор) → **S3 Object Lock, Compliance mode**
- Копія bucket в іншому регіоні для DR → **Cross-Region Replication** (наявні об'єкти — Batch Replication)
- Користувачі з різних континентів повільно завантажують великі файли → **S3 Transfer Acceleration + multipart upload**
- Файли понад 100 MB, нестабільна мережа → **Multipart upload**
- Тимчасово дати клієнту завантажити або скачати приватний файл → **Presigned URL**
- Багато команд, різні права до одного великого bucket → **S3 Access Points**
- Запустити обробку, щойно файл з'явився в bucket → **S3 Event Notification → Lambda / SQS / EventBridge**
- Партнери завантажують великі датасети — хай самі платять за трафік → **Requester Pays**
- Статичний сайт з HTTPS і власним доменом → **S3 + CloudFront (OAC) + ACM + Route 53**
- Дуже високий темп запитів до S3 → **Розподілити ключі по кількох префіксах**
- Найнижча затримка S3 для ML/аналітики в одній AZ → **S3 Express One Zone**
- Змінити клас або теги мільйонів наявних об'єктів → **S3 Batch Operations**
- Доступ до bucket лише з конкретної VPC або через конкретний endpoint → **Bucket policy з умовою aws:SourceVpce (або aws:SourceVpc)**
- Гарантувати швидке (Expedited) відновлення з Glacier у будь-який момент → **Provisioned capacity**
- Вирішити, коли переводити дані в IA, на основі реального доступу → **S3 Storage Class Analysis**

#### ⚠️ Пастки

- S3 не можна «змонтувати» як диск для БД — це об'єктне сховище, а не блочне.
- One Zone-IA і Express One Zone зберігають дані в одній AZ — при втраті AZ дані можуть зникнути.
- Видалення з IA/Glacier раніше мінімального терміну однаково оплачується за весь мінімум.

## 14. Блочне і файлове сховище: EBS, Instance Store, EFS, FSx

### Amazon EBS

| Тип | Макс. IOPS | Макс. пропускна | Для чого |
|---|---|---|---|
| **gp3** (SSD) | 3 000 базово, до 80 000 | 125 MiB/s базово, до 2 000 MiB/s | За замовчуванням: boot, більшість застосунків. IOPS і пропускна налаштовуються окремо від розміру |
| **gp2** (SSD) | 3 IOPS на GiB (малі томи — burst до 3 000), максимум 16 000 | до 250 MiB/s | Старший тип, IOPS прив'язані до розміру |
| **io2 Block Express** (SSD) | до 256 000 | до 4 000 MiB/s | Критичні БД, затримка < 1 мс, durability 99,999%, Multi-Attach |
| **io1** (SSD) | до 64 000 | до 1 000 MiB/s | Старший Provisioned IOPS |
| **st1** (HDD) | 500 | 500 MiB/s | Big data, логи, DWH — послідовне читання. Не boot |
| **sc1** (HDD) | 250 | 250 MiB/s | Холодні дані, найдешевше. Не boot |

- Розміри: gp3 і io2 — до 64 TiB (gp3 так з вересня 2025; раніше 16 TiB і 16 000 IOPS).
- EBS прив'язаний до **однієї AZ**. Перенести в іншу AZ або регіон → **snapshot** → створити том там (snapshot можна копіювати між регіонами).
- Snapshots — інкрементальні, зберігаються в S3. Автоматизація: **Data Lifecycle Manager (DLM)** або **AWS Backup**. **Snapshot Archive** — дешевше для рідко потрібних. **Recycle Bin** — захист від випадкового видалення. **Fast Snapshot Restore** — том одразу на повній швидкості.
- **Multi-Attach** (лише io1/io2) — один том до кількох Nitro-інстансів в одній AZ (кластерні застосунки).
- **Elastic Volumes** — змінити тип, розмір або IOPS тому без зупинки інстансу. Тому gp2 → gp3 — зазвичай дешевше і без простою.

### Amazon EFS

- Керована **NFS**-файлова система для **Linux**: одночасно для тисяч EC2, ECS, EKS і Lambda, **у кількох AZ** (або One Zone — дешевше).
- Росте автоматично до петабайтів, платиш за використане.
- Класи: Standard, **Infrequent Access**, **Archive** + lifecycle management.
- Throughput: **Elastic** (рекомендовано), Provisioned, Bursting. Performance mode — General Purpose.
- Шифрування, POSIX-права, Access Points, реплікація в інший регіон. Дорожча за EBS за ГБ, зате спільна.
- **Mount target** створюють у кожній AZ; його Security Group має дозволяти **NFS, порт 2049** від клієнтів.

### Amazon FSx

- **FSx for Windows File Server** — **SMB**, NTFS, інтеграція з **Active Directory**, DFS, Multi-AZ. Для Windows-застосунків, SharePoint, домашніх папок.
- **FSx for Lustre** — високопродуктивна ФС для **HPC, ML, рендерингу, фінансових моделей**: сотні GB/s, суб-мс затримка, **інтеграція з S3** (читає дані з S3, пише результати назад). Scratch (тимчасово, дешево) vs Persistent (довготривало, з реплікацією).
- **FSx for NetApp ONTAP** — **NFS + SMB + iSCSI** одночасно, Linux/Windows/macOS, snapshots, клонування, дедуплікація і компресія. Міграція з NetApp.
- **FSx for OpenZFS** — міграція ZFS/Linux NFS, snapshots, низька затримка.

#### 🎯 Тригери

- Спільна файлова система для кількох Linux-інстансів у різних AZ → **Amazon EFS**
- Спільна файлова система для Windows з Active Directory → **FSx for Windows File Server**
- HPC або ML, дуже висока продуктивність, дані лежать у S3 → **FSx for Lustre**
- Потрібні NFS і SMB одночасно / міграція з NetApp → **FSx for NetApp ONTAP**
- БД на EC2 потребує понад 100 000 стабільних IOPS → **io2 Block Express**
- Дешевий диск для великих послідовних логів і big data → **st1**
- Найдешевший блочний диск для холодних даних → **sc1**
- Знизити витрати на EBS без простою → **gp2 → gp3**
- 10 000 IOPS на невеликому томі дешево → **gp3 (IOPS окремо від розміру)**
- Перенести EBS-том в іншу AZ → **Snapshot → новий том в іншій AZ**
- Щоденні автоматичні знімки EBS з видаленням старих → **Data Lifecycle Manager або AWS Backup**
- Кластерний застосунок на кількох інстансах з одним спільним томом → **EBS Multi-Attach (io1/io2)**
- Файли в EFS майже не відкривають після 30 днів → **EFS lifecycle → Infrequent Access / Archive**
- EC2 не можуть змонтувати EFS (timeout) → **Дозволити порт 2049 (NFS) у Security Group mount target**
- Тимчасовий кеш з максимальними IOPS → **Instance store**

#### ⚠️ Пастки

- EBS — одна AZ і, як правило, один інстанс. EFS — багато інстансів, багато AZ, тільки Linux (NFS).
- HDD-томи (st1, sc1) не можуть бути boot-томом.
- Для Windows-шар — FSx for Windows, а не EFS.

## 15. Гібрид, міграція і перенесення даних

### Storage Gateway (on-prem доступ до хмарного сховища з локальним кешем)

- **S3 File Gateway** — NFS/SMB-шари, файли стають об'єктами в S3 (далі lifecycle, Glacier).
- **FSx File Gateway** — локальний кеш для FSx for Windows (з жовтня 2024 недоступний новим клієнтам).
- **Volume Gateway** (iSCSI):
  - **Cached** — основні дані в S3, «гарячі» — локально.
  - **Stored** — усі дані локально, асинхронний бекап в S3 (як EBS snapshots).
- **Tape Gateway** — віртуальна стрічкова бібліотека (VTL) для наявного бекап-ПЗ → S3 / Glacier. Заміна фізичних стрічок.

### Перенесення даних

- **AWS DataSync** — **онлайн**-перенесення і синхронізація великих обсягів: NFS, SMB, HDFS, об'єктні сховища, інші хмари ↔ S3, EFS, FSx. Агент on-prem, шифрування, перевірка цілісності, збереження метаданих і прав, розклад, обмеження пропускної. Також між сервісами AWS.
- **AWS Transfer Family** — керований **SFTP / FTPS / FTP / AS2**-сервер поверх S3 або EFS. Партнери працюють як раніше, нічого не змінюючи.
- **Snow Family (Snowball Edge)** — фізичні пристрої для **офлайн**-перенесення терабайтів і петабайтів і для edge-обчислень, коли мережа повільна або дорога.
  - Орієнтир: якщо передача мережею займе більше ~тижня → фізичний пристрій.
  - 🆕 З 7.11.2025 Snowball Edge **недоступний новим клієнтам**. AWS радить DataSync, **Data Transfer Terminal** (фізичні локації AWS для швидкого завантаження) або партнерів. На іспиті Snowball ще може бути правильною відповіддю.

### Міграція серверів і баз даних

- **AWS DMS** — міграція БД з мінімальним простоєм: джерело працює під час міграції, **CDC** (безперервна реплікація змін).
  - **Гомогенна** (MySQL → Aurora MySQL, Oracle → RDS Oracle) — DMS або нативні інструменти.
  - **Гетерогенна** (Oracle → Aurora PostgreSQL, SQL Server → MySQL) — спершу конвертація схеми **SCT / DMS Schema Conversion**, потім дані через DMS.
  - Також з/у S3, Kinesis, DynamoDB, Redshift.
  - SCT конвертує і схеми **сховищ даних** (Oracle, Teradata, Netezza → Redshift).
- **AWS Application Migration Service (MGN)** — **rehost / lift-and-shift** серверів (фізичних, VMware, Hyper-V, інших хмар) в EC2: безперервна блочна реплікація, короткий cutover.
- **AWS Elastic Disaster Recovery (DRS)** — DR серверів в AWS: постійна реплікація, RPO — секунди, RTO — хвилини.
- **VMware Cloud on AWS** — перенести VMware vSphere без змін (relocate).
- **7 R стратегій міграції:**
  - **Retire** — вимкнути непотрібне. **Retain** — поки залишити як є.
  - **Rehost** — lift & shift «як є» (MGN).
  - **Relocate** — перенести гіпервізор (VMware Cloud on AWS).
  - **Replatform** — lift, tinker & shift: невеликі оптимізації (БД → RDS, застосунок → Beanstalk).
  - **Repurchase** — перейти на SaaS.
  - **Refactor / Re-architect** — переписати під cloud-native (serverless, мікросервіси).

#### 🎯 Тригери

- On-prem застосунки зберігають файли в S3 через NFS/SMB з локальним кешем → **S3 File Gateway**
- Замінити фізичні стрічки, залишивши наявне бекап-ПЗ → **Tape Gateway**
- iSCSI-томи: основні дані в хмарі, локально лише кеш → **Volume Gateway (Cached)**
- Усі дані мають бути локально з бекапом в AWS → **Volume Gateway (Stored)**
- Перенести 50 TB з NAS в S3/EFS мережею — швидко, за розкладом, з перевіркою → **DataSync**
- Партнери надсилають файли по SFTP, а зберігати треба в S3 → **Transfer Family**
- Сотні терабайтів, повільний інтернет, дедлайн — тиждень → **Snowball Edge** (нові клієнти — Data Transfer Terminal або партнери)
- Oracle → Aurora PostgreSQL з мінімальним простоєм → **SCT (схема) + DMS (дані з CDC)**
- MySQL on-prem → RDS MySQL з мінімальним простоєм → **DMS** (гомогенна, SCT не потрібен)
- Перенести сотні серверів «як є» в EC2 швидко → **Application Migration Service (MGN)**
- DR для on-prem серверів в AWS з RPO в секунди → **Elastic Disaster Recovery**
- Перенести віртуалки VMware без зміни інструментів → **VMware Cloud on AWS**
- Невелика оптимізація при міграції: БД переносимо в керований сервіс → **Replatform (напр., на RDS)**

#### ⚠️ Пастки

- DataSync — перенесення і синхронізація; Storage Gateway — постійний гібридний доступ; Transfer Family — протоколи SFTP/FTP.
- SCT потрібен лише для гетерогенних міграцій (різні рушії БД).
- Snowball — офлайн (фізично); DataSync — онлайн (мережею).
