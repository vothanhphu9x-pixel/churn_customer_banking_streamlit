# 📌 NGHIỆP VỤ: DỰ ĐOÁN KHÁCH HÀNG RỜI BỎ NGÂN HÀNG (CUSTOMER CHURN)

> Tài liệu này tập hợp định nghĩa dữ liệu, hướng dẫn feature engineering và lưu ý nghiệp vụ để xây dựng một pipeline dự đoán churn cho khách hàng ngân hàng. Giữ mọi nội dung gốc; phần đầu được sắp xếp lại để dễ tìm thông tin.

## Mục lục

1. [Ngữ cảnh kinh doanh (Business Context)](#1-ngữ-cảnh-kinh-doanh-business-context)
2. [Mục tiêu bài toán (Business Objective)](#2-mục-tiêu-bài-toán-business-objective)
3. [Nguồn dữ liệu (Data Sources)](#3-nguồn-dữ-liệu-data-sources)
4. [Định nghĩa churn (Label Definition)](#4-định-nghĩa-churn-label-definition)
5. [Data Dictionary & Feature Sections](#5-data-dictionary--feature-sections)
   5.1 [Customer Master](#51-customer-master)
   5.2 [CASA — Hành vi tài khoản](#52-casa--hành-vi-tài-khoản)
   5.3 [Loan — Dòng tiền / Stress tài chính](#53-loan--dòng-tiền--stress-tài-chính)
   5.4 [Credit Card — Engagement / Chi tiêu](#54-credit-card--engagement--chi-tiêu)
   5.5 [Demographic — Phân khúc / Giải thích model](#55-demographic--phân-khúc--giải-thích-model)
   5.6 [Channel Usage — Hành vi kênh số](#56-channel-usage--hành-vi-sử-dụng-kênh-số)
   5.7 [Customer Interaction — Trải nghiệm & Khiếu nại](#57-customer-interaction--trải-nghiệm--khiếu-nại)
   5.8 [Campaign Response — Chiến dịch & Retention](#58-campaign-response--chiến-dịch--retention)
6. [Implementation notes & Edge cases](#6-implementation-notes--edge-cases)
7. [Tổng hợp vai trò dữ liệu & Kết luận](#7-tổng-hợp-vai-trò-dữ-liệu)

## How to read this README

- Mỗi section chứa: mô tả trường raw, policy về NULL, ý nghĩa nghiệp vụ và các engineered features đề xuất.
- Tuyệt đối đảm bảo time-awareness: mọi feature phải được tính từ dữ liệu có timestamp <= snapshot_date.
- Phần "Ghi chú" và "Implementation notes" chứa best-practices (dedupe, guard denominators, timezone, privacy).

## 1. Ngữ cảnh kinh doanh (Business Context)

Ngân hàng A đang đối mặt với tình trạng:

- Số lượng **khách hàng không còn giao dịch (dormant)** tăng nhanh
- Chi phí **thu hút khách hàng mới cao gấp 5–7 lần** chi phí giữ khách hàng hiện hữu
- Các chiến dịch chăm sóc khách hàng (retention) đang được triển khai đại trà, **hiệu quả thấp**

Ngân hàng hiện chỉ phát hiện khách hàng rời bỏ **sau khi họ đã đóng tài khoản hoặc ngừng giao dịch trong thời gian dài**, dẫn đến việc can thiệp quá muộn.

## 2. Mục tiêu bài toán (Business Objective)

Xây dựng mô hình Machine Learning nhằm:

> **Dự đoán sớm khả năng churn của khách hàng trong 1–3 tháng tiếp theo**,  
> từ đó giúp ngân hàng chủ động triển khai các chiến lược giữ chân phù hợp.

### Kết quả mong muốn:

- Thiết kế **Data Dictionary** cho toàn bộ dataset, đảm bảo định nghĩa dữ liệu nhất quán và phù hợp với biến mục tiêu _Customer Churn_
- Xây dựng **pipeline EDA** nhằm phân tích hành vi khách hàng, xu hướng sử dụng sản phẩm và phát hiện tín hiệu churn sớm
- Thực hiện **Feature Engineering** để chuyển đổi dữ liệu thô thành các đặc trưng có ý nghĩa cho mô hình học máy
- Xây dựng và áp dụng **mô hình Machine Learning** nhằm dự đoán xác suất churn của từng khách hàng
- Ứng dụng kết quả mô hình để **tối ưu chiến lược marketing**, giảm tỷ lệ churn và phân bổ chi phí marketing hiệu quả theo từng phân khúc khách hàng

**Key dữ liệu:**

- `customerid`: Mã định danh khách hàng
- `snapshot_month`: Tháng quan sát (ví dụ: 202410, 202411,...)

---

### 2.1 Timeline – Time Window, Label Window & Performance Window

| Snapshot Month | Time Window (3/6/12 tháng)                                                      | Label Window (Churn) | Dataset Type      |
| -------------- | ------------------------------------------------------------------------------- | -------------------- | ----------------- |
| Jan 2025       | Oct 2024 – Dec 2024 (3m) / Aug 2024 – Dec 2024 (6m) / Jan 2024 – Dec 2024 (12m) | Jan 2025             | Train             |
| Feb 2025       | Nov 2024 – Jan 2025 (3m) / Sep 2024 – Jan 2025 (6m) / Feb 2024 – Jan 2025 (12m) | Feb 2025             | Train             |
| …              | …                                                                               | …                    | …                 |
| Sep 2025       | Jun 2025 – Aug 2025 (3m) / Apr 2025 – Aug 2025 (6m) / Sep 2024 – Aug 2025 (12m) | Sep 2025             | Train             |
| Oct 2025       | Jul 2025 – Sep 2025 (3m) / Apr 2025 – Sep 2025 (6m) / Oct 2024 – Sep 2025 (12m) | Oct 2025             | Validation        |
| Nov 2025       | Aug 2025 – Oct 2025 (3m) / May 2025 – Oct 2025 (6m) / Nov 2024 – Oct 2025 (12m) | Nov 2025             | Test              |
| Dec 2025       | Sep 2025 – Nov 2025 (3m) / Jun 2025 – Nov 2025 (6m) / Dec 2024 – Nov 2025 (12m) | Dec 2025             | Out-of-time (OOT) |

- Performance Window (Label Window mở rộng): khoảng thời gian **sau snapshot** mà ta quan sát xem khách hàng có churn hay không.
- **Thiết lập trong project**
  - Performance Window: **1 – 3 tháng sau snapshot**
  - Áp dụng đặc biệt cho **Test & Out-of-time (OOT)** để đánh giá độ bền của mô hình.

---

### 2.2. Nguồn Dữ Liệu

Dữ liệu được thu thập từ các nguồn cốt lõi, phản ánh thông tin định danh, hành vi tài chính, mức độ tương tác và phản hồi marketing của khách hàng:

| Nguồn Dữ Liệu            | Mô Tả                                                                                                     | Granularity             |
| ------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------- |
| **Customer Master**      | Thông tin định danh khách hàng; bao gồm `customer_id`, nhãn churn và trạng thái khách hàng                | Khách hàng              |
| **CASA**                 | Giao dịch tài khoản thanh toán: số dư, dòng tiền, tần suất giao dịch; nguồn tín hiệu churn sớm quan trọng | Khách hàng - Tháng      |
| **Loan**                 | Thông tin khoản vay và nghĩa vụ thanh toán; phản ánh áp lực tài chính                                     | Khách hàng - Tháng      |
| **Credit Card**          | Giao dịch thẻ tín dụng: chi tiêu, sử dụng hạn mức, thanh toán; đo lường mức độ engagement                 | Khách hàng - Tháng      |
| **Demographic**          | Thông tin nhân khẩu học phục vụ phân khúc và diễn giải mô hình                                            | Khách hàng              |
| **Channel Usage**        | Hành vi sử dụng kênh số; phát hiện sớm dấu hiệu churn                                                     | Khách hàng - Tháng      |
| **Customer Interaction** | Lịch sử tương tác và khiếu nại; yếu tố rủi ro churn quan trọng                                            | Khách hàng - Tháng      |
| **Campaign Response**    | Phản hồi chiến dịch marketing; phục vụ chiến lược giữ chân khách hàng                                     | Khách hàng - Chiến dịch |

---

### 2.4 Tổng hợp vai trò dữ liệu

| Nhóm dữ liệu         | Vai trò                        |
| -------------------- | ------------------------------ |
| Customer Master      | Anchor & label                 |
| CASA                 | ⭐⭐⭐⭐⭐ Early churn         |
| Loan                 | Stress tài chính               |
| Credit Card          | Engagement                     |
| Demographic          | Explain & segment              |
| Channel Usage        | ⭐⭐⭐⭐⭐ Digital early churn |
| Customer Interaction | Experience-driven churn        |
| Campaign Response    | Retention strategy             |

---

## 3. Định nghĩa churn (Label Definition)

#### `churn_label`

- **Kiểu dữ liệu:** BOOLEAN / INTEGER (0/1)
- **Mô tả:** Khách hàng có churn (rời bỏ tài khoản CASA) hay không
- **Mã hóa:**
  - `0`: Không Churn (khách hàng giữ lại CASA)
  - `1`: Churn (khách hàng đóng/ngừng sử dụng CASA)

---

### Các Phương Án Định Nghĩa Churn

#### **PHƯƠNG ÁN 1: ĐÓNG TÀI KHOẢN (ACCOUNT CLOSURE)** ⭐ KHUYẾN NGHỊ

**Mô tả:**

> Tài khoản CASA chính thức bị đóng (account formally closed)

**Logic:**

```
IF snapshot_month = M, THEN:
  - Observation period: Tháng M (thu thập features từ tháng M)
  - Label period: Tháng M+1 (kiểm tra trạng thái tài khoản)

  churn = 1 IF casa_status(M+1) = 'CLOSED'
  churn = 0 IF casa_status(M+1) = 'ACTIVE'
```

**Ưu điểm:**

- ✅ Rõ ràng, không mơ hồ
- ✅ Đúng nghĩa churn theo định nghĩa chuẩn
- ✅ Dễ thu thập dữ liệu (có trong hệ thống core banking)

**Nhược điểm:**

- ⚠️ Không bắt được khách hàng có ý định churn nhưng chưa đóng tài khoản

**Khuyến nghị:** ✅ **PHƯƠNG ÁN TỐT NHẤT** cho CASA (sản phẩm có vòng đời rõ ràng)

---

#### **PHƯƠNG ÁN 2: TÀI KHOẢN NGỦ (DORMANT ACCOUNT)**

**Mô tả:**

> Tài khoản CASA không có giao dịch trong N tháng liên tiếp

**Logic:**

```
IF snapshot_month = M, THEN:
  - Observation period: Tháng M
  - Label period: Tháng M+1 đến M+N (look ahead N months)

  churn = 1 IF casa_transaction_count = 0
            for N consecutive months (thường N = 3)
  churn = 0 IF casa_transaction_count > 0
```

**Ưu điểm:**

- ✅ Phát hiện sớm (early warning signal)
- ✅ Bắt được ý định churn trước khi đóng tài khoản

**Nhược điểm:**

- ⚠️ Có thể nhiễu (khách hàng đi du lịch, tạm ngừng giao dịch)
- ⚠️ Cần định nghĩa N phù hợp (3, 6, 12 tháng?)

**Khuyến nghị:** ⚠️ **BỔ SUNG** (dùng làm early warning, không thay thế PHƯƠNG ÁN 1)

---

#### **PHƯƠNG ÁN 3: SỐ DƯ BẰNG 0 (ZERO BALANCE)**

**Mô tả:**

> Số dư CASA bằng 0 và duy trì 0 trong N tháng liên tiếp

**Logic:**

```
IF snapshot_month = M, THEN:
  churn = 1 IF casa_closing_balance(M+1) = 0
            AND casa_closing_balance(M+2) = 0
  churn = 0 ELSE
```

**Ưu điểm:**

- ✅ Khách hàng đã rút hết tiền → Tín hiệu mạnh

**Nhược điểm:**

- ⚠️ Có thể tạm thời (chờ giao dịch lớn)
- ⚠️ Chưa đóng tài khoản chính thức

**Khuyến nghị:** ✓ **BỔ SUNG** (feature cho model, không dùng làm label chính)

---

#### **PHƯƠNG ÁN 4: GIẢM SỬ DỤNG SẢN PHẨM (PRODUCT REDUCTION)**

**Mô tả:**

> Khách hàng giảm số lượng sản phẩm sử dụng nhưng vẫn giữ CASA

**Logic:**

```
IF snapshot_month = M, THEN:
  churn = 1 IF (product_count(M+1) < product_count(M))
            AND casa_status = 'ACTIVE'
  churn = 0 ELSE
```

**Ưu điểm:**

- ✅ Bắt được xu hướng chuyển sang đối thủ

**Nhược điểm:**

- ⚠️ Phức tạp, có thể do migration sản phẩm nội bộ
- ⚠️ Không liên quan trực tiếp đến CASA churn

**Khuyến nghị:** ⚠️ **TÙY TRƯỜNG HỢP** (phù hợp bài toán cross-sell, không phù hợp CASA churn)

---

### Định Nghĩa Churn Khuyến Nghị ⭐

#### **🎯 ĐỊNH NGHĨA CHÍNH THỨC**

```
ĐỊNH NGHĨA CHURN CHO MÔ HÌNH DỰ ĐOÁN CASA
═══════════════════════════════════════════════

Định nghĩa:
"Khách hàng được phân loại là CHURN nếu tài khoản CASA
của họ chính thức bị đóng hoặc được tuyên bố ngừng hoạt
động bởi ngân hàng trong tháng dự đoán (snapshot_month + 1)."

Cách tính:
───────────
1. Thời điểm quan sát: snapshot_month (Tháng M)
   - Thu thập tất cả features đến cuối tháng M
   - Bao gồm: giao dịch, số dư, thông tin nhân khẩu học

2. Kỳ dự đoán: snapshot_month + 1 (Tháng M+1)
   - Kiểm tra trạng thái tài khoản CASA trong tháng M+1

3. Gán nhãn:
   ✓ churn = 1 NẾU casa_account_status(M+1) = 'CLOSED'
              HOẶC casa_status_code = 04 (mã đóng tài khoản)
              HOẶC account_closure_date IS NOT NULL trong M+1

   ✓ churn = 0 NẾU casa_account_status(M+1) = 'ACTIVE'
              HOẶC 'DORMANT' (nhưng chưa đóng chính thức)
```

Loại bỏ các trường hợp sau khỏi dataset (Exclusion Rules):

| Điều Kiện                    | Lý Do Loại Trừ                                  |
| ---------------------------- | ----------------------------------------------- |
| `death_flag = 1`             | Khách hàng qua đời (không phải churn nghiệp vụ) |
| `fraud_flag = 1`             | Tài khoản gian lận (bất thường)                 |
| `regulatory_freeze = 1`      | Đóng băng theo quy định (không tự nguyện)       |
| `moratorium_flag = 1`        | Tài khoản trong giai đoạn ân hạn                |
| `customer_tenure_months < 3` | Khách hàng quá mới (tránh onboarding churn)     |
| `casa_months_active < 2`     | Tài khoản CASA quá mới                          |

---

## 4. Data Dictionary – Customer Churn Dataset

### 4.1. Customer Master – Thông Tin Định Danh Khách Hàng

Bảng Customer Master đóng vai trò **định danh khách hàng**, cung cấp **label churn** và các thuộc tính nền tảng phục vụ phân khúc.

#### Feature Classification – Customer Master

| Feature Name              | Vai trò            | Đưa vào Model | Lý do                                                       |
| ------------------------- | ------------------ | ------------- | ----------------------------------------------------------- |
| `signup_date`             | Raw date           | ❌            | Không học trực tiếp; dùng để tạo feature tenure             |
| `tenure`                  | Engineered feature | ✅            | Feature nền rất mạnh trong bài toán churn                   |
| `relationship_start_date` | Raw date           | ❌            | Trùng ý nghĩa với signup_date; dùng để kiểm tra consistency |
| `account_open_date`       | Raw date           | ❌            | Tham chiếu vòng đời khách hàng, không học trực tiếp         |
| `date_of_birth`           | Raw date           | ❌            | Không học trực tiếp; dùng để tạo feature age                |
| `age`                     | Engineered feature | ✅            | Giải thích hành vi churn theo nhóm độ tuổi                  |
| `gender`                  | Categorical        | ⚠️ (Optional) | Có thể sử dụng; predictive power thường thấp                |
| `city`                    | Raw location       | ❌            | Cardinality cao, dễ gây noise                               |
| `region`                  | Engineered feature | ✅            | Giảm cardinality, ổn định hơn city                          |
| `customer_type`           | Business category  | ✅            | Phản ánh hành vi và giá trị khách hàng                      |
| `segment`                 | Business segment   | ✅            | Quan trọng cho churn prediction & retention strategy        |
| `tier`                    | Loyalty level      | ✅            | Tier cao thường có xác suất churn thấp                      |
| `risk_rating`             | Risk indicator     | ⚠️            | Có predictive power; cần kiểm soát **leakage**              |
| `customer_name`           | PII                | ❌            | Không predictive, vi phạm privacy                           |
| `phone`                   | PII                | ❌            | Không predictive                                            |
| `email`                   | PII                | ❌            | Không predictive                                            |
| `customer_id`             | Identifier         | ❌            | Chỉ dùng để join dữ liệu                                    |
| `account_id`              | Identifier         | ❌            | Chỉ dùng để join dữ liệu                                    |
| `account_close_date`      | Outcome date       | ❌❌          | **LEAKAGE – dùng để tạo label churn**                       |
| `close_reason`            | Outcome info       | ❌❌          | Hậu quả của churn, không phải nguyên nhân                   |
| `status`                  | Status flag        | ❌            | Dùng để derive **label churn**, không làm feature           |
| `kyc_status`              | Governance         | ❌            | Trường compliance, không mang tính predictive               |

---

#### `tenure` (derived from `signup_date`)

- **Kiểu dữ liệu:** INTEGER (số tháng) hoặc FLOAT (số năm)
- **Mô tả:** Thời gian khách hàng gắn bó với ngân hàng kể từ ngày đăng ký (`signup_date`) đến `snapshot_date`
- **Derived from:** `signup_date` (công thức: `months_between(snapshot_date, signup_date)` hoặc `floor((snapshot_date - signup_date)/30)`)
- **Ví dụ:** 36 (tháng) hoặc 3.0 (năm)
- **Null Policy:** NULLABLE nếu `signup_date` missing; khuyến nghị điền -1 hoặc NULL và thêm flag `tenure_missing = 1`
- **Ý nghĩa nghiệp vụ:**
  - Tenure lớn → thường ít rủi ro churn hơn; khách hàng có lịch sử dài có giá trị LTV cao hơn
  - Tenure rất nhỏ (mới mở) → cần quan sát hành vi onboarding, ưu tiên retention
  - Dùng bucket (new / medium / long-tenure) cho segmentation và sampling

#### `relationship_start_date`

- **Kiểu dữ liệu:** DATE / TIMESTAMP
- **Mô tả:** Ngày bắt đầu quan hệ (có thể khác `signup_date` nếu có giai đoạn chuyển đổi, ví dụ chính thức mở tài khoản)
- **Ví dụ:** 2019-11-01
- **Null Policy:** NULLABLE; nếu missing nên map sang `signup_date` nếu có hoặc giữ NULL
- **Ý nghĩa nghiệp vụ:**
  - Dùng để tính `tenure` chính xác theo customer relationship (MOB)
  - Phân biệt khách hàng mở tài khoản lâu nhưng mới có giao dịch (reactivated)
  - Hữu ích cho phân tích SCD / lifecycle events

#### `account_open_date`

- **Kiểu dữ liệu:** DATE / TIMESTAMP
- **Mô tả:** Ngày mở tài khoản (account-level) — có thể xuất hiện cho từng product (CASA/Loan/CC)
- **Ví dụ:** 2021-03-15
- **Null Policy:** NULLABLE nếu bản ghi không liên quan đến một sản phẩm cụ thể
- **Ý nghĩa nghiệp vụ:**
  - Dùng phân tích `age_of_account` để hiểu maturity của relationship với từng product
  - So sánh `age_of_account` giữa các product để xác định cross-sell opportunities

#### `age` (derived from `date_of_birth`)

- **Kiểu dữ liệu:** INTEGER (năm)
- **Mô tả:** Tuổi khách hàng tính tới `snapshot_date`, dẫn xuất từ `date_of_birth`
- **Derived from:** `date_of_birth` (công thức: `floor((snapshot_date - date_of_birth)/365.25)`)
- **Ví dụ:** 38
- **Null Policy:** NULLABLE nếu `date_of_birth` missing; có thể bucket thành `age_group` nếu thiếu chi tiết
- **Ý nghĩa nghiệp vụ:**
  - Thông tin quan trọng cho segmentation, sản phẩm phù hợp (savings, pension, mortgage)
  - Kết hợp với income/tier để target sản phẩm cao cấp
  - Dùng làm biến tương tác (age × tenure, age_group × product_usage)

#### `gender`

- **Kiểu dữ liệu:** STRING (M / F / O / U)
- **Mô tả:** Giới tính khách hàng — chuẩn hoá thành M / F / O (other) / U (unknown)
- **Ví dụ:** M
- **Null Policy:** 'U' (unknown) nếu thiếu
- **Ý nghĩa nghiệp vụ:**
  - Dùng để tùy chỉnh nội dung campaign, phân tích behavioural differences
  - Tránh dùng trực tiếp làm feature chính trong các model nhạy cảm; cân nhắc fairness

#### `region` (derived from `city`)

- **Kiểu dữ liệu:** STRING
- **Mô tả:** Vùng hoặc thành phố lớn (ví dụ HCMC, HN, DN) được chuẩn hoá từ `city`
- **Derived from:** `city` (mapping `city` → `region`)
- **Ví dụ:** HCMC
- **Null Policy:** 'UNKNOWN' nếu `city` missing hoặc không map được
- **Ý nghĩa nghiệp vụ:**
  - Dùng cho phân tích địa lý, tối ưu phân phối chi nhánh/kanal, campaign theo vùng
  - Region thường correlate với income, product availability, phí dịch vụ

#### `customer_type`

- **Kiểu dữ liệu:** STRING (ví dụ: retail / corporate / SME)
- **Mô tả:** Loại khách hàng theo mô hình kinh doanh (cá nhân, doanh nghiệp nhỏ, doanh nghiệp lớn)
- **Ví dụ:** retail
- **Null Policy:** 'UNKNOWN' hoặc default 'retail' tuỳ governance
- **Ý nghĩa nghiệp vụ:**
  - Xác định ruleset, mức fee, sản phẩm ưu tiên, mô hình scoring khác nhau
  - Quan trọng khi phân tích churn, CLTV, và chiến lược cross-sell

---

#### `segment`

- **Kiểu dữ liệu:** STRING (ví dụ: Mass / Affluent / Private / Youth)
- **Mô tả:** Phân đoạn marketing / kinh doanh do business team định nghĩa (có thể dựa trên RFM hoặc tier)
- **Ví dụ:** Affluent
- **Null Policy:** 'UNSEGMENTED' nếu chưa xác định
- **Ý nghĩa nghiệp vụ:**
  - Key cho targeting campaign, ưu tiên dịch vụ và phân bổ ngân sách marketing
  - Dùng làm stratification khi training model và báo cáo KPI

#### `tier`

- **Kiểu dữ liệu:** STRING hoặc INTEGER (ví dụ: Bronze / Silver / Gold / Platinum hoặc 1/2/3/4)
- **Mô tả:** Hạng khách hàng theo giá trị/thuộc tính (hạn mức, LTV, VIP status)
- **Ví dụ:** Gold
- **Null Policy:** 'Standard' hoặc NULLABLE nếu không có thông tin
- **Ý nghĩa nghiệp vụ:**
  - Ảnh hưởng tới service-level (ưu tiên CS), fees và ưu đãi
  - Thường correlate với product penetration và propensity to churn/revenue

#### `risk_rating`

- **Kiểu dữ liệu:** STRING hoặc INTEGER (ví dụ: Low / Medium / High hoặc 1..5)
- **Mô tả:** Đánh giá rủi ro khách hàng (tín dụng / tuân thủ / rủi ro giao dịch) do bộ phận risk gán
- **Ví dụ:** Medium hoặc 3
- **Null Policy:** 'UNASSIGNED' hoặc NULL nếu chưa có đánh giá
- **Ý nghĩa nghiệp vụ:**
  - Dùng cho quyết định cross-sell (không đề xuất sản phẩm rủi ro cao cho khách hàng risk cao)
  - Quan trọng cho monitoring, limit change, action list (ví dụ tighten credit, follow-up)

#### `account_close_date`

- **Kiểu dữ liệu:** DATE / TIMESTAMP
- **Mô tả:** Ngày tài khoản chính thức bị đóng (account-level close date)
- **Ví dụ:** 2025-11-30
- **Null Policy:** NULLABLE — NULL nghĩa là tài khoản vẫn mở tại snapshot_date
- **Ý nghĩa nghiệp vụ:**
  - **DÙNG LÀM LABEL, KHÔNG DÙNG LÀ FEATURE**: `account_close_date` thường dùng để xác định nhãn churn / closed-at trong bài toán supervised learning (ví dụ: churn within next N days). Vì đây là thông tin tương lai/target tại thời điểm snapshot, không nên dùng trực tiếp làm feature đầu vào cho model.
  - Dùng để xác định thời điểm đóng và cho các phân tích hậu kiểm (post-hoc analysis) về hành vi trước đóng tài khoản.

#### `close_reason`

- **Kiểu dữ liệu:** STRING / VARCHAR (categorical)
- **Mô tả:** Mã hoặc mô tả nguyên nhân khách hàng đóng tài khoản (ví dụ: 'CUSTOMER_REQUEST', 'MIGRATION', 'FRAUD', 'DEATH')
- **Ví dụ:** CUSTOMER_REQUEST
- **Null Policy:** NULLABLE — NULL nếu tài khoản chưa đóng hoặc nguyên nhân không được ghi
- **Ý nghĩa nghiệp vụ:**
  - **HẬU QUẢ, KHÔNG PHẢI NGUYÊN NHÂN PREDICTIVE**: `close_reason` phản ánh hậu quả hoặc lý do sau khi tài khoản đã đóng. Nó hữu ích cho phân tích phân loại nguyên nhân đóng và cho báo cáo nghiệp vụ, nhưng không nên coi là feature dự báo (predictor) vì thường chỉ có sau khi đóng.
  - Có thể dùng để phân loại mẫu (post-hoc) để hiểu phân bố lý do đóng và để tinh chỉnh chiến lược giữ chân theo từng nhóm lý do.

#### `status`

- **Kiểu dữ liệu:** STRING (ví dụ: ACTIVE / DORMANT / CLOSED / SUSPENDED / PENDING)
- **Mô tả:** Trạng thái hiện tại của tài khoản/quan hệ tại thời điểm snapshot
- **Ví dụ:** CLOSED
- **Null Policy:** NOT NULL nếu hệ thống nguồn cập nhật trạng thái liên tục; nếu thiếu, dùng 'UNKNOWN'
- **Ý nghĩa nghiệp vụ:**
  - **DÙNG ĐỂ TẠO LABEL CHURN**: `status` có thể được map trực tiếp thành nhãn churn (ví dụ status == 'CLOSED' → churn = 1). Khi dùng để tạo label, cần chắc chắn chỉ sử dụng trạng thái tại một thời điểm nhất định (snapshot) và tránh rò rỉ target vào feature set.
  - Khi dùng trong EDA, status giúp phân tích phân bố khách hàng theo lifecycle; khi deploy model, cần tách rõ trường nào là target và không leak.

#### `kyc_status`

- **Kiểu dữ liệu:** STRING (ví dụ: VERIFIED / PENDING / REJECTED / NOT_SUBMITTED)
- **Mô tả:** Trạng thái KYC (know-your-customer) của khách hàng theo quy trình tuân thủ
- **Ví dụ:** VERIFIED
- **Null Policy:** 'NOT_SUBMITTED' hoặc NULL nếu chưa thực hiện KYC
- **Ý nghĩa nghiệp vụ:**
  - **GOVERNANCE — KHÔNG PREDICTIVE**: `kyc_status` là trường liên quan đến compliance/governance; thông tin này quan trọng cho hoạt động ngân hàng (onboarding, hạn chế dịch vụ) nhưng thường không mang tính predictive cho churn modelling.
  - Tuy nhiên, trong một số context nghiệp vụ, `kyc_status` có thể correlate với hành vi (ví dụ nhiều trường `PENDING` → hạn chế giao dịch), do đó có thể được dùng như một biến contextual nếu có lý do nghiệp vụ rõ ràng và không gây rò rỉ thông tin.

---

#### Ghi chú triển khai

- Khi tạo label churn từ `account_close_date` / `status`: phải xác định window label rõ ràng (ví dụ churn in next 30 days) và dùng `snapshot_date` tách rõ train/test để tránh data leakage.
- Các trường `close_reason` và `kyc_status` thường chỉ xuất hiện hoặc thay đổi sau một số sự kiện; nếu vô tình đưa các trường này vào feature set mà không xử lý time-order, sẽ gây rò rỉ target.
- Khuyến nghị: luôn tách feature layer (features derived tính tại hoặc trước snapshot_date) và label layer (target derived từ dữ liệu tương lai sau snapshot_date).
- Customer master là bảng **anchor**, không phải nguồn feature mạnh nhưng bắt buộc cho toàn bộ bài toán.

#### customer_name

- Kiểu dữ liệu: STRING / TEXT
- Mô tả: Tên đầy đủ của khách hàng (ví dụ: "Nguyễn Văn A"). Dùng cho hiển thị, xác thực hồ sơ và liên hệ.
- Ví dụ: "Trần Thị B"
- Null Policy: NULLABLE; nếu missing giữ NULL. Khi cần thống kê, map NULL → 'unknown' hoặc giữ flag is_name_missing.
- Ý nghĩa nghiệp vụ: Giúp nhận diện người dùng; có thể dùng cho trải nghiệm cá nhân hóa (gọi tên trong email/SMS). Không dùng trực tiếp làm feature cho mô hình — nếu cần cung cấp tín hiệu, tạo các đặc trưng tóm tắt (độ dài tên, số chữ, indicator chứa số) hoặc mã hóa/anonymize.

#### phone

- Kiểu dữ liệu: STRING (có thể chứa ký tự '+' và dấu cách)
- Mô tả: Số điện thoại liên hệ của khách hàng, có thể ở định dạng quốc tế hoặc địa phương.
- Ví dụ: "+84912345678", "0912345678"
- Null Policy: NULLABLE; nếu missing giữ NULL. Khi cần join hoặc phân tích, tạo cột normalized_phone và hashed_phone.
- Ý nghĩa nghiệp vụ: Dùng cho liên hệ, xác thực (2FA) và marketing. Không dùng số gốc làm feature — thay vào đó trích xuất country_code, length, is_valid_phone, mobile_provider_indicator hoặc hash để join an toàn.

#### email

- Kiểu dữ liệu: STRING / TEXT
- Mô tả: Địa chỉ email của khách hàng, dùng cho thông báo, xác thực tài khoản và liên hệ.
- Ví dụ: "nguyenvana@example.com"
- Null Policy: NULLABLE; nếu missing giữ NULL. Tạo flag is_email_missing nếu cần.
- Ý nghĩa nghiệp vụ: Email cho biết nhà cung cấp email (domain) và có thể phản ánh tính chất người dùng (corporate vs free). Không dùng email plaintext làm feature; thay vào đó trích xuất domain, kiểm tra định dạng hợp lệ, hoặc hash email cho mục đích join.

#### customer_id

- Kiểu dữ liệu: INTEGER hoặc STRING (unique identifier)
- Mô tả: ID duy nhất của khách hàng trong hệ thống (ví dụ: "CUST_00012345" hoặc số nguyên 12345). Dùng làm key để join các bảng liên quan.
- Ví dụ: "100234", "CUST-2025-0001"
- Null Policy: NOT NULL (thiếu customer_id thường là lỗi dữ liệu). Nếu gặp NULL, cần điều tra và loại bỏ/ghi nhãn record.
- Ý nghĩa nghiệp vụ: Khoá nhận diện khách hàng, dùng để tổng hợp, ghép dữ liệu lịch sử, tính các feature ở mức khách hàng (ví dụ tổng số tài khoản, tổng giao dịch). Tránh dùng `customer_id` thô làm input cho mô hình vì có thể chứa tín hiệu không mong muốn (ví dụ id tăng theo thời gian).

#### account_id

- Kiểu dữ liệu: INTEGER hoặc STRING (unique identifier cho account)
- Mô tả: ID cho từng account/tài khoản — một customer có thể có nhiều account (ví dụ tài khoản thanh toán, tài khoản dịch vụ).
- Ví dụ: "ACC_000987", 987
- Null Policy: NULLABLE tùy bảng; trong các bảng account-level, account_id nên NOT NULL. Nếu null có thể biểu thị guest/anonymous trong một số event.
- Ý nghĩa nghiệp vụ: Dùng để phân cấp dữ liệu theo account, tổng hợp (num_accounts per customer), và tính feature account-level (account_age, last_activity). Khi mô hình ở mức customer, nên aggregate từ account_id thay vì dùng account_id thô.

#### relationship_start_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày bắt đầu quan hệ chính thức giữa customer và service (có thể khác `signup_date` nếu có giai đoạn chuyển đổi, ví dụ chính thức mở tài khoản hoặc kích hoạt dịch vụ).
- Ví dụ: 2019-11-01
- Null Policy: NULLABLE; nếu missing nên map sang `signup_date` nếu có hoặc giữ NULL. Khi tính toán tenure, ưu tiên dùng `relationship_start_date` nếu nó phản ánh mốc quan hệ thực tế.
- Ý nghĩa nghiệp vụ: Dùng để tính tenure chính xác theo customer relationship; phân biệt khách hàng đã đăng ký lâu nhưng chỉ mới bắt đầu giao dịch (ví dụ reactivated). Quan trọng cho các feature thời gian: tenure_days, months_since_relationship_start, cohort analysis.

---

#### Ghi chú chung (Best practices)

- Không dùng trực tiếp các trường PII (`customer_name`, `phone`, `email`) làm input mô hình. Nếu cần tín hiệu, trích xuất các đặc trưng tóm tắt hoặc hash/anonymize.
- Dùng `customer_id` và `account_id` để join và aggregate; tránh dùng id thô như feature.
- Khi chia sẻ dữ liệu: hash các trường nhạy cảm với salt được quản lý an toàn; kiểm tra compliance (GDPR/PDPA).
- Luôn đảm bảo tính time-aware khi tạo feature: chỉ dùng giá trị tại thời điểm cut-off để tránh data leakage.

---

### 4.2 CASA – Hành vi giao dịch tài khoản

**Vai trò**

- Phát hiện **dấu hiệu churn sớm**
- Nguồn feature mạnh nhất cho mô hình churn

**Key insight**

- Giảm số dư (balance trend ↓)
- Giảm inflow, tăng outflow
- Tần suất giao dịch giảm
- Chuyển từ active sang dormant

#### CASA có thể giúp dự đoán **70–80% churn** nếu feature engineering tốt.

| Feature                     | Category   | Used in Model | Ghi chú                                  |
| --------------------------- | ---------- | ------------- | ---------------------------------------- |
| customerid                  | Raw        | ❌            | ID khách hàng                            |
| id                          | Raw        | ❌            | ID kỹ thuật / key                        |
| casa_daily_average_balance  | Raw        | ✅            | Feature cơ bản mạnh                      |
| casa_inflow                 | Raw        | ✅            | Tín hiệu churn sớm                       |
| casa_outflow                | Raw        | ✅            | Kết hợp với inflow                       |
| casa_transaction_count      | Raw        | ✅            | Biểu hiện mức độ tương tác               |
| casa_transaction_avg_amount | Raw        | ⚠️            | Tùy ngữ cảnh                             |
| casa_closing_balance        | Raw        | ❌            | Chỉ dùng để tính delta                   |
| casa_opening_balance        | Raw        | ❌            | Nguồn tính delta                         |
| casa_active_flag            | Raw        | ❌            | Dùng lagged                              |
| casa_account_status         | Raw        | ❌            | Map trước                                |
| casa_status_code            | Raw        | ❌            | Mã trạng thái tài khoản                  |
| account_closure_date        | Outcome    | ❌❌          | Leakage (dữ liệu rò rỉ), **label churn** |
| balance_drop_1m             | Engineered | ✅            | Feature chính                            |
| balance_drop_3m             | Engineered | ✅            | Feature chính                            |
| inflow_trend_3m             | Engineered | ✅            | Feature chính                            |
| txn_gap_days                | Engineered | ✅            | Churn sớm                                |
| inactive_streak_months      | Engineered | ✅            | Tình trạng dormancy                      |
| volatility_balance          | Engineered | ✅            | Độ ổn định tài khoản                     |

---

#### id

- Kiểu dữ liệu: STRING / INTEGER
- Mô tả: Khóa bản ghi (row-level id) trong nguồn dữ liệu CASA.
- Ví dụ: 12345
- Null Policy: NOT NULL
- Ý nghĩa nghiệp vụ: Dùng để truy vết bản ghi nguồn; không dùng làm feature.
- Gợi ý: Dùng cho debug / dedupe; drop khi làm feature table.

#### customerid

- Kiểu dữ liệu: STRING / INTEGER
- Mô tả: Mã định danh khách hàng (khóa để join với Customer Master và các bảng khác).
- Ví dụ: "CUST_000123"
- Null Policy: NOT NULL (nếu có NULL là lỗi dữ liệu cần điều tra)
- Ý nghĩa nghiệp vụ: Anchor key để aggregate account-level sang customer-level (ví dụ num_accounts, total_balance).
- Gợi ý: Chuẩn hoá kiểu, kiểm tra duplicates, tạo hashed_customerid nếu chia sẻ dữ liệu.

---

#### snapshot_month

- Kiểu dữ liệu: STRING / INTEGER (YYYYMM) hoặc DATE (last day of month)
- Mô tả: Tháng quan sát (ví dụ 202411) — dùng làm thời điểm snapshot để tính feature và label.
- Ví dụ: 202411
- Null Policy: NOT NULL
- Ý nghĩa nghiệp vụ: Xác định cut-off (snapshot_date) cho training/labeling; mọi derived feature phải tính đến snapshot_month để tránh data leakage.
- Gợi ý: Chuẩn hoá sang DATE (e.g., last day of month) để tính khoảng thời gian dễ dàng.

#### casa_status_code

- Kiểu dữ liệu: STRING / CATEGORICAL
- Mô tả: Mã trạng thái tài khoản CASA tại thời điểm ghi nhận (ví dụ: ACTIVE, DORMANT, CLOSED, SUSPENDED).
- Ví dụ: ACTIVE
- Null Policy: 'UNKNOWN' nếu missing
- Ý nghĩa nghiệp vụ: Trạng thái là chỉ báo trực tiếp cho churn/dormancy; dùng để derive label (status == CLOSED → churn) nhưng phải tránh dùng trực tiếp làm feature nếu nó phản ánh tương lai.
- Gợi ý: Chuẩn hoá mapping (ACTIVE→1, DORMANT→0.5, CLOSED→0), tạo lagged_status để dùng trong bảng thời điểm trước snapshot.

#### account_closure_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày tài khoản CASA bị đóng (nếu có).
- Ví dụ: 2025-11-30
- Null Policy: NULLABLE (NULL = still open)
- Ý nghĩa nghiệp vụ: DÙNG LÀ LABEL/OUTCOME — không dùng làm feature. Sử dụng để xác định churn window (e.g., closed within next 30 days).
- Gợi ý: Khi build dataset supervised, chỉ derive label từ account_closure_date ở thời điểm sau snapshot_date.

#### casa_closing_balance

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Số dư cuối kỳ (closing balance) tại ngày snapshot hoặc cuối tháng.
- Ví dụ: 1200000.50
- Null Policy: NULLABLE; nếu missing, có thể infer từ transaction history hoặc giữ NULL và tạo flag.
- Ý nghĩa nghiệp vụ: Thể hiện trạng thái vốn trên tài khoản; giảm mạnh có thể là early signal của churn.
- Gợi ý chuyển đổi:
  - Tính delta so với prior period: delta_1m = closing_balance - closing_balance_lag1
  - Tính rolling mean, volatility (std) trong 3/6 tháng
  - Tạo indicator balance_drop_1m / balance_drop_3m

#### casa_inflow

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tổng luồng tiền vào tài khoản trong chu kỳ (ví dụ tổng tiền nhận trong tháng).
- Ví dụ: 5000000.00
- Null Policy: NULLABLE; nếu missing coi là 0 hoặc giữ NULL với flag is_inflow_missing
- Ý nghĩa nghiệp vụ: Giảm inflow (lương, chuyển khoản) là chỉ báo mạnh cho disengagement / churn risk.
- Gợi ý chuyển đổi:
  - Tính trend: inflow_trend_3m = slope hoặc pct_change over 3 months
  - Tạo ratio inflow / avg_balance

#### casa_outflow

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tổng luồng tiền ra tài khoản trong chu kỳ (ví dụ chi tiêu, rút tiền).
- Ví dụ: 4500000.00
- Null Policy: NULLABLE; nếu missing coi là 0
- Ý nghĩa nghiệp vụ: Thay đổi đột ngột trong outflow (ví dụ rút tiền lớn) có thể báo hiệu churn hoặc lifecycle event (travel, purchase).
- Gợi ý: Tính net_flow = inflow - outflow; tạo features net_flow_pct, outflow_spike_flag.

#### casa_transaction_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số giao dịch phát sinh trên tài khoản trong chu kỳ (tháng/ngày tùy nguồn).
- Ví dụ: 12
- Null Policy: NOT NULL (0 nếu không có giao dịch)
- Ý nghĩa nghiệp vụ: Giảm transaction_count rất thường gặp trước churn. Early warning signal.
- Gợi ý chuyển đổi:
  - txn_count_trend = pct_change hoặc slope over 3 months
  - txn_gap_days = khoảng ngày lớn nhất giữa 2 giao dịch

#### casa_transaction_avg_amount

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Trung bình giá trị mỗi giao dịch trong chu kỳ (inflow/outflow separately or combined).
- Ví dụ: 420000.00
- Null Policy: NULLABLE; nếu no txn giữ NULL
- Ý nghĩa nghiệp vụ: Thay đổi trong average amount có thể phản ánh thay đổi hành vi (giảm tần suất nhưng tăng giá trị, v.v.).
- Gợi ý: Tính var/volatility của txn amount, tạo features high_value_txn_flag.

#### casa_opening_balance (dùng delta)

- Kiểu dữ liệu: NUMERIC
- Mô tả: Số dư đầu kỳ; dùng để tính delta so với closing_balance để hiểu biến động trong kỳ.
- Ví dụ: 1500000.00
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Delta giữa opening và closing phản ánh cash flow trong kỳ; dùng để detect sudden withdrawals/deposits.
- Gợi ý: Tính delta_open_close = closing_balance - opening_balance; chuẩn hóa theo avg_balance.

#### casa_active_flag (lagged)

- Kiểu dữ liệu: BOOLEAN / INTEGER (0/1)
- Mô tả: Cờ chỉ báo account có activity trong kỳ trước (lagged) — ví dụ có >=1 transaction trong last month.
- Ví dụ: 1
- Null Policy: NOT NULL (default 0)
- Ý nghĩa nghiệp vụ: Lagged active flag giúp phân biệt transient inactivity vs long-term dormant. Lagging tránh data leakage.
- Gợi ý: Tạo lagged flags cho 1m, 3m, 6m (active_lag1, active_lag3, ...)

#### casa_account_status (mapping trước)

- Kiểu dữ liệu: STRING / CATEGORICAL (mapped)
- Mô tả: Status đã được mapping/chuẩn hoá (ví dụ: map raw status → {OPEN, DORMANT, CLOSED, SUSPENDED}).
- Ví dụ: DORMANT
- Null Policy: 'UNKNOWN'
- Ý nghĩa nghiệp vụ: Standardized status giúp phân tích cohort và tạo label. Mapping phải sử dụng chỉ dữ liệu up-to-snapshot.
- Gợi ý: Tạo ordinal encoding hoặc one-hot; tránh leak bằng cách chỉ dùng status history up to snapshot.

---

#### Engineered features (Feature engineering)

##### balance_drop_1m

- Kiểu dữ liệu: NUMERIC (DECIMAL) hoặc BOOLEAN (indicator)
- Mô tả: Mức giảm (absolute hoặc pct) của closing balance so với 1 tháng trước.
- Ví dụ: -350000.00 hoặc -0.23 (tức giảm 23%)
- Null Policy: NULLABLE; nếu lag missing giữ NULL và tạo flag missing
- Ý nghĩa nghiệp vụ: Giảm số dư 1 tháng là early signal churn (rút tiền chuyển đi).
- Gợi ý: Tính both absolute_drop và pct_drop; tạo indicator nếu pct_drop < -0.2.

##### balance_drop_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Mức giảm (absolute/pct) của closing balance so với 3 tháng trước (rolling).
- Ví dụ: -1200000.00 hoặc -0.45
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Giảm dần trong 3 tháng mạnh hơn 1 tháng cho thấy disengagement có xu hướng.
- Gợi ý: Tính slope của balance series over 3 months (linear regression) để capture trend.

##### inflow_trend_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Độ dốc hoặc tỉ lệ thay đổi của inflow trong 3 tháng (có thể là slope hoặc pct_change).
- Ví dụ: -0.15 (giảm 15% over 3m)
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Sụt giảm inflow (ví dụ mất nguồn thu nhập) là chỉ báo rủi ro churn.
- Gợi ý: Dùng regression slope hoặc z-score so với population to detect significant drop.

##### txn_count_trend

- Kiểu dữ liệu: NUMERIC
- Mô tả: Thay đổi của số lượng giao dịch (trend) trong window (ví dụ 3 tháng).
- Ví dụ: -0.30 (giảm 30%)
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Giảm tần suất giao dịch là early warning signal.
- Gợi ý: Tính pct_change over 1m/3m, hoặc slope; kết hợp với txn_gap_days.

##### txn_gap_days

- Kiểu dữ liệu: INTEGER
- Mô tả: Khoảng ngày lớn nhất (hoặc trung bình) giữa 2 giao dịch gần nhất trong window (day gap).
- Ví dụ: 45
- Null Policy: NULLABLE (nếu không có giao dịch → NULL hoặc set large number)
- Ý nghĩa nghiệp vụ: Gap lớn → dormant; dùng để detect prolonged inactivity.
- Gợi ý: Tính max_gap và avg_gap trong last 3/6 months; cắt bucket (0-7,8-30,31-90,>90).

##### inactive_streak_months

- Kiểu dữ liệu: INTEGER
- Mô tả: Số tháng liên tiếp không có giao dịch (dormant streak) tính tới snapshot.
- Ví dụ: 2
- Null Policy: 0 nếu có giao dịch trong month; else computed
- Ý nghĩa nghiệp vụ: Streak dài tăng nguy cơ churn; dùng làm feature phân lớp (0,1-2,3+).
- Gợi ý: Compute from monthly aggregation, create bins.

##### volatility_balance

- Kiểu dữ liệu: NUMERIC
- Mô tả: Độ biến động số dư trong window (ví dụ standard deviation of daily balances or monthly closing balances).
- Ví dụ: 250000.00
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Volatility cao có thể cho thấy erratic behavior hoặc large inflows/outflows; phụ trợ cho interpretation của balance drops.
- Gợi ý: Compute std over 3/6 months; normalize by mean_balance.

---

#### Gợi ý triển khai (pandas / SQL)

- Tính các lag/rolling cần thiết theo nhóm `customerid` / `account_id` và `snapshot_month`.
- Luôn tính features chỉ dựa trên dữ liệu up-to-and-including snapshot_date để tránh data leakage.
- Khi aggregate từ account-level lên customer-level: sử dụng aggregations (sum, mean, max, count, pct_change) và tạo distinct counts (num_accounts_with_activity).
- Thêm các flags missing (e.g., balance_missing_flag) để mô hình học được pattern missingness.

---

### 4.3 Loan – Dòng tiền & stress tài chính

**Vai trò**

- Đánh giá áp lực tài chính của khách hàng

**Key insight**

- CASA giảm + khoản vay lớn → churn risk cao
- Trễ hạn thanh toán làm trải nghiệm xấu
- Khách hàng churn sau khi tất toán khoản vay

Loan không phải nguyên nhân duy nhất của churn nhưng **khuếch đại rủi ro churn**.

#### Feature Classification – Loan

| Feature Name             | Vai trò            | Đưa vào Model | Lý do                                                    |
| ------------------------ | ------------------ | ------------- | -------------------------------------------------------- |
| id                       | Identifier         | ❌            | Key kỹ thuật                                             |
| customerid               | Identifier         | ❌            | Key nối dữ liệu                                          |
| snapshot_month           | Time index         | ❌            | Mốc thời gian; không dùng trực tiếp                      |
| loan_outstanding_balance | Financial metric   | ✅            | Phản ánh nghĩa vụ nợ hiện tại; liên quan trực tiếp churn |
| loan_monthly_payment     | Financial metric   | ✅            | Áp lực dòng tiền hàng tháng                              |
| loan_count               | Aggregated count   | ✅            | Nhiều khoản vay → stress tài chính cao hơn               |
| loan_to_casa_ratio       | Engineered ratio   | ✅            | Đo mức độ phụ thuộc CASA để trả nợ                       |
| loan_payment_ratio       | Engineered ratio   | ✅            | Tỷ lệ trả nợ/thu nhập CASA; áp lực thanh toán            |
| loan_balance_trend_3m    | Engineered trend   | ✅            | Xu hướng dư nợ 3 tháng                                   |
| payment_miss_streak      | Engineered trend   | ✅            | Số kỳ liên tiếp bỏ sót thanh toán                        |
| arrears_months_count     | Engineered count   | ✅            | Số tháng trễ hạn                                         |
| loan_to_income_proxy     | Engineered ratio   | ✅            | Proxy thu nhập từ CASA nếu có                            |
| loan_payment_status_lag  | Engineered feature | ✅            | Phản ánh hành vi thanh toán quá khứ (tránh leakage)      |
| loan_arrears_flag_lag    | Engineered feature | ✅            | Trễ hạn trong quá khứ là tín hiệu churn mạnh             |
| loan_has_arrears         | Binary flag        | ❌            | Không dùng trực tiếp; dùng để tạo lagged arrears feature |
| loan_payment_status      | Status flag        | ❌            | Không dùng trực tiếp; dùng để tạo lag / severity score   |
| loan_status              | Outcome flag       | ❌❌          | **LEAKAGE – DEFAULT là hậu quả**                         |
| loan_written_off         | Outcome flag       | ❌❌          | **LEAKAGE – write-off xảy ra sau churn**                 |

---

#### loan_outstanding_balance

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tổng dư nợ hiện tại của khách hàng.
- Ví dụ: 1250000.0
- Null Policy: NULLABLE; nếu missing, giữ NULL và tạo flag.
- Ý nghĩa nghiệp vụ: Số dư nợ cao → áp lực tài chính tăng, khả năng churn cao.
- Gợi ý chuyển đổi:
  - Tính log(value + 1) để giảm skew
  - Chuẩn hóa (z-score) nếu dùng cho ML

#### loan_monthly_payment

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Số tiền trả nợ hàng tháng.
- Ví dụ: 3500.0
- Null Policy: NULLABLE; nếu missing, giữ NULL và tạo flag.
- Ý nghĩa nghiệp vụ: Thanh toán hàng tháng cao → áp lực dòng tiền tăng, tín hiệu churn.
- Gợi ý chuyển đổi:
  - Tính tỷ lệ payment/inflow
  - Tính log(value + 1) nếu phân phối lệch

#### loan_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lượng khoản vay khách hàng đang có.
- Ví dụ: 3
- Null Policy: NULLABLE; nếu missing, giữ NULL và tạo flag.
- Ý nghĩa nghiệp vụ: Nhiều khoản vay → stress tài chính cao, tăng nguy cơ churn.
- Gợi ý chuyển đổi:
  - Nhóm bins (1,2,3,4+) để interpretability
  - Tạo feature ratio: loan_count / casa_account_age

#### loan_to_casa_ratio

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tỷ lệ giữa tổng outstanding loan và CASA closing balance hoặc CASA_inflow.
- Ví dụ: 4.2
- Null Policy: NULLABLE; nếu CASA missing thì giữ NULL và tạo flag.
- Ý nghĩa nghiệp vụ: Loan/CASA ratio tăng → khách hàng căng dòng tiền; tỷ lệ cao là red flag cho risk & churn.
- Gợi ý chuyển đổi:
  - Tính cả absolute_ratio và log_ratio
  - Tạo bins (<=1, 1-3, 3-5, >5)

#### loan_payment_ratio

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tỷ lệ thanh toán nợ hàng tháng / CASA inflow.
- Ví dụ: 0.35 (35% inflow dùng trả nợ)
- Null Policy: NULLABLE; giữ NULL nếu inflow missing
- Ý nghĩa nghiệp vụ: Tỷ lệ cao → áp lực thanh toán lớn, tín hiệu churn.
- Gợi ý chuyển đổi:
  - Tạo bins (0-0.2,0.2-0.5,0.5+)
  - Tính log ratio nếu phân phối lệch

#### loan_balance_trend_3m

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Xu hướng dư nợ trong 3 tháng gần nhất (delta hoặc slope)
- Ví dụ: +5000 (dư nợ tăng 5000 so với 3 tháng trước)
- Null Policy: NULLABLE; nếu thiếu tháng nào, giữ NULL
- Ý nghĩa nghiệp vụ: Dư nợ tăng liên tục → áp lực tài chính tăng, churn cao.
- Gợi ý chuyển đổi:
  - Tính slope hoặc delta trung bình 3 tháng
  - Tạo bins (tăng, giảm, ổn định)

#### payment_miss_streak

- Kiểu dữ liệu: INTEGER
- Mô tả: Số kỳ thanh toán liên tiếp bị bỏ lỡ
- Ví dụ: 2
- Null Policy: NULLABLE; giữ 0 nếu chưa từng trễ hạn
- Ý nghĩa nghiệp vụ: Streak dài → nguy cơ churn mạnh
- Gợi ý chuyển đổi:
  - Nhóm bins (0,1,2,3+)
  - Kết hợp với loan_outstanding_balance

#### arrears_months_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số tháng có trễ hạn
- Ví dụ: 3
- Null Policy: NULLABLE; giữ 0 nếu chưa trễ hạn
- Ý nghĩa nghiệp vụ: Chỉ số arrears → tín hiệu cảnh báo churn
- Gợi ý chuyển đổi:
  - Tạo ratio: arrears_months_count / loan_tenure_months
  - Nhóm bins (0,1-2,3-5,>5)

#### loan_to_income_proxy

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Proxy thu nhập khách hàng dựa trên CASA inflow
- Ví dụ: 0.25 (tỷ lệ nợ / inflow)
- Null Policy: NULLABLE; giữ NULL nếu inflow missing
- Ý nghĩa nghiệp vụ: Tỷ lệ nợ / thu nhập cao → áp lực tài chính, tín hiệu churn
- Gợi ý chuyển đổi:
  - Tính log_ratio
  - Nhóm bins (0-0.2,0.2-0.5,0.5+)

#### loan_payment_status_lag

- Kiểu dữ liệu: CATEGORICAL / BINARY
- Mô tả: Trạng thái thanh toán nợ quá khứ (lag 1 tháng, 2 tháng,…)
- Ví dụ: 0 = thanh toán đầy đủ, 1 = trễ hạn
- Null Policy: NULLABLE; nếu chưa có lịch sử, giữ NULL
- Ý nghĩa nghiệp vụ: Hành vi trễ hạn quá khứ → dự báo churn
- Gợi ý chuyển đổi:
  - One-hot encoding hoặc giữ binary 0/1
  - Có thể tính severity score từ số lần trễ hạn

#### loan_arrears_flag_lag

- Kiểu dữ liệu: BINARY
- Mô tả: Flag trễ hạn từ lịch sử (lag)
- Ví dụ: 1 = có trễ hạn trong quá khứ
- Null Policy: NULLABLE; giữ 0 nếu chưa trễ hạn
- Ý nghĩa nghiệp vụ: Trễ hạn trong quá khứ → tín hiệu churn mạnh
- Gợi ý chuyển đổi:
  - Giữ binary
  - Tính số tháng liên tiếp trễ hạn

#### loan_has_arrears

- Kiểu dữ liệu: BINARY
- Mô tả: Khách hàng đang có khoản trễ hạn hiện tại
- Ví dụ: 1 = đang trễ hạn
- Null Policy: NULLABLE; giữ 0 nếu không
- Ý nghĩa nghiệp vụ: Không dùng trực tiếp vào model để tránh leakage; dùng để tạo lagged feature
- Gợi ý chuyển đổi:
  - Tạo lag feature: loan_arrears_flag_lag

#### loan_payment_status

- Kiểu dữ liệu: CATEGORICAL / BINARY
- Mô tả: Trạng thái thanh toán hiện tại
- Ví dụ: 0 = OK, 1 = trễ hạn
- Null Policy: NULLABLE; giữ NULL nếu không xác định
- Ý nghĩa nghiệp vụ: Không dùng trực tiếp vào model; dùng để tạo lag / severity score
- Gợi ý chuyển đổi:
  - Tạo severity score hoặc lagged feature

#### loan_status

- Kiểu dữ liệu: BINARY / CATEGORICAL
- Mô tả: Trạng thái khoản vay (DEFAULT/ACTIVE)
- Ví dụ: 1 = default
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: **LEAKAGE – hậu quả, không dùng làm feature**
- Gợi ý chuyển đổi: Không dùng

#### loan_written_off

- Kiểu dữ liệu: BINARY
- Mô tả: Khoản vay đã được write-off
- Ví dụ: 1 = viết nợ xấu
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: **LEAKAGE – xảy ra sau churn**, không dùng
- Gợi ý chuyển đổi: Không dùng

---

#### Gợi ý triển khai (pandas / SQL)

- Tính lagged fields theo `customerid` và `snapshot_month` (ví dụ: lag1, lag3)
- Khi tính tỷ lệ dùng denominator guard (if denominator <= 0 → NULL) và thêm flag zero_income
- Sử dụng rolling windows và regression slope để capture trend (balance_trend_3m)
- Thử nghiệm thresholds cho payment burden (e.g., >0.3, >0.5) và validate độ lift trên validation set

---

### 4.4 Credit Card – Engagement & chi tiêu

**Vai trò**

- Đo mức độ gắn kết của khách hàng

**Key insight**

- Giảm chi tiêu thẻ = giảm engagement
- Utilization rate bất thường
- Ngừng dùng thẻ dù vẫn còn hạn mức

Bảng này giúp phân biệt **active churn vs temporary inactivity**.

#### Feature Classification – Credit Card

| Feature Name                    | Vai trò          | Đưa vào Model | Lý do                                          |
| ------------------------------- | ---------------- | ------------- | ---------------------------------------------- |
| id                              | Identifier       | ❌            | Key kỹ thuật                                   |
| customerid                      | Identifier       | ❌            | Key nối dữ liệu                                |
| snapshot_month                  | Time index       | ❌            | Mốc thời gian; không dùng trực tiếp            |
| credit_card_transaction_count   | Aggregated count | ✅            | Số giao dịch thể hiện engagement               |
| credit_card_spending            | Financial metric | ✅            | Tổng chi tiêu trên thẻ                         |
| credit_card_utilization_rate    | Engineered ratio | ✅            | Tỷ lệ sử dụng tín dụng; áp lực tài chính       |
| credit_card_outstanding_balance | Financial metric | ✅            | Dư nợ hiện tại; liên quan churn                |
| card_product_type               | Categorical      | ⚠️            | Loại thẻ; thông tin context                    |
| statement_balance               | Financial metric | ✅            | Số dư trên sao kê; dùng để tính delta/trend    |
| minimum_due                     | Financial metric | ✅            | Thanh toán tối thiểu; áp lực dòng tiền         |
| payment_amount                  | Financial metric | ✅            | Thanh toán thực tế                             |
| auto_debit_flag                 | Binary flag      | ✅            | Khách hàng tự động thanh toán → giảm rủi ro    |
| credit_card_count               | Aggregated count | ✅            | Chuyển thành binary has_card                   |
| has_card                        | Binary flag      | ✅            | 1 = có thẻ, 0 = không                          |
| credit_card_payment_status      | Status flag      | ❌            | Không dùng trực tiếp; tạo lag / severity score |
| credit_card_has_arrears         | Binary flag      | ❌            | Không dùng trực tiếp; tạo lagged arrears flag  |
| credit_card_limit               | Financial metric | ✅            | Dùng normalize spending / tỷ lệ chi tiêu       |
| spending_trend_3m               | Engineered trend | ✅            | Xu hướng chi tiêu 3 tháng                      |
| txn_cnt_trend                   | Engineered trend | ✅            | Xu hướng số lượng giao dịch                    |
| utilization_change_1m           | Engineered ratio | ✅            | Thay đổi tỷ lệ sử dụng tháng trước             |
| inactive_card_months            | Engineered count | ✅            | Số tháng thẻ không giao dịch → dormancy        |
| payment_delay_streak            | Engineered trend | ✅            | Số kỳ liên tiếp trễ hạn thanh toán             |

---

#### credit_card_transaction_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lượng giao dịch trên thẻ trong kỳ
- Ví dụ: 15
- Null Policy: NULLABLE; nếu missing, giữ 0
- Ý nghĩa nghiệp vụ: Giao dịch thấp → engagement thấp; tín hiệu churn
- Gợi ý chuyển đổi:
  - Tạo bins (0-5,6-15,16+)
  - Tính trend 3 tháng nếu cần

#### credit_card_spending

- Kiểu dữ liệu: NUMERIC
- Mô tả: Tổng chi tiêu trên thẻ
- Ví dụ: 2500.0
- Null Policy: NULLABLE; giữ 0 nếu không chi tiêu
- Ý nghĩa nghiệp vụ: Chi tiêu giảm → tín hiệu disengagement/churn
- Gợi ý chuyển đổi:
  - Log(value + 1)
  - Tính trend 3 tháng

#### credit_card_utilization_rate

- Kiểu dữ liệu: NUMERIC (0-1)
- Mô tả: Tỷ lệ chi tiêu/thẻ / hạn mức thẻ
- Ví dụ: 0.65
- Null Policy: NULLABLE; nếu limit missing, giữ NULL
- Ý nghĩa nghiệp vụ: Tỷ lệ cao → rủi ro tài chính; tỷ lệ thấp → disengagement
- Gợi ý chuyển đổi:
  - Tạo bins (0-0.3,0.3-0.7,0.7+)
  - Tính delta so với tháng trước

#### credit_card_outstanding_balance

- Kiểu dữ liệu: NUMERIC
- Mô tả: Dư nợ hiện tại trên thẻ
- Ví dụ: 1200.0
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Dư nợ cao → áp lực tài chính; tín hiệu churn
- Gợi ý chuyển đổi:
  - Log(value + 1)
  - Delta/trend 3 tháng

#### card_product_type

- Kiểu dữ liệu: CATEGORICAL
- Mô tả: Loại thẻ (classic/gold/platinum)
- Ví dụ: gold
- Null Policy: NULLABLE; tạo category "unknown" nếu missing
- Ý nghĩa nghiệp vụ: Thẻ cao cấp → chi tiêu lớn hơn; interpretability
- Gợi ý chuyển đổi:
  - One-hot encoding
  - Map rank numeric (classic=1, gold=2, platinum=3)

#### statement_balance

- Kiểu dữ liệu: NUMERIC
- Mô tả: Số dư trên sao kê
- Ví dụ: 3500.0
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Dùng để tạo delta/trend; thanh toán thấp → rủi ro
- Gợi ý chuyển đổi:
  - Delta/trend so với kỳ trước

#### minimum_due

- Kiểu dữ liệu: NUMERIC
- Mô tả: Thanh toán tối thiểu
- Ví dụ: 500.0
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Không thanh toán → tín hiệu rủi ro
- Gợi ý chuyển đổi:
  - Tính ratio payment_amount / minimum_due

#### payment_amount

- Kiểu dữ liệu: NUMERIC
- Mô tả: Thanh toán thực tế
- Ví dụ: 500.0
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Thanh toán thấp → tín hiệu churn / rủi ro
- Gợi ý chuyển đổi:
  - Delta so với minimum_due
  - Lag / streak

#### auto_debit_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 = tự động thanh toán, 0 = không
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Giảm rủi ro churn; tiện lợi cho khách hàng
- Gợi ý chuyển đổi:
  - Giữ binary
  - Kết hợp với payment_amount

#### credit_card_count / has_card

- Kiểu dữ liệu: INTEGER / BINARY
- Mô tả: Số thẻ khách hàng có / 1 = có thẻ, 0 = không
- Null Policy: NULLABLE; giữ 0 nếu không có
- Ý nghĩa nghiệp vụ: Không có thẻ → engagement thấp
- Gợi ý chuyển đổi:
  - Chuyển sang binary has_card
  - Nhóm bins nếu count >1

#### credit_card_payment_status

- Kiểu dữ liệu: CATEGORICAL / BINARY
- Mô tả: Trạng thái thanh toán hiện tại
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Không dùng trực tiếp; tạo lagged / severity score
- Gợi ý chuyển đổi:
  - Lagged payment status
  - Severity score

#### credit_card_has_arrears

- Kiểu dữ liệu: BINARY
- Mô tả: Có khoản trễ hạn
- Null Policy: NULLABLE; giữ 0 nếu không
- Ý nghĩa nghiệp vụ: Không dùng trực tiếp; tạo lagged arrears flag
- Gợi ý chuyển đổi:
  - Lagged arrears flag
  - Payment_delay_streak

#### credit_card_limit

- Kiểu dữ liệu: NUMERIC
- Mô tả: Hạn mức thẻ
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Dùng normalize spending / utilization rate
- Gợi ý chuyển đổi:
  - Tính ratio spending / limit
  - Log(value + 1) nếu skewed

#### spending_trend_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Xu hướng chi tiêu 3 tháng
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Chi tiêu giảm → disengagement
- Gợi ý chuyển đổi:
  - Delta trung bình hoặc slope 3 tháng
  - Tạo bins tăng/giảm/ổn định

#### txn_cnt_trend

- Kiểu dữ liệu: NUMERIC
- Mô tả: Xu hướng số lượng giao dịch
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Giao dịch giảm → tín hiệu churn
- Gợi ý chuyển đổi:
  - Delta / slope 3 tháng

#### utilization_change_1m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Thay đổi tỷ lệ sử dụng tháng trước
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Tăng nhanh → rủi ro; giảm → disengagement
- Gợi ý chuyển đổi:
  - Delta / pct_change
  - Tạo bins nhỏ/trung/big

#### inactive_card_months

- Kiểu dữ liệu: INTEGER
- Mô tả: Số tháng thẻ không giao dịch
- Null Policy: NULLABLE; giữ 0 nếu luôn hoạt động
- Ý nghĩa nghiệp vụ: Dormancy → tín hiệu churn
- Gợi ý chuyển đổi:
  - Tạo bins (0,1-3,4-6,>6)
  - Kết hợp với spending_trend_3m

#### payment_delay_streak

- Kiểu dữ liệu: INTEGER
- Mô tả: Số kỳ liên tiếp trễ hạn thanh toán
- Null Policy: NULLABLE; giữ 0 nếu chưa trễ
- Ý nghĩa nghiệp vụ: Streak dài → tín hiệu churn mạnh
- Gợi ý chuyển đổi:
  - Nhóm bins (0,1-2,3+)
  - Kết hợp với credit_card_outstanding_balance

---

### 4.5 Demographic – Phân khúc & giải thích model

**Vai trò**

- Phân khúc khách hàng
- Giải thích hành vi churn

**Key insight**

- Nhóm tuổi trẻ churn nhanh hơn
- Thu nhập thấp nhạy cảm với phí
- Khu vực, nghề nghiệp ảnh hưởng retention

Demographic **không phải early signal**, nhưng rất quan trọng cho explainability.

#### Feature Classification – Customer

| Feature Name         | Vai trò                  | Đưa vào Model | Lý do                                                    |
| -------------------- | ------------------------ | ------------- | -------------------------------------------------------- |
| `customer_age`       | Demographic              | ✅            | Tuổi tác ảnh hưởng hành vi và khả năng mua sản phẩm      |
| `income_level`       | Demographic / Financial  | ✅            | Thu nhập quyết định khả năng chi tiêu và đầu tư sản phẩm |
| `employment_status`  | Demographic              | ✅            | Ổn định việc làm liên quan đến rủi ro khách hàng churn   |
| `product_count`      | Behavioral               | ✅            | Số lượng sản phẩm hiện tại phản ánh mức độ gắn bó        |
| `occupation`         | Demographic              | ✅            | Nghề nghiệp ảnh hưởng thu nhập và nhu cầu sản phẩm       |
| `residence_location` | Demographic / Behavioral | ✅            | Vùng sinh sống ảnh hưởng kênh tiếp cận và hành vi mua    |
| `channel_preference` | Behavioral               | ✅            | Thói quen kênh tiếp cận giúp cá nhân hóa marketing       |
| `tenure_months`      | Engineered feature       | ✅            | Thời gian gắn bó với công ty/ sản phẩm                   |
| `product_density`    | Engineered ratio         | ✅            | Số sản phẩm trung bình theo tháng gắn bó                 |
| `customerid`         | Identifier               | ❌            | Trùng với id                                             |
| `customer_age_group` | Demographic              | ❌            | Trùng `customer_age`, không cần thêm                     |

---

#### customer_age

- Kiểu dữ liệu: INTEGER (năm)
- Mô tả: Tuổi hiện tại của khách hàng tính tới `snapshot_date` (derived từ `date_of_birth` nếu có).
- Ví dụ: 38
- Null Policy: NULLABLE; nếu missing có thể để NULL và thêm flag `age_missing` hoặc băm vào nhóm `unknown`.
- Ý nghĩa nghiệp vụ: Tuổi ảnh hưởng tới hành vi tài chính và propensity churn (ví dụ người trẻ thường có churn cao hơn). Dùng cho segmentation và tương tác feature.
- Gợi ý: Tạo cả `age` (số) và `age_group` (bucket: 18-25,26-35,36-45,46-60,60+).

#### income_level

- Kiểu dữ liệu: NUMERIC (số nguyên/decimal) hoặc CATEGORICAL (Low/Medium/High)
- Mô tả: Thu nhập (monthly/annual) hoặc mức thu nhập đã được nhóm hoá.
- Ví dụ: 15000000 (VND/tháng) hoặc 'Affluent'
- Null Policy: NULLABLE; nếu missing có thể dùng proxy (có thể ước tính từ `tier`, `segment` hoặc `product_count`) và tạo flag `income_missing`.
- Ý nghĩa nghiệp vụ: Income tác động trực tiếp đến khả năng chi trả và propensity mua sản phẩm; high income thường ít churn nhưng có khác biệt theo sản phẩm.
- Gợi ý: Nếu có giá trị thô, tạo `income_bucket`, log-transform (`log_income`), và `income_per_product` nếu cần.

#### employment_status

- Kiểu dữ liệu: STRING / CATEGORICAL
- Mô tả: Trạng thái việc làm của khách hàng (ví dụ: employed, self-employed, unemployed, retired, student).
- Ví dụ: employed
- Null Policy: 'UNKNOWN' nếu missing
- Ý nghĩa nghiệp vụ: Employment status là proxy cho thu nhập ổn định và rủi ro thanh khoản; thất nghiệp/temporary contract có thể làm tăng nguy cơ churn.
- Gợi ý: Chuẩn hoá categories, tạo `is_employed_flag`, và kết hợp với `income_level` để compute `stability_score`.

#### product_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lượng sản phẩm/dịch vụ mà khách hàng đang sở hữu với ngân hàng (ví dụ CASA, loan, card, insurance).
- Ví dụ: 3
- Null Policy: NOT NULL (0 nếu không có sản phẩm)
- Ý nghĩa nghiệp vụ: Product_count cao thường correlate với stickiness; khách hàng đa sản phẩm ít có xu hướng churn.
- Gợi ý: Tạo `product_count_by_type` (counts per product family) và `has_credit_products_flag`.

#### occupation

- Kiểu dữ liệu: STRING / CATEGORICAL
- Mô tả: Nghề nghiệp chính của khách hàng (ví dụ: 'IT', 'Teacher', 'Farmer', 'Business Owner').
- Ví dụ: IT
- Null Policy: 'UNKNOWN'
- Ý nghĩa nghiệp vụ: Occupation có thể correlate với thu nhập, seasonality, và khả năng sử dụng kênh; dùng cho phân tích segmentation và explainability.
- Gợi ý: Chuẩn hoá thành nhóm nghề lớn (white-collar, blue-collar, self-employed, public-sector) để giảm cardinality.

---

#### residence_location

- Kiểu dữ liệu: STRING (city/district) hoặc STRUCT (city, region)
- Mô tả: Nơi cư trú/đăng ký của khách hàng; có thể là city, province hoặc region.
- Ví dụ: HCMC, District 1
- Null Policy: 'UNKNOWN' nếu missing
- Ý nghĩa nghiệp vụ: Location ảnh hưởng tới product availability, fees, và hành vi sử dụng (digital vs branch). Dùng cho targeting campaign và phân tích địa lý churn.
- Gợi ý: Chuẩn hoá thành `city` → `region`; tạo features `is_urban_flag`, `distance_to_nearest_branch` nếu có dữ liệu.

#### channel_preference

- Kiểu dữ liệu: STRING / CATEGORICAL (multi-label possible)
- Mô tả: Kênh giao dịch ưa thích của khách hàng (ví dụ: 'mobile', 'branch', 'ATM', 'web', 'callcenter').
- Ví dụ: mobile
- Null Policy: 'UNKNOWN' nếu missing
- Ý nghĩa nghiệp vụ: Channel preference giúp xác định digital adoption; khách hàng chuyển từ digital → offline hoặc ngược lại có thể là tín hiệu thay đổi engagement.
- Gợi ý: One-hot encode kênh chính, tạo features `is_digital_user` (mobile/web), `channel_switch_count` (số lần chuyển kênh trong window).

---

#### Ghi chú về các cột không dùng làm feature trực tiếp

- `id`, `customerid`: Technical keys — không dùng làm feature.
- `customer_age_group`: Trùng với `age`/`customer_age` — chọn 1 representation để tránh trùng thông tin (age numeric + age_group categorical recommended).

---

#### Derived features (công thức & ý nghĩa)

#### tenure_months = snapshot_month - created_date

- Kiểu dữ liệu: INTEGER (số tháng)
- Mô tả: Thời gian (tháng) kể từ khi tài khoản/quan hệ được tạo tới snapshot.
- Ví dụ: 36
- Null Policy: NULLABLE nếu created_date missing
- Ý nghĩa nghiệp vụ: Tenure biểu thị maturity; tenure lớn thường giảm nguy cơ churn. Dùng làm feature trực tiếp hoặc bucket.
- Gợi ý: Chuẩn hoá `snapshot_month` và `created_date` sang DATE, tính months_between và tạo bins (new/medium/long-tenure).

#### product_density = product_count / tenure

- Kiểu dữ liệu: NUMERIC (float)
- Mô tả: Mật độ sản phẩm theo thời gian — trung bình products acquired per month (tính đến snapshot).
- Ví dụ: 0.08 (tức trung bình 0.08 product/month)
- Null Policy: NULLABLE; nếu tenure = 0 hoặc NULL ⇒ set NULL và tạo flag
- Ý nghĩa nghiệp vụ: Product_density cao cho thấy tốc độ cross-sell; sudden drop trong product_density có thể là dấu hiệu disengagement.
- Gợi ý: guard denominator (if tenure <= 0 → NULL), và create `product_density_bucket`.

---

#### Gợi ý triển khai (pandas / SQL)

- Chuẩn hoá các cột time-based (snapshot_date, created_date) trước khi tính `tenure_months`.
- Khi tạo `product_density`, xử lý edge cases (tenure = 0, product_count null).
- Tạo cả dạng numeric và categorical cho age/income để phục vụ cả model tree-based và linear models.
- Thêm flags cho missingness để mô hình học pattern missingness.

---

### 4.6 Channel Usage – Hành vi sử dụng kênh số

**Vai trò**

- Phát hiện churn sớm thông qua digital behavior

**Key insight**

- Login frequency giảm
- Active days giảm
- Digital drop-off thường xảy ra **trước churn 1–2 tháng**

Channel usage là **early churn detector** rất hiệu quả.

#### Feature Classification – Channel / Digital Activity (Revised)

| Feature Name               | Vai trò                 | Đưa vào Model | Ghi chú / Lý do                                 |
| -------------------------- | ----------------------- | ------------- | ----------------------------------------------- |
| customer_id                | Identifier              | ❌            | Key nối dữ liệu                                 |
| snapshot_month             | Time-based              | ❌            | Mốc thời gian                                   |
| channel_type               | Channel / Behavioral    | ✅            | Mobile / Web / ATM / Branch / Call center       |
| login_count                | Behavioral              | ✅            | Số lần đăng nhập                                |
| transaction_count          | Behavioral              | ✅            | Tần suất giao dịch                              |
| transaction_amount         | Behavioral              | ⚠️            | Optional, tổng giá trị giao dịch                |
| active_flag                | Behavioral              | ⚠️            | Raw activity                                    |
| last_activity_date         | Behavioral              | ✅            | Quan trọng, dùng tạo days_since_last_login      |
| device_type                | Channel / Behavioral    | ⚠️            | iOS / Android / Web                             |
| failed_login_count         | Behavioral              | ⚠️            | Chỉ số trải nghiệm / security                   |
| session_duration           | Behavioral              | ⚠️            | Engagement / thời gian dùng ứng dụng            |
| days_since_last_login      | Engineered / Behavioral | ✅            | Số ngày kể từ lần login cuối                    |
| avg_login_count_3m         | Engineered / Behavioral | ✅            | Trung bình số login 3 tháng gần nhất            |
| login_trend_3m             | Engineered / Behavioral | ✅            | Xu hướng login gần đây                          |
| inactive_30d_flag          | Engineered              | ✅            | Chỉ báo không hoạt động 30 ngày                 |
| channel_active_count       | Engineered / Channel    | ✅            | Số kênh đang dùng                               |
| digital_transaction_ratio  | Engineered / Channel    | ✅            | Tỷ lệ giao dịch digital / tổng                  |
| channel_preference         | Channel / Behavioral    | ❌            | Thói quen kênh, chỉ dùng cho phân tích business |
| inactive_flag (sau N ngày) | Leakage                 | ❌❌          | Tạo sau N ngày → **leakage**, không dùng        |
| churn_flag (nội bộ)        | Leakage                 | ❌❌          | Label nội bộ → **leakage**, không dùng          |

> 👉 **Ghi chú:** Các feature liên quan đến **channel usage** là nguồn feature churn mạnh nhất, tương đương CASA trong dữ liệu tài chính.

---

#### customer_id

- Kiểu dữ liệu: STRING / INTEGER
- Mô tả: Join key tới Customer Master.
- Ví dụ: CUST_000123
- Null Policy: NOT NULL
- Ý nghĩa nghiệp vụ: Dùng để gộp feature across tables; không dùng làm feature.

#### snapshot_month

- Kiểu dữ liệu: STRING / INTEGER (YYYYMM) hoặc DATE (last day of month)
- Mô tả: Tháng quan sát (cut-off) cho các feature time-based.
- Ví dụ: 202411
- Null Policy: NOT NULL

---

#### Raw channel/activity fields

#### channel_type

- Kiểu dữ liệu: STRING / CATEGORICAL
- Mô tả: Kênh tương tác (mobile_app / internet / atm / branch / call_center).
- Ví dụ: mobile_app
- Null Policy: 'UNKNOWN'
- Ý nghĩa nghiệp vụ: Biết kênh giúp đánh giá digital adoption và kênh nguy cơ mất kết nối.

#### login_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lần đăng nhập (app/web) trong chu kỳ (tháng/ngày tuỳ nguồn).
- Ví dụ: 12
- Null Policy: NOT NULL (0 nếu không có activity)
- Ý nghĩa nghiệp vụ: Proxy cho engagement; giảm login_count thường precedes churn.

#### transaction_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số giao dịch qua kênh (transaction events) trong chu kỳ.
- Ví dụ: 8
- Null Policy: NOT NULL (0)
- Ý nghĩa nghiệp vụ: Direct engagement metric; giảm mạnh → early churn signal.

#### transaction_amount

- Kiểu dữ liệu: NUMERIC (DECIMAL)
- Mô tả: Tổng giá trị giao dịch trong chu kỳ (optional, contextual).
- Ví dụ: 4500000.00
- Null Policy: NULLABLE; nếu missing set NULL và tạo flag
- Ý nghĩa nghiệp vụ: Thể hiện intensity/monetary engagement; dùng thận trọng (outliers).

#### active_flag

- Kiểu dữ liệu: BOOLEAN / INTEGER (0/1)
- Mô tả: Cờ account có activity trong chu kỳ (>=1 login or txn).
- Ví dụ: 1
- Null Policy: NOT NULL (default 0)
- Ý nghĩa nghiệp vụ: Dùng cho filter và aggregates; tạo lagged_active_flag để tránh leakage.

#### last_activity_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày hoạt động cuối cùng (login hoặc transaction) tính tới snapshot.
- Ví dụ: 2024-10-21
- Null Policy: NULLABLE; nếu NULL nghĩa là chưa có activity recorded
- Ý nghĩa nghiệp vụ: Rất quan trọng cho tính recency; days_since_last_login derived từ đây là predictor mạnh.

#### device_type

- Kiểu dữ liệu: STRING (iOS / Android / Web)
- Mô tả: Loại thiết bị dùng để truy cập.
- Ví dụ: Android
- Null Policy: 'UNKNOWN'
- Ý nghĩa nghiệp vụ: Device patterns giúp debugging UX/compatibility issues và phân tích retention by device.

#### failed_login_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lần đăng nhập thất bại trong chu kỳ.
- Ví dụ: 3
- Null Policy: NOT NULL (0)
- Ý nghĩa nghiệp vụ: High failed_login_count → friction / UX issues → churn risk.

#### session_duration

- Kiểu dữ liệu: NUMERIC (seconds)
- Mô tả: Tổng hoặc trung bình thời lượng phiên (session) trong chu kỳ.
- Ví dụ: 420 (seconds)
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Thời lượng phiên thấp có thể cho thấy engagement kém.

---

#### Labels / business fields (cẩn trọng với leakage)

| channel_preference           | Label business |
| ---------------------------- | -------------- |
| inactive_flag tạo sau N ngày | Leakage        |
| churn_flag nội bộ            | Leakage        |

Ghi chú: Các cột dạng `inactive_flag`/`churn_flag` chỉ dùng để báo cáo/label-derivation và không được đưa vào feature set nếu chúng được tạo sau snapshot_date.

---

#### 1️⃣ Engagement & Recency (MẠNH NHẤT)

##### days_since_last_login

- Kiểu dữ liệu: INTEGER (days)
- Mô tả: `snapshot_date - last_activity_date` (số ngày kể từ lần hoạt động cuối cùng)
- Ví dụ: 45
- Null Policy: NULLABLE nếu last_activity_date missing
- Ý nghĩa nghiệp vụ: Recency là predictor mạnh cho churn; days tăng → churn risk tăng.

##### days_since_last_transaction

- Kiểu dữ liệu: INTEGER (days)
- Mô tả: `snapshot_date - last_transaction_date`
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Tương tự last_login nhưng đo transaction-specific engagement.

##### inactive_30d_flag

- Kiểu dữ liệu: BINARY (0/1)
- Mô tả: =1 nếu days_since_last_login >= 30
- Null Policy: 0 nếu last_activity_date present and days < 30; NULL nếu last_activity_date missing (tạo flag missing riêng)
- Ý nghĩa nghiệp vụ: Simple threshold-based early-warning.

##### inactive_60d_flag

- Kiểu dữ liệu: BINARY (0/1)
- Mô tả: =1 nếu days_since_last_login >= 60

---

#### 2️⃣ Frequency & Intensity

##### avg_login_count_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Trung bình login_count trong 3 tháng gần nhất
- Null Policy: NULLABLE nếu insufficient history
- Ý nghĩa nghiệp vụ: Giúp capture frequency trend; dùng cho normalization.

##### avg_transaction_count_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Trung bình transaction_count trong 3 tháng gần nhất

##### total_login_count_3m

- Kiểu dữ liệu: INTEGER
- Mô tả: Tổng login_count trong 3 tháng gần nhất

##### total_transaction_count_3m

- Kiểu dữ liệu: INTEGER
- Mô tả: Tổng transaction_count trong 3 tháng gần nhất

---

#### 3️⃣ Trend / Decline (TÍN HIỆU CHURN SỚM)

##### login_trend_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: `login_count_current_month - mean(login_count_previous_2_months)` (positive = increasing)
- Null Policy: NULLABLE
- Ý nghĩa nghiệp vụ: Negative trend → giảm engagement → early churn signal.

##### transaction_trend_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: `transaction_count_current_month - mean(transaction_count_previous_2_months)`

##### login_drop_flag

- Kiểu dữ liệu: BINARY
- Mô tả: =1 nếu login_trend_3m < 0

##### transaction_drop_flag

- Kiểu dữ liệu: BINARY
- Mô tả: =1 nếu transaction_trend_3m < 0

---

#### 4️⃣ Channel Mix / Diversity

##### channel_active_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lượng channel_type mà user có activity (>0) trong snapshot_month
- Ý nghĩa nghiệp vụ: Channel diversification cao → resilient; only-branch users may be higher risk for digital drop-off.

##### digital_channel_active_flag

- Kiểu dữ liệu: BINARY
- Mô tả: =1 nếu mobile_app hoặc internet banking có activity

##### branch_only_flag / atm_only_flag

- Kiểu dữ liệu: BINARY
- Mô tả: Indicators for channel concentration

---

#### 5️⃣ Channel Dependency

##### digital_transaction_ratio

- Kiểu dữ liệu: NUMERIC (0..1)
- Mô tả: `digital_transaction_count / total_transaction_count` (guard denominator)
- Null Policy: NULLABLE if total_transaction_count = 0
- Ý nghĩa nghiệp vụ: High digital ratio → digital-first; changes in digital ratio can indicate channel migration or friction.

##### branch_dependency_ratio / atm_dependency_ratio

- Kiểu dữ liệu: NUMERIC

---

#### 6️⃣ Stability / Volatility

##### login_volatility_3m

- Kiểu dữ liệu: NUMERIC
- Mô tả: Standard deviation of login_count over last 3 months
- Ý nghĩa nghiệp vụ: High volatility may signal unstable behavior (spikes then drop) — use with trend features.

##### transaction_volatility_3m

- Kiểu dữ liệu: NUMERIC

---

#### 7️⃣ Experience / Friction (nếu có)

##### failed_login_ratio

- Kiểu dữ liệu: NUMERIC
- Mô tả: `failed_login_count / total_login_attempts` (guard denominator)
- Ý nghĩa nghiệp vụ: High ratio → UX friction → potential churn trigger.

##### avg_session_duration

- Kiểu dữ liệu: NUMERIC (seconds)
- Mô tả: Tổng session_duration / số session
- Ý nghĩa nghiệp vụ: Short sessions may indicate low engagement or poor UX.

---

#### Implementation notes (pandas / SQL)

- Always compute features using data up-to-and-including `snapshot_date` to avoid leakage.
- Use groupby `customer_id` and time-windowed aggregations (rolling / window functions) for 1m/3m features.
- Guard denominators (if denom <= 0 then set NULL and create flag `*_denom_zero_flag`).
- Create missingness flags for critical fields (e.g., `last_activity_missing_flag`).
- Normalize counts by customer-specific baselines if needed (e.g., divide by avg_activity_population).

### 4.7 Customer Interaction – Trải nghiệm & khiếu nại

**Vai trò**

- Đánh giá churn do trải nghiệm xấu

**Key insight**

- Khách hàng có complaint churn **cao gấp 2–3 lần**
- Complaint chưa được giải quyết → churn gần như chắc chắn

Bảng này hỗ trợ **early warning và root cause analysis**.

#### Feature Classification – Customer Interaction / Support (Revised)

| Feature Name                    | Vai trò / Nhóm           | Đưa vào Model | Nhận xét / Lý do                                   |
| ------------------------------- | ------------------------ | ------------- | -------------------------------------------------- |
| customer_id                     | Identifier               | ❌            | Key nối dữ liệu                                    |
| interaction_id                  | Identifier / Technical   | ❌            | Key kỹ thuật                                       |
| interaction_date                | Time-based               | ❌            | Mốc thời gian                                      |
| interaction_channel             | Channel / Behavioral     | ✅            | call / email / chat / branch                       |
| interaction_type                | Behavioral               | ✅            | complaint / inquiry / request                      |
| interaction_reason              | Behavioral               | ✅            | phí / lỗi app / giao dịch                          |
| interaction_status              | Behavioral / Leakage     | ⚠️            | Chỉ dùng lagged / summary, tránh leakage           |
| resolution_code                 | Behavioral / Leakage     | ⚠️            | Chỉ dùng historical / lagged, không dùng trực tiếp |
| priority_level                  | Behavioral / Lagged      | ⚠️            | Low / medium / high; dùng historical / summary     |
| assigned_team                   | Operational / Behavioral | ⚠️            | Ops / Tech / CS; optional                          |
| interaction_text                | NLP / Text               | ⚠️            | Dùng NLP trích xuất sentiment, keyword             |
| interaction_count_1m            | Engineered / Recency     | ✅            | Số lần tương tác 1 tháng gần nhất                  |
| interaction_count_3m            | Engineered / Recency     | ✅            | Số lần tương tác 3 tháng gần nhất                  |
| complaint_count_3m              | Engineered / Behavioral  | ✅            | Số khiếu nại 3 tháng                               |
| days_since_last_interaction     | Engineered / Recency     | ✅            | Khoảng thời gian kể từ lần tương tác cuối          |
| unresolved_ticket_count         | Behavioral / Experience  | ✅            | Số ticket chưa giải quyết                          |
| high_priority_interaction_ratio | Behavioral / Experience  | ✅            | Tỷ lệ tương tác ưu tiên cao                        |
| repeat_complaint_flag           | Behavioral / Experience  | ✅            | Cờ khiếu nại lặp lại                               |
| avg_resolution_time             | Behavioral / Experience  | ✅            | Thời gian xử lý trung bình                         |
| negative_interaction_ratio      | Behavioral / NLP         | ⚠️            | Tỷ lệ tương tác tiêu cực                           |
| complaint_sentiment_score       | Behavioral / NLP         | ⚠️            | Điểm sentiment từ nội dung khiếu nại               |
| escalation_flag                 | Behavioral / NLP         | ⚠️            | Cờ tăng cấp khiếu nại                              |
| call_center_ratio               | Channel / Behavioral     | ✅            | Tỷ lệ tương tác qua call center                    |
| digital_support_ratio           | Channel / Behavioral     | ✅            | Tỷ lệ tương tác qua kênh digital                   |

---

#### customer_id

- Kiểu dữ liệu: STRING / UUID
- Mô tả: Khóa nối đến bảng khách hàng; định danh duy nhất cho mỗi customer.
- Ví dụ: `CUST_00012345`
- Null Policy: NOT NULL; nếu missing, loại bản ghi khỏi pipeline match hoặc map sang `unknown_customer` nhưng không dùng cho huấn luyện.
- Ý nghĩa nghiệp vụ: Join key chính để liên kết interaction với các bảng giao dịch, tài khoản.

#### interaction_id

- Kiểu dữ liệu: STRING / UUID
- Mô tả: Định danh duy nhất cho mỗi interaction (ticket / session / case).
- Ví dụ: `INT_20241231_0001`
- Null Policy: NOT NULL; cần cho de-dup và tracking lifecycle.
- Ý nghĩa nghiệp vụ: Dùng để đo thời gian xử lý, trạng thái, và liên kết thao tác support.

#### interaction_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Thời điểm interaction xảy ra (thời gian bắt đầu interaction hoặc timestamp ghi nhận).
- Ví dụ: `2025-12-01 14:37:22`
- Null Policy: NULLABLE; nếu missing, loại bản ghi khỏi các feature time-series.
- Ý nghĩa nghiệp vụ: Cột thời gian chuẩn để làm rolling windows, recency, và tính snapshot-aware features. Tất cả feature thời gian phải sử dụng `interaction_date <= snapshot_date` để tránh leakage.

#### interaction_channel

- Kiểu dữ liệu: CATEGORICAL (call/email/chat/branch/other)
- Mô tả: Kênh mà khách hàng tương tác.
- Ví dụ: `call`, `chat`, `email`, `branch`
- Null Policy: NULLABLE; map missing thành `unknown`.
- Ý nghĩa nghiệp vụ: Phân tích hành vi kênh, đo digital adoption vs call center usage.

#### interaction_type

- Kiểu dữ liệu: CATEGORICAL (complaint/inquiry/request/feedback)
- Mô tả: Loại interaction theo mục đích nghiệp vụ.
- Ví dụ: `complaint`, `inquiry`
- Null Policy: NULLABLE; nếu missing, map `other`.
- Ý nghĩa nghiệp vụ: Tách complaint vs informational interactions.

#### interaction_reason

- Kiểu dữ liệu: CATEGORICAL / FREE TEXT (nếu có taxonomy)
- Mô tả: Lý do interaction (ví dụ: phí / lỗi app / giao dịch thất bại / sao kê)
- Ví dụ: `app_error`, `fee_query`, `transaction_failure`
- Null Policy: NULLABLE; map thành `unknown_reason` nếu missing.
- Ý nghĩa nghiệp vụ: Dùng để cluster loại vấn đề phổ biến và tính các feature per-reason.

#### interaction_status

- Kiểu dữ liệu: CATEGORICAL (open/closed/awaiting_customer)
- Mô tả: Trạng thái hiện tại của ticket tại thời điểm ghi nhận row.
- Ví dụ: `open` / `closed`
- Null Policy: NULLABLE; map `unknown`.
- Ý nghĩa nghiệp vụ: Có thể dùng để đo unresolved ticket nhưng cần chú ý LEAKAGE (nếu status là trạng thái _current_ sau snapshot_date thì gây leakage).
- Leakage note: `interaction_status` mang tính leakage nếu bạn sử dụng giá trị hiện tại mà không ràng buộc về thời điểm snapshot. Luôn chỉ dùng trạng thái như được ghi tại hoặc trước `snapshot_date`, hoặc use lagged/archived snapshots.

#### resolution_code

- Kiểu dữ liệu: CATEGORICAL (resolved/unresolved/escalated/...)
- Mô tả: Kết quả xử lý ticket.
- Ví dụ: `resolved`, `unresolved`
- Null Policy: NULLABLE; nếu missing, treat as `unknown`.
- Ý nghĩa nghiệp vụ: Dùng để tính unresolved counts, avg resolution time.
- Leakage note: `resolution_code` lấy từ hiện trạng (current month) có thể dẫn tới leakage; chỉ dùng nếu value timestamped and <= snapshot_date.

#### priority_level

- Kiểu dữ liệu: CATEGORICAL (low/medium/high)
- Mô tả: Mức độ ưu tiên của ticket.
- Ví dụ: `high`
- Null Policy: NULLABLE; map `medium` hoặc `unknown` tùy chính sách.
- Ý nghĩa nghiệp vụ: Dùng để tính tỷ lệ high-priority interactions.
- Time-aware note: nếu chỉ có bản ghi `priority` hiện tại, hãy sử dụng lagged value (priority tại thời điểm interaction hoặc last-known-priority trước snapshot_date).

#### assigned_team

- Kiểu dữ liệu: CATEGORICAL (ops/tech/CS/other)
- Mô tả: Team được gán để xử lý.
- Ví dụ: `CS`
- Null Policy: NULLABLE; map `unassigned`.
- Ý nghĩa nghiệp vụ: Dùng để phân tích load distribution và SLA theo team.

#### interaction_text

- Kiểu dữ liệu: TEXT (free text)
- Mô tả: Nội dung văn bản khách hàng gửi (chat, email, notes). Dùng cho NLP / sentiment / topic modeling.
- Ví dụ: `"Tôi bị trừ phí không rõ lý do"`
- Null Policy: NULLABLE; nếu missing, skip NLP-derived features.
- Ý nghĩa nghiệp vụ: Nguồn chính cho sentiment, intent, và escalation signals.
- NLP notes:
  - Tiền xử lý: normalize unicode, lowercasing, remove PII (phone/email), mask account numbers, tokenize, remove stopwords nếu cần.
  - Vectorization: TF-IDF, embeddings (sentence-transformers), hoặc topic models.
  - Privacy: interaction_text có thể chứa PII; áp dụng masking/anonymization trước khi lưu tính toán.
  - Sampling: để huấn luyện mô hình sentiment, cân nhắc sample stratified theo `interaction_type` và `channel`.
  - Time-awareness: chỉ train/compute features using text from records with `interaction_date <= snapshot_date`.

---

#### Ghi chú leakage & time-awareness

- Tuyệt đối không dùng bất kỳ trường nào thể hiện trạng thái "hiện tại" sau `snapshot_date` (vd. `interaction_status` evaluated after snapshot) trừ khi bạn have time-stamped history or use lagged snapshots.
- Khi có trường chỉ tồn tại ở trạng thái hiện tại (ví dụ `resolution_code` only recorded after resolution), hãy build lagged versions hoặc only use events with `interaction_date <= snapshot_date`.
- Đối với `priority_level`, nếu datasource chỉ cung cấp current-priority, tìm cách lấy priority recorded at interaction time hoặc compute last_known_priority as-of snapshot.

---

#### Engineered features (mẫu) — Định nghĩa, kiểu, windows, chú ý tính time-aware

Tất cả engineered features phải được tính bằng cách filter các hàng có `interaction_date <= snapshot_date`. `snapshot_date` là mốc thời gian tại đó bạn tính feature vector cho mỗi customer.

##### Frequency / Recency (quan trọng nhất)

###### interaction_count_1m

- Kiểu dữ liệu: INTEGER
- Mô tả: Số lượng interaction của customer trong 30 ngày trước `snapshot_date` (xem chính xác window policy: 30 days inclusive/exclusive).
- Công thức: count(interaction_id) where interaction_date > snapshot_date - 30d and interaction_date <= snapshot_date
- Ví dụ: 5
- Notes: Exclude system-generated interactions if flagged. Guard: nếu interaction_id duplicated, dedupe by interaction_id.

###### interaction_count_3m

- Kiểu dữ liệu: INTEGER
- Mô tả: Số interaction trong 90 ngày trước `snapshot_date`.
- Công thức: count(...) with 90d window
- Notes: Useful for medium-term activity trend.

###### complaint_count_3m

- Kiểu dữ liệu: INTEGER
- Mô tả: Số `interaction_type == complaint` trong 90 ngày.
- Công thức: count(...) filtered by type

###### days_since_last_interaction

- Kiểu dữ liệu: INTEGER
- Mô tả: Số ngày kể từ interaction_date lớn nhất (<= snapshot_date) tới snapshot_date.
- Công thức: datediff(snapshot_date, max(interaction_date where interaction_date <= snapshot_date))
- Null Policy: nếu không có interaction trước snapshot_date, set a large sentinel (e.g., 9999) hoặc NULL — document choice.

##### Chất lượng trải nghiệm (rất mạnh)

###### unresolved_ticket_count

- Kiểu dữ liệu: INTEGER
- Mô tả: Số ticket chưa được resolved tính tới `snapshot_date`.
- Công thức: count(interaction_id where resolution_code != 'resolved' AND interaction_date <= snapshot_date)
- Leakage / Time note: resolution_code must be as-of snapshot_date; nếu chỉ có resolution recorded later, this will leak.

###### high_priority_interaction_ratio

- Kiểu dữ liệu: FLOAT (0-1)
- Mô tả: Tỷ lệ interactions có priority == high trong window (ví dụ 90d).
- Công thức: high_count / total_count (add smoothing e.g., +1 denominator guard)
- Notes: Guard denominator when total_count small.

###### repeat_complaint_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 nếu customer có >1 complaint về cùng `interaction_reason` trong 90d, else 0.
- Công thức: exists reason where count(complaints with same reason) > 1

###### avg_resolution_time

- Kiểu dữ liệu: FLOAT (days)
- Mô tả: Trung bình thời gian (days) từ `interaction_date` tới `resolved_date` cho các ticket resolved trước hoặc tại `snapshot_date`.
- Công thức: mean(resolved_date - interaction_date) for resolved tickets with resolved_date <= snapshot_date
- Null Policy: nếu không có resolved tickets, set NULL or large sentinel; document choice.

##### Sentiment / Nội dung (nâng cao)

###### negative_interaction_ratio

- Kiểu dữ liệu: FLOAT
- Mô tả: Tỷ lệ interactions có sentiment negative trong window.
- Công thức: negative_count / total_count (use NLP sentiment score threshold)
- NLP note: define negative threshold clearly (e.g., polarity < -0.2 or model score).

###### complaint_sentiment_score

- Kiểu dữ liệu: FLOAT
- Mô tả: Trung bình sentiment score cho interactions có type == complaint.
- Công thức: mean(sentiment_score for complaints)
- Notes: sentiment model must be consistent across dataset.

###### escalation_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 nếu interaction_text or resolution_code shows escalation (keyword-based or model-predicted) within window.
- Construction: via keyword matching (`escalate`, `supervisor`) or classifier on text.

##### Channel behavior

###### call_center_ratio

- Kiểu dữ liệu: FLOAT
- Mô tả: Tỷ lệ interactions qua `call` trên tổng interactions trong window.
- Công thức: count(channel == 'call') / total_count

###### digital_support_ratio

- Kiểu dữ liệu: FLOAT
- Mô tả: Tỷ lệ interactions qua digital channels (chat + email + in-app) trong window.
- Công thức: digital_count / total_count

#### Implementation notes & edge cases

#### Best Practices – Customer Interaction / Support Features

1. **Loại bỏ trùng lặp (De-duplication)**

   - Data source có thể gửi các event trùng.
   - Dedupe theo `interaction_id`; nếu không có, dedupe theo `(customer_id, interaction_date, channel, type, truncated_text_hash)`.

2. **Bảo vệ mẫu số khi tính ratios (Guard denominators)**

   - Khi tính tỷ lệ, thêm smoothing (Laplace +1) hoặc đặt giá trị mặc định nếu `total_count` quá nhỏ.

3. **Khách hàng ít tương tác (Long-tail customers)**

   - Với khách hàng không có tương tác, đặt counts = 0 và recency = sentinel lớn hoặc NULL.
   - Giữ nhất quán trong toàn pipeline.

4. **Múi giờ (Time zones)**

   - Chuẩn hóa `interaction_date` sang UTC (hoặc cùng một timezone cố định) trước khi tính các window tính toán.

5. **Dữ liệu đến trễ (Backfills and late-arriving events)**

   - Nếu pipeline nhận các event trễ, đảm bảo tính feature từ snapshot đã finalized hoặc xử lý explicit event lateness bằng watermarking.

6. **Bảo mật (Privacy)**

   - Mask/remove PII từ `interaction_text` trước khi lưu hoặc dùng NLP.
   - Xem xét access control khác biệt cho raw text.

7. **Lấy mẫu / cân bằng nhãn (Sampling / label balance)**
   - Khi huấn luyện model downstream, stratify theo complaint vs non-complaint và theo channel để tránh bias.

---

### 4.8 Campaign Response – Chiến dịch & retention

**Vai trò**

- Đánh giá khách hàng có bị bỏ rơi hay không
- Phục vụ chiến lược giữ chân

**Key insight**

- Ignore campaign liên tục → disengaged
- Không có touchpoint → churn do bị bỏ rơi
- Marketing fatigue làm tăng churn

Campaign response không phải core predictor nhưng rất quan trọng cho **retention strategy**.

#### Feature Classification – Campaign / Marketing Exposure (Unified)

| Feature Name                | Category / Role         | Used in Model | Notes / Lý do / Ghi chú                        |
| --------------------------- | ----------------------- | ------------- | ---------------------------------------------- |
| customer_id                 | Identifier              | ❌            | Key nối dữ liệu                                |
| campaign_id                 | Identifier / Technical  | ❌            | Key kỹ thuật                                   |
| campaign_type               | Campaign / Behavioral   | ✅            | retention / upsell / cross-sell                |
| campaign_channel            | Channel / Behavioral    | ✅            | sms / email / call / app                       |
| campaign_start_date         | Time-based              | ✅            | Ngày bắt đầu chiến dịch                        |
| campaign_end_date           | Time-based / Optional   | ⚠️            | Optional, dùng cho window nếu cần              |
| campaign_sent_date          | Exposure / Time-based   | ✅            | Ngày gửi campaign                              |
| campaign_response_flag      | Behavioral / Label      | ⚠️            | Dùng làm label nếu time-bounded, tránh leakage |
| response_date               | Time-based              | ⚠️            | Chỉ dùng để tạo engineered features            |
| response_type               | Behavioral              | ⚠️            | click / enroll / ignore                        |
| offer_type                  | Offer / Behavioral      | ⚠️            | fee waiver / cashback                          |
| campaign_received_count_3m  | Engineered / Exposure   | ✅            | Số campaign nhận trong 3 tháng                 |
| days_since_last_campaign    | Engineered / Recency    | ✅            | Số ngày kể từ campaign gần nhất                |
| campaign_channel_diversity  | Engineered / Channel    | ✅            | Số kênh khác nhau nhận campaign                |
| campaign_response_rate_6m   | Behavioral / Engineered | ✅            | Tỷ lệ phản hồi trong 6 tháng                   |
| ignore_campaign_ratio       | Behavioral / Engineered | ✅            | Tỷ lệ campaign bỏ qua                          |
| last_campaign_ignored_flag  | Behavioral / Engineered | ✅            | Cờ campaign gần nhất bị bỏ qua                 |
| responded_to_retention_flag | Behavioral / Retention  | ✅            | Phản hồi chiến dịch retention                  |
| retention_offer_accept_rate | Behavioral / Retention  | ✅            | Tỷ lệ chấp nhận ưu đãi retention               |
| churn_after_retention_flag  | Behavioral / Analysis   | ⚠️            | Chỉ phân tích, không train                     |
| campaign_frequency_1m       | Behavioral / Exposure   | ✅            | Số campaign trong 1 tháng                      |
| over_contact_flag           | Behavioral / Exposure   | ✅            | Cờ gửi quá nhiều campaign                      |

---

#### customer_id

- Kiểu dữ liệu: STRING / UUID
- Mô tả: Khóa nối tới bảng khách hàng.
- Ví dụ: `CUST_00012345`
- Null Policy: NOT NULL; nếu missing, loại bản ghi khỏi pipeline match hoặc map sang `unknown_customer` (không dùng cho huấn luyện).
- Ý nghĩa nghiệp vụ: Join key để liên kết exposures, responses với các bảng khác.

#### campaign_id

- Kiểu dữ liệu: STRING / UUID
- Mô tả: Định danh chiến dịch (technical id).
- Ví dụ: `CMP_202501_PROMO01`
- Null Policy: NOT NULL; cần để dedupe và nhóm theo chiến dịch.
- Ý nghĩa nghiệp vụ: Dùng để phân tích performance theo campaign.

#### campaign_type

- Kiểu dữ liệu: CATEGORICAL (retention / upsell / cross-sell / acquisition / other)
- Mô tả: Mục tiêu chiến dịch.
- Ví dụ: `retention`
- Null Policy: NULLABLE; map `unknown` nếu missing.
- Ý nghĩa nghiệp vụ: Dùng để tách hiệu quả theo mục tiêu.
- Caution: `campaign_type` evaluated as-of current time may cause reverse causality (ví dụ: marking as `retention` because customer recently had churn symptoms). Prefer using classification assigned before `campaign_sent_date`.

#### campaign_channel

- Kiểu dữ liệu: CATEGORICAL (sms / email / call / app / push / other)
- Mô tả: Kênh gửi campaign.
- Ví dụ: `sms`
- Null Policy: NULLABLE; map `unknown`.
- Ý nghĩa nghiệp vụ: Phân tích hiệu suất per channel.

#### campaign_start_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày bắt đầu chiến dịch (campaign-level start).
- Ví dụ: `2025-11-01`
- Null Policy: NULLABLE; nếu missing, fallback sang `campaign_sent_date`.

#### campaign_end_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày kết thúc chiến dịch (nếu có).
- Null Policy: NULLABLE; optional.

#### campaign_sent_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày khách hàng được gửi exposure (timestamp exposure / touch).
- Ví dụ: `2025-12-15 09:10:00`
- Null Policy: NOT NULL; nếu missing, record không được tính là exposure.
- Ý nghĩa nghiệp vụ: Đây là mốc để xác định exposure as-of snapshot_date; mọi feature exposure phải sử dụng `campaign_sent_date <= snapshot_date`.

#### campaign_response_flag

- Kiểu dữ liệu: BOOLEAN / BINARY (1/0)
- Mô tả: Khách hàng có phản hồi (click/enroll/accept/opt-in) cho chiến dịch này hay không.
- Null Policy: NOT NULL (treat missing as 0 nếu hệ thống đảm bảo logging của exposures)
- Ý nghĩa nghiệp vụ: Target/label candidate or response signal.
- Leakage note: `campaign_response_flag` taken from current month or after snapshot_date is a source of leakage; only use responses with `response_date <= snapshot_date` when building features or labels.

#### response_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Thời điểm khách hàng thực hiện hành động trả lời (click/enroll).
- Null Policy: NULLABLE; nếu NULL => no response.
- Leakage note: `response_date` after snapshot_date leaks. Always ensure `response_date <= snapshot_date` when using as feature.

#### response_type

- Kiểu dữ liệu: CATEGORICAL (click / enroll / ignore / other)
- Mô tả: Loại phản hồi.
- Null Policy: NULLABLE; map `no_response` cho missing.
- Ý nghĩa nghiệp vụ: Dùng để phân loại chất lượng phản hồi.

#### offer_type

- Kiểu dữ liệu: CATEGORICAL (fee_waiver / cashback / discount / voucher / other)
- Mô tả: Loại ưu đãi được gửi.
- Null Policy: NULLABLE; map `standard` or `unknown`.
- Ý nghĩa nghiệp vụ: Hiệu quả tùy vào offer; useful for uplift analysis.

#### created_date

- Kiểu dữ liệu: DATE / TIMESTAMP
- Mô tả: Ngày ghi nhận record (audit).
- Null Policy: NOT NULL
- Ý nghĩa nghiệp vụ: Dùng cho auditing và debugging; không dùng để tính exposure windows.

---

#### Leakage & time-aware cautions

- `campaign_response_flag` and `response_date` are leakage risks if you use their current-month values without time bounding. Always restrict to responses with `response_date <= snapshot_date`.
- `campaign_type = retention` marked after observation of behavior can introduce reverse causality. Prefer campaign metadata assigned before sending.
- If only "current" response aggregations are available (e.g., monthly summary), prefer raw event-level logs with `campaign_sent_date`/`response_date` timestamped.

---

#### Engineered features (mẫu) — Định nghĩa, kiểu, windows, time-aware

All engineered features must be computed using exposures/responses with `campaign_sent_date <= snapshot_date` and responses with `response_date <= snapshot_date`.

##### Exposure / Attention

###### campaign_received_count_3m

- Kiểu dữ liệu: INTEGER
- Mô tả: Số campaign exposures customer nhận trong 90 ngày trước `snapshot_date`.
- Công thức: count(campaign_id) where campaign_sent_date > snapshot_date - 90d AND campaign_sent_date <= snapshot_date
- Ví dụ: 4

###### days_since_last_campaign

- Kiểu dữ liệu: INTEGER
- Mô tả: Số ngày kể từ lần nhận campaign gần nhất tới `snapshot_date`.
- Công thức: datediff(snapshot_date, max(campaign_sent_date where campaign_sent_date <= snapshot_date))
- Null Policy: set sentinel or NULL if never exposed.

###### campaign_channel_diversity

- Kiểu dữ liệu: INTEGER or FLOAT
- Mô tả: Số lượng kênh khác nhau đã nhận campaign trong window (e.g., distinct channels in 90d).

##### Responsiveness (rất mạnh)

###### campaign_response_rate_6m

- Kiểu dữ liệu: FLOAT (0-1)
- Mô tả: Tỷ lệ campaign exposures có response trong 180 ngày.
- Công thức: sum(response_flag where campaign_sent_date in 180d window) / count(exposures in same window)
- Notes: Guard denominator (smoothing + laplace) and ensure response_date <= snapshot_date.

###### ignore_campaign_ratio

- Kiểu dữ liệu: FLOAT
- Mô tả: Tỷ lệ exposures without any response (or explicit ignore) in window.

###### last_campaign_ignored_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 nếu last received campaign (<= snapshot_date) was ignored.

##### Retention effectiveness

###### responded_to_retention_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 nếu customer responded to a campaign whose `campaign_type == 'retention'` in window.
- Leakage note: don't use retention responses after snapshot to label training target.

###### retention_offer_accept_rate

- Kiểu dữ liệu: FLOAT
- Mô tả: acceptance rate for retention-type offers in a longer window (e.g., 6-12 months).

###### churn_after_retention_flag

- Kiểu dữ liệu: BINARY
- Mô tả: (For analysis only) whether customer churned after receiving retention offer. Marked ⚠️: use for analysis, not training unless carefully time-bounded and causality considered.

##### Fatigue / Over-contact

###### campaign_frequency_1m

- Kiểu dữ liệu: INTEGER
- Mô tả: Số exposures trong 30 ngày.

###### over_contact_flag

- Kiểu dữ liệu: BINARY
- Mô tả: 1 nếu campaign_frequency_1m > threshold (e.g., 3) OR campaign_received_count_3m > another threshold.
- Ý nghĩa: dấu hiệu contact fatigue, có thể correlate với opt-out or negative sentiment.

#### Ghi chú triển khai & các trường hợp đặc biệt

1. **Event-level vs summary-level**

   - Ưu tiên dùng dữ liệu **từng event** với timestamp cho exposures/responses.
   - Các tổng hợp theo tháng (summary-level) thường gây **leakage** và mất độ chính xác về thời gian.

2. **Loại bỏ trùng lặp (De-dup)**

   - Dedupe theo `(customer_id, campaign_id, campaign_sent_date)` hoặc theo `exposure_id` nếu có.

3. **Nhiều lần gửi cùng campaign (Multiple exposures per campaign)**

   - Nếu cùng campaign gửi nhiều lần, xử lý mỗi exposure riêng biệt.
   - Hoặc dedupe theo `(campaign + customer + day)` tùy business rule.

4. **Bảo vệ mẫu số khi tính tỷ lệ (Guard denominators)**

   - Thêm smoothing (ví dụ +1) khi tính các tỷ lệ.

5. **Missing response_date**

   - Xử lý như **không phản hồi** trừ khi downstream system báo khác.

6. **Attribution window**

   - Xác định khoảng thời gian sau `campaign_sent_date` mà phản hồi được tính là thuộc exposure đó (ví dụ: 7 ngày, 14 ngày).
   - Giữ nhất quán attribution window giữa các feature và label.

7. **Múi giờ (Time zones)**

   - Chuẩn hóa timestamp sang cùng một múi giờ trước khi tính window.

8. **Dữ liệu phản hồi đến trễ (Late-arriving responses)**
   - Nếu pipeline nhận các event trễ, tính feature từ snapshot đã finalized hoặc xử lý lateness bằng watermarking.

---

## 5. Kết luận nghiệp vụ

Customer churn trong ngân hàng **không xảy ra đột ngột**, mà là một chuỗi tín hiệu suy giảm:

> Digital usage ↓ → Transaction ↓ → Balance ↓ → Complaint ↑ → Churn

Bộ dữ liệu gồm 7 bảng trên:

- Đủ để xây dựng mô hình churn ML hiệu suất cao
- Phù hợp cho cả **prediction – explanation – action**
- Hỗ trợ thiết kế chiến lược retention chủ động và hiệu quả
