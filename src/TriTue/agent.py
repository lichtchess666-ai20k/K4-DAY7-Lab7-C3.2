"""Retrieval-augmented agent for Tri Tue's Lab 7 solution."""

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Answer questions by grounding an injected LLM in retrieved chunks."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        return self.answer_from_results(question, results)

    def answer_from_results(self, question: str, results: list[dict]) -> str:
        """Answer from a caller-supplied retrieval set without searching again."""

        if results:
            context_parts = []
            for index, result in enumerate(results, start=1):
                metadata = result.get("metadata", {})
                source = metadata.get("source_url") or metadata.get("source") or "không rõ"
                context_parts.append(
                    f"[Ngữ cảnh {index} | nguồn: {source}]\n{result['content']}"
                )
            context = "\n\n".join(context_parts)
        else:
            context = "Không tìm thấy ngữ cảnh phù hợp trong kho tri thức."

        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức. "
            "Chỉ trả lời bằng thông tin có trong NGỮ CẢNH; không bịa thêm dữ kiện. "
            "Nếu ngữ cảnh không đủ, hãy nói rõ là không đủ thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI:\n{question}\n\n"
            "TRẢ LỜI: Hãy trả lời ngắn gọn bằng ngôn ngữ của câu hỏi."
        )
        return self.llm_fn(prompt)
