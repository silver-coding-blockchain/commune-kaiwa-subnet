from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, text):
        return self.model.encode(text)

    def similarity(self, text_embed_a, text_embed_b):
        return self.model.similarity(text_embed_a, text_embed_b).item()


if __name__ == "__main__":
    ebm = EmbeddingModel()
    a = ebm.embed("The weather is lovely today.")
    b = ebm.embed("It's so sunny outside!")
    c = ebm.embed("He drove to the stadium.")

    print("a,b", ebm.similarity(a, b))
    print("a,c", ebm.similarity(a, c))
    print("b,c", ebm.similarity(b, c))
