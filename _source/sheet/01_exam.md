# AWS Solutions Architect – Associate (SAA-C03): шпаргалка

## 1. Іспит: головні факти

- **Код іспиту:** SAA-C03 — актуальний станом на вересень 2026. Сайти, які пишуть про «SAA-C04», помиляються: на сайті AWS такого іспиту немає.
- **Формат:** 65 питань = 50 оцінюваних + 15 неоцінюваних (які саме — невідомо, тож старайся на кожному). **130 хвилин.** Ціна **$150**.
- **Прохідний бал:** 720 з 1000. Модель компенсаторна: не треба «здати» кожен домен окремо — рахується загальний бал.
- **Штрафу за неправильну відповідь немає** → ніколи не залишай питання порожнім.
- **Типи питань:** multiple choice (1 правильна з 4) і multiple response (2 або більше правильних з 5+; у питанні написано, скільки обрати).
- **Домени:** Design Secure Architectures — **30%**, Resilient — **26%**, High-Performing — **24%**, Cost-Optimized — **20%**.
- **+30 хвилин (ESL +30):** якщо англійська не рідна — у кабінеті aws.training/Certification → *Request Exam Accommodations* → *ESL +30 MINUTES*. Подається один раз і **до запису на іспит** (якщо вже записаний — скасуй запис, подай запит, запишись знову). Схвалюється автоматично.
- **Мови:** англійська, французька, італійська (до 31.12.2026), японська, корейська, португальська (Бразилія), іспанська, китайська. Української немає — вчи терміни англійською.
- **Назви сервісів:** в іспиті короткі назви (Amazon SNS замість Amazon Simple Notification Service). Повні назви — за кнопкою **Help** під час іспиту.
- **Де складати:** центр Pearson VUE або онлайн з проктором (вдома, з веб-камерою, чистий стіл).
- **Результат:** одразу після іспиту бала не показують — він приходить на email і в кабінет, зазвичай за кілька годин (AWS обіцяє до 5 робочих днів).
- Сертифікат діє **3 роки**. Після здачі в кабінеті є знижка 50% на наступний іспит AWS.

## 2. Тактика: як читати питання {quick}

- Спочатку прочитай **останнє речення** — там критерій вибору («MOST cost-effective», «LEAST operational overhead»).
- Подумки випиши всі вимоги: RPO/RTO, бюджет, «без змін коду», «serverless», регіони, шифрування. Правильна відповідь виконує **всі** вимоги одночасно.
- Відкидай неможливе: Deny-правило в Security Group, Gateway endpoint для SQS, WAF на NLB, читання з RDS Multi-AZ standby, EBS-том до інстансу в іншій AZ, Lambda на 2 години.
- Якщо є керований (managed) сервіс, варіант «напишемо свій скрипт на EC2 / cron» майже завжди неправильний.
- Два варіанти схожі — шукай одну відмінну деталь: Standard vs FIFO, Gateway vs Interface, User pool vs Identity pool, Compliance vs Governance.
- Час: ~2 хв на питання. Не впевнений — дай найкращу відповідь, познач *Flag for review* і йди далі. В кінці поверніться до позначених.
- В питаннях можуть бути старі назви: Kinesis Data Firehose = **Amazon Data Firehose**; QuickSight = **Amazon Quick**; Kinesis Data Analytics = **Managed Service for Apache Flink**; SageMaker = **SageMaker AI**; AWS SSO = **IAM Identity Center**; CloudWatch Events = **EventBridge**.

### Ключові фрази в питаннях

| Фраза в питанні | Що це означає |
|---|---|
| MOST cost-effective / LOWEST cost | Найдешевше, що виконує **всі** вимоги: Spot, lifecycle S3, serverless, Savings Plans, gateway endpoint |
| LEAST operational overhead / minimal management | Керований або serverless сервіс, мінімум компонентів, без власних скриптів і EC2 |
| MOST secure / least privilege | Мінімальні права, IAM roles замість ключів, KMS, приватні підмережі, VPC endpoints |
| highly available | Кілька AZ: Multi-AZ, ASG у 2+ AZ + ALB |
| fault tolerant | Працює **без перерви** навіть під час збою (надлишковість, active-active) |
| durable | Дані не загубляться: S3 (11 дев'яток), реплікація, бекапи |
| scalable / elastic | Auto Scaling, serverless, DynamoDB on-demand, Aurora Serverless |
| decouple / buffer / spikes | SQS між компонентами |
| real-time (мілісекунди, свої споживачі, replay) | Kinesis Data Streams |
| near real-time, доставка в S3/Redshift/OpenSearch без коду | Amazon Data Firehose |
| without code changes / minimal changes | RDS Proxy, Storage Gateway, EFS, Global Accelerator, MGN (lift-and-shift), Babelfish |
| temporary credentials | IAM Role + STS |
| static IP | NLB з Elastic IP або Global Accelerator |
| global users + static/dynamic web content | CloudFront |
| global users + TCP/UDP + fast regional failover | Global Accelerator |
| on-premises + low-latency access to cloud storage | Storage Gateway (локальний кеш) |
| migrate TBs/PBs over the network | DataSync |
| orchestrate / workflow / human approval | Step Functions |
