from chromadb import PersistentClient
from chromadb.utils import embedding_functions as ef

class Memory:
    def __init__(self):
        self.client = PersistentClient(path="../../memory")
        self.ef = ef.DefaultEmbeddingFunction()

        self.collections = {}

    def _get_collection(self, char_name):
        if char_name not in self.collections:
            self.collections[char_name] = self.client.get_or_create_collection(
                name=f'sonoro-{char_name}',
                embedding_function=self.ef
            )

        return self.collections[char_name]

    def add(self, char_name:str, ids:list[str], documents:list[str], metadatas: list[dict]) -> None:
        self._get_collection(char_name).add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    # for now don't have the delete option

    def react(self, char_name:str, text, tags=None, semantic_topk=5, tag_topk=5):
        # DIRECT MATCHES
        collection = self._get_collection(char_name)

        r = collection.query(
            query_texts=[text],
            n_results=semantic_topk,
            include=['distances', 'documents', 'metadatas']
        )

        res = {}
        for i, ds in zip(r['ids'][0], r['distances'][0]):
            res[i] = {
                'score': 1.0 - ds, # might be negative (for now, only for testing purposes)
                'reason': 'semantic'
            }

        # TAG MATCHES
        if tags is not None:
            c_tags = [
                {'tags': {'$contains': t}}
                for t in tags
            ]
            
            t_where = {
                '$or': c_tags
            } if len(c_tags) > 1 else c_tags[0]

            r_tags = collection.get(
                where=t_where,
                limit=tag_topk
            )

            for i in r_tags['ids']:
                if i in res:
                    res[i]['reason'] = 'semantic+tag'
                else:
                    res[i] = {
                        'score': 0.5,
                        'reason': 'tag'
                    }

        if len(res) == 0: return {}

        retrieved = collection.get(ids=list(res))

        return {
            'memories': retrieved['documents'],
            'tags': list(set(tag for m in retrieved['metadatas'] for tag in m['tags'] if tag != 'none'))
        }
