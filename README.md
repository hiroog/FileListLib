# File listing library

git のように ignorefile の指定が可能なファイルリストツールです。python 3.x が必要です。


## 目的

UE4 のように 100GB を超えるプロジェクトはチーム内で配布用に複製するにも時間がかかります。
高速なコピーツールはいくつかありますが、どんなに速くても限界はあります。
最も速いのは不要なファイルをコピーしないことです。
このツールは除外ファイルを指定しておくことで最小限のファイルコピーを行います。

また Perforce にも除外ファイルの指定はありますが、制限が多く git のような柔軟な記述ができません。ライブラリとして Perforce への import list の生成にも使用しています。



## 使用例

```
$ python3 FileTools.py --list
```

## 除外指定ファイル付きフォルダコピー

```
$ python3 FileTools.py src --copy dest
```

## 除外指定ファイル

ignorefile は default で `.flignore` になります。`--ignore` オプションで変更可能です。
git と同じようにサブフォルダへの配置も可能です。

ignorefile のフォーマットは Python の正規表現を使います。git/mercurial との互換性はありません。

sample_dir/.flignore や sample_dir/test/.flignore を参考にしてください。

```
#  \.bin$               末尾の拡張子のみ
#  [^/]+\.bin$          末尾の拡張子のみ、'.' で始まるケースを除く
#  ^/Intermediate/      .flignore がある場所の Intermediate folder のみ
#  /Build/BatchFiles/   .flignore がある場所から辿って Build/BatchFiles folder のみ
#  /ThirdParty/         .flignore がある場所以下の任意の ThirdParty folder にマッチ
#  ^/[^/]+\.sln$        .flignore がある場所直下の *.sln のみ
#  /workspace.mel$      任意の場所の "workspace.mel" のみ
#  -bkup.log$           任意の場所の "*-bkup.log" のみ
#
# フォルダ ".git" のみ
/\.git/
#
# フォルダ "__pycache__" のみ
/__pycache__/
#
# ファイル ".gitignore" のみ
/\.gitignore$
#
# ".bin" directory のみ除外 (file "*.bin" は含む)
/\.bin/
#
# extension "*.tmp" file のみ除外 (directory ".tmp" は含む)
\.tmp$
#
# file "c.file" のみ除外 (file "aaaac.file" は含む)
/c\.file$
#
# file "*d.file" をすべて除外
d\.file$
#
# "*e.file*" をすべて除外。ファイルもディレクトリも区別なし。
e\.file
#
# .flignore ファイルと同じ場所にある "f.data" ファイルのみ除外 (sample_dir/f.data は含む)
^/f\.data$
```

## 除外ファイルの使い分け

配布用のコピーは binary 含める、backup 用はソースコードのみにするなど、用途に応じて使い分けができます。

```
$ python3 FileTools.py --ignore .copy_ignore src --copy dest
```
```
$ python3 FileTools.py --ignore .backup_ignore src --copy dest
```
