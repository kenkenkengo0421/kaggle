import subprocess
import io
from pathlib import Path
import pandas as pd
import time


def compe_discussion_load(slug, max_pages):
    """
    slug:      コンペの名前
    max_pages: 取得したい最大ページ数
    """
    all_topics = []
    for page in range(1, max_pages + 1):
        print(f"トピック一覧を取得中... ({page} / {max_pages} ページ目)")

        result = subprocess.run(
            ["kaggle", "competitions", "topics", "list", slug, "--csv", "--page", str(page)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:        
            print(f"{page}ページの取得に失敗したか、データがありません。終了します。")
            break

        try:
            csv_text = "id,title," + result.stdout.split("id,title,", 1)[1]
            df_page = pd.read_csv(io.StringIO(csv_text))
            df_page['id'] = pd.to_numeric(df_page['id'], errors='coerce')
            df_page = df_page.dropna(subset=['id']).astype({'id': 'int64'})
        
            if df_page.empty:
                break
            
            all_topics.append(df_page)
        except Exception as e:
            print(f"{page}ページの解析中にスキップ可能なエラーが発生しました: {e}")
            break
        
        time.sleep(1)

    if not all_topics:
        raise RuntimeError("トピックが1件も取得できませんでした。")
    
    discussion_topics = pd.concat(all_topics, ignore_index=True)
    print(f"合計 {len(discussion_topics)} 件のトピックを処理します。\n")

    sections = []

    for topic in discussion_topics.itertuples(index=False):
        response = subprocess.run(
            ["kaggle", "competitions", "topics", "show", f"{slug}/{topic.id}"],
            capture_output=True,
            text=True,
        )

        if response.returncode != 0:
            raise RuntimeError(f"取得失敗: {topic.id}\n{response.stdout}\n{response.stderr}")

        sections.append(
            f"{'=' * 80}\n"
            f"{topic.title}\n"
            f"https://kaggle.com{slug}/discussion/{topic.id}\n\n"
            f"{response.stdout}"
        )
        print(f"取得完了: {topic.title}")
        time.sleep(0.5)

    root_dir = Path(__file__).resolve().parent.parent
    output = root_dir / "discussion" / "discussions.txt"    
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n".join(sections), encoding="utf-8")
    print(f"\n保存完了: {output}（合計 {len(sections)} トピック）")
