# Практичні питання (оригінальні, у стилі SAA-C03)

Формат: `## Q<номер> | <домен>`, далі EN, UA, варіанти (зірочка після літери — правильна відповідь), WHY — пояснення.

## Q1 | secure
EN: An application running on Amazon EC2 instances needs to read objects from an Amazon S3 bucket in the same account. The security team prohibits storing long-term credentials on the instances. What should a solutions architect do?
UA: Застосунок на EC2 має читати об'єкти з S3 у тому ж акаунті. Служба безпеки забороняє зберігати довгострокові облікові дані на інстансах. Що зробити?
A: Create an IAM user, generate access keys, and store them in the application configuration file.
B*: Create an IAM role with read access to the bucket and attach it to the instances through an instance profile.
C: Store IAM user access keys in AWS Secrets Manager and retrieve them at startup.
D: Make the bucket public and restrict access with a security group.
WHY: Роль через instance profile дає тимчасові облікові дані, які оновлюються автоматично. Ключі IAM-користувача (A, C) — довгострокові, навіть якщо лежать у Secrets Manager. У S3 немає Security Groups, а публічний bucket — діра в безпеці.

## Q2 | secure
EN: A company has 40 AWS accounts in AWS Organizations. The security team must ensure that no member account can disable AWS CloudTrail or leave the organization, even if an account administrator tries to. What is the MOST effective solution?
UA: У компанії 40 акаунтів в AWS Organizations. Жоден member-акаунт не повинен мати змоги вимкнути CloudTrail або вийти з організації, навіть адміністратор акаунта. Яке рішення найефективніше?
A*: Attach a service control policy (SCP) to the organization root or OUs that denies cloudtrail:StopLogging, cloudtrail:DeleteTrail, and organizations:LeaveOrganization.
B: Create an IAM policy in each account that denies these actions and attach it to all users.
C: Use AWS Config rules to detect when CloudTrail is disabled.
D: Enable AWS Security Hub in all accounts.
WHY: SCP обмежує всіх у member-акаунтах, зокрема адміністраторів і root-користувача, і її не можна обійти зсередини акаунта. IAM-політики (B) адмін акаунта може змінити. Config і Security Hub (C, D) лише виявляють порушення, а не забороняють.

## Q3 | secure
EN: A company wants its employees to sign in once with their existing corporate identity provider (Okta) and access multiple AWS accounts in AWS Organizations with role-based permissions. Which solution requires the LEAST operational overhead?
UA: Співробітники мають входити один раз через корпоративний IdP (Okta) і працювати в кількох акаунтах AWS Organizations з рольовими правами. Яке рішення потребує найменше операційних зусиль?
A: Create IAM users in every account and synchronize passwords with a script.
B*: Use AWS IAM Identity Center with Okta as the external identity provider and assign permission sets to the accounts.
C: Use Amazon Cognito user pools federated with Okta.
D: Deploy AWS Managed Microsoft AD and create a trust with Okta.
WHY: IAM Identity Center — стандартне рішення для єдиного входу співробітників у багато акаунтів з зовнішнім IdP (SAML/SCIM) і permission sets. Cognito (C) — для користувачів застосунків, а не для доступу до акаунтів AWS. IAM-користувачі в кожному акаунті (A) — багато ручної роботи. Managed AD (D) тут зайвий.

## Q4 | secure
EN: A mobile app must let users upload photos directly to an Amazon S3 bucket. Each user must be able to write only to their own prefix. Users sign in with social identity providers. Which solution should be used?
UA: Мобільний застосунок має завантажувати фото користувачів прямо в S3. Кожен користувач може писати лише у свій префікс. Вхід — через соцмережі. Яке рішення обрати?
A: Embed an IAM user's access keys in the mobile app.
B*: Use an Amazon Cognito identity pool to issue temporary AWS credentials with an IAM policy that restricts access to the user's own prefix.
C: Use a Cognito user pool and grant the user pool access to S3 with a bucket policy.
D: Generate S3 presigned URLs in the mobile app by using the root user's credentials.
WHY: Identity Pool обмінює токен входу на тимчасові AWS-credentials; в IAM-політиці змінна ${cognito-identity.amazonaws.com:sub} обмежує кожного його префіксом. Ключі в застосунку (A, D) — неприпустимо. User Pool сам по собі AWS-ключів не видає (C).

## Q5 | secure
EN: A company stores sensitive data in Amazon S3. Compliance requires that the company audit every use of the encryption key and control who can use the key. Which encryption option meets these requirements?
UA: Компанія зберігає чутливі дані в S3. Вимоги: аудит кожного використання ключа шифрування і контроль того, хто може ним користуватися. Який варіант шифрування підходить?
A: Server-side encryption with Amazon S3 managed keys (SSE-S3)
B*: Server-side encryption with an AWS KMS customer managed key (SSE-KMS)
C: Server-side encryption with customer-provided keys (SSE-C)
D: Client-side encryption with keys stored on an EC2 instance
WHY: SSE-KMS з customer managed key: кожне використання ключа видно в CloudTrail, а доступ керується key policy. SSE-S3 (A) не дає окремого аудиту і контролю ключа. У SSE-C (C) ключем керує клієнт, AWS його не зберігає. D — складно й небезпечно.

## Q6 | secure
EN: An application on Amazon EC2 connects to an Amazon RDS for MySQL database. The database password must be rotated automatically every 30 days without application downtime. What should the solutions architect use?
UA: Застосунок на EC2 підключається до RDS for MySQL. Пароль до БД треба автоматично змінювати кожні 30 днів без простою застосунку. Що використати?
A: An AWS Systems Manager Parameter Store SecureString parameter
B*: AWS Secrets Manager with automatic rotation enabled
C: An encrypted file on Amazon EFS that a cron job updates
D: AWS KMS to generate a new password every month
WHY: Secrets Manager має вбудовану автоматичну ротацію для RDS, а застосунок щоразу бере актуальний секрет. Parameter Store (A) не має вбудованої ротації. C — саморобний скрипт. KMS (D) керує ключами шифрування, а не паролями до БД.

## Q7 | secure
EN: A web application behind an Application Load Balancer is receiving SQL injection attempts and a high volume of requests from a small set of IP addresses. What should a solutions architect do to protect the application with the LEAST effort?
UA: Вебзастосунок за ALB отримує спроби SQL injection і дуже багато запитів з кількох IP-адрес. Як захистити його з найменшими зусиллями?
A*: Associate an AWS WAF web ACL with the ALB that uses managed SQL injection rules and a rate-based rule.
B: Add deny rules for the IP addresses to the ALB security group.
C: Enable AWS Shield Standard on the ALB.
D: Deploy a Network Load Balancer in front of the ALB.
WHY: WAF працює на рівні 7: готові правила від SQL injection і rate-based rule, що обмежує запити з одного IP. У Security Group немає Deny-правил (B). Shield Standard (C) уже ввімкнений і захищає від DDoS рівнів 3–4, а не від SQL injection. NLB (D) не фільтрує HTTP.

