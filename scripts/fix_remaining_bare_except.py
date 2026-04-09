#!/usr/bin/env python3
"""Fix all remaining bare except: clauses in src/"""
from pathlib import Path
import re

FIXES = {
    'src/agents/tafsir_agent.py': [
        ('            except:\n                self.tafsir_retrieval = None',
         '            except Exception as e:\n                logger.warning("tafsir_agent.retrieval_failed", error=str(e))\n                self.tafsir_retrieval = None'),
        ('        except:\n            return passages[:300]',
         '        except Exception as e:\n            logger.warning("tafsir_agent.generation_failed", error=str(e))\n            return passages[:300]'),
        ('        except:\n            return "خطأ في التفسير."',
         '        except Exception as e:\n            logger.warning("tafsir_agent.error", error=str(e))\n            return "خطأ في التفسير."'),
    ],
    'src/api/middleware/error_handler.py': [
        ('    except:\n        pass',
         '    except Exception as e:\n        logger.warning("error_handler.safe_str_failed", error=str(e))\n        pass'),
    ],
    'src/knowledge/vector_store.py': [
        ('                except:\n                    pass',
         '                except Exception as e:\n                    logger.warning("vector_store.stats_failed", error=str(e))\n                    pass'),
    ],
    'src/api/routes/rag.py': [
        ('            except:\n                pass',
         '            except Exception as e:\n                logger.warning("rag_route.error", error=str(e))\n                pass'),
    ],
}

total = 0
for filepath, replacements in FIXES.items():
    p = Path(filepath)
    if not p.exists():
        print(f"⏭️  Not found: {filepath}")
        continue
    
    content = p.read_text(encoding='utf-8')
    original = content
    count = 0
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            count += 1
            print(f"  ✅ {filepath}: {old[:40]}...")
    
    if count > 0:
        p.write_text(content, encoding='utf-8')
        total += count
        print(f"✅ {filepath}: {count} fixes")

print(f"\n🎉 Total fixes: {total}")
