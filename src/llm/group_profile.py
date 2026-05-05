import base64
import json
import logging
import mimetypes
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable

from src.llm.prompts import PROMPT_WITH_IMAGE

load_dotenv()

logger = logging.getLogger(__name__)


def format_peps_as_markdown(csv_path: Path, group_id: int) -> str:
    pep_group_df = pd.read_csv(csv_path)
    pep_df = pep_group_df[pep_group_df.group_id == group_id]
    pep_df = pep_df.sort_values(
        ["pagerank_group", "in-degree_group", "out-degree_group"], ascending=False
    )
    pep_df = pep_df.rename(
        columns={
            "pagerank_group": "PageRank",
            "in-degree_group": "in-degree",
            "out-degree_group": "out-degree",
        }
    )
    # LLMに渡すテキストを作る
    return pep_df.to_markdown(index=False)


def encode_image_as_data_url(image_path: str | Path) -> str:
    path = Path(image_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/png"

    with path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


class GroupProfile(BaseModel):
    group_name: str = Field(default_factory=str, description="短い名称")
    description: str = Field(default_factory=str, description="4〜5文程度の説明")

    def __str__(self) -> str:
        lines = []
        lines.append(self.group_name)
        lines.append("説明:")
        lines.append(self.description)
        return "\n".join(lines)


class BaseGroupProfileGenerator(ABC):
    """グループプロファイル生成の基底クラス"""

    def __init__(self, model_name: str, group_data_dir: Path):
        self.model_name = model_name
        self.group_data_dir = group_data_dir

    @abstractmethod
    def generate_single(self, group_id: int) -> GroupProfile:
        """単一グループのプロファイルを生成"""
        pass

    @traceable(name="generate_all_group_profiles")
    def generate_all(self) -> list[dict]:
        """全グループのプロファイルを生成"""
        peps_group_df = pd.read_csv(self.group_data_dir / "pep_group_metrics.csv")
        group_ids = peps_group_df.group_id.unique()
        total_groups = len(group_ids)
        logger.info(f"Processing {total_groups} groups")

        group_profiles = []
        for i, group_id in enumerate(group_ids):
            logger.info(f"[{i + 1}/{total_groups}] Processing group {group_id}")
            group_profile = self.generate_single(group_id)
            data_dict = {"group_id": group_id}
            data_dict.update(group_profile.model_dump())
            group_profiles.append(data_dict)
            logger.info(f"Completed group {group_id}: {group_profile.group_name}")
        return group_profiles

    def save_to_csv(self) -> None:
        """プロファイルをCSVに保存"""
        start_time = time.time()

        group_profiles = self.generate_all()
        group_profiles_df = pd.DataFrame(group_profiles)
        group_profiles_df.to_csv(
            self.group_data_dir / "group_profiles.csv", index=False
        )

        execution_time_seconds = round(time.time() - start_time, 1)

        # メタデータを保存
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": self.model_name,
            "execution_time_seconds": execution_time_seconds,
        }
        metadata_path = self.group_data_dir / "group_profiles_metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Metadata saved to {metadata_path}")


class SubgraphOnlyProfileGenerator(BaseGroupProfileGenerator):
    """サブグラフ画像のみを使用してプロファイルを生成"""

    def generate_single(self, group_id: int) -> GroupProfile:
        """単一グループのプロファイルを生成（サブグラフ画像のみ使用）"""
        path = self.group_data_dir / "pep_group_metrics.csv"
        pep_md_table = format_peps_as_markdown(path, group_id)

        subgraph_image_path = (
            self.group_data_dir / "subgraphs" / "images" / f"group_{group_id}.png"
        )
        data_url = encode_image_as_data_url(subgraph_image_path)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT_WITH_IMAGE),
                (
                    "human",
                    [
                        {
                            "type": "text",
                            "text": (
                                "PEP一覧:\n\n{pep_md_table}\n\n"
                                "このPEPグループの名前と説明を書いてください。\n"
                                "あわせて、添付したネットワーク図も参考にしてください。\n"
                                "出力形式:\n"
                                "group_name: ...\n"
                                "description: ...\n"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": "{data_url}"},
                        },
                    ],
                ),
            ]
        )
        llm = ChatOpenAI(model=self.model_name, temperature=0).with_structured_output(
            GroupProfile
        )
        chain = prompt | llm
        result = chain.invoke(
            {
                "pep_md_table": pep_md_table,
                "data_url": data_url,
            }
        )
        return cast(GroupProfile, result)
