# P0 MVP 詳細仕様書 (v0.9)

> **目的**  
> 3 か月でリリースする LINE ミニアプリ + Apple/Google Wallet パス発行サービスの **コード生成を直接 LLM に依頼できる** 粒度まで記述したエンジニアリング仕様書。

---
## 0. 用語
| 用語 | 意味 |
|------|------|
| **LIFF** | LINE Front‑end Framework。LINE ミニアプリを React で実装する SDK。 |
| **Pass** | Apple Wallet の `.pkpass` または Google Wallet Object。 |
| **Issuer API** | Pass 生成・署名・更新を行うバックエンドサブシステム。 |
| **Org** | 店舗・主催者アカウント。 |

---
## 1. システム概要
```
┌────────────┐      HTTPS     ┌─────────────┐
│ LINE MiniApp │ ◀──────────▶ │  API Gateway │
└────────────┘                 │    (FastAPI)│
     ▲  id_token  ▼            ├─────────────┤
┌────────────┐                │  IssuerSvc  │───▶ S3 (.pkpass)
│  LINE Login │                │  AuthSvc    │───▶ PostgreSQL
└────────────┘                └─────────────┘
```
- **Frontend**: React 18 + TypeScript + LIFF v2
- **Backend**: FastAPI 0.110, Python 3.11
- **DB**: PostgreSQL 15 (RDS)
- **Storage**: S3 互換 (MinIO / AWS S3)

---
## 2. ユーザーストーリー & 受入れ基準 (抜粋)
| ID | As a | I want | So that | Acceptance Criteria |
|----|------|--------|---------|---------------------|
| US‑01 | 店舗担当者 | Canva 風 UI でパス画像とテキストを編集 | コーディング無しで会員証を作れる | UI で入力した値が即時プレビューに反映 / 保存ボタンで backend `POST /designs` が 201 を返す |
| US‑02 | 店舗担当者 | QR を印刷して配布 | 客がスマホで読み取れる | 発行後に DeepLink(URL) と QR PNG が返る |
| US‑03 | エンドユーザ | リンクをタップして 30 秒以内に Wallet に追加 | 面倒なく特典を受け取れる | パスが Wallet アプリに表示 / 失敗した場合エラーメッセージ |

---
## 3. フロントエンド詳細
### 3‑1. ディレクトリ構成
```
frontend/
  src/
    components/
      DesignerCanvas.tsx
      AddToWalletButton.tsx
    pages/
      Home.tsx         // LIFF 起点
      AdminDashboard.tsx
    hooks/
      useApi.ts
    liff.ts           // LIFF 初期化
```
### 3‑2. 主要コンポーネント API
```tsx
// AddToWalletButton props
interface Props {
  designId: string;   // 発行対象デザイン ID
}
```

---
## 4. バックエンド詳細
### 4‑1. エンドポイント一覧
| Method | Path | 認証 | 説明 |
|--------|------|------|------|
| POST | `/auth/line` | 無し | id_token を検証 → JWT 発行 |
| POST | `/designs` | Org JWT | JSON/PDF+画像アップロードでテンプレ保存 |
| POST | `/passes` | User JWT | Pass 発行。body 例は §4‑2 |
| GET  | `/passes/{id}` | User JWT | DeepLink と QR 返却 |
| POST | `/passes/{id}/update` | Org JWT | 外観やフィールドの差し替え |
| GET  | `/stats/org/{org_id}` | Org JWT | 発行・使用統計 (24h キャッシュ) |

### 4‑2. `/passes` リクエスト/レスポンス
```jsonc
// Request body (application/json)
{
  "design_id": "uuid",
  "metadata": {              // 任意
    "tier": "silver",
    "coupon": "WELCOME10"
  }
}

// Success 201
{
  "pass_id": "uuid",
  "platforms": {
    "apple": {
      "deep_link": "https://.../card.pkpass",
      "serial": "ABC123XYZ"
    },
    "google": {
      "deep_link": "https://pay.google.com/gp/v/save/..."
    }
  },
  "qr_png": "data:image/png;base64,...",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### 4‑3. エラー形式
```jsonc
{
  "error": {
    "code": "PASS_LIMIT_REACHED",
    "message": "Free quota exceeded (500 / month)"
  }
}
```

---
## 5. データベース DDL
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE orgs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  line_user_id VARCHAR(64) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE designs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID REFERENCES orgs(id) ON DELETE CASCADE,
  template_json JSONB NOT NULL,
  preview_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE passes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  design_id UUID REFERENCES designs(id) ON DELETE SET NULL,
  platform VARCHAR(10) CHECK (platform IN ('apple','google')),
  serial VARCHAR(32) UNIQUE NOT NULL,
  deep_link TEXT NOT NULL,
  expires_at TIMESTAMPTZ,
  issued_at TIMESTAMPTZ DEFAULT now(),
  last_updated TIMESTAMPTZ DEFAULT now()
);
```

---
## 6. 環境変数 (Backend)
| VAR | 内容 |
|-----|------|
| `LINE_CHANNEL_SECRET` | LIFF 署名検証用 |
| `JWT_SECRET` | HS256 用シークレットキー |
| `APPLE_PASS_CERT_P12` | base64 エンコードした p12 ファイル |
| `APPLE_PASS_CERT_PASSWORD` | p12 パスワード |
| `GOOGLE_WALLET_CREDENTIALS` | JSON 認証情報 |
| `S3_ENDPOINT` | MinIO/S3 エンドポイント URL |

---
## 7. OpenAPI (YAML 抜粋)
```yaml
paths:
  /passes:
    post:
      summary: Create pass
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreatePassReq'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreatePassRes'
components:
  schemas:
    CreatePassReq:
      type: object
      properties:
        design_id: { type: string, format: uuid }
        metadata: { type: object }
      required: [design_id]
    CreatePassRes:
      type: object
      properties:
        pass_id: { type: string, format: uuid }
        platforms:
          type: object
          properties:
            apple:
              type: object
              properties:
                deep_link: { type: string }
                serial: { type: string }
            google:
              type: object
              properties:
                deep_link: { type: string }
        qr_png: { type: string }
        expires_at: { type: string, format: date-time }
```

---
## 8. テスト計画
### 8‑1. ユニットテスト
- FastAPI endpoints → Pytest + HTTPX
- Pass Signer → 与えられた JSON から再生成した `.pkpass` が `pass.json` と一致すること。

### 8‑2. E2Eテスト
- Playwright で LIFF → Pass 発行 → Wallet 追加画面まで自動化。
- GitHub Actions Matrix: iOS 17 Safari / Android 14 Chrome。

---
## 9. CI/CD フロー
1. Push → GitHub Actions で `pytest` & `docker build`。
2. main ブランチ merge で ECR push → AWS Fargate Blue/Green デプロイ。
3. CloudFormation で DB マイグレーションを自動適用。

---
## 10. 今後拡張 (P1 以降のフック)
- `passes` テーブルに `token_id` (NFT) 列追加。
- EventBridge/SQS で発行イベントを外部連携 (Zapier, Shopify)。

---
### 付記: LLM への指示例
```txt
あなたはバックエンドエンジニアです。以下 OpenAPI と DDL に従い、FastAPI 実装を作成してください。
- JWT 認証は HS256。ライブラリは pyjwt。
- DB は asyncpg + SQLAlchemy 2.0。
- S3 には aioboto3 でアップロード。
- Apple PassKit 署名は passpy を使い、証明書は環境変数から読み込む。
```

> **以上**


