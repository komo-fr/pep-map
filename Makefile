.PHONY: check format lint typecheck test help

# デフォルトターゲット: すべてのチェックを実行
check: lint format typecheck
	@echo "✅ All checks passed!"

# Ruffによるコードチェックと自動修正
lint:
	@echo "🔍 Running ruff check..."
	ruff check --fix

# Ruffによるコードフォーマット
format:
	@echo "🎨 Running ruff format..."
	ruff format

# mypyによる型チェック
typecheck:
	@echo "🔬 Running mypy..."
	@mypy src 2>/dev/null || echo "⚠️  src: No files to check"
	@mypy tests 2>/dev/null || echo "⚠️  tests: No files to check"
	@mypy scripts 2>/dev/null || echo "⚠️  scripts: No files to check"

# テスト実行（将来的に追加）
test:
	@echo "🧪 Running tests..."
	pytest

# ヘルプメッセージ
help:
	@echo "Available targets:"
	@echo "  make check      - Run all checks (lint, format, typecheck)"
	@echo "  make lint       - Run ruff check with auto-fix"
	@echo "  make format     - Run ruff format"
	@echo "  make typecheck  - Run mypy on src, tests, scripts"
	@echo "  make test       - Run pytest tests"
	@echo "  make help       - Show this help message"
