Довідник для режиму підказок. Формат заголовка (у файлі починається з «## »):
id | Назва | аліаси через кому (з урахуванням регістру) | категорія | емодзі
WHAT / IMAGE / WHEN (через ;) / EXAM (через ;, «ситуація → відповідь») / CONFUSE (id через кому) / LESSON (id уроку)

## ec2 | Amazon EC2 | EC2, Amazon EC2 | compute | 🖥️
WHAT: Віртуальні сервери в оренду: обираєш процесор, пам'ять, диск і ОС, платиш посекундно.
IMAGE: Автопрокат комп'ютерів: тип інстансу — модель авто (C — спорткар, R — вантажівка з великим кузовом).
WHEN: Потрібен повний контроль над ОС і ПЗ; застосунок не переписати під serverless; особливі вимоги (GPU, ліцензії)
EXAM: повний контроль над ОС → EC2; переривні задачі найдешевше → Spot Instances; ліцензії на фізичні ядра → Dedicated Hosts
CONFUSE: lambda, fargate
LESSON: ec2

## asg | EC2 Auto Scaling | Auto Scaling group, Auto Scaling groups, EC2 Auto Scaling, AWS Auto Scaling, Auto Scaling, ASG | compute | 📈
WHAT: Автоматично додає й прибирає EC2 за навантаженням і замінює нездорові інстанси; тримає min/desired/max у кількох AZ.
IMAGE: Менеджер супермаркету: черги ростуть — відкриває каси, спад — закриває, касир захворів — ставить заміну.
WHEN: Змінне навантаження; висока доступність у кількох AZ; автоматична заміна зламаних серверів
EXAM: тримати CPU біля 50% → target tracking; відомий пік → scheduled scaling; циклічні піки → predictive scaling; ASG не замінює сервер із завислим застосунком → ELB health checks
CONFUSE: elb
LESSON: scaling

## beanstalk | AWS Elastic Beanstalk | Elastic Beanstalk, Beanstalk | compute | 🌱
WHAT: PaaS: завантажуєш код, а AWS сам створює EC2, Auto Scaling, балансувальник і моніторинг.
IMAGE: Ресторан під ключ: приносиш рецепти, а приміщення й кухню ставлять за тебе.
WHEN: Швидко задеплоїти вебзастосунок без знань інфраструктури; розгортання blue/green чи immutable
EXAM: розробники хочуть просто задеплоїти код → Elastic Beanstalk; нова версія з миттєвим відкатом → blue/green (swap URL)
CONFUSE: cloudformation, lambda
LESSON: serverless

## batch | AWS Batch | AWS Batch | compute | 🏭
WHAT: Черги й планувальник для пакетних задач будь-якої тривалості на EC2, Spot або Fargate.
IMAGE: Цех для великих замовлень без поспіху: задачі чекають у черзі, цех сам бере потрібних робітників.
WHEN: Тисячі пакетних задач; задачі довші за 15 хв (межа Lambda); економія на Spot
EXAM: пакетна обробка з чергами і Spot → AWS Batch; задача на 40 хв → не Lambda, а Batch або ECS
CONFUSE: lambda, emr
LESSON: serverless

## outposts | AWS Outposts | Outposts | compute | 🏢
WHAT: Стійки з обладнанням AWS у твоєму дата-центрі: ті самі сервіси й API, але локально.
IMAGE: Шафа-філія AWS у твоєму офісі.
WHEN: Дані мають фізично лишатися on-prem; наднизька затримка до локальних систем
EXAM: дані мають лишатися у власному дата-центрі, але потрібні сервіси AWS → Outposts
CONFUSE: localzones, wavelength
LESSON: cloud

## localzones | AWS Local Zones | Local Zones, Local Zone | compute | 🏙️
WHAT: Розширення регіону у великому місті: EC2, EBS та інші сервіси з одноцифровими мілісекундами до мешканців.
IMAGE: Філія AWS у твоєму місті.
WHEN: Ігри, стрімінг, рендеринг для користувачів конкретного мегаполіса
EXAM: одноцифрові мілісекунди для користувачів у конкретному місті → Local Zones
CONFUSE: outposts, wavelength
LESSON: cloud

## wavelength | AWS Wavelength | Wavelength | compute | 📶
WHAT: Обчислення AWS усередині 5G-мереж мобільних операторів.
IMAGE: AWS у вежі 5G поруч із телефоном.
WHEN: Мобільні застосунки з ультранизькою затримкою (AR/VR, ігри, IoT)
EXAM: ультранизька затримка для мобільних пристроїв у 5G → Wavelength
CONFUSE: localzones
LESSON: cloud

## vmware | VMware Cloud on AWS | VMware Cloud on AWS | compute | 🔁
WHAT: Середовище VMware vSphere на виділеному обладнанні AWS, яким керують звичними інструментами VMware.
IMAGE: Перевезти будинок разом з фундаментом.
WHEN: Швидко перенести віртуалки VMware без змін (стратегія Relocate)
EXAM: перенести VMware без зміни інструментів → VMware Cloud on AWS
CONFUSE: mgn
LESSON: migration

## lambda | AWS Lambda | Lambda, AWS Lambda | serverless | 👨‍🍳
WHAT: Запускає твій код у відповідь на подію без серверів; до 15 хв на виклик, платиш за час виконання.
IMAGE: Кухар на виклик: приходить, готує страву до 15 хвилин, платиш лише за приготоване.
WHEN: Обробка подій (S3, SQS, API); API без серверів; короткі задачі й автоматизація
EXAM: serverless API → API Gateway + Lambda; обробити файл після завантаження в S3 → S3 event → Lambda; cold start → provisioned concurrency; задача довша за 15 хв → не Lambda
CONFUSE: fargate, ec2, batch
LESSON: serverless

## apigw | Amazon API Gateway | API Gateway | serverless | 🧑‍💼
WHAT: Керований «вхід» для API: REST, HTTP і WebSocket, з авторизацією, лімітами, кешем і ключами.
IMAGE: Офіціант: приймає замовлення, перевіряє гостя, не пускає натовп.
WHEN: API перед Lambda чи іншими бекендами; ліміти й ключі для клієнтів; чат у реальному часі (WebSocket)
EXAM: різні ліміти для клієнтів → usage plans і throttling; двосторонній чат → WebSocket API; власна перевірка токенів → Lambda authorizer
CONFUSE: alb
LESSON: serverless

## fargate | AWS Fargate | Fargate | serverless | 🚢
WHAT: Запуск контейнерів ECS або EKS без керування серверами: платиш за процесор і пам'ять задачі.
IMAGE: Порт сам дає крани й причали — ти лише привозиш контейнери.
WHEN: Контейнери без адміністрування EC2; довгі задачі понад 15 хв без серверів
EXAM: контейнери без керування серверами → Fargate (ECS або EKS)
CONFUSE: lambda, ecs
LESSON: serverless

## ecs | Amazon ECS | ECS, Amazon ECS | containers | 📦
WHAT: Оркестрація контейнерів від AWS: запускає й масштабує задачі на EC2 або Fargate.
IMAGE: Диспетчер порту, що розставляє контейнери.
WHEN: Контейнери без складності Kubernetes; мікросервіси з ALB
EXAM: контейнеру потрібен доступ до S3 → ECS task IAM role; контейнери без серверів → ECS на Fargate
CONFUSE: eks, fargate
LESSON: serverless

## eks | Amazon EKS | EKS, Amazon EKS, Kubernetes | containers | ☸️
WHAT: Керований Kubernetes: AWS веде керівну частину кластера, ти запускаєш поди на EC2 або Fargate.
IMAGE: Той самий порт, але за міжнародними правилами Kubernetes.
WHEN: Команда вже на Kubernetes; потрібна переносимість між хмарами; open-source інструменти K8s
EXAM: компанія вже використовує Kubernetes → EKS (на власних серверах — EKS Anywhere)
CONFUSE: ecs
LESSON: serverless

## ecr | Amazon ECR | ECR, Amazon ECR | containers | 🗃️
WHAT: Приватний реєстр образів контейнерів зі скануванням вразливостей і реплікацією.
IMAGE: Склад контейнерів перед відправкою в порт.
WHEN: Зберігати образи для ECS, EKS і Lambda
EXAM: сканувати образи на вразливості → ECR + Inspector
CONFUSE: ecs
LESSON: serverless

## amplify | AWS Amplify | Amplify | frontend | 📱
WHAT: Хостинг і бекенд для веб- і мобільних застосунків з автоматичним розгортанням фронтенду.
IMAGE: Конструктор сайту й застосунку «під ключ» для фронтенд-розробників.
WHEN: Швидко розгорнути full-stack веб- чи мобільний застосунок
EXAM: швидко розгорнути фронтенд і бекенд мобільного застосунку → Amplify
CONFUSE: beanstalk
LESSON: ai

## devicefarm | AWS Device Farm | Device Farm | frontend | 📲
WHAT: Тестування застосунків на сотнях реальних телефонів, планшетів і браузерів в AWS.
IMAGE: Кімната з сотнями справжніх телефонів для перевірки.
WHEN: Перевірити мобільний застосунок на різних пристроях
EXAM: тестування на реальних пристроях → Device Farm
CONFUSE: amplify
LESSON: ai

## s3 | Amazon S3 | S3, Amazon S3 | storage | 🪣
WHAT: Об'єктне сховище будь-якого обсягу: файли як об'єкти в bucket, доступ через API, надійність 11 дев'яток.
IMAGE: Безрозмірний склад з коробками, у кожної — ярлик-адреса.
WHEN: Файли, медіа, бекапи, логи, data lake, статичні сайти
EXAM: надійне сховище будь-якого обсягу → S3; статичний сайт з HTTPS → S3 + CloudFront; тимчасове посилання на файл → presigned URL
CONFUSE: ebs, efs
LESSON: s3

## glacier | S3 Glacier | S3 Glacier, Glacier, Glacier Instant Retrieval, Glacier Flexible Retrieval, Glacier Deep Archive, Deep Archive, Amazon Glacier | storage | 🧊
WHAT: Архівні класи S3: Instant Retrieval (мілісекунди, мінімум 90 днів), Flexible Retrieval (хвилини–години, 90), Deep Archive (до 12–48 год, 180, найдешевше).
IMAGE: Архів поруч, підвал і сховище в горах.
WHEN: Бекапи й архіви; зберігання для регулятора роками
EXAM: 7–10 років, доступ до 48 год, найдешевше → Glacier Deep Archive; архів з доступом раз на квартал миттєво → Glacier Instant Retrieval
CONFUSE: s3it
LESSON: s3

## s3it | S3 Intelligent-Tiering | S3 Intelligent-Tiering, Intelligent-Tiering | storage | 🤖
WHAT: Клас S3, що сам переносить об'єкти між рівнями за частотою доступу; без плати за отримання.
IMAGE: Розумний комірник, що сам переставляє речі.
WHEN: Невідомий або змінний патерн доступу
EXAM: невідомий патерн доступу, економія без ручної роботи → Intelligent-Tiering
CONFUSE: lifecycle
LESSON: s3

## ebs | Amazon EBS | EBS, Amazon EBS, gp3, gp2, io2 Block Express, io2, io1, st1, sc1 | storage | 💽
WHAT: Блочні диски для EC2 в одній AZ; знімки (snapshots) зберігаються в S3. Типи: gp3 — універсальний SSD, продуктивність налаштовується окремо від розміру (gp2 — попередник, де IOPS залежать від розміру); io2 Block Express — найшвидший SSD для критичних баз; st1 — HDD для великих послідовних даних; sc1 — найдешевший холодний HDD.
IMAGE: Жорсткий диск, прикручений до одного комп'ютера в одній кімнаті.
WHEN: Системні диски й бази на EC2; стабільні IOPS
EXAM: 100 000+ IOPS на одному томі → io2 Block Express; дешевше за gp2 → gp3; перенести в іншу AZ → snapshot
CONFUSE: efs, instancestore
LESSON: disks

## instancestore | Instance store | Instance store, instance store | storage | 📝
WHAT: Локальні диски фізичного сервера EC2: найшвидші, але дані зникають при зупинці чи збої.
IMAGE: Записи крейдою на дошці.
WHEN: Кеш, буфери, тимчасові дані
EXAM: найвищі IOPS для тимчасових даних → instance store
CONFUSE: ebs
LESSON: ec2

## efs | Amazon EFS | EFS, Amazon EFS | storage | 🗂️
WHAT: Керована спільна файлова система NFS для Linux у кількох AZ; об'єм росте автоматично.
IMAGE: Спільна мережева папка для всіх Linux-серверів офісу.
WHEN: Спільні файли для багатьох EC2, контейнерів і Lambda
EXAM: спільна файлова система для Linux у кількох AZ → EFS; не монтується → дозволити порт 2049 у Security Group
CONFUSE: fsxwin, ebs
LESSON: disks

## fsx | Amazon FSx | FSx, Amazon FSx | storage | 🗄️
WHAT: Сімейство керованих файлових систем: for Windows File Server, for Lustre, for NetApp ONTAP, for OpenZFS.
IMAGE: Спеціалізовані файлові сервери під різні задачі.
WHEN: Windows-файли з AD; HPC; мультипротокольне сховище; переїзд з NetApp чи ZFS
EXAM: Windows + AD → FSx for Windows; HPC + S3 → FSx for Lustre; NFS і SMB одночасно → FSx for NetApp ONTAP
CONFUSE: efs
LESSON: disks

## fsxwin | FSx for Windows File Server | FSx for Windows File Server, FSx for Windows | storage | 🪟
WHAT: Керований файловий сервер Windows: SMB, NTFS, інтеграція з Active Directory, Multi-AZ.
IMAGE: Звичний Windows-сервер з папками, але без адміністрування.
WHEN: Спільні файли для Windows-застосунків, домашні папки, SharePoint
EXAM: спільні файли для Windows з Active Directory → FSx for Windows File Server
CONFUSE: efs
LESSON: disks

## fsxlustre | FSx for Lustre | FSx for Lustre, Lustre | storage | 🏎️
WHAT: Високопродуктивна файлова система для HPC і ML: сотні GB/s, затримка менше мілісекунди, інтеграція з S3.
IMAGE: Болід Формули-1 серед файлових систем.
WHEN: HPC, машинне навчання, рендеринг, фінансові моделі
EXAM: HPC з даними в S3 і величезною швидкістю → FSx for Lustre
CONFUSE: efs
LESSON: disks

## fsxontap | FSx for NetApp ONTAP | FSx for NetApp ONTAP, NetApp ONTAP, ONTAP | storage | 🧰
WHAT: Керований NetApp ONTAP: NFS, SMB і iSCSI одночасно, знімки, клонування, дедуплікація.
IMAGE: Швейцарський ніж файлових сховищ.
WHEN: Потрібен одночасний доступ з Linux і Windows; переїзд з NetApp
EXAM: NFS і SMB одночасно або міграція з NetApp → FSx for NetApp ONTAP
CONFUSE: fsxwin
LESSON: disks

## dlm | Amazon Data Lifecycle Manager | Data Lifecycle Manager, DLM | storage | 🗓️
WHAT: Автоматично створює і видаляє знімки EBS та AMI за розкладом.
IMAGE: Фотограф, що щодня фотографує диски й прибирає старі фото.
WHEN: Регулярні знімки EBS з обмеженим строком зберігання
EXAM: щоденні знімки EBS з видаленням старих → Data Lifecycle Manager або AWS Backup
CONFUSE: backup
LESSON: disks

## backup | AWS Backup | AWS Backup, Backup Vault Lock, Vault Lock | storage | 💾
WHAT: Централізовані плани бекапів для EC2, EBS, RDS, Aurora, DynamoDB, EFS, FSx, S3 тощо, з копіями між регіонами й акаунтами.
IMAGE: Єдиний сейф для копій усього, з таймером проти видалення (Vault Lock).
WHEN: Бекапи багатьох сервісів за одним планом; захист від ransomware
EXAM: централізовані бекапи з копією в інший регіон → AWS Backup; бекап не видалить навіть адмін → Backup Vault Lock
CONFUSE: dlm, objectlock
LESSON: resilience

## rds | Amazon RDS | RDS, Amazon RDS | database | 🛢️
WHAT: Керовані реляційні бази (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Db2): патчі, бекапи й Multi-AZ робить AWS.
IMAGE: Найнятий адміністратор бази даних.
WHEN: Класичні застосунки з SQL і транзакціями
EXAM: висока доступність з автоматичним перемиканням → Multi-AZ; розвантажити читання → read replicas; Lambda вичерпує з'єднання → RDS Proxy
CONFUSE: aurora, dynamodb
LESSON: rds

## aurora | Amazon Aurora | Aurora, Amazon Aurora | database | 🌟
WHAT: Сумісна з MySQL і PostgreSQL база від AWS: 6 копій у 3 AZ, до 15 реплік, сховище до 256 TiB.
IMAGE: Турбо-версія MySQL/PostgreSQL.
WHEN: Потрібні максимальна доступність і продуктивність реляційної бази
EXAM: розділити аналітику й веб-трафік → custom endpoints; перемотати назад без бекапу → Backtrack (лише MySQL); копія для тестів → cloning
CONFUSE: rds
LESSON: rds

## aurora-sl | Aurora Serverless v2 | Aurora Serverless v2, Aurora Serverless | database | 🌓
WHAT: Aurora, що сама масштабує потужність в ACU (≈2 GiB пам'яті кожна) і може «засинати» до 0 ACU.
IMAGE: Автомобіль з автоматичною коробкою, що вміє заснути на стоянці.
WHEN: Непередбачуване або переривчасте навантаження; dev/test
EXAM: база простоює вночі й на вихідних → Aurora Serverless v2
CONFUSE: dynamodb
LESSON: rds

## aurora-global | Aurora Global Database | Aurora Global Database, Global Database | database | 🌍
WHAT: Реплікація Aurora на рівні сховища до 10 інших регіонів: затримка менше секунди, перемикання менш ніж за хвилину.
IMAGE: Філії бази в інших містах, що відстають менше ніж на секунду.
WHEN: Відновлення реляційної бази після падіння регіону; швидке локальне читання по світу
EXAM: RPO близько 1 с і RTO менше 1 хв між регіонами → Aurora Global Database
CONFUSE: readreplica, globaltables
LESSON: rds

## rdsproxy | Amazon RDS Proxy | RDS Proxy | database | ☎️
WHAT: Пул з'єднань між застосунком і RDS/Aurora: менше навантаження, швидше перемикання, IAM-автентифікація.
IMAGE: Секретар, що тримає телефонні лінії.
WHEN: Тисячі коротких з'єднань (Lambda); швидше перемикання без змін коду
EXAM: Lambda вичерпує з'єднання до бази → RDS Proxy
CONFUSE: elasticache
LESSON: rds

## dynamodb | Amazon DynamoDB | DynamoDB, Amazon DynamoDB | database | 🗃️
WHAT: Serverless NoSQL «ключ-значення» з мілісекундною затримкою на будь-якому масштабі; елемент до 400 KB.
IMAGE: Гігантська картотека з миттєвим пошуком за номером картки.
WHEN: Сесії, кошики, профілі, IoT, лідерборди — прості запити за ключем при величезному навантаженні
EXAM: serverless база з мілісекундною затримкою → DynamoDB; непередбачуваний трафік → on-demand; складні JOIN → не DynamoDB
CONFUSE: rds, dax
LESSON: nosql

## dax | DynamoDB Accelerator (DAX) | DynamoDB Accelerator, DAX | database | 🚀
WHAT: Кеш у пам'яті перед DynamoDB: мікросекунди, сумісний API, майже без змін коду.
IMAGE: Кишенька з найчастішими картками.
WHEN: Дуже часті читання тих самих елементів DynamoDB
EXAM: мікросекунди для DynamoDB без переписування → DAX
CONFUSE: elasticache
LESSON: nosql

## globaltables | DynamoDB Global Tables | DynamoDB Global Tables, Global Tables, global tables | database | 🌐
WHAT: Таблиця DynamoDB у кількох регіонах із записом у будь-якому (multi-active).
IMAGE: Однакова картотека в кількох містах, яку можна правити будь-де.
WHEN: Глобальний застосунок з локальним записом; стійкість до падіння регіону
EXAM: запис з низькою затримкою в кількох регіонах → DynamoDB Global Tables
CONFUSE: aurora-global
LESSON: nosql

## elasticache | Amazon ElastiCache | ElastiCache, Amazon ElastiCache, Redis OSS, Redis, Valkey, Memcached | database | 🧠
WHAT: Керований кеш у пам'яті: Redis OSS / Valkey (реплікація, Multi-AZ, складні структури) або Memcached (простий).
IMAGE: Записник на столі — не треба щоразу бігти в архів.
WHEN: Зменшити навантаження на базу; сесії; лідерборди
EXAM: лідерборд у реальному часі → Redis/Valkey sorted sets; сесії для stateless-серверів → ElastiCache або DynamoDB
CONFUSE: dax, memorydb
LESSON: nosql

## memorydb | Amazon MemoryDB | MemoryDB | database | 💡
WHAT: Сумісна з Redis/Valkey основна база в пам'яті з надійним збереженням (не просто кеш).
IMAGE: Записник, який не згорить навіть при пожежі.
WHEN: Потрібна швидкість Redis і водночас надійне зберігання
EXAM: Redis-сумісна основна база з надійністю зберігання → MemoryDB
CONFUSE: elasticache
LESSON: nosql

## documentdb | Amazon DocumentDB | DocumentDB, MongoDB | database | 📄
WHAT: Керована документна база, сумісна з MongoDB.
IMAGE: Папки з документами JSON.
WHEN: Застосунки на MongoDB
EXAM: перенести MongoDB-застосунок у керований сервіс → DocumentDB
CONFUSE: dynamodb
LESSON: nosql

## neptune | Amazon Neptune | Neptune | database | 🕸️
WHAT: Графова база для даних, де головне — зв'язки.
IMAGE: Карта знайомств.
WHEN: Соцмережі, рекомендації, виявлення шахрайських зв'язків, knowledge graphs
EXAM: «друзі друзів», шахрайські кільця → Neptune
CONFUSE: dynamodb
LESSON: nosql

## keyspaces | Amazon Keyspaces | Keyspaces, Cassandra | database | 🔑
WHAT: Serverless база, сумісна з Apache Cassandra (CQL).
IMAGE: Та сама Cassandra, але без адміністрування.
WHEN: Перенести навантаження з Cassandra
EXAM: мігрувати Cassandra в керований сервіс → Keyspaces
CONFUSE: dynamodb
LESSON: nosql

## timestream | Amazon Timestream | Timestream | database | ⏱️
WHAT: База для часових рядів: показники з мітками часу.
IMAGE: Щоденник показників по годинах.
WHEN: IoT-датчики, метрики, телеметрія
EXAM: дані IoT-датчиків з часовими мітками → Timestream
CONFUSE: dynamodb
LESSON: nosql

## redshift | Amazon Redshift | Redshift, Redshift Spectrum, Redshift Serverless | analytics | 🏬
WHAT: Колонкове сховище даних (OLAP) для складної аналітики на петабайтах; Spectrum читає дані прямо з S3.
IMAGE: Склад з упорядкованими полицями для звітів.
WHEN: Регулярна важка BI-аналітика; поєднати сховище з даними в S3
EXAM: складна аналітика на петабайтах → Redshift; запити до S3 з Redshift без завантаження → Redshift Spectrum; швидке завантаження → команда COPY
CONFUSE: athena, rds
LESSON: analytics

## vpc | Amazon VPC | VPC, Amazon VPC | network | 🏘️
WHAT: Приватна мережа в регіоні з твоїм діапазоном адрес, підмережами, маршрутами й охороною.
IMAGE: Огороджене містечко з кварталами.
WHEN: Будь-які ресурси з мережею: EC2, RDS, Lambda у VPC
EXAM: публічна підмережа = маршрут на Internet Gateway; приватні сервери виходять в інтернет → NAT Gateway
CONFUSE: subnet
LESSON: vpc

## subnet | Підмережа (subnet) | subnet, subnets, Subnet, public subnet, private subnet, Public subnet, Private subnet, public subnets, private subnets | concept | 🧩
WHAT: Частина VPC в одній AZ. Публічна має маршрут на Internet Gateway, приватна — ні.
IMAGE: Квартал містечка в одному районі.
WHEN: Розділити ресурси: балансувальники в публічних, сервери й бази — у приватних
EXAM: база недоступна з інтернету → приватна підмережа; у кожній підмережі AWS резервує 5 IP
CONFUSE: vpc
LESSON: vpc

## igw | Internet Gateway | Internet Gateway, internet gateway, IGW, Egress-only Internet Gateway | network | 🚪
WHAT: Ворота між VPC та інтернетом; маршрут 0.0.0.0/0 на них робить підмережу публічною. Egress-only — лише вихід для IPv6.
IMAGE: Головні ворота містечка на трасу.
WHEN: Публічні ресурси: ALB, бастіон, NAT Gateway
EXAM: чому підмережа публічна → маршрут 0.0.0.0/0 на IGW; IPv6 лише назовні → Egress-only Internet Gateway
CONFUSE: natgw
LESSON: vpc

## natgw | NAT Gateway | NAT Gateway, NAT gateway, NAT gateways, NAT instance | network | ↗️
WHAT: Дає серверам у приватних підмережах вихід в інтернет без вхідного доступу; платний за годину і за кожен ГБ.
IMAGE: Виїзд з односторонньою смугою.
WHEN: Приватним серверам потрібні оновлення з інтернету
EXAM: приватні сервери качають оновлення → NAT Gateway у публічній підмережі (для HA — по одному на AZ); дорогий трафік до S3 через NAT → gateway endpoint
CONFUSE: igw, endpoints
LESSON: vpc

## sg | Security Group | Security Group, Security Groups, security group, security groups, SG | security | 🛡️
WHAT: Файрвол на рівні інстансу: stateful, лише Allow-правила, може посилатися на інші Security Groups.
IMAGE: Охоронець біля дверей будинку, що пам'ятає, хто вийшов.
WHEN: Дозволити конкретні порти й джерела для інстансів, баз, балансувальників
EXAM: база приймає трафік лише від вебсерверів → SG бази з джерелом = SG вебсерверів; заблокувати IP → не SG, а NACL
CONFUSE: nacl
LESSON: vpc

## nacl | Network ACL | Network ACL, network ACL, NACL, NACLs | security | 🚧
WHAT: Файрвол на рівні підмережі: stateless, є Allow і Deny, правила перевіряються за номерами.
IMAGE: Шлагбаум кварталу, що нічого не пам'ятає.
WHEN: Заблокувати IP чи діапазон для всієї підмережі
EXAM: заблокувати конкретну IP-адресу → NACL з Deny; не забути порти 1024–65535 для відповідей
CONFUSE: sg
LESSON: vpc

## endpoints | VPC endpoints | VPC endpoint, VPC endpoints, Gateway endpoint, gateway endpoint, Gateway endpoints, gateway endpoints, Interface endpoint, interface endpoint, Interface endpoints, interface endpoints | network | 🔒
WHAT: Приватний доступ із VPC до сервісів AWS без інтернету: gateway (S3 і DynamoDB, безкоштовно) та interface (PrivateLink, майже всі сервіси, платно).
IMAGE: Приватні дороги до складів AWS.
WHEN: Приватні сервери працюють з S3, DynamoDB, SQS, KMS тощо без NAT
EXAM: до S3 без інтернету й безкоштовно → gateway endpoint; до SQS чи KMS приватно → interface endpoint; з офісу до S3 приватно → interface endpoint
CONFUSE: natgw, privatelink
LESSON: vpc

## privatelink | AWS PrivateLink | PrivateLink | network | 🪟
WHAT: Приватний доступ до конкретного сервісу через interface endpoint; власник публікує сервіс через NLB.
IMAGE: Віконце видачі: отримуєш послугу, не заходячи в чуже містечко.
WHEN: Надати свій сервіс іншим VPC чи акаунтам; адреси можуть перетинатися
EXAM: сервіс для сотень клієнтських VPC з однаковими CIDR → PrivateLink
CONFUSE: peering, tgw
LESSON: connectivity

## peering | VPC Peering | VPC Peering, VPC peering | network | 🌉
WHAT: Пряме з'єднання двох VPC (між акаунтами й регіонами); нетранзитивне, адреси не можуть перетинатися.
IMAGE: Міст між двома містечками.
WHEN: З'єднати 2–3 VPC просто й дешево
EXAM: дві VPC з великим трафіком найдешевше → VPC peering; A–B і B–C не дають A–C
CONFUSE: tgw
LESSON: connectivity

## tgw | AWS Transit Gateway | Transit Gateway, TGW | network | 🔀
WHAT: Мережевий хаб для десятків і сотень VPC, VPN і Direct Connect із транзитивною маршрутизацією.
IMAGE: Транспортна розв'язка, де сходяться всі дороги.
WHEN: Багато VPC і офіс; сегментація маршрутів; спільне використання через RAM
EXAM: з'єднати десятки VPC і офіс транзитивно → Transit Gateway
CONFUSE: peering
LESSON: connectivity

## vpn | AWS Site-to-Site VPN | Site-to-Site VPN, VPN, Virtual Private Gateway, VGW, Customer Gateway | network | 🔐
WHAT: Зашифровані IPsec-тунелі між офісом і AWS через інтернет; 2 тунелі, налаштування за хвилини.
IMAGE: Броньований фургон по загальній трасі.
WHEN: Швидкий і недорогий зв'язок з офісом; резерв для Direct Connect
EXAM: зашифрований канал до офісу швидко → Site-to-Site VPN; резерв для Direct Connect → VPN
CONFUSE: dx, clientvpn
LESSON: connectivity

## clientvpn | AWS Client VPN | Client VPN | network | 💻
WHAT: VPN-доступ окремих користувачів (ноутбуків) до VPC на базі OpenVPN.
IMAGE: Особистий пропуск працівника з ноутбуком.
WHEN: Віддалені співробітники підключаються до приватних ресурсів
EXAM: віддалені співробітники підключаються до VPC → Client VPN
CONFUSE: vpn
LESSON: connectivity

## dx | AWS Direct Connect | Direct Connect, Direct Connect Gateway, DX | network | 🛤️
WHAT: Виділений приватний канал до AWS: 1–400 Gbps, стабільна швидкість; прокладання — тижні; сам не шифрує.
IMAGE: Власна приватна залізниця до AWS.
WHEN: Великі постійні обсяги; стабільна затримка; дешевший вихідний трафік
EXAM: стабільний канал для великих обсягів → Direct Connect; шифрування → VPN поверх DX або MACsec; до VPC у кількох регіонах → Direct Connect Gateway
CONFUSE: vpn
LESSON: connectivity

## route53 | Amazon Route 53 | Route 53, Amazon Route 53 | network | 🧭
WHAT: Керований DNS з перевірками здоров'я і політиками маршрутизації (weighted, latency, failover, geolocation…).
IMAGE: Довідкова інтернету, що обирає, яку адресу тобі дати.
WHEN: Домени, розподіл трафіку між регіонами, перемикання на запасний
EXAM: кореневий домен на ALB → alias record; 10% трафіку на нову версію → weighted; перемикання між регіонами → failover + health checks
CONFUSE: ga, cloudfront
LESSON: edge

## r53resolver | Route 53 Resolver | Route 53 Resolver, Resolver endpoints | network | 📞
WHAT: DNS у VPC; inbound і outbound endpoints з'єднують DNS офісу і VPC.
IMAGE: Довідкові, що передають запити в обидва боки.
WHEN: Гібридний DNS між офісом і AWS
EXAM: офіс має розпізнавати приватні імена AWS → inbound endpoint; VPC — імена офісу → outbound endpoint
CONFUSE: route53
LESSON: connectivity

## cloudfront | Amazon CloudFront | CloudFront, Amazon CloudFront, Lambda@Edge, CloudFront Functions | network | 🌍
WHAT: CDN: кешує контент на edge-локаціях і прискорює доставку по всьому світу; OAC, signed URL, WAF.
IMAGE: Мережа місцевих магазинів з копіями товару.
WHEN: Статичний і динамічний вебконтент для глобальних користувачів; захист і кеш перед S3 чи ALB
EXAM: знизити затримку для глобальних користувачів → CloudFront; S3 лише через CloudFront → OAC; доступ до багатьох файлів для підписників → signed cookies
CONFUSE: ga
LESSON: edge

## ga | AWS Global Accelerator | Global Accelerator | network | 🏎️
WHAT: 2 статичні anycast IP; трафік іде мережею AWS до найближчого здорового регіону; TCP і UDP; нічого не кешує.
IMAGE: VIP-коридор аеропорту з двома постійними входами.
WHEN: Ігри та VoIP на UDP; статичні IP для whitelist; швидке перемикання між регіонами
EXAM: UDP, статичні IP, швидке перемикання регіонів → Global Accelerator
CONFUSE: cloudfront, route53
LESSON: edge

## elb | Elastic Load Balancing | Elastic Load Balancing, ELB, load balancer, Load balancer, load balancers | network | ⚖️
WHAT: Керовані балансувальники: ALB (рівень 7), NLB (рівень 4), GWLB (рівень 3); розподіляють трафік і перевіряють здоров'я цілей.
IMAGE: Адміністратор, що розводить покупців по касах.
WHEN: Розподілити трафік між серверами в кількох AZ
EXAM: HTTP-маршрутизація за шляхом → ALB; статичний IP і TCP/UDP → NLB; сторонні файрволи → GWLB
CONFUSE: asg
LESSON: scaling

## alb | Application Load Balancer | Application Load Balancer, ALB | network | 🧑‍💼
WHAT: Балансувальник рівня 7: маршрутизація за шляхом, доменом, заголовками; цілі — EC2, IP, Lambda, контейнери.
IMAGE: Адміністратор, що читає, куди тобі треба.
WHEN: Вебзастосунки й мікросервіси по HTTP/HTTPS
EXAM: /api і /images на різні сервери → path-based routing; кілька доменів із сертифікатами → SNI
CONFUSE: nlb, apigw
LESSON: scaling

## nlb | Network Load Balancer | Network Load Balancer, NLB | network | 🚇
WHAT: Балансувальник рівня 4 (TCP/UDP/TLS): мільйони запитів, наднизька затримка, статичний IP у кожній AZ.
IMAGE: Швидкісний турнікет на стадіоні.
WHEN: TCP- і UDP-сервіси; статичні IP; основа PrivateLink
EXAM: статичний IP для whitelist → NLB з Elastic IP; WAF на NLB не ставиться
CONFUSE: alb, ga
LESSON: scaling

## gwlb | Gateway Load Balancer | Gateway Load Balancer, GWLB | network | 🛃
WHAT: Балансувальник рівня 3 (GENEVE, порт 6081) для віртуальних апаратів безпеки сторонніх вендорів.
IMAGE: Пункт огляду багажу, через який проходить увесь потік.
WHEN: Пропустити трафік через сторонні файрволи, IDS/IPS
EXAM: увесь трафік через сторонній файрвол → Gateway Load Balancer
CONFUSE: networkfirewall
LESSON: scaling

## flowlogs | VPC Flow Logs | VPC Flow Logs, Flow Logs | network | 📜
WHAT: Записують метадані IP-трафіку (хто, куди, порт, ACCEPT чи REJECT) у CloudWatch Logs, S3 або Firehose.
IMAGE: Журнал в'їздів і виїздів на КПП.
WHEN: Діагностика мережі, аудит, пошук підозрілих з'єднань
EXAM: хто стукає в інстанс і чому відхилено → VPC Flow Logs
CONFUSE: cloudtrail
LESSON: connectivity

## iam | AWS IAM | IAM | security | 🪪
WHAT: Керує тим, хто (users, groups, roles) і що (policies) може робити в AWS; явний Deny перемагає все.
IMAGE: Бюро перепусток офісного центру.
WHEN: Будь-який доступ до AWS: людей, застосунків і сервісів
EXAM: застосунку на EC2 потрібен S3 → IAM role (instance profile); стеля прав для ролі → permission boundary
CONFUSE: identitycenter, cognito
LESSON: iam

## iamrole | IAM role | IAM role, IAM roles, instance profile | security | 🎫
WHAT: Набір прав, який тимчасово «надягають» сервіси, застосунки чи люди; тимчасові ключі видає STS.
IMAGE: Тимчасовий бейдж, який охорона видає на кілька годин.
WHEN: Права для EC2, Lambda, ECS; доступ з іншого акаунта; федерація
EXAM: без довгострокових ключів на EC2 → роль через instance profile; доступ з іншого акаунта → роль з trust policy
CONFUSE: iam
LESSON: iam

## sts | AWS STS | STS, AssumeRole | security | ⏳
WHAT: Видає тимчасові облікові дані: AssumeRole, AssumeRoleWithSAML, AssumeRoleWithWebIdentity.
IMAGE: Охорона, що видає тимчасові бейджі.
WHEN: Перемикання ролей, доступ з іншого акаунта, федерація
EXAM: тимчасові облікові дані → IAM role + STS; стороння компанія → умова sts:ExternalId
CONFUSE: iamrole
LESSON: iam

## organizations | AWS Organizations | AWS Organizations, Organizations | security | 🏛️
WHAT: Об'єднує багато акаунтів: OU, спільний рахунок (consolidated billing), SCP і RCP.
IMAGE: Головний офіс мережі компаній.
WHEN: Багато акаунтів; централізовані правила й рахунок
EXAM: один рахунок і спільні знижки → consolidated billing; обмежити всі акаунти → SCP
CONFUSE: controltower
LESSON: iam

## scp | Service control policy (SCP) | SCP, SCPs, service control policy, service control policies, RCP, RCPs | security | 📏
WHAT: Політика Organizations, що задає максимум дозволів для акаунтів і OU; сама прав не дає і не діє на management account. RCP (resource control policy) — така сама «стеля», але для ресурсів акаунтів.
IMAGE: Стеля правил головного офісу для філій.
WHEN: Заборонити дії або регіони для всіх акаунтів
EXAM: заборонити вимикати CloudTrail в усіх акаунтах → SCP; лише дозволені регіони → SCP з aws:RequestedRegion
CONFUSE: iam
LESSON: iam

## controltower | AWS Control Tower | Control Tower | security | 🗼
WHAT: Готова landing zone для багатьох акаунтів: Account Factory, guardrails (SCP, Config), централізовані логи.
IMAGE: Забудовник, що ставить нові офіси за стандартом.
WHEN: Швидко налаштувати мультиакаунтне середовище за кращими практиками
EXAM: багато акаунтів «правильно» з guardrails автоматично → Control Tower
CONFUSE: organizations
LESSON: iam

## identitycenter | IAM Identity Center | IAM Identity Center, Identity Center, AWS SSO | security | 🔑
WHAT: Єдиний вхід співробітників у всі акаунти AWS і бізнес-застосунки; з AD або зовнішнім IdP (Okta, Entra ID).
IMAGE: Одна перепустка на всі офіси компанії.
WHEN: Єдиний вхід (SSO) для працівників у багатьох акаунтах
EXAM: вхід через корпоративний Okta в багато акаунтів → IAM Identity Center
CONFUSE: cognito
LESSON: iam

## cognito | Amazon Cognito | Cognito, Amazon Cognito, User Pool, User Pools, user pool, user pools, Identity Pool, Identity Pools, identity pool, identity pools | security | 👥
WHAT: Вхід для клієнтів застосунку: User Pools (реєстрація, вхід, JWT) та Identity Pools (тимчасові AWS-ключі).
IMAGE: Реєстрація відвідувачів торгового центру і видача ключів від шафок.
WHEN: Вхід у мобільних і вебзастосунках, через соцмережі; прямий доступ користувачів до S3 чи DynamoDB
EXAM: реєстрація й вхід через соцмережі → User Pool; користувачі пишуть прямо в S3 → Identity Pool
CONFUSE: identitycenter
LESSON: iam

## directory | AWS Directory Service | Directory Service, Managed Microsoft AD, AD Connector, Simple AD, Active Directory | security | 📇
WHAT: Active Directory в AWS: Managed Microsoft AD (справжній AD з довірою), AD Connector (проксі до офісного AD), Simple AD.
IMAGE: Корпоративна телефонна книга з перепустками.
WHEN: Windows-застосунки з AD; вхід через наявний AD
EXAM: повний AD з довірою до офісного → Managed Microsoft AD; використати офісний AD без копіювання → AD Connector
CONFUSE: identitycenter
LESSON: iam

## ram | AWS Resource Access Manager | AWS RAM, Resource Access Manager | security | 🤝
WHAT: Ділиться ресурсами між акаунтами: підмережами (VPC sharing), Transit Gateway, правилами Resolver тощо.
IMAGE: Спільні сходи між сусідніми офісами.
WHEN: Кілька акаунтів працюють в одній мережі
EXAM: спільна VPC для кількох акаунтів → VPC sharing через AWS RAM
CONFUSE: organizations
LESSON: iam

## kms | AWS KMS | KMS, AWS KMS | security | 🗝️
WHAT: Керовані ключі шифрування з аудитом кожного використання; напряму шифрує до 4 KB, далі — envelope encryption.
IMAGE: Банк ключів, який не віддає ключ на руки.
WHEN: Шифрування S3, EBS, RDS та інших; контроль доступу до ключів
EXAM: аудит використання ключа → SSE-KMS; той самий ключ в інших регіонах → multi-Region keys; throttling KMS від S3 → S3 Bucket Keys
CONFUSE: cloudhsm, secrets
LESSON: encryption

## cloudhsm | AWS CloudHSM | CloudHSM | security | 🔐
WHAT: Виділений апаратний модуль безпеки (FIPS 140 Level 3); ключі під повним контролем клієнта.
IMAGE: Власний сейф у сховищі банку, код знаєш лише ти.
WHEN: Регуляторні вимоги до виділеного HSM; Oracle TDE, SSL offload
EXAM: ключі лише під контролем компанії, FIPS 140 Level 3 → CloudHSM
CONFUSE: kms
LESSON: encryption

## acm | AWS Certificate Manager | AWS Certificate Manager, Certificate Manager, ACM | security | 📜
WHAT: Безкоштовні публічні TLS-сертифікати для ELB, CloudFront і API Gateway з автоматичним поновленням.
IMAGE: Паспортний стіл для сайтів, що сам продовжує паспорти.
WHEN: HTTPS на балансувальниках і CloudFront
EXAM: HTTPS без ручного поновлення → ACM; сертифікат для CloudFront → регіон us-east-1
CONFUSE: kms
LESSON: encryption

## secrets | AWS Secrets Manager | Secrets Manager | security | 🤫
WHAT: Зберігає секрети (паролі, ключі) і автоматично змінює їх (ротація), зокрема для RDS і Aurora.
IMAGE: Сейф з автозаміною замків.
WHEN: Паролі до бази з регулярною зміною; секрети в кількох регіонах
EXAM: автоматично змінювати пароль до бази → Secrets Manager
CONFUSE: paramstore, kms
LESSON: encryption

## paramstore | SSM Parameter Store | SSM Parameter Store, Parameter Store | management | 🗒️
WHAT: Сховище налаштувань і секретів (SecureString з KMS) в ієрархії; standard tier безкоштовний; без вбудованої ротації.
IMAGE: Шафка з підписаними конвертами налаштувань.
WHEN: Конфігурація й рядки підключення без ротації
EXAM: дешево зберігати конфігурацію → Parameter Store
CONFUSE: secrets
LESSON: encryption

## waf | AWS WAF | AWS WAF, WAF | security | 🚨
WHAT: Вебфайрвол рівня 7 для CloudFront, ALB, API Gateway, AppSync, Cognito: SQL injection, XSS, блок країн, ліміти запитів.
IMAGE: Фейс-контроль на вході.
WHEN: Захист вебзастосунків від атак на рівні HTTP
EXAM: SQL injection чи XSS → WAF; ліміт запитів з одного IP → rate-based rule; WAF не ставиться на NLB
CONFUSE: shield, networkfirewall
LESSON: security-services

## shield | AWS Shield | AWS Shield, Shield Advanced, Shield Standard, Shield | security | 🛡️
WHAT: Захист від DDoS: Standard — безкоштовно для всіх; Advanced — платно, з командою експертів 24/7 і компенсацією витрат.
IMAGE: Дамба від натовпу.
WHEN: Захист від DDoS для CloudFront, Route 53, ELB, Global Accelerator, Elastic IP
EXAM: DDoS + експерти 24/7 + захист від зростання рахунку → Shield Advanced
CONFUSE: waf
LESSON: security-services

## fwmanager | AWS Firewall Manager | Firewall Manager | security | 🎛️
WHAT: Централізовано керує WAF, Shield Advanced, Security Groups і Network Firewall у всіх акаунтах організації.
IMAGE: Єдиний пульт правил для всієї мережі магазинів.
WHEN: Однакові правила безпеки в багатьох акаунтах
EXAM: керувати правилами WAF і Security Groups в усіх акаунтах → Firewall Manager
CONFUSE: waf, securityhub
LESSON: security-services

## networkfirewall | AWS Network Firewall | Network Firewall | security | 🧱
WHAT: Керований stateful/stateless файрвол для VPC з IPS і фільтрацією за доменами.
IMAGE: Митниця на в'їзді в містечко.
WHEN: Фільтрувати трафік VPC, зокрема вихідний за доменами
EXAM: вихідний трафік лише на дозволені домени → Network Firewall
CONFUSE: waf, sg
LESSON: security-services

## guardduty | Amazon GuardDuty | GuardDuty | security | 👮
WHAT: Виявляє загрози за CloudTrail, VPC Flow Logs і DNS-логами: криптомайнінг, викрадені ключі, підозрілі IP.
IMAGE: Розумні камери, що помічають дивну поведінку.
WHEN: Постійний моніторинг загроз в акаунтах
EXAM: незвичні API-виклики, криптомайнінг, скомпрометований інстанс → GuardDuty
CONFUSE: inspector, macie
LESSON: security-services

## inspector | Amazon Inspector | Amazon Inspector, Inspector | security | 🔍
WHAT: Безперервно шукає вразливості (CVE) в EC2, образах ECR і Lambda.
IMAGE: Технагляд, що шукає тріщини.
WHEN: Керування вразливостями серверів і контейнерів
EXAM: знайти вразливості в EC2 і контейнерах → Inspector
CONFUSE: guardduty
LESSON: security-services

## macie | Amazon Macie | Macie | security | 🐕
WHAT: За допомогою ML знаходить чутливі дані (персональні дані, номери карток) в S3.
IMAGE: Пес-шукач персональних даних.
WHEN: Аудит персональних даних у сховищі
EXAM: знайти персональні дані (PII) в S3 → Macie
CONFUSE: guardduty
LESSON: security-services

## detective | Amazon Detective | Detective | security | 🕵️
WHAT: Розслідування інцидентів: будує граф подій і допомагає знайти першопричину знахідок GuardDuty.
IMAGE: Слідчий з дошкою зв'язків.
WHEN: Аналіз уже виявленого інциденту
EXAM: знайти першопричину інциденту безпеки → Detective
CONFUSE: guardduty, securityhub
LESSON: security-services

## securityhub | AWS Security Hub | Security Hub | security | 📟
WHAT: Єдина панель знахідок безпеки (GuardDuty, Inspector, Macie…) і перевірки стандартів (CIS, PCI DSS).
IMAGE: Пульт охорони, куди сходяться всі тривоги.
WHEN: Централізований стан безпеки багатьох акаунтів
EXAM: одна панель безпеки + перевірки CIS → Security Hub
CONFUSE: fwmanager, detective
LESSON: security-services

## artifact | AWS Artifact | AWS Artifact | security | 📑
WHAT: Портал зі звітами відповідності самого AWS (SOC, PCI, ISO) і угодами (напр., BAA).
IMAGE: Архів сертифікатів будівлі для аудитора.
WHEN: Аудитору потрібні звіти AWS
EXAM: звіт SOC 2 або PCI від AWS → AWS Artifact
CONFUSE: auditmanager
LESSON: security-services

## auditmanager | AWS Audit Manager | Audit Manager | security | ✅
WHAT: Автоматично збирає докази відповідності для аудитів.
IMAGE: Помічник, що складає папку доказів для перевірки.
WHEN: Підготовка до аудитів за стандартами і регуляціями
EXAM: автоматичний збір доказів для аудиту → Audit Manager
CONFUSE: artifact
LESSON: security-services

## accessanalyzer | IAM Access Analyzer | IAM Access Analyzer, Access Analyzer, IAM Access Advisor, Access Advisor | security | 🔎
WHAT: Знаходить ресурси, відкриті зовнішнім акаунтам, і допомагає прибрати зайві права (Access Advisor показує невикористані сервіси).
IMAGE: Ревізор перепусток.
WHEN: Аудит доступів і принцип мінімальних прав
EXAM: ресурси, доступні зовнішнім акаунтам → Access Analyzer; прибрати невикористані права → Access Advisor
CONFUSE: iam
LESSON: iam

## s3ia | S3 Standard-IA і One Zone-IA | S3 Standard-IA, Standard-IA, S3 One Zone-IA, One Zone-IA | storage | 🧺
WHAT: Класи S3 для рідкого доступу з миттєвим читанням: зберігання дешевше, але є плата за кожен прочитаний гігабайт і мінімум 30 днів. One Zone-IA зберігає дані лише в одній AZ — ще дешевше, але зникне разом із зоною.
IMAGE: Комора: рідко потрібні речі, але дістаєш одразу; за кожен похід у комору — невелика плата. One Zone-IA — комора в одному будинку: згорів будинок — згоріла й комора.
WHEN: Бекапи й архіви, які читають раз на місяць, але мають відкриватися миттєво; One Zone-IA — копії та дані, які легко відтворити (мініатюри, повторні копії)
EXAM: рідкий доступ, але мілісекунди → S3 Standard-IA; ще дешевше, а дані можна відтворити → S3 One Zone-IA; доступ раз на квартал, мілісекунди → Glacier Instant Retrieval; патерн доступу невідомий → Intelligent-Tiering
CONFUSE: s3it, glacier, s3
LESSON: s3

## s3ta | S3 Transfer Acceleration | S3 Transfer Acceleration, Transfer Acceleration | storage | 🚀
WHAT: Прискорене завантаження файлів у S3 з далеких країн: дані заходять у найближчу edge-локацію і далі йдуть мережею AWS.
IMAGE: Здаєш посилку в найближче відділення, а далі вона летить власним літаком перевізника, а не трясеться місцевими дорогами.
WHEN: Користувачі з різних континентів завантажують великі файли в один bucket
EXAM: завантаження в S3 з усього світу повільне → S3 Transfer Acceleration (+ multipart upload для великих файлів)
CONFUSE: cloudfront, ga
LESSON: s3

## sse | Шифрування S3 (SSE) | SSE-S3, SSE-KMS, DSSE-KMS, SSE-C | security | 🔐
WHAT: S3 шифрує об'єкти під час запису. SSE-S3 — ключами, якими керує S3 (увімкнено за замовчуванням для всіх нових об'єктів з 2023 року); SSE-KMS — ключем у KMS з аудитом у CloudTrail і контролем доступу до ключа; DSSE-KMS — два шари шифрування; SSE-C — ключ приносить клієнт з кожним запитом, AWS його не зберігає.
IMAGE: Сейф на складі. SSE-S3 — ключ у завідувача. SSE-KMS — ключ у банківській скриньці з журналом, хто його брав. SSE-C — ключ приносиш сам щоразу й забираєш із собою.
WHEN: Будь-які дані в S3; вимоги аудиту чи власного контролю над ключами
EXAM: аудит використання ключа й окремі права на нього → SSE-KMS; ключ має бути лише в компанії → SSE-C або шифрування на клієнті; забагато запитів до KMS і дорого → S3 Bucket Keys
CONFUSE: kms, cloudhsm
LESSON: encryption

## ondemand | On-Demand Instances | On-Demand Instances, On-Demand Instance, On-Demand, On-Demand Capacity Reservations, Capacity Reservations, Capacity Reservation | cost | 🚕
WHAT: Оплата EC2 посекундно чи погодинно без жодних зобов'язань: найдорожча година, зате максимальна гнучкість. Capacity Reservations — бронь потужності в конкретній AZ за ціною On-Demand.
IMAGE: Таксі: сів — поїхав, платиш за лічильником. Capacity Reservation — таксі, замовлене заздалегідь на певний час.
WHEN: Короткі або непередбачувані навантаження, які не можна переривати; тести; перші місяці, поки навантаження невідоме
EXAM: коротка задача, яку не можна переривати, обсяг невідомий → On-Demand; гарантована потужність у певній AZ на подію → On-Demand Capacity Reservation; постійне навантаження 24/7 → Savings Plans або RI, а не On-Demand
CONFUSE: spot, savingsplans, ri
LESSON: ec2

## dedicated | Dedicated Hosts і Dedicated Instances | Dedicated Hosts, Dedicated Host, Dedicated Instances, Dedicated Instance, BYOL | compute | 🏠
WHAT: Обладнання лише для тебе. Dedicated Instances — твої інстанси на серверах, які не ділиш з іншими клієнтами. Dedicated Host — цілий фізичний сервер під твоїм контролем: видно сокети й ядра, тож можна використати власні ліцензії (BYOL).
IMAGE: Окремий будинок замість квартири в багатоповерхівці. Dedicated Host — ще й ключі від щитової: знаєш, скільки там ядер і що де стоїть.
WHEN: Ліцензії, прив'язані до фізичних ядер чи сокетів (Windows Server, SQL Server, Oracle); вимоги регулятора щодо ізоляції обладнання
EXAM: власні ліцензії на ядра чи сокети → Dedicated Hosts; ізоляція обладнання без керування хостом → Dedicated Instances
CONFUSE: ec2, placement
LESSON: ec2

## eip | Elastic IP | Elastic IP, Elastic IPs, Elastic IP address, Elastic IP addresses | network | 📌
WHAT: Статична публічна IPv4-адреса, яку можна швидко переприв'язати до іншого інстансу. Кожна публічна IPv4-адреса в AWS платна, навіть коли не використовується.
IMAGE: Постійний номер телефону, який переставляєш в інший апарат, коли старий зламався.
WHEN: Сервер, до якого звертаються за незмінною IP-адресою; білий список IP у партнерів
EXAM: фіксована IP-адреса для одного сервера → Elastic IP; статичні IP для балансувальника → NLB (по одній Elastic IP на AZ); дві статичні глобальні IP для всього застосунку → Global Accelerator
CONFUSE: nlb, ga
LESSON: vpc

## graviton | AWS Graviton | Graviton, Graviton2, Graviton3, Graviton4 | compute | 🌱
WHAT: Процесори AWS на архітектурі ARM: краще співвідношення ціни й продуктивності та менше енергії, ніж у порівнянних x86-інстансів.
IMAGE: Гібридне авто: та сама дорога, але менше пального за кілометр.
WHEN: Linux-застосунки, контейнери, бази й Lambda, які збираються під ARM
EXAM: знизити вартість обчислень без переписування логіки → інстанси Graviton (або Lambda на arm64)
CONFUSE: ec2
LESSON: cost

## parquet | Apache Parquet | Parquet, Apache Parquet, ORC | concept | 📚
WHAT: Стовпчиковий формат файлів для аналітики: читаються лише потрібні колонки, дані стиснуті, тож Athena чи Redshift Spectrum сканують у рази менше даних.
IMAGE: CSV — книжка, яку читаєш від початку до кінця, щоб знайти одне слово. Parquet — книжка зі змістом: одразу відкриваєш потрібну главу.
WHEN: Data lake у S3 під Athena, Redshift Spectrum, EMR
EXAM: зменшити вартість і пришвидшити запити Athena → Parquet або ORC + стиснення + партиції; перетворити JSON у Parquet без коду → Data Firehose
CONFUSE: athena, glue
LESSON: analytics

## fileproto | NFS, SMB, iSCSI | NFS, SMB, iSCSI | concept | 🔌
WHAT: Мови, якими сервери говорять із мережевим сховищем. NFS — спільні папки для Linux; SMB — спільні папки для Windows; iSCSI — диск по мережі (блочний доступ).
IMAGE: Три різні розетки: під кожну вилку свій сервіс AWS.
WHEN: Вибір файлового сховища чи гібридного шлюзу за протоколом
EXAM: NFS для Linux у кількох AZ → EFS; SMB з Active Directory → FSx for Windows File Server; NFS, SMB та iSCSI одночасно → FSx for NetApp ONTAP; iSCSI-диски в офісі з копією в хмарі → Volume Gateway
CONFUSE: efs, fsxwin, storagegw
LESSON: disks

## bucketpolicy | Resource-based policy (bucket policy) | bucket policy, bucket policies, Bucket policy, Bucket policies, resource-based policy, resource-based policies, Resource-based policy, Resource-based policies | security | 🪧
WHAT: Політика, прикріплена до самого ресурсу (S3 bucket, черга SQS, ключ KMS, функція Lambda): вона каже, хто може до нього звертатися, — зокрема користувачі й сервіси з інших акаунтів.
IMAGE: Табличка на дверях складу «Входити можуть: …» — на відміну від перепустки, яку людина носить із собою (identity-based policy).
WHEN: Доступ до ресурсу з іншого акаунта чи від іншого сервісу AWS; умови доступу (лише HTTPS, лише з певного VPC endpoint)
EXAM: дати іншому акаунту доступ до bucket → bucket policy з Principal цього акаунта; дозволити доступ лише через VPC endpoint → bucket policy з умовою aws:SourceVpce; вимагати HTTPS → Deny, якщо aws:SecureTransport = false
CONFUSE: iam, iamrole, scp
LESSON: iam

## boundary | Permission boundary | Permission boundary, permission boundary, Permission boundaries, permission boundaries, permissions boundary, permissions boundaries | security | 🚧
WHAT: «Стеля» прав для окремого користувача чи ролі: навіть якщо політика дає більше, діє лише те, що дозволяє і політика, і межа.
IMAGE: Обмежувач швидкості на авто стажера: хай хоч як тисне на газ, більше за ліміт не поїде.
WHEN: Дозволити розробникам самим створювати ролі, але не вищі за певні права
EXAM: розробники створюють ролі, але не можуть дати собі більше прав → permission boundary; обмежити весь акаунт чи OU → SCP
CONFUSE: scp, iam
LESSON: iam

## federation | Федерація (SAML, OIDC) | SAML 2.0, SAML, OIDC, OpenID Connect, identity federation, Identity federation, web identity federation | security | 🛂
WHAT: Вхід в AWS зі зовнішнім обліковим записом (корпоративний каталог, Google, Apple) без створення IAM-користувачів: після перевірки AWS видає тимчасові облікові дані через STS.
IMAGE: Гостьовий бейдж: охорона перевіряє паспорт іншої країни (зовнішній постачальник ідентичності) і видає тимчасову перепустку.
WHEN: Працівники входять корпоративним логіном; користувачі мобільного застосунку входять через соцмережі
EXAM: працівники входять у багато акаунтів корпоративним логіном → IAM Identity Center (SAML або Active Directory); вхід у мобільний застосунок через Google чи Apple → Cognito; не створювати IAM-користувачів для тисяч людей → федерація
CONFUSE: identitycenter, cognito, sts
LESSON: iam

## pitr | Point-in-time recovery (PITR) | PITR, point-in-time recovery, Point-in-time recovery, point-in-time restore | concept | ⏪
WHAT: Відновлення бази на будь-яку секунду в межах періоду зберігання (у RDS і DynamoDB — до 35 днів). Відновлення створює нову базу чи таблицю.
IMAGE: Перемотка відеозапису на потрібну хвилину до того, як хтось усе зіпсував.
WHEN: Захист від випадкового видалення чи псування даних
EXAM: відновити таблицю на момент перед помилковим видаленням → PITR; повернути Aurora MySQL назад без нової бази → Backtrack
CONFUSE: backup, rds
LESSON: rds

## ddbstreams | DynamoDB Streams | DynamoDB Streams | database | 📜
WHAT: Стрічка змін таблиці DynamoDB (додали, змінили, видалили елемент), яка зберігається 24 години; її можна обробляти функціями Lambda.
IMAGE: Стрічка новин «що змінилося в картотеці».
WHEN: Реагувати на зміни: надіслати лист, оновити пошук, порахувати статистику
EXAM: реагувати на кожну зміну в таблиці → DynamoDB Streams + Lambda
CONFUSE: kds, dynamodb
LESSON: nosql

## sqs | Amazon SQS | SQS, Amazon SQS | integration | 📥
WHAT: Керована черга повідомлень (pull): Standard — майже без лімітів, FIFO — порядок і без дублів; зберігання до 14 днів.
IMAGE: Талончики в черзі поліклініки.
WHEN: Розв'язати компоненти; згладити піки; воркери обробляють у своєму темпі
EXAM: не губити замовлення під час піків → SQS; порядок без дублів → SQS FIFO; обробка двічі → збільшити visibility timeout
CONFUSE: sns, kds
LESSON: integration

## sns | Amazon SNS | SNS, Amazon SNS | integration | 📣
WHAT: Pub/sub (push): одне повідомлення — багатьом підписникам (SQS, Lambda, email, SMS, HTTP).
IMAGE: Гучномовець для всіх одразу.
WHEN: Сповіщення; розсилка однієї події кільком системам
EXAM: одна подія — кілька незалежних обробників → SNS → кілька SQS (fan-out)
CONFUSE: sqs, eventbridge
LESSON: integration

## eventbridge | Amazon EventBridge | EventBridge, Amazon EventBridge, EventBridge Scheduler, CloudWatch Events | integration | 🔔
WHAT: Шина подій від AWS, твоїх застосунків і SaaS з правилами маршрутизації; Scheduler — запуск за розкладом.
IMAGE: Диспетчерська з правилами і будильником.
WHEN: Подієві архітектури; реакція на події AWS; cron без серверів
EXAM: подія від SaaS-партнера → EventBridge; запуск щоночі о 2:00 → EventBridge Scheduler; реагувати на знахідку GuardDuty → правило EventBridge
CONFUSE: sns
LESSON: integration

## stepfunctions | AWS Step Functions | Step Functions | integration | 🎼
WHAT: Оркестрація багатокрокових процесів: послідовність, розгалуження, повтори, очікування ручного схвалення.
IMAGE: Диригент з партитурою.
WHEN: Довгі бізнес-процеси; поєднання багатьох сервісів без «клею»
EXAM: процес з повторами і ручним схваленням → Step Functions Standard (до року); масові короткі потоки → Express
CONFUSE: sqs, lambda
LESSON: integration

## mq | Amazon MQ | Amazon MQ | integration | 🐇
WHAT: Керовані брокери ActiveMQ і RabbitMQ для застосунків на JMS, AMQP, MQTT, STOMP.
IMAGE: Перекладач для старих систем.
WHEN: Перенести наявний брокер повідомлень без переписування коду
EXAM: мігрувати застосунок на RabbitMQ чи ActiveMQ без змін → Amazon MQ
CONFUSE: sqs
LESSON: integration

## appflow | Amazon AppFlow | AppFlow | integration | 🔄
WHAT: Переносить дані між SaaS (Salesforce, SAP, Zendesk) і S3 чи Redshift без коду.
IMAGE: Конвеєр між чужими сервісами і твоїм складом.
WHEN: Регулярне вивантаження даних із SaaS
EXAM: дані з Salesforce у S3 без коду → AppFlow
CONFUSE: glue
LESSON: analytics

## kds | Amazon Kinesis Data Streams | Kinesis Data Streams, Kinesis, KDS | analytics | 🌊
WHAT: Потік даних у реальному часі з кількома споживачами і перемоткою (replay); зберігання від 24 год до 365 днів.
IMAGE: Річка з пам'яттю, з якої беруть воду кілька заводів.
WHEN: Клікстрім, IoT, логи в реальному часі з кількома обробниками
EXAM: реальний час + кілька споживачів + перемотка → Kinesis Data Streams
CONFUSE: firehose, sqs, msk
LESSON: analytics

## firehose | Amazon Data Firehose | Amazon Data Firehose, Kinesis Data Firehose, Data Firehose, Firehose | analytics | 🚒
WHAT: Керована доставка потоків у S3, Redshift, OpenSearch, Splunk тощо (майже реальний час), з перетворенням у Parquet.
IMAGE: Трубопровід, що сам доставляє в резервуар.
WHEN: Складати потік у сховище без коду
EXAM: потік у S3 як Parquet без серверів → Data Firehose
CONFUSE: kds
LESSON: analytics

## flink | Managed Service for Apache Flink | Managed Service for Apache Flink, Apache Flink, Flink, Kinesis Data Analytics | analytics | 🧮
WHAT: Аналіз потоків у реальному часі (агрегації у вікнах часу, аномалії) на Apache Flink.
IMAGE: Лабораторія, що аналізує воду прямо в річці.
WHEN: Обчислення над потоком «на льоту»
EXAM: аналіз потоку у вікнах часу → Managed Service for Apache Flink
CONFUSE: kds
LESSON: analytics

## kvs | Amazon Kinesis Video Streams | Kinesis Video Streams | analytics | 📹
WHAT: Приймає відеопотоки з камер для зберігання, аналітики і ML.
IMAGE: Річка відео з камер.
WHEN: Відео з камер для розпізнавання
EXAM: відео з камер на аналіз → Kinesis Video Streams
CONFUSE: kds
LESSON: analytics

## msk | Amazon MSK | MSK, Amazon MSK, Apache Kafka, Kafka | analytics | 📨
WHAT: Керований Apache Kafka (і MSK Serverless) для наявних Kafka-застосунків.
IMAGE: Та сама Kafka, але без обслуговування.
WHEN: Перенести Kafka-застосунки
EXAM: наявні Kafka-застосунки → MSK
CONFUSE: kds
LESSON: analytics

## glue | AWS Glue | AWS Glue, Glue, Glue Data Catalog, Data Catalog, Glue DataBrew | analytics | 🧴
WHAT: Serverless ETL на Spark, Data Catalog (опис таблиць) і crawlers, що самі визначають схему.
IMAGE: Бібліотекар і сортувальник озера даних.
WHEN: Перетворити й описати дані для Athena, Redshift Spectrum, EMR
EXAM: ETL без серверів, CSV → Parquet → Glue; обробляти лише нові файли → job bookmarks
CONFUSE: emr, athena
LESSON: analytics

## athena | Amazon Athena | Athena | analytics | 🦉
WHAT: Serverless SQL прямо по файлах у S3; платиш за обсяг прочитаних даних.
IMAGE: Питаєш SQL прямо в озера.
WHEN: Разові запити до логів і даних у S3
EXAM: SQL по логах у S3 без серверів → Athena; дешевше → Parquet + партиції
CONFUSE: redshift
LESSON: analytics

## emr | Amazon EMR | EMR, Amazon EMR | analytics | 🏗️
WHAT: Керовані кластери Spark, Hadoop, Hive, Presto для великих даних; task-вузли можна на Spot.
IMAGE: Важкий завод великих даних.
WHEN: Великі задачі Spark/Hadoop з контролем над фреймворками
EXAM: Spark чи Hadoop дешево → EMR з task-вузлами на Spot
CONFUSE: glue
LESSON: analytics

## opensearch | Amazon OpenSearch Service | OpenSearch Service, OpenSearch | analytics | 🔍
WHAT: Повнотекстовий пошук і аналіз логів з дашбордами (сумісний з Elasticsearch).
IMAGE: Пошуковик по твоїх даних.
WHEN: Пошук по каталогу; аналіз логів
EXAM: повнотекстовий пошук по товарах → OpenSearch
CONFUSE: athena
LESSON: analytics

## quick | Amazon Quick (QuickSight) | Amazon Quick, QuickSight, Quick Sight | analytics | 📊
WHAT: BI-дашборди для бізнесу (колишній QuickSight): serverless, SPICE, вбудовування в застосунки.
IMAGE: Вітрина з графіками для керівників.
WHEN: Інтерактивні дашборди поверх Athena, Redshift та інших джерел
EXAM: дашборди для бізнесу → Amazon Quick (QuickSight)
CONFUSE: opensearch
LESSON: analytics

## lakeformation | AWS Lake Formation | Lake Formation | analytics | 🏞️
WHAT: Будує і захищає data lake на S3: дозволи до окремих колонок і рядків для Athena, Redshift Spectrum, EMR, Glue.
IMAGE: Охорона озера з перепустками до окремих ділянок.
WHEN: Детальні права доступу до даних в озері; обмін між акаунтами
EXAM: права до колонок і рядків у data lake → Lake Formation
CONFUSE: glue
LESSON: analytics

## dataexchange | AWS Data Exchange | Data Exchange | analytics | 🛍️
WHAT: Маркетплейс сторонніх датасетів з доставкою в S3.
IMAGE: Магазин готових даних.
WHEN: Купити чи отримати дані від постачальників
EXAM: сторонні датасети від постачальника → Data Exchange
CONFUSE: appflow
LESSON: analytics

## rekognition | Amazon Rekognition | Rekognition | ml | 👁️
WHAT: Аналіз зображень і відео: об'єкти, обличчя, текст, модерація контенту.
IMAGE: Очі застосунку.
WHEN: Модерація фото, пошук облич, розпізнавання об'єктів
EXAM: модерація фото користувачів → Rekognition
CONFUSE: textract
LESSON: ai

## textract | Amazon Textract | Textract | ml | 🧾
WHAT: Витягує текст, форми і таблиці зі сканів і PDF.
IMAGE: Бухгалтер, що читає документи.
WHEN: Обробка рахунків, анкет, договорів
EXAM: дані з рахунків і форм у PDF → Textract
CONFUSE: rekognition, comprehend
LESSON: ai

## comprehend | Amazon Comprehend | Comprehend | ml | 💬
WHAT: Аналіз тексту (NLP): тональність, сутності, ключові фрази, мова, персональні дані.
IMAGE: Читач, що розуміє настрій тексту.
WHEN: Аналіз відгуків, листів, звернень
EXAM: тональність відгуків → Comprehend
CONFUSE: textract
LESSON: ai

## transcribe | Amazon Transcribe | Transcribe | ml | 👂
WHAT: Перетворює мову на текст (дзвінки, відео, субтитри).
IMAGE: Вуха застосунку.
WHEN: Розшифровка дзвінків, субтитри
EXAM: записи дзвінків у текст → Transcribe
CONFUSE: polly
LESSON: ai

## polly | Amazon Polly | Polly | ml | 🦜
WHAT: Перетворює текст на природне мовлення.
IMAGE: Папуга, що читає вголос.
WHEN: Озвучення статей, голосові відповіді
EXAM: озвучити текст → Polly
CONFUSE: transcribe
LESSON: ai

## translate | Amazon Translate | Amazon Translate, Translate | ml | 🌐
WHAT: Машинний переклад тексту.
IMAGE: Перекладач у кишені.
WHEN: Локалізація контенту, переклад звернень
EXAM: перекласти контент → Translate
CONFUSE: comprehend
LESSON: ai

## lex | Amazon Lex | Amazon Lex, Lex | ml | 🤖
WHAT: Чат-боти з розумінням голосу і тексту.
IMAGE: Співрозмовник на лінії.
WHEN: Бот для сайту чи кол-центру
EXAM: чат-бот → Lex
CONFUSE: polly
LESSON: ai

## sagemaker | Amazon SageMaker AI | SageMaker AI, SageMaker, Amazon SageMaker | ml | 🧪
WHAT: Платформа, щоб будувати, навчати й розгортати власні ML-моделі.
IMAGE: Лабораторія для вирощування власного «мозку».
WHEN: Потрібна власна модель, а не готовий сервіс
EXAM: навчити й розгорнути свою модель → SageMaker AI
CONFUSE: rekognition
LESSON: ai

## cloudwatch | Amazon CloudWatch | CloudWatch, Amazon CloudWatch, CloudWatch agent, CloudWatch Logs, CloudWatch alarm, CloudWatch alarms | management | 📈
WHAT: Метрики, логи, аларми й дашборди; пам'ять і диск EC2 — лише з CloudWatch agent.
IMAGE: Приладова панель автомобіля.
WHEN: Моніторинг, сповіщення, реакція на метрики
EXAM: пам'ять і диск EC2 → CloudWatch agent; сповіщення про ERROR у логах → metric filter + alarm
CONFUSE: cloudtrail
LESSON: ops

## cloudtrail | AWS CloudTrail | CloudTrail | management | 🎥
WHAT: Журнал усіх викликів API: хто, що, коли і звідки; 90 днів історії безкоштовно.
IMAGE: Відеореєстратор дій.
WHEN: Аудит, розслідування, комплаєнс
EXAM: хто видалив чи змінив ресурс → CloudTrail; журнал усіх акаунтів → organization trail
CONFUSE: cloudwatch, config
LESSON: ops

## config | AWS Config | AWS Config, Config rules, Config rule, Config | management | 📸
WHAT: Інвентар та історія налаштувань ресурсів і правила відповідності з автовиправленням.
IMAGE: Фотоархів стану з перевіркою на відповідність правилам.
WHEN: Комплаєнс, відстеження змін конфігурацій
EXAM: перевіряти, що всі EBS зашифровані → Config rule; автоматично виправляти → remediation
CONFUSE: cloudtrail
LESSON: ops

## xray | AWS X-Ray | X-Ray | management | 🩻
WHAT: Трасування запитів через мікросервіси: де затримка чи помилка.
IMAGE: Рентген маршруту запиту.
WHEN: Пошук вузьких місць у розподілених застосунках
EXAM: де гальмує запит між мікросервісами → X-Ray
CONFUSE: cloudwatch
LESSON: ops

## ssm | AWS Systems Manager | Systems Manager, SSM, Session Manager, Patch Manager, Run Command | management | 🕹️
WHAT: Керування автопарком серверів: вхід без SSH (Session Manager), команди (Run Command), патчі (Patch Manager), Parameter Store.
IMAGE: Пульт керування автопарком.
WHEN: Адміністрування багатьох EC2 і власних серверів
EXAM: доступ без відкритого порту 22 → Session Manager; патчі за розкладом → Patch Manager
CONFUSE: config
LESSON: ops

## cloudformation | AWS CloudFormation | CloudFormation, StackSets | management | 📐
WHAT: Інфраструктура як код: шаблони YAML/JSON створюють однакові середовища; StackSets — у багатьох акаунтах і регіонах.
IMAGE: Креслення будинку.
WHEN: Повторюване розгортання, DR-регіон, багато акаунтів
EXAM: однакова інфраструктура в багатьох акаунтах → StackSets; швидко відтворити в іншому регіоні → CloudFormation
CONFUSE: beanstalk
LESSON: ops

## servicecatalog | AWS Service Catalog | Service Catalog | management | 📚
WHAT: Каталог затверджених шаблонів для самообслуговування користувачів з обмеженими правами.
IMAGE: Меню дозволених страв.
WHEN: Стандартизувати, що можуть запускати команди
EXAM: користувачі запускають лише затверджені шаблони → Service Catalog
CONFUSE: cloudformation
LESSON: ops

## trustedadvisor | AWS Trusted Advisor | Trusted Advisor | management | 🧑‍🏫
WHAT: Рекомендації щодо вартості, безпеки, стійкості, продуктивності й лімітів сервісів.
IMAGE: Досвідчений порадник-аудитор.
WHEN: Регулярна перевірка акаунта на кращі практики
EXAM: перевірити наближення до лімітів сервісів → Trusted Advisor або Service Quotas
CONFUSE: computeoptimizer
LESSON: ops

## computeoptimizer | AWS Compute Optimizer | Compute Optimizer | cost | 📏
WHAT: ML-рекомендації правильного розміру для EC2, Auto Scaling, EBS, Lambda, ECS на Fargate, RDS.
IMAGE: Кравець, що підбирає розмір одягу.
WHEN: Інстанси завеликі або замалі
EXAM: рекомендації щодо розміру інстансів → Compute Optimizer
CONFUSE: trustedadvisor
LESSON: cost

## health | AWS Health Dashboard | AWS Health Dashboard, Health Dashboard | management | 🩺
WHAT: Події AWS, що зачіпають саме твої ресурси (збої, планове обслуговування); інтеграція з EventBridge.
IMAGE: Лікар, що попереджає про планові процедури.
WHEN: Знати про обслуговування і збої, що стосуються тебе
EXAM: сповіщення про планове обслуговування інстансів → Health Dashboard + EventBridge
CONFUSE: cloudwatch
LESSON: ops

## licensemanager | AWS License Manager | License Manager | management | 🧾
WHAT: Облік і контроль ліцензій (Microsoft, Oracle, SAP), заборона перевищення лімітів.
IMAGE: Облікова книга ліцензій.
WHEN: Власні ліцензії (BYOL) на EC2 і власних серверах
EXAM: контролювати використання ліцензій → License Manager
CONFUSE: ec2
LESSON: ops

## grafana | Managed Grafana і Managed Prometheus | Amazon Managed Grafana, Managed Grafana, Managed Service for Prometheus, Grafana, Prometheus | management | 📉
WHAT: Керовані Grafana (дашборди) і Prometheus (метрики контейнерів) без власних серверів.
IMAGE: Табло з графіками для DevOps.
WHEN: Метрики EKS і контейнерів у звичних інструментах
EXAM: дашборди Prometheus для EKS без серверів → Managed Prometheus + Managed Grafana
CONFUSE: cloudwatch
LESSON: ops

## costexplorer | AWS Cost Explorer | Cost Explorer | cost | 🧮
WHAT: Аналіз і прогноз витрат, поради щодо Savings Plans і RI.
IMAGE: Банківська виписка з графіками.
WHEN: Зрозуміти, куди йдуть гроші
EXAM: проаналізувати витрати за місяці і спрогнозувати → Cost Explorer
CONFUSE: budgets, cur
LESSON: cost

## budgets | AWS Budgets | AWS Budgets, Budgets | cost | 💳
WHAT: Сповіщення, коли фактичні чи прогнозовані витрати перевищать поріг; Budget Actions — автоматичні дії.
IMAGE: Ліміт на картці з SMS-сповіщенням.
WHEN: Контроль бюджету
EXAM: сповіщення, коли прогноз перевищить суму → AWS Budgets
CONFUSE: costexplorer
LESSON: cost

## cur | AWS Cost and Usage Report | Cost and Usage Report, CUR | cost | 📃
WHAT: Найдетальніші дані про витрати (кожен ресурс, кожна година) у S3 для аналізу в Athena.
IMAGE: Чек до копійки.
WHEN: Глибокий аналіз і розподіл витрат
EXAM: найдетальніші дані про витрати для Athena → Cost and Usage Report
CONFUSE: costexplorer
LESSON: cost

## savingsplans | Savings Plans | Savings Plans, Savings Plan, Compute Savings Plans, Compute Savings Plan, EC2 Instance Savings Plan, Database Savings Plans | cost | 💰
WHAT: Знижка за зобов'язання витрачати $/год 1 або 3 роки: Compute (до ~66%, будь-яке сімейство, Fargate, Lambda), EC2 Instance (до ~72%).
IMAGE: Абонемент у спортзал.
WHEN: Стабільне навантаження з потребою гнучкості
EXAM: 24/7 на роки + гнучкість сімейств і Fargate → Compute Savings Plans
CONFUSE: ri, spot
LESSON: cost

## ri | Reserved Instances | Reserved Instances, Reserved Instance, Standard RI, Convertible RI, RIs, RI | cost | 📅
WHAT: Знижка до ~72% за зобов'язання на 1–3 роки для конкретного типу інстансу; Convertible — можна міняти сімейство.
IMAGE: Лізинг конкретного авто.
WHEN: Стабільне навантаження на відомому типі інстансу
EXAM: стабільні інстанси 24/7 → Reserved Instances або Savings Plans
CONFUSE: savingsplans
LESSON: ec2

## spot | Spot Instances | Spot Instances, Spot Instance, Spot | cost | 🎟️
WHAT: Вільні потужності EC2 зі знижкою до 90%; AWS може забрати їх з попередженням за 2 хвилини.
IMAGE: Горящий тур.
WHEN: Задачі, які можна переривати: batch, CI/CD, рендеринг, stateless-сервери в ASG
EXAM: нічні задачі, які можна перезапускати, найдешевше → Spot Instances
CONFUSE: savingsplans
LESSON: ec2

## anomaly | Cost Anomaly Detection | Cost Anomaly Detection | cost | 🚩
WHAT: ML-сповіщення про незвичні стрибки витрат.
IMAGE: Банк помітив дивну покупку.
WHEN: Вчасно ловити неочікувані витрати
EXAM: автоматично помітити раптовий стрибок витрат → Cost Anomaly Detection
CONFUSE: budgets
LESSON: cost

## storagegw | AWS Storage Gateway | Storage Gateway, S3 File Gateway, File Gateway, Volume Gateway, Tape Gateway | migration | 🔌
WHAT: Гібридний доступ офісу до сховища AWS з локальним кешем: S3 File, Volume (Cached чи Stored) і Tape Gateway.
IMAGE: Перехідник між офісом і хмарою.
WHEN: Офісні програми зберігають дані в AWS; заміна стрічок
EXAM: NFS/SMB-папки з файлами в S3 → S3 File Gateway; замінити фізичні стрічки → Tape Gateway
CONFUSE: datasync
LESSON: migration

## datasync | AWS DataSync | DataSync | migration | 🚚
WHAT: Онлайн-перенесення і синхронізація великих обсягів з NFS, SMB, HDFS у S3, EFS, FSx — з перевіркою і за розкладом.
IMAGE: Швидкісна вантажівка по трасі.
WHEN: Перенести терабайти мережею; регулярна синхронізація
EXAM: перенести 50 TB з NAS мережею з перевіркою → DataSync
CONFUSE: storagegw, snow
LESSON: migration

## snow | AWS Snow Family | Snowball Edge, Snowball, Snow Family, Snowcone, Snowmobile | migration | 🧳
WHAT: Фізичні пристрої для офлайн-перенесення терабайтів і петабайтів та обчислень на місці (з 11.2025 недоступні новим клієнтам).
IMAGE: Контейнер з даними, який везуть поштою.
WHEN: Мережа надто повільна чи дорога
EXAM: сотні терабайтів і повільний інтернет → Snowball Edge
CONFUSE: datasync
LESSON: migration

## transfer | AWS Transfer Family | Transfer Family, SFTP, FTPS | migration | 📮
WHAT: Керований SFTP/FTPS/FTP/AS2-сервер поверх S3 або EFS.
IMAGE: Поштове віконце для партнерів.
WHEN: Партнери надсилають файли за старими протоколами
EXAM: партнери надсилають файли по SFTP, а зберігати треба в S3 → Transfer Family
CONFUSE: datasync
LESSON: migration

## dms | AWS Database Migration Service | Database Migration Service, AWS DMS, DMS, CDC | migration | 🚛
WHAT: Міграція баз з мінімальним простоєм і безперервним копіюванням змін (CDC).
IMAGE: Переїзд магазину без зачинення.
WHEN: Перенести базу в AWS або між рушіями
EXAM: MySQL з офісу в RDS з мінімальним простоєм → DMS; різні рушії → SCT + DMS
CONFUSE: sct
LESSON: migration

## sct | AWS Schema Conversion Tool | Schema Conversion Tool, DMS Schema Conversion, SCT | migration | 🔤
WHAT: Конвертує схеми й код баз між різними рушіями (Oracle → PostgreSQL, сховища даних → Redshift).
IMAGE: Перекладач креслень.
WHEN: Міграції між різними рушіями (гетерогенні)
EXAM: Oracle → Aurora PostgreSQL → SCT (схема) + DMS (дані)
CONFUSE: dms
LESSON: migration

## mgn | AWS Application Migration Service | Application Migration Service, MGN | migration | 🏠
WHAT: Перенесення серверів «як є» (фізичних, VMware, з інших хмар) в EC2 з безперервною реплікацією.
IMAGE: Перевезти будинок цілком.
WHEN: Швидко перенести сотні серверів без змін
EXAM: сотні серверів в EC2 без змін (lift-and-shift) → Application Migration Service
CONFUSE: vmware, dms
LESSON: migration

## drs | AWS Elastic Disaster Recovery | Elastic Disaster Recovery, DRS | migration | 🚑
WHAT: Відновлення серверів в AWS після аварії: постійна реплікація, RPO — секунди, RTO — хвилини.
IMAGE: Швидка допомога для серверів.
WHEN: Резерв для власних або хмарних серверів
EXAM: DR для серверів з офісу з RPO в секунди → Elastic Disaster Recovery
CONFUSE: backup
LESSON: resilience

## region | Region (регіон) | Region, Regions | concept | 🗺️
WHAT: Географічний регіон AWS (напр., eu-central-1) з кількома ізольованими зонами доступності.
IMAGE: Місто в мережі міст AWS.
WHEN: Вибір за законами, затримкою, ціною і наявністю сервісів
EXAM: дані мають лишатися в ЄС → регіон у ЄС + SCP на інші регіони
CONFUSE: az
LESSON: cloud

## az | Availability Zone | Availability Zone, Availability Zones, AZ, AZs | concept | 🏢
WHAT: Один або кілька ізольованих дата-центрів у регіоні з окремим живленням і мережею.
IMAGE: Окремий район міста.
WHEN: Висока доступність: розкладати ресурси щонайменше у 2 AZ
EXAM: пережити збій дата-центру → розгортання у 2+ AZ
CONFUSE: region
LESSON: cloud

## multiaz | Multi-AZ | Multi-AZ | concept | 👯
WHAT: Розгортання в кількох AZ; у RDS — синхронна запасна копія з автоматичним перемиканням.
IMAGE: Дублер у запасній кімнаті.
WHEN: Висока доступність баз і застосунків
EXAM: автоматичне перемикання бази в іншу AZ → RDS Multi-AZ; з запасної копії Multi-AZ читати не можна
CONFUSE: readreplica
LESSON: rds

## readreplica | Read replica | Read Replicas, Read replicas, Read Replica, Read replica, read replicas, read replica | concept | 📖
WHAT: Асинхронна копія бази лише для читання: розвантажує основну базу, може бути в іншому регіоні.
IMAGE: Помічник, що відповідає на запитання.
WHEN: Багато читань і звітів
EXAM: звіти гальмують основну базу → read replica
CONFUSE: multiaz
LESSON: rds

## rpo | RPO | RPO | concept | ⏪
WHAT: Recovery Point Objective — скільки даних (за часом) можна втратити під час аварії.
IMAGE: Скільки останніх сторінок щоденника не шкода.
WHEN: Вибір стратегії бекапів і реплікації
EXAM: RPO близько 1 с для реляційної бази між регіонами → Aurora Global Database
CONFUSE: rto
LESSON: resilience

## rto | RTO | RTO | concept | ⏱️
WHAT: Recovery Time Objective — за скільки часу система має знову запрацювати.
IMAGE: Через скільки ресторан знову годує гостей.
WHEN: Вибір стратегії відновлення
EXAM: RTO десятки хвилин і мінімальна ціна → Pilot Light
CONFUSE: rpo
LESSON: resilience

## cidr | CIDR | CIDR | concept | 🔢
WHAT: Запис діапазону IP-адрес (10.0.0.0/16): чим менше число після «/», тим більше адрес.
IMAGE: Номери будинків у містечку.
WHEN: Планування VPC і підмереж
EXAM: розмір VPC — від /16 до /28; peering неможливий при перетині CIDR
CONFUSE: subnet
LESSON: vpc

## ami | AMI | AMI, AMIs | concept | 📀
WHAT: Образ машини: ОС + ПЗ + налаштування для запуску EC2; регіональний, копіюється в інші регіони.
IMAGE: Зліпок комп'ютера для клонування.
WHEN: Швидкий старт однакових серверів; резерв в іншому регіоні
EXAM: той самий сервер в іншому регіоні → copy AMI; швидкий старт → golden AMI
CONFUSE: ebs
LESSON: ec2

## placement | Placement group | placement group, placement groups, Placement group, Placement groups | concept | 🧷
WHAT: Як розміщувати EC2: cluster (поруч і швидко), spread (окремо, до 7 на AZ), partition (секціями).
IMAGE: Команда за одним столом, кожен у своєму будинку або секції.
WHEN: HPC, критичні сервери, великі розподілені системи
EXAM: HPC з мінімальною затримкою → cluster; критичні сервери окремо → spread; Hadoop чи Kafka → partition
CONFUSE: az
LESSON: ec2

## iops | IOPS | IOPS | concept | 💨
WHAT: Кількість операцій читання-запису за секунду — швидкість диска для дрібних запитів.
IMAGE: Скільки коробок на секунду встигає обробити комірник.
WHEN: Вибір типу EBS під базу
EXAM: понад 80 000 IOPS на одному томі → io2 Block Express; gp3 — IOPS окремо від розміру
CONFUSE: ebs
LESSON: disks

## envelope | Envelope encryption | envelope encryption, Envelope encryption | concept | ✉️
WHAT: Дані шифрує ключ даних, а його шифрує ключ KMS; так шифрують дані понад 4 KB.
IMAGE: Лист у конверті, конверт у сейфі.
WHEN: Шифрування великих файлів через KMS
EXAM: шифрувати файли більші за 4 KB через KMS → envelope encryption
CONFUSE: kms
LESSON: encryption

## oac | Origin Access Control | Origin Access Control, OAC, OAI | concept | 🔏
WHAT: Дозволяє читати приватний bucket S3 лише через CloudFront; OAI — застарілий попередник.
IMAGE: Склад відчиняється лише кур'єрам CloudFront.
WHEN: Статичний сайт чи медіа з приватного S3 через CloudFront
EXAM: заборонити прямий доступ до S3, лише через CloudFront → OAC
CONFUSE: presigned
LESSON: edge

## presigned | Presigned URL | presigned URL, Presigned URL, presigned URLs, Presigned URLs | concept | 🎫
WHAT: Тимчасове посилання на приватний об'єкт S3 з правами того, хто його підписав.
IMAGE: Тимчасовий пропуск на одну коробку.
WHEN: Дати користувачу скачати чи завантажити файл, не відкриваючи bucket
EXAM: тимчасово дати доступ до приватного файлу → presigned URL
CONFUSE: oac
LESSON: s3

## objectlock | S3 Object Lock | S3 Object Lock, Object Lock, WORM | concept | ⏲️
WHAT: WORM-захист об'єктів: compliance (не видалить ніхто, навіть root), governance (з особливим дозволом), legal hold.
IMAGE: Сейф з таймером.
WHEN: Регуляторне зберігання записів
EXAM: ніхто не може видалити записи 7 років → Object Lock compliance mode
CONFUSE: versioning
LESSON: s3

## lifecycle | S3 Lifecycle | Lifecycle rules, lifecycle rules, Lifecycle rule, lifecycle rule, Lifecycle, lifecycle | concept | ♻️
WHAT: Правила, що автоматично переводять об'єкти в дешевші класи і видаляють їх з часом.
IMAGE: Автоматичне переселення речей з віком.
WHEN: Дані старіють і рідше потрібні
EXAM: через 90 днів у Glacier, через 5 років видалити → lifecycle rule
CONFUSE: s3it
LESSON: s3

## versioning | Versioning | Versioning, versioning | concept | 🕰️
WHAT: Зберігає всі версії об'єкта в S3; видалення ставить маркер, стару версію можна повернути.
IMAGE: Машина часу для файлів.
WHEN: Захист від випадкового видалення; потрібна для реплікації
EXAM: захист від випадкового видалення → versioning (+ MFA Delete)
CONFUSE: objectlock
LESSON: s3

## crr | S3 Replication (CRR / SRR) | Cross-Region Replication, Same-Region Replication, CRR, SRR | concept | 🔁
WHAT: Автоматичне копіювання нових об'єктів S3 в інший регіон (CRR) або в той самий (SRR); потрібен versioning.
IMAGE: Філія складу в іншому місті.
WHEN: Відновлення після аварії, комплаєнс, менша затримка для інших регіонів
EXAM: копія кожного нового об'єкта в іншому регіоні → CRR; наявні об'єкти → S3 Batch Replication
CONFUSE: lifecycle
LESSON: s3

## dlq | Dead-letter queue | dead-letter queues, dead-letter queue, Dead-letter queue, DLQ | concept | ☠️
WHAT: Окрема черга для повідомлень, які не вдалося обробити після кількох спроб.
IMAGE: Папка для безнадійних талончиків.
WHEN: Відокремити «отруйні» повідомлення для аналізу
EXAM: повідомлення постійно падають з помилкою → DLQ
CONFUSE: visibility
LESSON: integration

## visibility | Visibility timeout | visibility timeout, Visibility timeout | concept | 🙈
WHAT: Час, протягом якого взяте з SQS повідомлення невидиме для інших споживачів (за замовчуванням 30 с, максимум 12 год).
IMAGE: Талон у руках лікаря.
WHEN: Налаштування під тривалість обробки
EXAM: повідомлення обробляються двічі → збільшити visibility timeout
CONFUSE: dlq
LESSON: integration

## fifo | FIFO | FIFO | concept | 🔢
WHAT: «Першим прийшов — першим пішов»: у SQS і SNS FIFO — строгий порядок у групі і без дублів.
IMAGE: Сувора черга за номерками.
WHEN: Порядок важливий: транзакції, команди
EXAM: строгий порядок без дублів → SQS FIFO
CONFUSE: sqs
LESSON: integration

## fanout | Fan-out | fan-out, Fan-out | concept | 🪭
WHAT: Шаблон: одне повідомлення SNS розсилається в кілька черг SQS для незалежної обробки.
IMAGE: Оголошення в гучномовець і копія в кожну поштову скриньку.
WHEN: Одна подія — кілька незалежних обробників
EXAM: три незалежні обробники кожної події → SNS fan-out → SQS
CONFUSE: sns
LESSON: integration

## coldstart | Cold start | cold starts, cold start, Cold start | concept | 🥶
WHAT: Затримка першого виклику Lambda, поки створюється й ініціалізується середовище.
IMAGE: Кухар щойно прийшов і розкладає ножі.
WHEN: API з вимогами до затримки
EXAM: прибрати cold start → provisioned concurrency; для Java → SnapStart
CONFUSE: lambda
LESSON: serverless

## shared | Shared Responsibility Model | Shared Responsibility Model, Shared Responsibility | concept | 🤝
WHAT: AWS відповідає за безпеку хмари (OF), клієнт — за безпеку в хмарі (IN): дані, доступи, налаштування.
IMAGE: Орендодавець і орендар квартири.
WHEN: Питання «хто відповідає за…»
EXAM: хто патчить ОС на EC2 → клієнт; на RDS → AWS
CONFUSE: wellarchitected
LESSON: responsibility

## wellarchitected | AWS Well-Architected | Well-Architected Framework, Well-Architected Tool, Well-Architected | concept | 🏛️
WHAT: Рамка кращих практик AWS із 6 стовпів: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability.
IMAGE: Шість питань інспектора до будь-якої архітектури.
WHEN: Оцінка й покращення архітектури
EXAM: самоперевірка архітектури → Well-Architected Tool
CONFUSE: shared
LESSON: responsibility

## stateless | Stateless | stateless, Stateless | concept | 🎒
WHAT: Сервер не тримає стан користувача (сесії), тому його можна вільно додавати й прибирати.
IMAGE: Касир не тримає твій кошик.
WHEN: Горизонтальне масштабування
EXAM: сесії для stateless-серверів → ElastiCache або DynamoDB
CONFUSE: elasticache
LESSON: scaling

## mfa | MFA | MFA Delete, MFA | concept | 📱
WHAT: Багатофакторна автентифікація: пароль + одноразовий код; MFA Delete захищає версії в S3 від видалення.
IMAGE: Другий замок на дверях.
WHEN: Root-користувач, адміністратори, небезпечні дії
EXAM: захистити root → MFA; вимагати MFA для видалення → умова aws:MultiFactorAuthPresent або MFA Delete
CONFUSE: iam
LESSON: iam
