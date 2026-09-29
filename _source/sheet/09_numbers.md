## 25. Цифри, ліміти і порти {quick}

Усі цифри звірені з документацією AWS станом на вересень 2026. На іспиті частіше питають не саму цифру, а наслідок: «Lambda — 15 хв, отже задача на годину — не Lambda».

### Іспит

| Що | Значення |
|---|---|
| Питання / час | 65 (50 оцінюваних) / 130 хв (+30 хв з ESL +30) |
| Прохідний бал | 720 з 1000 |
| Ціна / строк дії | $150 / 3 роки |

### Обчислення

| Що | Ліміт |
|---|---|
| Lambda — тривалість | 15 хв |
| Lambda — пам'ять | 128 MB – 10 240 MB (CPU росте разом з пам'яттю) |
| Lambda — /tmp | 512 MB – 10 GB |
| Lambda — payload | 6 MB синхронно, 1 MB асинхронно |
| Lambda — код | 50 MB zip, 250 MB розпакований, container image — 10 GB |
| Lambda — concurrency | 1 000 на регіон за замовчуванням |
| Spot — попередження | 2 хвилини |
| Spread placement group | 7 інстансів на AZ |
| Partition placement group | до 7 partitions на AZ |
| ASG — cooldown | 300 с за замовчуванням |
| Знижки | Spot до 90%; RI і EC2 Instance SP до ~72%; Compute SP до ~66%; Database SP до 35% |

### Сховище

| Що | Ліміт |
|---|---|
| S3 — об'єкт | до 50 TB (раніше 5 TB); один PUT — до 5 GB |
| S3 — multipart | рекомендовано від 100 MB, обов'язково понад 5 GB |
| S3 — продуктивність | 3 500 запитів на запис і 5 500 на читання за секунду на префікс |
| S3 — мінімальний строк | IA — 30 днів; Glacier Instant і Flexible — 90; Deep Archive — 180 |
| S3 — мінімальний розмір оплати | 128 KB (Standard-IA, One Zone-IA, Glacier Instant) |
| Glacier Flexible — отримання | Expedited 1–5 хв, Standard 3–5 год, Bulk 5–12 год |
| Glacier Deep Archive — отримання | Standard до 12 год, Bulk до 48 год |
| S3 Replication Time Control | 99,99% об'єктів за 15 хв |
| EBS gp3 | базово 3 000 IOPS і 125 MiB/s; до 80 000 IOPS, 2 000 MiB/s, 64 TiB |
| EBS io2 Block Express | до 256 000 IOPS, 4 000 MiB/s, 64 TiB |
| EBS gp2 | 3 IOPS на GiB, максимум 16 000 |
| EBS st1 / sc1 | 500 / 250 MiB/s; не можуть бути boot-томом |
| EBS Multi-Attach | io1/io2, до 16 Nitro-інстансів в одній AZ |

### Бази даних

| Що | Ліміт |
|---|---|
| RDS — автоматичні бекапи | 1–35 днів |
| RDS — read replicas | до 15 (MySQL, MariaDB, PostgreSQL) |
| RDS Multi-AZ — failover | зазвичай 60–120 с (Multi-AZ DB cluster — до ~35 с) |
| RDS — зупинка | до 7 днів, потім стартує сам |
| Aurora | 6 копій у 3 AZ, до 15 реплік, до 256 TiB |
| Aurora Global Database | до 10 вторинних регіонів, затримка < 1 с, RTO < 1 хв |
| Aurora Backtrack | до 72 год, лише MySQL |
| Aurora Serverless v2 | 1 ACU ≈ 2 GiB RAM, мінімум 0 ACU |
| DynamoDB — елемент | 400 KB |
| DynamoDB — PITR / Streams | 35 днів / 24 год |
| DynamoDB — RCU / WCU | 1 RCU = 1 strongly consistent читання/с до 4 KB (або 2 eventual); 1 WCU = 1 запис/с до 1 KB |

### Інтеграція і потоки

| Що | Ліміт |
|---|---|
| SQS — повідомлення | до 1 MiB (Extended Client Library — до 2 GB через S3) |
| SQS — зберігання | 1 хв – 14 днів (за замовчуванням 4 дні) |
| SQS — visibility timeout | 30 с за замовчуванням, максимум 12 год |
| SQS — long polling / delay | до 20 с / до 15 хв |
| SQS FIFO | 300 викликів/с (3 000 повідомлень/с з батчами по 10); дедуплікація 5 хв |
| SNS — повідомлення | 256 KB (до 1 MiB за налаштуванням з вересня 2026) |
| Kinesis Data Streams | зберігання 24 год – 365 днів; shard: запис 1 MB/s або 1 000 записів/с, читання 2 MB/s |
| Step Functions | Standard — до 1 року; Express — до 5 хв |
| API Gateway | таймаут інтеграції 29 с; payload 10 MB; 10 000 запитів/с (burst 5 000) |

### Мережа

| Що | Ліміт |
|---|---|
| VPC — CIDR | від /16 до /28; 5 зарезервованих IP у кожній підмережі |
| NACL — ephemeral ports | 1024–65535 |
| Site-to-Site VPN | 2 тунелі; до 1,25 Gbps на тунель (large — до 5 Gbps) |
| Direct Connect | Dedicated 1/10/100/400 Gbps; Hosted 50 Mbps – 25 Gbps |
| Global Accelerator | 2 статичні anycast IP |
| Route 53 multivalue | до 8 записів у відповіді |
| ELB deregistration delay | 300 с за замовчуванням |
| Gateway Load Balancer | протокол GENEVE, порт 6081 |

### Безпека і моніторинг

| Що | Ліміт |
|---|---|
| KMS — пряме шифрування | до 4 KB (більше — envelope encryption) |
| KMS — ротація | раз на рік за замовчуванням (90–2560 днів або вручну) |
| KMS — видалення ключа | очікування 7–30 днів |
| CloudTrail — Event history | 90 днів |
| CloudWatch — метрики EC2 | 5 хв (detailed monitoring — 1 хв) |
| CloudWatch Logs | зберігаються безстроково, доки не задаш retention |
| Shield Advanced | ~$3 000 на місяць на організацію |

### Порти, які варто знати

| Порт | Протокол або сервіс |
|---|---|
| 22 | SSH |
| 3389 | RDP (Windows) |
| 80 / 443 | HTTP / HTTPS |
| 3306 | MySQL, MariaDB, Aurora MySQL |
| 5432 | PostgreSQL, Aurora PostgreSQL |
| 1433 | Microsoft SQL Server |
| 1521 | Oracle |
| 2049 | NFS (EFS) |
| 445 | SMB (FSx for Windows) |
| 6379 | Redis OSS / Valkey |
| 11211 | Memcached |
| 53 | DNS |
