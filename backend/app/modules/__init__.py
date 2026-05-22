"""
機能モジュールパッケージ。

各サブパッケージ（auth / erp / master / …）は `__init__.py` で APIRouter を公開し、
`app.main` から `app.include_router(<module>.router, …)` で登録する。
"""