## Q8 | secure
EN: A company must block traffic from one specific malicious IP address to all instances in a subnet. What is the simplest solution?
UA: Треба заблокувати трафік з однієї шкідливої IP-адреси до всіх інстансів у підмережі. Яке рішення найпростіше?
A: Add a deny rule to the security group of the instances.
B*: Add an inbound deny rule for the IP address to the subnet's network ACL.
C: Remove the internet gateway from the VPC.
D: Configure a Route 53 Resolver DNS Firewall rule.
WHY: NACL підтримує Deny і діє на всю підмережу. Security Group вміє лише Allow (A). Видалення IGW (C) зламає весь доступ. DNS Firewall (D) фільтрує DNS-запити до доменів, а не вхідний трафік з IP.

## Q9 | secure
EN: EC2 instances in private subnets upload data to Amazon S3. The company wants the traffic to stay on the AWS network and wants to avoid NAT gateway data processing charges. What should the solutions architect do?
UA: EC2 у приватних підмережах завантажують дані в S3. Трафік має йти мережею AWS, а платити за обробку трафіку NAT Gateway не хочеться. Що зробити?
A: Create an interface VPC endpoint for Amazon SQS.
B*: Create a gateway VPC endpoint for Amazon S3 and add it to the route tables of the private subnets.
C: Move the instances to public subnets.
D: Create a VPC peering connection to Amazon S3.
WHY: Gateway endpoint до S3 безкоштовний, трафік не йде через інтернет і NAT. A — не той сервіс. C погіршує безпеку. VPC peering із S3 неможливий (D).

## Q10 | secure
EN: A company wants to allow access to an S3 bucket only from its VPC through a specific VPC endpoint. Requests from anywhere else, including the internet, must be denied. How can this be achieved?
UA: Доступ до S3-bucket має бути лише з VPC компанії через конкретний VPC endpoint. Усі інші запити, зокрема з інтернету, треба забороняти. Як це зробити?
A: Configure a security group on the S3 bucket.
B*: Add a bucket policy that denies all requests unless they come through the specific VPC endpoint (aws:SourceVpce condition).
C: Enable S3 Block Public Access only.
D: Enable S3 Object Lock in compliance mode.
WHY: Умова aws:SourceVpce у bucket policy пропускає лише запити через конкретний endpoint. У S3 немає Security Groups (A). Block Public Access (C) не блокує автентифіковані запити з інтернету. Object Lock (D) захищає від видалення, а не контролює мережевий доступ.

## Q11 | secure
EN: A company runs workloads in many AWS accounts. The security team needs a central view of findings from Amazon GuardDuty, Amazon Inspector, and Amazon Macie, plus automated checks against the CIS AWS Foundations Benchmark. Which service should be used?
UA: Робочі навантаження в багатьох акаунтах. Служба безпеки хоче бачити знахідки GuardDuty, Inspector і Macie в одному місці та мати автоматичні перевірки CIS AWS Foundations Benchmark. Який сервіс обрати?
A: AWS Config
B: Amazon Detective
C*: AWS Security Hub
D: AWS Trusted Advisor
WHY: Security Hub збирає знахідки GuardDuty, Inspector, Macie та інших і перевіряє стандарти (CIS, PCI DSS, AWS Foundational Security Best Practices). Config (A) — конфігурації ресурсів. Detective (B) — розслідування. Trusted Advisor (D) — загальні рекомендації.

## Q12 | secure
EN: A company must find and report personally identifiable information (PII) stored in thousands of S3 buckets across its organization. Which service should be used?
UA: Треба знайти й показати персональні дані (PII), що зберігаються в тисячах S3-bucket по всій організації. Який сервіс використати?
A*: Amazon Macie
B: Amazon GuardDuty
C: Amazon Inspector
D: AWS Audit Manager
WHY: Macie за допомогою ML знаходить чутливі дані (PII) в S3. GuardDuty (B) шукає загрози, Inspector (C) — вразливості в EC2/ECR/Lambda, Audit Manager (D) збирає докази для аудиту.

## Q13 | secure
EN: A company needs to store encryption keys in a dedicated, single-tenant hardware security module validated at FIPS 140 Level 3. The company must have exclusive control of the keys. Which service meets these requirements?
UA: Ключі шифрування треба зберігати у виділеному (single-tenant) апаратному модулі з сертифікацією FIPS 140 Level 3, і ключі мають бути лише під контролем компанії. Який сервіс підходить?
A: AWS KMS with AWS managed keys
B: AWS Secrets Manager
C*: AWS CloudHSM
D: AWS Certificate Manager
WHY: CloudHSM — виділений HSM, ключі повністю під контролем клієнта. KMS (A) — керований мультитенантний сервіс. Secrets Manager (B) зберігає секрети, ACM (D) — сертифікати.

## Q14 | secure
EN: A company is designing a VPC for a three-tier web application. The web servers must be reachable from the internet only through a load balancer, and the database must not be reachable from the internet. Which TWO actions should the solutions architect take? (Choose TWO.)
UA: Проєктується VPC для трирівневого вебзастосунку. Вебсервери мають бути доступні з інтернету лише через балансувальник, а БД — взагалі недоступна з інтернету. Які ДВІ дії виконати? (Оберіть дві відповіді.)
A*: Place the Application Load Balancer in public subnets and the web and database instances in private subnets.
B: Assign public IP addresses to the database instances and restrict them with network ACLs.
C*: Configure the database security group to allow inbound traffic only from the security group of the web tier.
D: Place all tiers in a single public subnet to simplify routing.
E: Use a NAT gateway to allow inbound connections to the web servers.
WHY: ALB у публічних підмережах, сервери й БД — у приватних (A), а SG бази пускає лише SG вебсерверів (C). Публічні IP для БД (B) і все в одній публічній підмережі (D) відкривають доступ з інтернету. NAT Gateway (E) дає лише вихідний доступ, не вхідний.

## Q15 | secure
EN: A company uses an Application Load Balancer and needs HTTPS with a certificate that renews automatically. What is the simplest solution?
UA: Потрібен HTTPS на ALB із сертифікатом, який поновлюється автоматично. Яке рішення найпростіше?
A*: Request a public certificate from AWS Certificate Manager (ACM) and attach it to the HTTPS listener of the ALB.
B: Buy a certificate from a third-party certificate authority and upload it to every EC2 instance.
C: Use a self-signed certificate on the ALB.
D: Store the certificate in AWS Secrets Manager and rotate it with a Lambda function.
WHY: ACM безкоштовно видає публічні сертифікати й автоматично їх поновлює, з ALB інтеграція вбудована. B і D вимагають ручної роботи. Самопідписаному сертифікату (C) браузери не довіряють.

