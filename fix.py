import os
import re

dir_path = 'src/agents/collection'
for filename in os.listdir(dir_path):
    if not filename.endswith('.py') or filename == 'base.py':
        continue
    filepath = os.path.join(dir_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if uses retrieve_candidates
    if 'async def retrieve_candidates' not in content:
        continue
        
    # Replace single line
    old_block_single = r'''results = await self.vector_store.search\(query=query, collection=self.COLLECTION, top_k=top_k\)'''
    new_block_single = r'''query_embedding = await self.embedding_model.encode_query(query)
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=top_k,
            )'''
            
    content = re.sub(old_block_single, new_block_single, content)

    # Replace multi-line
    old_block_multi = r'''results = await self\.vector_store\.search\(\s*query=query,\s*collection=self\.COLLECTION,\s*top_k=top_k,?\s*\)'''
    content = re.sub(old_block_multi, new_block_single, content)
    
    # Remove swallowed exceptions in retrieve_candidates
    except_pattern = r'''except Exception:\n\s*return \[\]'''
    new_except = r'''except Exception as e:
            import logging
            logging.getLogger(self.__class__.__name__).error(f"Retrieval failed: {e}")
            return []'''
    content = re.sub(except_pattern, new_except, content)
    
    # Check if there is an empty except block in generate_answer
    llm_except_pattern = r'''except Exception:\n\s*pass'''
    llm_new_except = r'''except Exception as e:
                import logging
                logging.getLogger(self.__class__.__name__).error(f"LLM generation failed: {e}")
                pass'''
    content = re.sub(llm_except_pattern, llm_new_except, content)
    
    # Ensure they return if not self.embedding_model
    store_check1 = r'''if not self\.vector_store:\n\s*return \[\]'''
    new_store_check = r'''if not self.vector_store or getattr(self, "embedding_model", None) is None:
            import logging
            logging.getLogger(self.__class__.__name__).error("Missing vector_store or embedding_model")
            return []'''
    content = re.sub(store_check1, new_store_check, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
