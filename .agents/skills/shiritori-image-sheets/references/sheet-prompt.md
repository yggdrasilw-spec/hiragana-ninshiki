# 1枚16語の生成指示

以下の技術条件と、計画から作った16場面を1つのプロンプトにする。コマの意味を短い具体的場面で示す。テキストを絵に描かせない。絵の縮小率・白い余白率は追加しない。

```text
Create ONE square vocabulary illustration contact sheet with EXACTLY sixteen
separate illustrations in a strict 4 by 4 grid. Read the subjects row-major,
left to right, then top to bottom.

Draw FIVE perfectly straight continuous horizontal and FIVE vertical divider
lines INCLUDING THE OUTER FRAME, solid pure MAGENTA (#ff00ff), approximately
8px thick. Internal lines at 25%, 50%, 75% of width and height. Magenta is
reserved ONLY for divider lines and must not appear inside the illustrations.

Use each cell generously. No large blank margins are needed. Keep each complete
illustration, its scene and shadow entirely within its own cell. Nothing crosses
the divider lines or extends into a neighbouring cell. Do not shrink the subjects
to the central half of their panels. No captions, labels, letters, numbers,
watermarks or extra panels.

Warm watercolor children's picture-book style, clear recognizable shapes,
accurate subjects and normal anatomy. Each scene must match its assigned meaning.
The following sixteen scenes are in exact cell order:
```

この後に計画から `1. ...`〜`16. ...` を連結する。番号はプロンプトの順序指定だけで、画像には描かない。

罫線の修正依頼は対象シートを表示・確認してから画像編集ツールで行う。16語と順番、絵の内容を維持し、問題の罫線・越境だけを直す。余白の拡大を修正条件にしない。