## Q16 | secure
EN: A company must retain financial records in Amazon S3 for 7 years. No one, including the root user, may delete or overwrite the records during that period. Which solution meets this requirement?
UA: Фінансові записи треба зберігати в S3 7 років. Ніхто, навіть root, не може видалити чи перезаписати їх у цей період. Яке рішення підходить?
A: Enable versioning and MFA Delete.
B*: Enable S3 Object Lock in compliance mode with a 7-year retention period.
C: Enable S3 Object Lock in governance mode.
D: Apply a bucket policy that denies s3:DeleteObject.
WHY: У compliance mode ніхто, навіть root, не видалить і не змінить об'єкт до кінця строку. Governance mode (C) можна обійти з особливим дозволом. Bucket policy (D) адміністратор може змінити. Versioning + MFA Delete (A) ускладнює видалення, але не забороняє його.

## Q17 | secure
EN: Application servers must be administered without opening inbound SSH ports or managing bastion hosts. All session activity must be logged. What should the solutions architect recommend?
UA: Сервери треба адмініструвати без відкритих SSH-портів і без бастіонів, а всі сесії мають логуватися. Що порекомендувати?
A: Use EC2 Instance Connect with a public IP address on each instance.
B*: Use AWS Systems Manager Session Manager with session logging to Amazon S3 or CloudWatch Logs.
C: Create a Site-to-Site VPN and use SSH over the VPN.
D: Enable EC2 serial console access for all instances.
WHY: Session Manager дає доступ до shell без відкритих портів і бастіонів, сесії логуються в S3/CloudWatch. A потребує відкритого порту 22 і публічного IP. C — усе одно SSH і відкритий порт. D — для аварійної діагностики, не для щоденної роботи.

## Q18 | secure
EN: A SaaS vendor needs access to resources in a customer's AWS account. The customer wants to grant access without sharing long-term credentials and wants to prevent the confused deputy problem. What should the customer do?
UA: SaaS-вендору потрібен доступ до ресурсів в акаунті клієнта. Клієнт не хоче передавати довгострокові ключі й хоче захиститися від проблеми confused deputy. Що зробити клієнту?
A: Create an IAM user for the vendor and share its access keys.
B*: Create an IAM role that the vendor's account can assume, and require an external ID in the role's trust policy.
C: Invite the vendor's account into the customer's organization.
D: Share the root user credentials protected by MFA.
WHY: Крос-акаунтна роль з умовою sts:ExternalId у trust policy — стандартний захист від confused deputy для третіх сторін. Ключі (A) і root (D) — неприпустимо. Додавати чужий акаунт в організацію (C) не треба.

## Q19 | secure
EN: A company wants to ensure that all new Amazon EBS volumes in a Region are encrypted, without changing any deployment scripts. What should the solutions architect do?
UA: Усі нові EBS-томи в регіоні мають бути зашифровані, але скрипти розгортання змінювати не можна. Що зробити?
A*: Enable EBS encryption by default for the Region.
B: Create an AWS Config rule that deletes unencrypted volumes.
C: Add encryption parameters to every CloudFormation template.
D: Use SSE-S3 for the EBS volumes.
WHY: «EBS encryption by default» автоматично шифрує всі нові томи в регіоні. B лише реагує постфактум, а видаляти томи — погано. C вимагає змінювати шаблони. SSE-S3 (D) — для S3, не для EBS.

## Q20 | secure
EN: For data residency reasons, a company wants to restrict all accounts in its organization to only the eu-central-1 and eu-west-1 Regions. What should the solutions architect implement?
UA: Через вимоги до розміщення даних усі акаунти організації мають працювати лише в регіонах eu-central-1 і eu-west-1. Що впровадити?
A: IAM policies in every account that deny other Regions
B*: An SCP that denies actions when aws:RequestedRegion is not one of the approved Regions, with exceptions for global services
C: AWS Config rules that alert on resources in other Regions
D: VPC endpoint policies
WHY: SCP з умовою aws:RequestedRegion централізовано забороняє інші регіони для всіх акаунтів (для глобальних сервісів, як IAM, роблять винятки). IAM-політики в кожному акаунті (A) — багато роботи, і їх можна змінити. Config (C) лише сповіщає. Endpoint policies (D) тут ні до чого.

## Q21 | resilient
EN: A company runs a web application on a single EC2 instance, and its MySQL database runs on the same instance. The company wants high availability with minimal application changes. Which solution meets these requirements?
UA: Вебзастосунок і MySQL працюють на одному EC2. Потрібна висока доступність з мінімальними змінами в застосунку. Яке рішення підходить?
A*: Move the database to Amazon RDS for MySQL Multi-AZ, and run the web tier in an Auto Scaling group across multiple Availability Zones behind an Application Load Balancer.
B: Take daily snapshots of the instance and restore them in another Availability Zone when needed.
C: Increase the instance size and enable detailed monitoring.
D: Move the application to a larger instance in a cluster placement group.
WHY: ALB + ASG у кількох AZ + RDS Multi-AZ прибирають єдину точку відмови з мінімальними змінами (MySQL лишається MySQL). B — це бекап, а не висока доступність. C і D — усе ще один сервер в одній AZ.

## Q22 | resilient
EN: An order processing system receives unpredictable spikes of orders. The backend sometimes fails under load, and orders are lost. What should the solutions architect do to decouple the components and prevent order loss?
UA: Система обробки замовлень отримує непередбачувані піки. Бекенд під навантаженням падає, і замовлення губляться. Як розв'язати компоненти й не втрачати замовлення?
A*: Send orders to an Amazon SQS queue, have the backend workers poll the queue, and scale the workers based on the queue depth.
B: Increase the size of the backend instances.
C: Use Amazon SNS to push orders directly to the backend instances.
D: Store orders on instance store volumes until they are processed.
WHY: SQS зберігає повідомлення (до 14 днів) і згладжує піки; воркери забирають їх у своєму темпі, а ASG масштабує їх за довжиною черги. SNS (C) не зберігає повідомлення, якщо одержувач недоступний. B не вирішує проблему піків. Instance store (D) втрачає дані.

## Q23 | resilient
EN: Consumers sometimes process messages from an Amazon SQS queue twice. Processing one message takes up to 2 minutes. The visibility timeout of the queue is 30 seconds. What should be done?
UA: Споживачі іноді обробляють повідомлення з SQS двічі. Обробка одного повідомлення триває до 2 хвилин, visibility timeout черги — 30 секунд. Що зробити?
A*: Increase the visibility timeout of the queue to longer than the maximum processing time.
B: Switch to long polling.
C: Reduce the message retention period.
D: Configure a delay queue of 15 minutes.
WHY: Якщо обробка довша за visibility timeout, повідомлення знову стає видимим і його бере інший споживач. Треба збільшити timeout. Long polling (B) лише зменшує порожні запити. C і D не впливають на повторну обробку.

