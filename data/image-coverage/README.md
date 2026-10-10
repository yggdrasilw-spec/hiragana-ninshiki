# 動作語・抽象語の画像点検（2026-10-10）

全6,191語をID（CSVのヘッダーを除く行番号）で照合し、動作・心情・性質・関係・制度・時間・位置・数量などを対象に画像を追加しました。自然現象と従来の画像候補一覧に残っていた語も点検しました。固有名や生物・物体など、今回の範囲外の語は記録上区別しています。

`review-2026-10-10.json` に各語の語義、対象理由、画像参照、追加・再利用・既存の区分を保存しています。語義が一致する語は画像を共有します。語義・読み・難易度・既存画像は変更していません。

AI生成画像は16語ずつの4×4シートから256×256 PNGへ切り出し、全コマの配置と意味を目視確認しました。意味がずれたコマは再生成し、元シートと修正シートの双方を保存しています。原シートは `assets/shiritori/sheets/`、生成プロンプトと修正記録は `prompts-2026-10-10.json`、各PNGの由来と共有先は `assets/shiritori/manifest.json` にあります。

数・割合・図形・力の向きなどはPillowで正確な図を作り、目視確認して登録しました。再作成は次のコマンドで行えます（PythonとPillowが必要です）。

```powershell
python scripts/build-shiritori-concept-diagrams.py --output tmp/concept-diagrams --preview-dir tmp/concept-diagram-previews
python scripts/audit-shiritori-image-coverage.py
node tests/shiritori-data.cjs
```

点検スクリプトは対象語の未設定、全画像参照のファイル存在、画像破損、登録の重複・孤立、256×256のサイズ、辞書と点検記録の不一致を検出します。辞書を変更した場合は点検記録も更新してください。
