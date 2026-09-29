## 29. Як готуватися: план на 14 днів і день іспиту

### Як вчитися на цьому сайті

- **📘 Шпаргалка** — прочитай розділ, потім увімкни «🙈 Сховати відповіді» і пройди тригери, торкаючись розмитої відповіді лише після того, як сам відповів. Позначай «Вивчено».
- **⚡ Швидко** — лише тригери, пастки, порівняння і цифри. Для повторення в останні дні.
- **🗺️ Схеми** — усі архітектурні схеми в одному місці.
- **🎲 Квіз** — випадкові тригери; ті, що «не знав», повертаються частіше.
- **📝 Тест** — 65 практичних питань у стилі іспиту: режим «Тренування» (пояснення одразу) і «Іспит» (таймер, результат у кінці).
- Прогрес зберігається в браузері телефона. Сайт працює і без інтернету, якщо хоч раз відкрити його онлайн. На телефоні його можна додати на головний екран як застосунок.

### План на 14 днів (1–2 години на день)

| День | Що вчити | Практика |
|---|---|---|
| 1 | Розділи 1–3: іспит, тактика, основи | Квіз: 20 тригерів |
| 2 | 4–5: IAM, шифрування | Квіз по розділах 4–5 |
| 3 | 6: сервіси безпеки | Тест: набір «Безпека» у режимі «Тренування» |
| 4 | 7: VPC і мережа, схеми VPC і гібриду | Квіз по розділу 7 |
| 5 | 8–9: Route 53, CloudFront, Global Accelerator, ELB, Auto Scaling | Квіз по розділах 8–9 |
| 6 | 10–11: EC2, serverless, контейнери | Квіз по розділах 10–11 |
| 7 | 12: SQS, SNS, EventBridge, Step Functions | «⚡ Швидко» по днях 1–6 |
| 8 | 13–14: S3, EBS, EFS, FSx | Тест: набір «Продуктивність» |
| 9 | 15–17: міграція, RDS, Aurora | Квіз по розділах 15–17 |
| 10 | 18–19: DynamoDB, кеш, інші БД | Тест: набір «Відмовостійкість» |
| 11 | 20–22: аналітика, ML, моніторинг | Квіз по розділах 20–22 |
| 12 | 23–25: DR, вартість, цифри | Тест: набір «Вартість» |
| 13 | Повний тест у режимі «Іспит» (130 хв) | Розібрати **кожну** помилку |
| 14 | 26–28: порівняння, пастки, зміни | «Мої помилки» в тесті + «⚡ Швидко» |

- Якщо стабільно набираєш **80%+** у практичних тестах — записуйся на іспит.
- Додатково: офіційний безкоштовний набір питань AWS (Official Practice Question Set) у **AWS Skill Builder**; популярні платні тести — Tutorials Dojo.
- Подай запит **ESL +30 хвилин до запису** на іспит.

### День іспиту: чек-лист

- **Документ:** паспорт або інше посвідчення з фото; ім'я має збігатися з ім'ям у профілі AWS Certification.
- **Онлайн-іспит (Pearson VUE, OnVUE):** заздалегідь пройди перевірку системи (system test) на тому самому комп'ютері й мережі. Check-in відкривається за 30 хв до початку. Потрібні тиха окрема кімната, чистий стіл, телефон поза досяжністю; кімнату фотографуєш під час check-in.
- Під час онлайн-іспиту перерв, як правило, немає — підготуйся заздалегідь. Говорити вголос і виходити з кадру не можна. Нотатки — лише на вбудованій цифровій дошці (whiteboard).
- **У центрі тестування** приходь раніше; речі залишаєш у шафці, для нотаток дають дошку.
- **Тактика:** ~2 хв на питання. Не знаєш — познач (flag), дай найкращу відповідь, повернися в кінці. Відповідай на **всі** питання, бо штрафу немає.
- Спершу читай останнє речення питання, шукай ключові слова: **MOST cost-effective, LEAST operational overhead, highly available, real-time**.
- Результат прийде на email і в кабінет, зазвичай за кілька годин (до 5 робочих днів).

## Джерела

- [Офіційний гайд іспиту SAA-C03 (AWS)](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03.html) — домени, завдання, сервіси в межах іспиту
- [Сторінка сертифікації AWS SAA](https://aws.amazon.com/certification/certified-solutions-architect-associate/) — формат, ціна, мови
- [Правила перед іспитом, accommodations (AWS)](https://aws.amazon.com/certification/policies/before-testing)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- [Логіка оцінки політик IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [Класи зберігання S3](https://aws.amazon.com/s3/storage-classes/) і [варіанти відновлення з Glacier](https://docs.aws.amazon.com/AmazonS3/latest/userguide/restoring-objects-retrieval-options.html)
- [Типи томів EBS](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volume-types.html)
- [Ліміти Lambda](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) і [ліміти SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)
- [Read replicas у RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html)
- Оголошення AWS: [S3 50 TB](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/), [SQS 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib), [SNS 1 MiB](https://aws.amazon.com/about-aws/whats-new/2026/09/amazon-sns-1mib-support/), [gp3](https://aws.amazon.com/about-aws/whats-new/2025/09/amazon-ebs-size-provisioned-performance-gp3-volumes), [Aurora Global Database 10 регіонів](https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-aurora-global-database-support-10-secondary-region-clusters/), [Aurora Serverless v2 до 0 ACU](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-aurora-serverless-v2-scaling-zero-capacity), [Kinesis 10 MiB](https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-kinesis-data-streams-10x-larger-record-sizes), [VPN 5 Gbps](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-site-to-site-vpn-5-gbps-bandwidth-tunnels), [Regional NAT Gateway](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-nat-gateway-regional-availability), [DynamoDB strong consistency між регіонами](https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-dynamo-db-global-tables-multi-region-strong-consistency-generally-available/), [Database Savings Plans](https://aws.amazon.com/about-aws/whats-new/2025/12/database-savings-plans-savings), [зміни доступності сервісів](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-service-availability/)
- Шпаргалки спільноти, з якими звірявся: [awsfundamentals.com](https://awsfundamentals.com/blog/solutions-architect-associate-exam-cheat-sheet), [GitHub sv222](https://github.com/sv222/AWS-Solutions-Architect-Associate-Exam-2026)
- Практичні питання в розділі «Тест» — оригінальні, складені для навчання; це не реальні питання іспиту