## Q24 | resilient
EN: A financial application must process transactions in the exact order in which they are received and must never process a transaction more than once. Which configuration should be used?
UA: Фінансовий застосунок має обробляти транзакції строго в порядку надходження і ніколи не обробляти одну транзакцію двічі. Що використати?
A: An Amazon SQS standard queue
B*: An Amazon SQS FIFO queue with message group IDs
C: An Amazon SNS standard topic
D: Amazon Data Firehose
WHY: FIFO-черга гарантує порядок у межах message group і обробку рівно один раз (дедуплікація). Standard (A) може дублювати й міняти порядок. SNS standard (C) порядок не гарантує. Firehose (D) — доставка в сховища, а не черга транзакцій.

## Q25 | resilient
EN: Every image uploaded to Amazon S3 must trigger three independent processes: thumbnail generation, metadata extraction, and virus scanning. Each process must receive every event and process it independently, even if one process is temporarily unavailable. What is the MOST appropriate architecture?
UA: Кожне завантажене в S3 зображення має запускати три незалежні процеси: мініатюри, метадані й антивірус. Кожен має отримати кожну подію й обробити її незалежно, навіть якщо один процес тимчасово недоступний. Яка архітектура найкраща?
A: An S3 event notification to a single SQS queue that all three processes poll
B*: An S3 event notification to an SNS topic that fans out to three SQS queues, one for each process
C: Three S3 event notifications to three Lambda functions without retries
D: An S3 event notification to Amazon Data Firehose
WHY: Fan-out SNS → кілька SQS: у кожного процесу своя черга, він отримує всі події й обробляє їх незалежно, навіть після тимчасового збою. З однієї черги (A) кожне повідомлення отримає лише один споживач. C — без буфера й повторів події можна втратити. Firehose (D) — для доставки в сховища.

## Q26 | resilient
EN: A company needs a relational database that can survive the failure of an entire AWS Region with an RPO of about 1 second and an RTO of less than 1 minute. Which solution meets these requirements?
UA: Потрібна реляційна БД, яка переживе падіння цілого регіону AWS з RPO близько 1 секунди і RTO менше 1 хвилини. Яке рішення підходить?
A: An Amazon RDS Multi-AZ deployment
B: Amazon RDS with cross-Region automated backups
C*: Amazon Aurora Global Database
D: Amazon Aurora with Aurora Replicas in the same Region
WHY: Aurora Global Database реплікує на рівні сховища в інші регіони із затримкою зазвичай до 1 с, а перемикання займає менше хвилини. Multi-AZ (A) і репліки в тому ж регіоні (D) не захищають від падіння регіону. Бекапи (B) дають набагато більші RPO/RTO.

## Q27 | resilient
EN: A company needs a disaster recovery strategy for its web application with an RTO of 10–30 minutes at the lowest possible cost. The database must be continuously replicated to the DR Region, and the application servers can be started only when needed. Which DR strategy should be used?
UA: Потрібна DR-стратегія з RTO 10–30 хвилин і найменшою вартістю. БД має постійно реплікуватися в DR-регіон, а сервери застосунку можна запускати лише під час аварії. Яку стратегію обрати?
A: Backup and restore
B*: Pilot light
C: Warm standby
D: Multi-site active-active
WHY: Pilot light: у DR-регіоні постійно працює лише «ядро» (реплікована БД), а сервери запускаються при аварії — RTO десятки хвилин і низька вартість. Backup & restore (A) — години. Warm standby (C) і active-active (D) дорожчі.

## Q28 | resilient
EN: An application uses Amazon DynamoDB and serves users in North America and Europe. Users in both Regions must be able to write data with low latency, and the application must survive a Regional outage. What should the solutions architect use?
UA: Застосунок на DynamoDB обслуговує користувачів у Північній Америці та Європі. В обох регіонах треба швидко записувати дані, а застосунок має пережити падіння регіону. Що використати?
A: DynamoDB with on-demand capacity in a single Region
B*: DynamoDB global tables
C: DynamoDB Accelerator (DAX)
D: DynamoDB Streams with a Lambda function that copies data to a table in another Region
WHY: Global Tables — multi-active реплікація між регіонами: запис і читання локально, стійкість до падіння регіону. DAX (C) — кеш у межах регіону. D — саморобна реплікація з конфліктами й затримками. A — один регіон.

## Q29 | resilient
EN: A legacy application runs on a single EC2 instance and cannot be modified or scaled horizontally. The company wants the instance to be replaced automatically if it becomes unhealthy. What is the MOST cost-effective solution?
UA: Старий застосунок працює на одному EC2, змінювати або горизонтально масштабувати його не можна. Інстанс має автоматично замінюватися, якщо стане нездоровим. Яке рішення найвигідніше?
A*: Create an Auto Scaling group with a minimum, maximum, and desired capacity of 1.
B: Run two instances behind a load balancer.
C: Use a CloudWatch alarm that sends an email to an administrator.
D: Create an AMI of the instance every hour.
WHY: ASG з min = max = desired = 1 автоматично замінює нездоровий інстанс і не змінює архітектуру застосунку. B — застосунок не підтримує масштабування, і це дорожче. C — ручна робота. D — лише бекап.

## Q30 | resilient
EN: Many AWS Lambda functions connect to an Amazon RDS for PostgreSQL database. During traffic spikes, the database runs out of connections. Which solution addresses this with the LEAST application change?
UA: Багато функцій Lambda підключаються до RDS for PostgreSQL, і під час піків у БД закінчуються з'єднання. Що вирішить проблему з найменшими змінами в застосунку?
A*: Use Amazon RDS Proxy between the Lambda functions and the database.
B: Increase the memory size of the Lambda functions.
C: Migrate the database to Amazon DynamoDB.
D: Add a read replica.
WHY: RDS Proxy тримає пул з'єднань і повторно їх використовує; змінюється лише endpoint. Пам'ять Lambda (B) не впливає на кількість з'єднань. DynamoDB (C) — велика переробка. Read replica (D) не допоможе з'єднанням на запис.

## Q31 | resilient
EN: A company runs an application on EC2 instances in an Auto Scaling group behind an ALB. Some instances stop responding, but the Auto Scaling group does not replace them because the EC2 status checks pass. What should be done?
UA: Застосунок працює на EC2 в Auto Scaling group за ALB. Деякі інстанси перестають відповідати, але ASG їх не замінює, бо статус-перевірки EC2 проходять. Що зробити?
A*: Configure the Auto Scaling group to use Elastic Load Balancing health checks.
B: Enable detailed monitoring.
C: Increase the health check grace period to 1 hour.
D: Replace the ALB with a Network Load Balancer.
WHY: За замовчуванням ASG дивиться лише на статус EC2. З ELB health checks ASG замінює інстанси, які не відповідають балансувальнику. B лише частіше збирає метрики. C ще більше затримає заміну. D нічого не змінює.

