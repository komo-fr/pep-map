# Scripts

## fetch_peps.py

GitHubからPEPリポジトリをダウンロードし、メタデータと引用関係を抽出してCSVファイルとして出力する。

### 基本的な使い方

```bash
python -m scripts.fetch_peps
```

### 出力ファイル

- `data/processed/peps_metadata.csv` - PEPの基本情報（番号、タイトル、ステータス、著者など）
- `data/processed/citations.csv` - PEP間の引用関係（source, target, count）
- `data/processed/metadata.json` - 取得時のメタ情報（取得日時）

### オプション

```bash
# 出力先ディレクトリを指定
python -m scripts.fetch_peps --output-dir custom/output

# 一時ファイルを保持（デフォルトは削除）
python -m scripts.fetch_peps --keep-raw

# 詳細ログを表示
python -m scripts.fetch_peps --verbose
```

### ヘルプ

```bash
python -m scripts.fetch_peps --help
```