## Q32 | resilient
EN: A media company stores video files in an S3 bucket in us-east-1. For compliance, a copy of every new object must be stored automatically in a bucket in eu-west-1. What should the solutions architect configure?
UA: Медіакомпанія зберігає відео в S3 у us-east-1. За вимогами копія кожного нового об'єкта має автоматично потрапляти в bucket в eu-west-1. Що налаштувати?
A: An S3 Lifecycle rule that transitions objects to eu-west-1
B*: S3 Cross-Region Replication (CRR), with versioning enabled on both buckets
C: S3 Transfer Acceleration
D: An AWS DataSync task that runs once a day
WHY: CRR автоматично копіює нові об'єкти в інший регіон, для неї потрібен versioning на обох bucket. Lifecycle (A) не переносить між регіонами. Transfer Acceleration (C) пришвидшує завантаження, а не реплікує. DataSync раз на день (D) — не «кожен новий об'єкт автоматично».

## Q33 | resilient
EN: An application runs in two AWS Regions and is accessed through DNS. Traffic must fail over automatically from the primary Region to the secondary Region if the primary becomes unhealthy. What should be configured?
UA: Застосунок працює у двох регіонах, доступ — через DNS. Якщо основний регіон стане нездоровим, трафік має автоматично перейти в резервний. Що налаштувати?
A: Amazon Route 53 weighted routing with equal weights
B*: Amazon Route 53 failover routing with a health check on the primary endpoint
C: Amazon Route 53 geolocation routing
D: Amazon Route 53 simple routing with two IP addresses
WHY: Failover routing + health check: поки primary здоровий, трафік іде туди, при збої — на secondary. Weighted (A) ділить трафік навпіл. Geolocation (C) — за країною користувача. Simple (D) не має health checks.

## Q34 | resilient
EN: A company is designing a stateless web tier that must scale horizontally. Where should the user session data be stored? (Choose TWO.)
UA: Проєктується stateless веб-рівень з горизонтальним масштабуванням. Де зберігати сесії користувачів? (Оберіть дві відповіді.)
A*: Amazon ElastiCache (Redis OSS or Valkey)
B*: Amazon DynamoDB
C: The instance store of each web server
D: An EBS volume attached to one web server
E: Amazon S3 Glacier Flexible Retrieval
WHY: Для stateless-серверів сесії виносять у спільне швидке сховище: ElastiCache (найшвидше) або DynamoDB (з TTL). Instance store і EBS (C, D) прив'язані до одного сервера, тож при масштабуванні сесії губляться. Glacier (E) — архів з доступом за хвилини або години.

## Q35 | resilient
EN: A long, multi-step business process calls several AWS services, retries steps on failure, and includes a manual approval step that can take several days. Which service should orchestrate the workflow?
UA: Довгий багатокроковий бізнес-процес викликає кілька сервісів AWS, повторює кроки при помилках і містить ручне схвалення, яке може тривати кілька днів. Що має оркеструвати процес?
A: Amazon SQS
B: AWS Lambda with a 15-minute timeout
C*: AWS Step Functions Standard workflows
D: Amazon EventBridge Scheduler
WHY: Step Functions Standard працюють до року, мають retry/catch і вміють чекати ручного схвалення (callback з task token). Lambda (B) — максимум 15 хв. SQS (A) — черга, а не оркестратор. Scheduler (D) — запуск за розкладом.

## Q36 | resilient
EN: A company wants to back up Amazon EC2, Amazon EBS, Amazon RDS, Amazon DynamoDB, and Amazon EFS resources across many accounts with a central policy and copy the backups to another Region. The backups must be protected from deletion, even by administrators. What should be used?
UA: Треба бекапити EC2, EBS, RDS, DynamoDB і EFS у багатьох акаунтах за централізованою політикою і копіювати бекапи в інший регіон. Бекапи мають бути захищені від видалення навіть адміністраторами. Що використати?
A*: AWS Backup with backup policies in AWS Organizations, cross-Region copy, and AWS Backup Vault Lock
B: Custom Lambda scripts that create snapshots in each account
C: Amazon Data Lifecycle Manager only
D: S3 Cross-Region Replication
WHY: AWS Backup централізує бекапи багатьох сервісів і копіює їх між регіонами й акаунтами, а Vault Lock (WORM) не дає видалити бекапи навіть адміністратору. B — власний код. DLM (C) — лише снапшоти EBS і AMI. CRR (D) — лише для S3.

## Q37 | resilient
EN: A company must run a containerized application without managing servers. The application must scale automatically and run across multiple Availability Zones. Which solution meets these requirements?
UA: Контейнерний застосунок треба запускати без керування серверами, з автоматичним масштабуванням і в кількох AZ. Яке рішення підходить?
A: Amazon EC2 instances with Docker installed in an Auto Scaling group
B*: Amazon ECS on AWS Fargate with a service spread across multiple Availability Zones behind an ALB
C: An AWS Elastic Beanstalk single-instance environment
D: AWS Batch on EC2 Spot Instances
WHY: ECS на Fargate — контейнери без серверів; сервіс розподіляє задачі між AZ і масштабується автоматично. A вимагає керувати EC2. C — один інстанс, без високої доступності. Batch (D) — для пакетних задач, а не для постійного вебсервісу.

## Q38 | performance
EN: A company has a read-heavy application that uses Amazon RDS for MySQL. Reports that the analytics team runs slow down the production database. What is the MOST effective solution?
UA: Застосунок з великою кількістю читань працює на RDS for MySQL. Звіти аналітиків гальмують робочу БД. Яке рішення найефективніше?
A*: Create a read replica and direct the reporting queries to the replica endpoint.
B: Enable Multi-AZ and send the reports to the standby instance.
C: Increase the storage size of the database.
D: Enable automated backups.
WHY: Read replica знімає читання з основної БД: звіти йдуть на endpoint репліки. Standby у Multi-AZ (B) не приймає запитів. C і D не розвантажують читання.

## Q39 | performance
EN: A gaming application needs a real-time leaderboard that is updated thousands of times per second and must return the top players with sub-millisecond latency. Which solution should be used?
UA: Грі потрібен лідерборд у реальному часі: тисячі оновлень за секунду і топ гравців із затримкою менше мілісекунди. Що використати?
A: Amazon RDS for MySQL with an index on the score column
B*: Amazon ElastiCache for Redis OSS (or Valkey) with sorted sets
C: Amazon S3 with S3 Select
D: Amazon Redshift
WHY: Sorted sets у Redis/Valkey створені саме для лідербордів: оновлення і вибір топ-N за мікросекунди–мілісекунди. RDS (A) повільніший під такий потік. S3 (C) і Redshift (D) — не для реального часу.

## Q40 | performance
EN: An application reads the same items from an Amazon DynamoDB table very frequently. The company needs microsecond read latency without significant changes to the application logic. What should be used?
UA: Застосунок дуже часто читає одні й ті самі елементи з DynamoDB. Потрібна мікросекундна затримка читання без суттєвих змін у логіці застосунку. Що використати?
A*: DynamoDB Accelerator (DAX)
B: Amazon ElastiCache for Memcached
C: DynamoDB global tables
D: More read capacity units for the table
WHY: DAX — кеш у пам'яті саме для DynamoDB із сумісним API: мікросекунди й мінімум змін. ElastiCache (B) вимагає писати логіку кешу. Global tables (C) — мульти-регіон, а не кеш. Більше RCU (D) не дасть мікросекунд.

## Q41 | performance
EN: A company serves static and dynamic content to users around the world from an application in us-east-1. Users in Asia experience high latency. What should the solutions architect do?
UA: Застосунок у us-east-1 віддає статичний і динамічний контент користувачам по всьому світу. В Азії велика затримка. Що зробити?
A*: Put Amazon CloudFront in front of the application with the ALB as the origin, and cache static content at edge locations.
B: Increase the size of the EC2 instances.
C: Use Route 53 simple routing.
D: Move the application to a larger ALB.
WHY: CloudFront кешує статику на edge-локаціях поруч із користувачами і пришвидшує динамічний контент мережею AWS. B і D не зменшують відстань до користувачів. Simple routing (C) нічого не пришвидшує.

## Q42 | performance
EN: A multiplayer game uses UDP and needs static IP addresses that clients can allow-list. Players are worldwide, and the company wants traffic routed to the nearest healthy Regional endpoint with fast failover. Which service should be used?
UA: Мультиплеєрна гра працює по UDP і потребує статичних IP, які клієнти додадуть у whitelist. Гравці по всьому світу; трафік має йти до найближчого здорового регіону зі швидким failover. Який сервіс обрати?
A: Amazon CloudFront
B*: AWS Global Accelerator
C: Amazon Route 53 latency-based routing
D: Application Load Balancer
WHY: Global Accelerator дає 2 статичні anycast IP, підтримує UDP і швидко перемикає регіони. CloudFront (A) — для кешу HTTP(S). Route 53 (C) залежить від DNS-кешу і не дає статичних IP. ALB (D) не підтримує UDP і не має статичних IP.

## Q43 | performance
EN: A company needs a shared file system for hundreds of Linux EC2 instances across multiple Availability Zones. The file system must grow automatically. Which storage service should be used?
UA: Потрібна спільна файлова система для сотень Linux EC2 у кількох AZ, яка росте автоматично. Який сервіс зберігання обрати?
A: Amazon EBS Multi-Attach
B*: Amazon EFS
C: Amazon FSx for Windows File Server
D: Amazon S3 mounted as a block device
WHY: EFS — спільна NFS-файлова система для Linux у кількох AZ, росте автоматично. EBS Multi-Attach (A) — лише io1/io2 в одній AZ і до 16 інстансів. FSx for Windows (C) — SMB для Windows. S3 (D) — об'єктне сховище, а не блочний пристрій.

## Q44 | performance
EN: A high performance computing (HPC) workload processes large datasets that are stored in Amazon S3. The workload needs a file system with sub-millisecond latency and hundreds of GB/s of throughput. Which service is the BEST fit?
UA: HPC-навантаження обробляє великі датасети з S3 і потребує файлової системи із затримкою менше мілісекунди та пропускною здатністю в сотні GB/s. Що підходить найкраще?
A: Amazon EFS with Bursting throughput
B*: Amazon FSx for Lustre linked to the S3 bucket
C: Amazon S3 Glacier Instant Retrieval
D: Amazon FSx for NetApp ONTAP
WHY: FSx for Lustre створена для HPC і ML: величезна пропускна здатність і суб-мілісекундна затримка, інтеграція з S3. EFS (A) повільніша для HPC. Glacier (C) — архів. ONTAP (D) — універсальне корпоративне сховище, не найкраще для HPC.

## Q45 | performance
EN: A database on Amazon EC2 needs 100,000 IOPS with consistent sub-millisecond latency on a single volume. Which EBS volume type should be used?
UA: Базі даних на EC2 потрібно 100 000 IOPS на одному томі зі стабільною затримкою менше мілісекунди. Який тип EBS обрати?
A: gp2
B: st1
C*: io2 Block Express
D: sc1
WHY: io2 Block Express дає до 256 000 IOPS із суб-мілісекундною затримкою. gp2 (A) — максимум 16 000 IOPS (навіть gp3 — до 80 000). st1 і sc1 (B, D) — HDD для послідовного читання, а не для IOPS.

## Q46 | performance
EN: A company ingests clickstream data from its website at a high rate. Several applications must process the same data in real time, and the company must be able to replay data from the last 7 days. Which service should be used?
UA: Сайт генерує потік кліків з високою швидкістю. Кілька застосунків мають обробляти ті самі дані в реальному часі, а дані за останні 7 днів треба мати змогу перечитати. Який сервіс обрати?
A*: Amazon Kinesis Data Streams with a 7-day retention period
B: Amazon Data Firehose
C: An Amazon SQS standard queue
D: Amazon SNS
WHY: У Kinesis Data Streams кілька споживачів читають той самий потік у реальному часі, а зберігання можна збільшити (до 365 днів) і перечитати дані. Firehose (B) лише доставляє, replay немає. У SQS (C) повідомлення видаляються після обробки і дістаються одному споживачу. SNS (D) не зберігає.

## Q47 | performance
EN: A company wants to load streaming JSON data into Amazon S3 in Apache Parquet format for analytics with Amazon Athena. There must be no servers to manage and minimal custom code. Which solution is the MOST suitable?
UA: Потоковий JSON треба складати в S3 у форматі Parquet для аналітики в Athena, без серверів і з мінімумом коду. Яке рішення найкраще?
A: Kinesis Data Streams with a custom consumer application on EC2
B*: Amazon Data Firehose with record format conversion to Parquet, delivering to S3
C: Amazon SQS with a Lambda function that writes CSV files
D: AWS DataSync
WHY: Firehose — керована доставка в S3 з вбудованою конвертацією JSON → Parquet (за схемою з Glue Data Catalog). A і C потребують власного коду. DataSync (D) переносить файли, а не потоки.

## Q48 | performance
EN: A company stores petabytes of historical data in Amazon S3 as CSV files. Analysts run occasional ad hoc SQL queries and complain about cost and speed. What should be done to improve performance and reduce cost with the LEAST operational overhead?
UA: Петабайти історичних даних лежать в S3 у CSV. Аналітики іноді роблять SQL-запити й скаржаться на ціну та швидкість. Як покращити швидкість і знизити витрати з найменшими операційними зусиллями?
A*: Convert the data to Apache Parquet, partition it, and query it with Amazon Athena.
B: Load all the data into an Amazon RDS database.
C: Run an Amazon EMR cluster with Hive 24/7.
D: Move the data to S3 Glacier Deep Archive.
WHY: В Athena платиш за обсяг сканування; колонковий Parquet і партиції скорочують сканування в рази — і швидше, і дешевше. RDS (B) не для петабайтів. EMR 24/7 (C) — дорого і складно. З Deep Archive (D) запити стануть неможливими.

## Q49 | performance
EN: A company wants to run SQL queries that join data in its Amazon Redshift data warehouse with large amounts of infrequently accessed data in Amazon S3, without loading the S3 data into Redshift. What should be used?
UA: Треба виконувати SQL-запити, що поєднують дані сховища Redshift з великими обсягами рідко потрібних даних у S3, не завантажуючи їх у Redshift. Що використати?
A: Amazon Athena federated query
B*: Amazon Redshift Spectrum
C: AWS Glue DataBrew
D: S3 Select
WHY: Redshift Spectrum дозволяє запитувати дані в S3 прямо з Redshift і поєднувати їх з таблицями сховища. Federated query в Athena (A) — з боку Athena, а не Redshift. DataBrew (C) — підготовка даних. S3 Select (D) не робить JOIN і закритий для нових клієнтів.

## Q50 | performance
EN: An application behind an ALB must route requests to different target groups based on the URL path (/api and /images). Which feature should be used?
UA: Застосунок за ALB має направляти запити в різні target groups за шляхом URL (/api і /images). Яку можливість використати?
A*: ALB path-based routing rules
B: NLB listeners on different ports
C: Route 53 weighted records
D: CloudFront geo restriction
WHY: ALB працює на рівні 7 і маршрутизує за шляхом, хостом, заголовками. NLB (B) — рівень 4, шляхів не бачить. Weighted routing (C) ділить трафік у відсотках. Geo restriction (D) блокує країни.

## Q51 | performance
EN: A company runs a CPU-intensive batch video transcoding workload on Amazon EC2. Which instance family is the MOST appropriate?
UA: На EC2 працює пакетне перекодування відео, яке сильно навантажує CPU. Яке сімейство інстансів найкраще підходить?
A: R (memory optimized)
B*: C (compute optimized)
C: I (storage optimized)
D: T (burstable performance)
WHY: C-сімейство оптимізоване під CPU: кодування відео, пакетна обробка, HPC. R — під пам'ять, I — під швидкі локальні диски, T — для нерегулярного невеликого навантаження з CPU-кредитами.

## Q52 | performance
EN: Java-based AWS Lambda functions have high latency on the first invocation after periods of inactivity (cold starts). Which TWO options reduce the cold start latency? (Choose TWO.)
UA: Функції Lambda на Java мають велику затримку при першому виклику після простою (cold start). Які ДВА варіанти її зменшать? (Оберіть дві відповіді.)
A*: Configure provisioned concurrency for the functions.
B*: Enable Lambda SnapStart.
C: Increase the function timeout.
D: Configure reserved concurrency.
E: Connect the functions to a VPC.
WHY: Provisioned concurrency тримає прогріті середовища, а SnapStart швидко відновлює вже ініціалізований знімок (Java). Timeout (C) не впливає на старт. Reserved concurrency (D) лише резервує й обмежує кількість виконань. VPC (E) старт не пришвидшує.

## Q53 | cost
EN: A company runs a steady-state workload on EC2 24/7 and expects to run it for at least 3 years. The company may change instance families and might move part of the workload to AWS Fargate. Which purchasing option provides the MOST savings with this flexibility?
UA: Стабільне навантаження на EC2 працює 24/7 щонайменше 3 роки. Компанія може міняти сімейства інстансів і, можливо, перенесе частину на Fargate. Що дасть найбільшу економію з такою гнучкістю?
A: On-Demand Instances
B: Standard Reserved Instances
C*: Compute Savings Plans
D: Spot Instances
WHY: Compute Savings Plans дають велику знижку за зобов'язання витрачати $/год і діють на будь-яке сімейство, регіон, а також на Fargate і Lambda. Standard RI (B) прив'язані до сімейства. Spot (D) можуть перерватися. On-Demand (A) — найдорожчий.

## Q54 | cost
EN: A company runs nightly batch jobs that can be interrupted and restarted. Each job takes about 3 hours, and start times are flexible. What is the MOST cost-effective compute option?
UA: Щоночі виконуються пакетні задачі, які можна переривати й перезапускати. Кожна триває близько 3 годин, час старту гнучкий. Що найвигідніше?
A*: EC2 Spot Instances (for example, managed by AWS Batch)
B: EC2 On-Demand Instances
C: EC2 Reserved Instances
D: Dedicated Hosts
WHY: Переривні задачі з гнучким часом ідеально лягають на Spot (до 90% знижки), а AWS Batch сам керує чергами і Spot. On-Demand (B) дорожчий. RI (C) — для постійного навантаження. Dedicated Hosts (D) — найдорожче, для ліцензій.

## Q55 | cost
EN: A company stores log files in Amazon S3. The logs are accessed frequently for the first 30 days and occasionally for the next 60 days. After that, they must be kept for 7 years for compliance but are almost never accessed. What is the MOST cost-effective solution?
UA: Логи лежать у S3. Перші 30 днів до них звертаються часто, наступні 60 — іноді, а потім їх треба зберігати 7 років для регулятора, майже не відкриваючи. Що найвигідніше?
A: Keep all logs in S3 Standard.
B*: Use a lifecycle policy: S3 Standard → S3 Standard-IA after 30 days → S3 Glacier Deep Archive after 90 days → expire after 7 years.
C: Store all logs in S3 One Zone-IA.
D: Store all logs in S3 Glacier Instant Retrieval from the first day.
WHY: Lifecycle переводить дані в дешевші класи з віком: IA для рідкого доступу, Deep Archive — найдешевше довге зберігання, expiration видаляє через 7 років. A — дорого. C — ризик втратити дані разом з AZ і немає архівного рівня. D — для частого доступу в перші 30 днів Glacier Instant Retrieval дорогий на читання.

## Q56 | cost
EN: Objects in an S3 bucket have unpredictable access patterns: some are accessed often and others rarely, and this changes over time. The company wants to optimize storage costs automatically without retrieval fees. Which storage class should be used?
UA: Доступ до об'єктів у S3 непередбачуваний: одні читають часто, інші рідко, і це змінюється з часом. Треба автоматично економити на зберіганні без плати за отримання даних. Який клас обрати?
A*: S3 Intelligent-Tiering
B: S3 Standard-IA
C: S3 One Zone-IA
D: S3 Glacier Flexible Retrieval
WHY: Intelligent-Tiering сам переносить об'єкти між рівнями залежно від доступу і не бере плати за отримання (лише невелику плату за моніторинг). Standard-IA і One Zone-IA (B, C) мають плату за отримання. Glacier Flexible (D) — архів з очікуванням.

## Q57 | cost
EN: EC2 instances in private subnets download large amounts of data from Amazon S3 and Amazon DynamoDB through a NAT gateway, and the NAT gateway data processing charges are high. What is the MOST cost-effective solution?
UA: EC2 у приватних підмережах завантажують багато даних з S3 і DynamoDB через NAT Gateway, і плата за обробку трафіку NAT велика. Що найвигідніше?
A*: Create gateway VPC endpoints for Amazon S3 and Amazon DynamoDB.
B: Replace the NAT gateway with a larger NAT gateway.
C: Create interface VPC endpoints for Amazon S3 and Amazon DynamoDB.
D: Move the instances to public subnets and assign Elastic IP addresses.
WHY: Gateway endpoints для S3 і DynamoDB безкоштовні й прибирають цей трафік з NAT. Interface endpoints (C) платні (за годину і за ГБ). B нічого не економить. D погіршує безпеку.

## Q58 | cost
EN: A company wants to be alerted when its forecasted monthly AWS spend exceeds $10,000. What should the solutions architect use?
UA: Компанія хоче отримати сповіщення, коли прогноз місячних витрат AWS перевищить $10 000. Що використати?
A*: AWS Budgets with a forecasted cost alert
B: AWS Cost Explorer reports that are reviewed weekly
C: AWS Trusted Advisor
D: A CloudWatch billing dashboard only
WHY: AWS Budgets надсилає сповіщення, коли фактичні або прогнозовані витрати перевищують поріг. Cost Explorer (B) — аналіз без автоматичних сповіщень. Trusted Advisor (C) — рекомендації. Дашборд (D) лише показує дані.

## Q59 | cost
EN: A company needs to allocate AWS costs to different departments that share the same AWS account. What should be done?
UA: Кілька відділів працюють в одному акаунті AWS. Як розподілити витрати між відділами?
A*: Tag resources with a department tag, activate the tag as a cost allocation tag, and analyze costs in AWS Cost Explorer.
B: Create a separate VPC for each department.
C: Use the cost optimization checks in AWS Trusted Advisor.
D: Enable detailed monitoring in Amazon CloudWatch.
WHY: Теги + активація cost allocation tags у Billing дозволяють бачити витрати за відділами в Cost Explorer і CUR. Окремі VPC (B) не розділяють рахунок. C і D не дають розподілу витрат.

## Q60 | cost
EN: A company's relational (PostgreSQL) database is used only during business hours on weekdays and is idle at night and on weekends. Which option is the MOST cost-effective with the least management?
UA: Реляційна БД (PostgreSQL) використовується лише в робочі години в будні, а вночі й на вихідних простоює. Що найвигідніше з мінімальним адмініструванням?
A*: Amazon Aurora Serverless v2 with a minimum capacity of 0 ACUs (automatic pause)
B: A provisioned Amazon RDS instance that runs 24/7 with Reserved Instances
C: PostgreSQL on a large EC2 instance
D: Amazon Redshift
WHY: Aurora Serverless v2 масштабується за навантаженням і може «засинати» (0 ACU), коли немає з'єднань, — уночі платиш лише за сховище. B платить 24/7. C — ручне адміністрування. Redshift (D) — для аналітики, а не для OLTP.

## Q61 | cost
EN: Two VPCs in the same Region exchange a large amount of data. Only these two VPCs need to be connected. Which option is the MOST cost-effective?
UA: Дві VPC в одному регіоні обмінюються великим обсягом даних, і з'єднати треба лише їх. Що найвигідніше?
A*: VPC peering
B: AWS Transit Gateway
C: A Site-to-Site VPN connection between the VPCs
D: AWS Direct Connect
WHY: Для двох VPC peering найдешевший: немає погодинної плати і плати за обробку кожного ГБ, як у Transit Gateway. VPN (C) і Direct Connect (D) — для з'єднання з on-prem і дорожчі.

## Q62 | cost
EN: A company has many S3 buckets and wants to find out which data should move to cheaper storage classes based on actual access patterns before it creates lifecycle rules. Which feature helps?
UA: У компанії багато S3-bucket. Перед створенням lifecycle-правил треба зрозуміти, які дані варто перевести в дешевші класи, за реальним доступом. Що допоможе?
A*: S3 Storage Class Analysis (and S3 Storage Lens)
B: S3 Transfer Acceleration
C: S3 Object Lock
D: S3 Requester Pays
WHY: Storage Class Analysis аналізує, як часто читають дані, і підказує, коли переводити їх у Standard-IA; Storage Lens дає огляд використання і витрат. Решта варіантів доступ не аналізує.

## Q63 | cost
EN: A stateless web application runs on EC2 instances in an Auto Scaling group. The baseline load is steady, but there are unpredictable spikes. Which approach is the MOST cost-effective while keeping the application available?
UA: Stateless-вебзастосунок працює на EC2 в Auto Scaling group. Базове навантаження стабільне, але бувають непередбачувані піки. Що найвигідніше без шкоди для доступності?
A*: Cover the baseline with Savings Plans or Reserved Instances, and handle the spikes with Spot and On-Demand Instances in a mixed instances policy.
B: Use only Spot Instances for all capacity.
C: Use only On-Demand Instances.
D: Use Dedicated Hosts for all capacity.
WHY: Постійну базу вигідно закрити Savings Plans або RI, а піки — Spot (дешево) і On-Demand (надійно) через mixed instances policy. Лише Spot (B) ризикує доступністю. Лише On-Demand (C) дорожче. Dedicated Hosts (D) — найдорожче.

## Q64 | cost
EN: A company transfers about 20 TB of data per month between its on-premises data center and AWS. Data transfer costs over the internet VPN are high, and the company needs consistent network performance. What should the solutions architect recommend?
UA: Щомісяця між дата-центром і AWS передається близько 20 TB. Трафік через VPN в інтернеті дорогий, а потрібна стабільна швидкість мережі. Що порекомендувати?
A*: AWS Direct Connect
B: A second Site-to-Site VPN connection
C: S3 Transfer Acceleration
D: Amazon CloudFront
WHY: Direct Connect дає стабільну пропускну здатність і дешевший вихідний трафік для великих постійних обсягів. Друга VPN (B) все одно йде через інтернет. Transfer Acceleration (C) пришвидшує завантаження в S3 за додаткову плату. CloudFront (D) — для доставки контенту користувачам.

## Q65 | cost
EN: A development environment runs on Amazon EC2 and Amazon RDS but is used only 10 hours a day on weekdays. Which TWO actions will reduce costs the MOST? (Choose TWO.)
UA: Середовище розробки на EC2 і RDS використовується лише 10 годин на день у будні. Які ДВІ дії найбільше зменшать витрати? (Оберіть дві відповіді.)
A*: Stop the EC2 instances outside business hours on an automated schedule (for example, EventBridge Scheduler with Lambda).
B*: Stop the RDS DB instances outside business hours on an automated schedule.
C: Purchase 3-year Reserved Instances for the development servers.
D: Enable Multi-AZ for the development database.
E: Move the development servers to Dedicated Instances.
WHY: Ресурси, які працюють ~50 годин із 168 на тиждень, найвигідніше вимикати за розкладом — тоді платиш лише за робочі години (сховище оплачується окремо). RDS можна зупиняти до 7 днів. RI (C) — для роботи 24/7. Multi-AZ (D) і Dedicated Instances (E) лише додадуть витрат.
